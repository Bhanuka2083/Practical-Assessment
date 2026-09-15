# Live Link

https://practical-assessment-seven-sepia.vercel.app/
https://practical-assessment-seven-sepia.vercel.app/

# POS Inventory & Order Management System

A production-ready, full-stack Point of Sale (POS) and inventory tracking platform built with FastAPI, React (TypeScript), PostgreSQL, and Docker Compose. Designed with atomic stock deductions, automated schema migrations, and enterprise-grade container lifecycle management.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Client / Admin Browser   |
                      +--------------+--------------+
                                     |
                                     v
                       [Port 80] Nginx Gateway
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
    Frontend (React + Vite)                         Backend (FastAPI)
    - POS Checkout & Cart Register                 - REST API (/api/v1)
    - Admin Inventory Dashboard                    - JWT Auth & RBAC
    - Real-time Stock Alerts                       - Stock Deduction Logic
             |                                               |
             +-----------------------+-----------------------+
                                     |
                                     v
                       PostgreSQL 16 (Relational DB)
                       - Normalized Transactions
                       - Isolated Named Volume Storage

```

---

## Tech Stack

| Layer             | Technology                    | Key Capabilities                                         |
| ----------------- | ----------------------------- | -------------------------------------------------------- |
| **Backend**       | Python 3.12, FastAPI, Uvicorn | Async I/O, Pydantic v2 schemas, SQLAlchemy 2.0 Async ORM |
| **Frontend**      | React 18, TypeScript, Vite    | Tailwind CSS, Lucide Icons, Axios API layer              |
| **Database**      | PostgreSQL 16 Alpine          | Acid transactions, row-level locks on checkout           |
| **Reverse Proxy** | Nginx Alpine                  | Client routing, static caching, API reverse-proxying     |
| **DevOps**        | Docker, Docker Compose        | Multi-stage builds, automated seeding, healthchecks      |

---

## Key Features

- **Real-time Inventory Tracking**: Dynamic `available_stock` calculation using SQLAlchemy hybrid properties (`stock - reserved_stock`).
- **Interactive Admin Management**: Real-time CRUD operations, price updating, low-stock threshold monitoring, and manual stock reconciliation.
- **Resilient Container Lifecycle**: Custom `entrypoint.sh` with automated connection polling to ensure PostgreSQL is fully initialized before database seeding and server launch.
- **Secured Documentation & Endpoints**: API routes mounted under `/api/v1`. Interactive Swagger (`/docs`), ReDoc (`/redoc`), and OpenAPI specifications are protected with HTTP Basic Authentication.
- **Data Persistence**: Production-hardened volume mapping ensuring zero data loss during container recycling.

---

## Repository Structure

```text
pos-order-inventory-system/
├── docker-compose.yml              # Multi-container orchestration
├── .env.example                    # Environment template
├── README.md                       # Project documentation
├── pos-backend/
│   ├── Dockerfile                  # Python 3.12 multi-stage build
│   ├── entrypoint.sh               # Health polling & DB initialization hook
│   ├── requirements.txt            # Python dependencies
│   └── app/
│       ├── main.py                 # FastAPI initialization & security config
│       ├── core/
│       │   ├── config.py           # Pydantic BaseSettings & env parsing
│       │   ├── database.py         # Async engine & sessionmaker
│       │   └── security.py         # JWT generation & password hashing
│       ├── db/
│       │   └── init_db.py          # Idempotent table creation & admin seeding
│       ├── models/                 # SQLAlchemy ORM models (Product, Order, etc.)
│       ├── schemas/                # Pydantic validation schemas
│       ├── repositories/           # Database access patterns
│       └── api/
│           └── v1/
│               ├── api.py          # Master API router configuration
│               └── endpoints/      # Route controllers (auth, products, cart, orders)
└── pos-frontend/
    ├── Dockerfile                  # Node build + Nginx runtime container
    ├── nginx.conf                  # Reverse proxy rules & SPA fallbacks
    ├── package.json
    └── src/
        ├── components/             # Reusable UI (Cart, Catalog, Modals)
        ├── pages/                  # Views (POS Register, Admin Panel)
        └── services/               # Axios API client handlers

```

---

## Getting Started

### Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) (v24.0+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.20+)

### 1. Clone & Configure Environment

```bash
git clone https://github.com/Bhanuka2083/Practical-Assessment.git
cd pos-order-inventory-system

```

Copy the environment template and customize credentials:

```bash
cp .env.example .env

```

Ensure your `.env` contains the required keys:

```ini
# Environment
ENVIRONMENT=development

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pos_db
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432

# Security & JWT
SECRET_KEY=1e614789d7482a48a2a25416feeffc83cd27f817b81d9498df24e910a2a78338
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Documentation Security (HTTP Basic Auth)
DOCS_USERNAME=admin
DOCS_PASSWORD=supersecretposdocs@12345678

```

### 2. Build & Launch

Start all services in detached mode:

```bash
docker compose up --build -d

```

Verify that all three services are running and healthy:

```bash
docker compose ps

```

---

## Access Points & Endpoints

| Resource                       | URL                                         | Credentials / Notes                        |
| ------------------------------ | ------------------------------------------- | ------------------------------------------ |
| **POS Web Interface**          | `http://localhost`                          | Main Point of Sale register & admin area   |
| **Backend Direct**             | `http://localhost:8000`                     | FastAPI direct port (Internal/Dev)         |
| **Interactive Docs (Swagger)** | `http://localhost:8000/docs`                | Requires `DOCS_USERNAME` & `DOCS_PASSWORD` |
| **ReDoc Reference**            | `http://localhost:8000/redoc`               | Requires `DOCS_USERNAME` & `DOCS_PASSWORD` |
| **OpenAPI Schema**             | `http://localhost:8000/api/v1/openapi.json` | Protected schema endpoint                  |
| **Container Healthcheck**      | `http://localhost:8000/health`              | Public diagnostic check (`200 OK`)         |

---

## Core API Routing Scheme

All functional business endpoints are version-scoped under `/api/v1`:

- **Authentication**:
- `POST /api/v1/auth/login` — Authenticate and receive JWT access token.
- `POST /api/v1/auth/register` — Register terminal operators.

- **Products & Catalog**:
- `GET /api/v1/products` — Retrieve product catalog with calculated stock.
- `POST /api/v1/products` — Create a new item (Admin only).
- `PUT /api/v1/products/{id}` — Inline update of title, price, or inventory.
- `DELETE /api/v1/products/{id}` — Remove item from catalog.

- **Cart Operations**:
- `GET /api/v1/cart` — Inspect active terminal cart session.
- `POST /api/v1/cart/items` — Add or increment line items.
- `DELETE /api/v1/cart/items/{product_id}` — Remove items from session.

- **Orders & Checkout**:
- `POST /api/v1/orders/checkout` — Atomic transaction checkout & stock commitment.
- `GET /api/v1/orders/{id}` — Fetch order receipt breakdown.

---

## Operational Commands

### View Logs

```bash
# Follow backend container output (seeding, requests, errors)
docker compose logs -f backend

# Follow frontend/nginx traffic
docker compose logs -f frontend

```

### Safe Service Teardown

To preserve all product data, orders, and customer records, stop containers without touching volumes:

```bash
docker compose down

```

> **Warning**: Never execute `docker compose down -v` unless you intentionally want to delete the persistent PostgreSQL volume and reset the database to an empty state.

# Live Images

![User 01 View](<LIVE IMG/User01.png>)
![User 02 View](<LIVE IMG/User02.png>)
![Admin panel](<LIVE IMG/Admin-panel.png>)
![Payment Process](<LIVE IMG/Payment-process.png>)
![Reserved Items](<LIVE IMG/Reserved-items.png>)
![Payment Complete](<LIVE IMG/Payment-complete.png>)
