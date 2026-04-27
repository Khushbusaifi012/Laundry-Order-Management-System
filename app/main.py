from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import CreateOrderRequest, Order, OrderStatus, UpdateStatusRequest
from app.store import OrderStore

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Laundry Order Management System",
    description="Mini OMS for dry cleaning: orders, status, billing, dashboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = OrderStore()


@app.get("/")
def serve_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/orders", response_model=Order, status_code=201)
def create_order(body: CreateOrderRequest) -> Order:
    order = Order.from_request(body)
    return store.add(order)


@app.patch("/orders/{order_id}/status", response_model=Order)
def update_order_status(order_id: str, body: UpdateStatusRequest) -> Order:
    updated = store.update_status(order_id, body.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated


@app.get("/orders", response_model=List[Order])
def list_orders(
    status: Optional[OrderStatus] = Query(default=None),
    customer_name: Optional[str] = Query(default=None),
    phone: Optional[str] = Query(default=None),
    garment: Optional[str] = Query(
        default=None,
        description="Bonus: filter orders containing this garment type",
    ),
) -> List[Order]:
    return store.list_filtered(
        status=status,
        customer_name=customer_name,
        phone=phone,
        garment=garment,
    )


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    order = store.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.delete(
    "/orders/{order_id}",
    status_code=204,
    summary="Delete order",
    response_description="Order removed (no body).",
    responses={404: {"description": "Order not found"}},
)
def delete_order(order_id: str) -> None:
    if not store.delete(order_id):
        raise HTTPException(status_code=404, detail="Order not found")


@app.get("/dashboard")
def dashboard() -> dict:
    return store.dashboard_stats()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
