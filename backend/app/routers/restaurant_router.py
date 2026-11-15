from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import require_role
from ..database import get_db
from ..models import MenuItem, Restaurant, User
from ..schemas import MenuItemCreate, MenuItemUpdate

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants & Menus"])


@router.get("/")
def list_restaurants(db: Session = Depends(get_db)):
    return db.query(Restaurant).all()


@router.get("/my-restaurant")
def get_owner_restaurant(
    current_user: User = Depends(require_role("OWNER")),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/{restaurant_id}/menu")
def get_menu(
    restaurant_id: int,
    search: Optional[str] = None,
    max_price: Optional[float] = Query(None, gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id)
    if search:
        query = query.filter(MenuItem.name.ilike(f"%{search}%"))
    if max_price is not None:
        query = query.filter(MenuItem.price <= max_price)
    return query.all()


@router.post("/menu", status_code=201)
def add_menu_item(
    payload: MenuItemCreate,
    current_user: User = Depends(require_role("OWNER")),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    item = MenuItem(restaurant_id=restaurant.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/menu/{item_id}")
def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    current_user: User = Depends(require_role("OWNER")),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found or unauthorized")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item
