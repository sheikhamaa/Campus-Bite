from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = Field(..., pattern="^(CUSTOMER|OWNER|DELIVERY)$")
    address: Optional[str] = None
    restaurant_name: Optional[str] = None
    restaurant_location: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: Optional[str] = "General"
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    is_available: Optional[bool] = None


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    restaurant_id: int
    delivery_address: str
    items: List[OrderItemCreate]


class OrderStatusUpdate(BaseModel):
    status: str


class AssignDeliveryPartner(BaseModel):
    delivery_partner_id: int


class RefundRequestCreate(BaseModel):
    reason: str = Field(..., min_length=5)


class RefundDecision(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class AIInsightQuery(BaseModel):
    question: str = Field(..., min_length=3)
