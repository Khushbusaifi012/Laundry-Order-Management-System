import sqlite3
from pathlib import Path
from typing import List, Optional

from app.models import Order, OrderStatus

_DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "oms.db"


def _filter_orders(
    orders: List[Order],
    status: Optional[OrderStatus] = None,
    customer_name: Optional[str] = None,
    phone: Optional[str] = None,
    garment: Optional[str] = None,
) -> List[Order]:
    result = list(orders)
    if status is not None:
        result = [o for o in result if o.status == status]
    if customer_name:
        q = customer_name.strip().lower()
        result = [o for o in result if q in o.customer_name.lower()]
    if phone:
        q = phone.strip()
        result = [o for o in result if q in o.phone]
    if garment:
        q = garment.strip().lower()
        result = [
            o
            for o in result
            if any(q in line.garment.lower() for line in o.items)
        ]
    result.sort(key=lambda o: o.created_at, reverse=True)
    return result


def _dashboard(orders: List[Order]) -> dict:
    revenue = sum(o.total for o in orders)
    per_status = {s.value: 0 for s in OrderStatus}
    for o in orders:
        per_status[o.status.value] = per_status.get(o.status.value, 0) + 1
    return {
        "total_orders": len(orders),
        "total_revenue": round(revenue, 2),
        "orders_per_status": per_status,
    }


class OrderStore:
    """Persists orders in SQLite at data/oms.db."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._path = db_path or _DEFAULT_DB
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )

    def _all_orders(self) -> List[Order]:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute("SELECT data FROM orders")
            rows = cur.fetchall()
        return [Order.model_validate_json(row[0]) for row in rows]

    def add(self, order: Order) -> Order:
        payload = order.model_dump_json()
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "INSERT INTO orders (id, data) VALUES (?, ?)",
                (order.id, payload),
            )
        return order

    def get(self, order_id: str) -> Optional[Order]:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute("SELECT data FROM orders WHERE id = ?", (order_id,))
            row = cur.fetchone()
        if row is None:
            return None
        return Order.model_validate_json(row[0])

    def update_status(self, order_id: str, status: OrderStatus) -> Optional[Order]:
        order = self.get(order_id)
        if order is None:
            return None
        updated = order.model_copy(update={"status": status})
        payload = updated.model_dump_json()
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "UPDATE orders SET data = ? WHERE id = ?",
                (payload, order_id),
            )
        return updated

    def delete(self, order_id: str) -> bool:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            return cur.rowcount > 0

    def list_filtered(
        self,
        status: Optional[OrderStatus] = None,
        customer_name: Optional[str] = None,
        phone: Optional[str] = None,
        garment: Optional[str] = None,
    ) -> List[Order]:
        return _filter_orders(
            self._all_orders(),
            status=status,
            customer_name=customer_name,
            phone=phone,
            garment=garment,
        )

    def dashboard_stats(self) -> dict:
        return _dashboard(self._all_orders())
