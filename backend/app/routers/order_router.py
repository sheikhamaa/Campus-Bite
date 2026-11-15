from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import AdminReminderLog, MenuItem, Order, OrderItem, PaymentLedger, Restaurant, Review, User
from ..schemas import (
    AssignDeliveryPartner,
    OrderCreate,
    OrderStatusUpdate,
    RefundDecision,
    RefundRequestCreate,
    ReviewCreate,
)

router = APIRouter(prefix="/api/orders", tags=["Orders, Payments & Reviews"])

OWNER_TRANSITIONS = {
    "PLACED": ["ACCEPTED", "CANCELLED"],
    "ACCEPTED": ["PREPARING"],
    "PREPARING": ["READY"],
}

DELIVERY_TRANSITIONS = {
    "ASSIGNED": ["OUT_FOR_DELIVERY"],
    "OUT_FOR_DELIVERY": ["DELIVERED"],
}


@router.post("/", status_code=201)
def place_order(
    payload: OrderCreate,
    current_user: User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    total = 0.0
    order_items = []
    for item_in in payload.items:
        menu_item = db.query(MenuItem).filter(
            MenuItem.id == item_in.menu_item_id,
            MenuItem.restaurant_id == payload.restaurant_id,
        ).first()
        if not menu_item or not menu_item.is_available:
            raise HTTPException(status_code=400, detail=f"Item ID {item_in.menu_item_id} is unavailable")

        line_total = menu_item.price * item_in.quantity
        total += line_total
        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                quantity=item_in.quantity,
                unit_price=menu_item.price,
            )
        )

    order = Order(
        customer_id=current_user.id,
        restaurant_id=payload.restaurant_id,
        status="PLACED",
        payment_status="mock_paid",
        total_amount=round(total, 2),
        delivery_address=payload.delivery_address,
        items=order_items,
    )
    db.add(order)
    db.flush()

    payment = PaymentLedger(
        order_id=order.id,
        transaction_type="PAYMENT",
        amount=order.total_amount,
        status="mock_paid",
    )
    db.add(payment)
    db.commit()
    db.refresh(order)
    return {"message": "Order placed and mock_paid", "order_id": order.id, "total_amount": order.total_amount}


@router.get("/")
def list_orders(
    status: Optional[str] = None,
    order_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.menu_item),
        joinedload(Order.restaurant),
        joinedload(Order.review),
    )

    if current_user.role == "CUSTOMER":
        query = query.filter(Order.customer_id == current_user.id)
    elif current_user.role == "OWNER":
        restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
        if not restaurant:
            return {"items": [], "total": 0, "page": page, "limit": limit}
        query = query.filter(Order.restaurant_id == restaurant.id)
    elif current_user.role == "DELIVERY":
        query = query.filter(Order.delivery_partner_id == current_user.id)

    if status:
        query = query.filter(Order.status == status)
    if order_date:
        query = query.filter(func.date(Order.created_at) == order_date)

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    results = []
    for order in orders:
        results.append(
            {
                "id": order.id,
                "restaurant_name": order.restaurant.name if order.restaurant else None,
                "customer_id": order.customer_id,
                "delivery_partner_id": order.delivery_partner_id,
                "delivery_address": order.delivery_address,
                "status": order.status,
                "payment_status": order.payment_status,
                "return_status": order.return_status,
                "return_reason": order.return_reason,
                "total_amount": order.total_amount,
                "created_at": order.created_at,
                "review": {"rating": order.review.rating, "comment": order.review.comment} if order.review else None,
                "items": [
                    {
                        "name": item.menu_item.name if item.menu_item else "Item",
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                    }
                    for item in order.items
                ],
            }
        )
    return {"items": results, "total": total, "page": page, "limit": limit}


@router.patch("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    current_user: User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "PLACED":
        raise HTTPException(status_code=400, detail="Orders can only be cancelled while in PLACED status")

    order.status = "CANCELLED"
    db.commit()
    return {"message": "Order cancelled successfully", "status": order.status}


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: User = Depends(require_role("OWNER", "DELIVERY")),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = payload.status
    if current_user.role == "OWNER":
        restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
        if not restaurant or order.restaurant_id != restaurant.id:
            raise HTTPException(status_code=403, detail="Not authorized for this order")
        allowed = OWNER_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid transition from {order.status} to {new_status}")
    elif current_user.role == "DELIVERY":
        if order.delivery_partner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Order not assigned to you")
        allowed = DELIVERY_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid transition from {order.status} to {new_status}")

    order.status = new_status
    db.commit()
    return {"message": f"Order status updated to {new_status}", "status": order.status}


@router.get("/delivery-partners")
def list_delivery_partners(
    current_user: User = Depends(require_role("OWNER")),
    db: Session = Depends(get_db),
):
    partners = db.query(User).filter(User.role == "DELIVERY").all()
    return [{"id": partner.id, "name": partner.name, "email": partner.email} for partner in partners]


@router.patch("/{order_id}/assign")
def assign_delivery_partner(
    order_id: int,
    payload: AssignDeliveryPartner,
    current_user: User = Depends(require_role("OWNER")),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    order = db.query(Order).filter(Order.id == order_id, Order.restaurant_id == restaurant.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "READY":
        raise HTTPException(status_code=400, detail="Delivery partner can only be assigned when order is READY")

    partner = db.query(User).filter(User.id == payload.delivery_partner_id, User.role == "DELIVERY").first()
    if not partner:
        raise HTTPException(status_code=404, detail="Delivery partner not found")

    order.delivery_partner_id = partner.id
    order.status = "ASSIGNED"
    db.commit()
    return {"message": f"Assigned to {partner.name}", "status": order.status}


@router.post("/{order_id}/refund-request")
def request_refund(
    order_id: int,
    payload: RefundRequestCreate,
    current_user: User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "DELIVERED":
        raise HTTPException(status_code=400, detail="Refunds can only be requested for DELIVERED orders")
    if order.return_status != "NONE":
        raise HTTPException(status_code=400, detail="A return/refund request has already been submitted for this order")

    order.return_status = "REQUESTED"
    order.return_reason = payload.reason
    db.commit()
    return {"message": "Return/refund request submitted", "return_status": order.return_status}


@router.patch("/{order_id}/refund-decision")
def decide_refund(
    order_id: int,
    payload: RefundDecision,
    current_user: User = Depends(require_role("OWNER")),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    order = db.query(Order).filter(Order.id == order_id, Order.restaurant_id == restaurant.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.return_status != "REQUESTED":
        raise HTTPException(status_code=400, detail="No pending refund request for this order")

    if payload.decision == "APPROVED":
        order.return_status = "APPROVED"
        order.payment_status = "refunded"
        order.status = "REFUNDED"
        refund_entry = PaymentLedger(
            order_id=order.id,
            transaction_type="REFUND",
            amount=order.total_amount,
            status="refunded",
        )
        db.add(refund_entry)
    else:
        order.return_status = "REJECTED"

    db.commit()
    return {"message": f"Refund {payload.decision.lower()}", "payment_status": order.payment_status}


@router.post("/{order_id}/review", status_code=201)
def submit_review(
    order_id: int,
    payload: ReviewCreate,
    current_user: User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "DELIVERED":
        raise HTTPException(status_code=400, detail="Reviews can only be submitted after delivery")
    if order.review:
        raise HTTPException(status_code=400, detail="Review already submitted for this order")

    review = Review(
        order_id=order.id,
        customer_id=current_user.id,
        restaurant_id=order.restaurant_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    return {"message": "Review submitted successfully"}


@router.get("/owner/stats-and-reminders")
def owner_stats_and_reminders(
    current_user: User = Depends(require_role("OWNER")),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    orders = db.query(Order).filter(Order.restaurant_id == restaurant.id).all()
    total_orders = len(orders)
    delivered_orders = sum(1 for order in orders if order.status == "DELIVERED")
    revenue = sum(order.total_amount for order in orders if order.payment_status == "mock_paid")

    reminders = db.query(AdminReminderLog).filter(
        AdminReminderLog.restaurant_id == restaurant.id
    ).order_by(AdminReminderLog.created_at.desc()).limit(20).all()

    return {
        "stats": {
            "total_orders": total_orders,
            "delivered_orders": delivered_orders,
            "total_revenue": round(revenue, 2),
        },
        "reminders": [
            {
                "id": reminder.id,
                "order_id": reminder.order_id,
                "message": reminder.message,
                "created_at": reminder.created_at,
            }
            for reminder in reminders
        ],
    }
