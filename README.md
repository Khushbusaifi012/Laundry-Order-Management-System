# Laundry Order Management System (Mini OMS)

A small **FastAPI** service for a dry cleaner: create orders, track status, compute bills, and view dashboard stats. Orders are saved in **SQLite** at `data/oms.db` (created automatically) so they **survive server restarts**. To wipe all data, delete that file while the server is stopped.

## Setup

**Requirements:** Python 3.10+ recommended (3.9+ should work).

```bash
cd "path/to/OMS"
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Run the API:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Web UI:** http://127.0.0.1:8000/ — dashboard, create order, filter orders, change status  
- **Interactive docs (Swagger):** http://127.0.0.1:8000/docs  
- **Health check:** http://127.0.0.1:8000/health  

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/orders` | Create order → returns `id`, `total`, `status` = `RECEIVED` |
| `PATCH` | `/orders/{order_id}/status` | Update status |
| `GET` | `/orders` | List orders; query: `status`, `customer_name`, `phone`, `garment` |
| `GET` | `/orders/{order_id}` | Get one order |
| `DELETE` | `/orders/{order_id}` | Remove order (**204** empty body); **404** if missing |
| `GET` | `/dashboard` | Totals: orders count, revenue, counts per status |

### Example: create order

```json
POST /orders
{
  "customer_name": "Asha Verma",
  "phone": "+91-9876501234",
  "items": [
    { "garment": "Shirt", "quantity": 3, "unit_price": 80 },
    { "garment": "Saree", "quantity": 1, "unit_price": 350 }
  ],
  "estimated_delivery_date": "2026-04-30"
}
```

Omit `estimated_delivery_date` to default to **3 calendar days** after the order time (UTC). Response includes `id` (e.g. `ORD-…`), `total` (590 for the example above), `status`, and `estimated_delivery_date`.

### Example: update status

```json
PATCH /orders/ORD-XXXXXXXXXX/status
{ "status": "PROCESSING" }
```

Allowed values: `RECEIVED`, `PROCESSING`, `READY`, `DELIVERED`.

### Example: filter orders

- `GET /orders?status=READY`
- `GET /orders?customer_name=Asha`
- `GET /orders?phone=98765`
- `GET /orders?garment=Saree` (bonus filter)

## Features implemented

- Create order with line items, quantities, and unit prices; **total bill** and **unique order ID**
- Status workflow: **RECEIVED → PROCESSING → READY → DELIVERED** (any valid value accepted on update; no forced transitions)
- List orders with filters: **status**, **customer name**, **phone**
- **Delete order** by id (`DELETE /orders/{order_id}`)
- **Dashboard:** total orders, total revenue, orders per status
- **SQLite** (`data/oms.db`): orders persist across **restarts** and **`--reload`**
- **Bonus:** filter by **garment** substring on line items; **estimated delivery date** on create (optional, default +3 days)
- **Simple frontend:** single-page UI at `/` (no React build step)
- **Postman:** import `postman_collection.json` (optional)

## AI usage report

*Personalize this section for your submission. Below is a honest template.*

| Tool | How you used it |
|------|------------------|
| *(e.g. ChatGPT / Cursor / Copilot)* | Scaffolding FastAPI routes, Pydantic models, README structure |

**Sample prompts you might have used:**

1. *“Generate a FastAPI app with in-memory order store: POST create order with items and computed total, PATCH status enum, GET list with query filters, GET dashboard aggregates.”*
2. *“Review this Python code for edge cases: empty items, negative quantity, invalid status.”*

**What AI got wrong or oversimplified (examples to document):**

- Suggested overly complex repository layers — **removed** to stay minimal.
- May confuse Pydantic v1 vs v2 syntax — **verified** against installed `pydantic` version.

**What you improved manually:**

- Chose explicit `OrderStatus` enum and 404 handling for missing orders.
- Added CORS so a simple HTML/JS UI or Postman can call the API easily.
- Added optional `garment` filter for the assignment bonus.

## Tradeoffs

**Skipped (time / scope):**

- MongoDB / hosted SQL — local **SQLite** is used instead (`data/oms.db`).
- Authentication.
- Separate React SPA (current UI is one `index.html` served by FastAPI).
- Deployment — can add Render/Railway later by pinning `requirements.txt` and running `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

**With more time:**

- PostgreSQL / hosted DB for multi-server deployments.
- Simple JWT or API key for staff-only endpoints.
- Estimated delivery date field and `GET` filter by date.

## Project structure

```
OMS/
  app/
    __init__.py
    main.py      # FastAPI routes + serves UI at /
    models.py    # Pydantic models + Order builder
    store.py     # SQLite persistence + list/filter/dashboard
  data/          # oms.db created at runtime (gitignored)
  static/
    index.html   # Simple frontend (vanilla HTML/CSS/JS)
  requirements.txt
  postman_collection.json
  README.md
```

## License

MIT (or replace with your preference for the assignment repo).
