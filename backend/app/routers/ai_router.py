import os

from fastapi import APIRouter, Depends, HTTPException
from openai import APIError, OpenAI, RateLimitError
from sqlalchemy.orm import Session, joinedload

from ..auth import require_role
from ..database import get_db
from ..models import Order, OrderItem, User
from ..schemas import AIInsightQuery

router = APIRouter(prefix="/api/ai", tags=["AI Order Insights"])


@router.post("/insights")
def get_order_insights(
    payload: AIInsightQuery,
    current_user: User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        raise HTTPException(status_code=503, detail="OpenAI API key is not configured on the server.")

    orders = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.menu_item),
        joinedload(Order.restaurant),
    ).filter(Order.customer_id == current_user.id).order_by(Order.created_at.desc()).all()

    if not orders:
        return {
            "answer": "You haven't placed any orders yet! Once you place orders, I can analyze your spending, favorite dishes, and order statuses."
        }

    order_context_lines = []
    for order in orders:
        items_str = ", ".join(
            f"{item.quantity}x {item.menu_item.name if item.menu_item else 'Dish'} (${item.unit_price})"
            for item in order.items
        )
        order_context_lines.append(
            f"- Order #{order.id} | Restaurant: {order.restaurant.name if order.restaurant else 'Unknown'} | "
            f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')} | Status: {order.status} | "
            f"Payment: {order.payment_status} | Total: ${order.total_amount} | Items: [{items_str}]"
        )

    context_text = "\n".join(order_context_lines)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are CampusBite AI. Use the customer's order history only to answer the question. Keep answers concise but helpful.",
                },
                {
                    "role": "user",
                    "content": f"Customer order history:\n{context_text}\n\nQuestion: {payload.question}",
                },
            ],
            temperature=0.4,
            max_tokens=250,
        )
        answer = response.choices[0].message.content.strip()
        return {"answer": answer}
    except (RateLimitError, APIError) as exc:
        raise HTTPException(status_code=503, detail=f"AI service temporarily unavailable: {exc}") from exc
