# Laundry Order Management System (Mini OMS)

A small **FastAPI** service for a dry cleaner: create orders, track status, compute bills, and view dashboard stats. Orders are stored in **SQLite** at `data/oms.db` (survives restarts). Delete that file to reset all data.

**Repository:** https://github.com/Khushbusaifi012/Laundry-Order-Management-System

## Setup

**Requirements:** Python 3.10.

```bash
cd "path/to/OMS"
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Run the API** (from the folder that contains the `app` package):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Web UI:** http://127.0.0.1:8000/
- **Swagger:** http://127.0.0.1:8000/docs
- **Health:** http://127.0.0.1:8000/health

Use **http://127.0.0.1** in the browser (not `http://0.0.0.0`). If port **8000** is busy (e.g. WinError 10013), try `--port 18080` and open the matching URL.

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/orders` | Create order → returns `id`, `total`, `status` = `RECEIVED` |
| `PATCH` | `/orders/{order_id}/status` | Update status |
| `GET` | `/orders` | List orders; query: `status`, `customer_name`, `phone`, `garment` |
| `GET` | `/orders/{order_id}` | Get one order |
| `DELETE` | `/orders/{order_id}` | Remove order (**204**); **404** if missing |
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

Omit `estimated_delivery_date` to default to **3 calendar days** after order time (UTC).

### Example: update status

```json
PATCH /orders/ORD-XXXXXXXXXX/status
{ "status": "PROCESSING" }
```

Allowed: `RECEIVED`, `PROCESSING`, `READY`, `DELIVERED`.

### Example: filter orders

- `GET /orders?status=READY`
- `GET /orders?customer_name=Asha`
- `GET /orders?phone=98765`
- `GET /orders?garment=Saree`

## Features implemented

- Create order (line items, qty, unit price) → **total** + **unique order ID**
- Status: **RECEIVED → PROCESSING → READY → DELIVERED** + **PATCH** to update
- List + filter: **status**, **customer name**, **phone**
- **DELETE** order by id
- **Dashboard:** total orders, revenue, counts per status
- **SQLite** persistence (`data/oms.db`)
- **Bonus:** garment filter, estimated delivery (optional + default + year validation)
- **Frontend:** single HTML page at `/`
- **Postman:** `postman_collection.json`

## Project structure

```
OMS/
  app/
    __init__.py
    main.py
    models.py
    store.py
  data/              # oms.db (gitignored)
  static/
    index.html
  requirements.txt
  postman_collection.json
  README.md
```
