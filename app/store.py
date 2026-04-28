import os
import sqlite3
from pathlib import Path
from typing import List, Optional

import psycopg

from app.models import Order, OrderStatus

_DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "oms.db"


def _resolved_db_path() -> Path:
    """Use OMS_DB_PATH on hosts with a persistent disk. Default: ./data/oms.db."""
    raw = os.environ.get("OMS_DB_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _DEFAULT_DB


def _postgres_dsn() -> Optional[str]:
    """Use Postgres only for postgresql:// URLs (Render). Ignore sqlite:// etc."""
    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        return None
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql://", 1)
    if not raw.startswith("postgresql://"):
        return None
    return raw


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
    """Persists orders: PostgreSQL when DATABASE_URL is set, else SQLite (data/oms.db)."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._pg_dsn = _postgres_dsn()
        if self._pg_dsn:
            self._sqlite_path = None
            self._init_postgres()
        else:
            self._sqlite_path = db_path or _resolved_db_path()
            self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        with sqlite3.connect(self._sqlite_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )

    def _init_postgres(self) -> None:
        with psycopg.connect(self._pg_dsn) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )

    def _all_orders(self) -> List[Order]:
        if self._pg_dsn:
            with psycopg.connect(self._pg_dsn) as conn:
                cur = conn.execute("SELECT data FROM orders")
                rows = cur.fetchall()
        else:
            with sqlite3.connect(self._sqlite_path) as conn:
                cur = conn.execute("SELECT data FROM orders")
                rows = cur.fetchall()
        return [Order.model_validate_json(row[0]) for row in rows]

    def add(self, order: Order) -> Order:
        payload = order.model_dump_json()
        if self._pg_dsn:
            with psycopg.connect(self._pg_dsn) as conn:
                conn.execute(
                    "INSERT INTO orders (id, data) VALUES (%s, %s)",
                    (order.id, payload),
                )
        else:
            with sqlite3.connect(self._sqlite_path) as conn:
                conn.execute(
                    "INSERT INTO orders (id, data) VALUES (?, ?)",
                    (order.id, payload),
                )
        return order

    def get(self, order_id: str) -> Optional[Order]:
        if self._pg_dsn:
            with psycopg.connect(self._pg_dsn) as conn:
                cur = conn.execute(
                    "SELECT data FROM orders WHERE id = %s", (order_id,)
                )
                row = cur.fetchone()
        else:
            with sqlite3.connect(self._sqlite_path) as conn:
                cur = conn.execute(
                    "SELECT data FROM orders WHERE id = ?", (order_id,)
                )
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
        if self._pg_dsn:
            with psycopg.connect(self._pg_dsn) as conn:
                conn.execute(
                    "UPDATE orders SET data = %s WHERE id = %s",
                    (payload, order_id),
                )
        else:
            with sqlite3.connect(self._sqlite_path) as conn:
                conn.execute(
                    "UPDATE orders SET data = ? WHERE id = ?",
                    (payload, order_id),
                )
        return updated

    def delete(self, order_id: str) -> bool:
        if self._pg_dsn:
            with psycopg.connect(self._pg_dsn) as conn:
                cur = conn.execute(
                    "DELETE FROM orders WHERE id = %s", (order_id,)
                )
                return cur.rowcount > 0
        with sqlite3.connect(self._sqlite_path) as conn:
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
