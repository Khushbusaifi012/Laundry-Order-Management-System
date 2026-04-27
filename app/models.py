from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class OrderStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    DELIVERED = "DELIVERED"


class GarmentLine(BaseModel):
    garment: str = Field(..., min_length=1, examples=["Shirt"])
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0, description="Price per item")


class CreateOrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=3)
    items: List[GarmentLine] = Field(..., min_length=1)
    estimated_delivery_date: Optional[date] = Field(
        default=None,
        description="Optional; defaults to 3 days from order creation if omitted",
    )

    @field_validator("estimated_delivery_date")
    @classmethod
    def delivery_must_be_modern_year(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v.year < 2000:
            raise ValueError(
                "estimated_delivery_date must be a real calendar year (e.g. 2026), not 0026"
            )
        return v


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


class Order(BaseModel):
    id: str
    customer_name: str
    phone: str
    items: List[GarmentLine]
    total: float
    status: OrderStatus
    created_at: datetime
    estimated_delivery_date: date

    @staticmethod
    def from_request(req: CreateOrderRequest) -> "Order":
        total = sum(line.quantity * line.unit_price for line in req.items)
        created = datetime.utcnow()
        delivery = req.estimated_delivery_date
        if delivery is None:
            delivery = (created + timedelta(days=3)).date()
        return Order(
            id=f"ORD-{uuid4().hex[:10].upper()}",
            customer_name=req.customer_name.strip(),
            phone=req.phone.strip(),
            items=req.items,
            total=round(total, 2),
            status=OrderStatus.RECEIVED,
            created_at=created,
            estimated_delivery_date=delivery,
        )
