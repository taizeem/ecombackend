# Multi-Vendor E-Commerce Backend API

A production-grade, concurrent e-commerce RESTful API built with **Django REST Framework** and **PostgreSQL**. The platform features role-based access control (RBAC), atomic checkout workflows with pessimistic row locking (`select_for_update`), verified-purchase reviews, and interactive OpenAPI 3.0 / Swagger documentation.

---

## Technical Highlights

* **Concurrency & Inventory Safety:** Atomic checkout orchestration using `transaction.atomic()` and PostgreSQL row-level locks (`select_for_update()`) to eliminate race conditions and overselling during peak traffic.
* **Role-Based Access Control (RBAC):** Strict isolation between **Buyer**, **Seller**, and **Admin** personas. Custom claims (`role`, `username`, `email`) are injected into both the JWT token payload and the authentication response.
* **Database & Query Optimization:** Eliminates N+1 query bottlenecks across high-read catalog and order routes through `select_related`, `prefetch_related`, and database-level aggregations (`Avg`, `Count`).
* **Domain Integrity:** Order items snapshot product prices at time-of-purchase to preserve financial history against catalog updates. Reviews enforce verified-purchase checks and prevent seller self-reviews.
* **Interactive API Documentation:** Automated OpenAPI 3.0 schema generation using `drf-spectacular`, hardened against anonymous schema-generation edge cases.
* **Automated Integration Testing:** End-to-end integration tests covering authentication, seller catalog isolation, cart lifecycle, concurrency rollbacks, and review permissions.

---

## Tech Stack

* **Language:** Python 3.12+
* **Framework:** Django & Django REST Framework (DRF)
* **Database:** PostgreSQL
* **Authentication:** SimpleJWT (JSON Web Tokens)
* **Package & Environment Manager:** `uv`
* **API Documentation:** `drf-spectacular` (Swagger UI & Redoc)
* **Filtering & Search:** `django-filter`

---

## System Architecture

```text
├── config/             # Root settings, URL routing, and OpenAPI configuration
├── users/              # Custom User model (BUYER/SELLER/ADMIN), JWT token flows, profile views
├── products/           # Categories, product catalog, seller product management
├── cart/               # Authenticated cart session management, item counters, stock checks
├── orders/             # Atomic checkout engine, order item snapshots, status workflows
└── reviews/            # Verified-purchase review system, star ratings, catalog aggregations

```

---

## Core Endpoints

### Authentication & Users (`/api/v1/auth/`)

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register/` | Register as a Buyer or Seller | Public |
| `POST` | `/api/v1/auth/login/` | Obtain JWT pair + custom role claims | Public |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh expired access token | Public |
| `GET` / `PATCH` | `/api/v1/auth/me/` | View or update profile details | Authenticated |

### Catalog & Seller Inventory (`/api/v1/products/`)

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `GET` | `/api/v1/products/` | Browse active catalog (filter, search, order) | Public |
| `GET` | `/api/v1/products//` | View product details with review metrics | Public |
| `GET` / `POST` | `/api/v1/seller/products/` | List/create products in seller's inventory | Seller Only |
| `GET` / `PATCH` / `DELETE` | `/api/v1/seller/products//` | Manage owned product details & stock | Seller (Owner) |

### Shopping Cart (`/api/v1/cart/`)

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `GET` | `/api/v1/cart/` | Retrieve active cart with itemized subtotal | Authenticated |
| `POST` | `/api/v1/cart/items/` | Add product to cart or increment quantity | Authenticated |
| `DELETE` | `/api/v1/cart/items//` | Remove specific item from cart | Authenticated |
| `DELETE` | `/api/v1/cart/clear/` | Flush all items from active cart | Authenticated |

### Orders & Checkout (`/api/v1/orders/`)

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `POST` | `/api/v1/orders/checkout/` | Atomic stock lock, deduction & order creation | Buyer |
| `GET` | `/api/v1/orders/` | List personal orders (Buyer) or sales (Seller) | Authenticated |
| `GET` | `/api/v1/orders//` | Inspect order line-items and shipment details | Authenticated |
| `PATCH` | `/api/v1/orders//status/` | Update shipment status (`PENDING` $\to$ `SHIPPED`) | Seller / Admin |

### Reviews & Ratings (`/api/v1/reviews/`)

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `GET` | `/api/v1/reviews/` | List product reviews | Public |
| `POST` | `/api/v1/reviews/` | Submit review (enforces verified purchase) | Verified Buyer |
| `PATCH` / `DELETE` | `/api/v1/reviews//` | Update or delete user's own review | Review Author |

---

## Local Setup & Installation

### 1. Prerequisites

* Python 3.12+
* PostgreSQL running locally or in Docker
* [uv](https://docs.astral.sh/uv/) installed:
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
# or: curl -LsSf https://astral.sh/uv/install.sh | sh                            # Linux/macOS

```



### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/ecommerce-backend.git
cd ecommerce-backend

```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-django-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=ecom_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=127.0.0.1
DB_PORT=5432

```

### 4. Install Dependencies

```bash
uv sync

```

### 5. Apply Database Migrations

```bash
uv run python manage.py migrate

```

### 6. Create Superuser (Admin)

```bash
uv run python manage.py createsuperuser

```

### 7. Run the Development Server

```bash
uv run python manage.py runserver

```

---

## API Documentation

Once the server is running, explore and test the endpoints interactively:

* **Swagger UI:** [http://127.0.0.1:8000/api/docs/](https://www.google.com/search?q=http://127.0.0.1:8000/api/docs/)
* **ReDoc:** [http://127.0.0.1:8000/api/redoc/](https://www.google.com/search?q=http://127.0.0.1:8000/api/redoc/)
* **OpenAPI Raw Schema:** [http://127.0.0.1:8000/api/schema/](https://www.google.com/search?q=http://127.0.0.1:8000/api/schema/)

---

## Running the Automated Test Suite

The test suite validates authentication, role-based access boundaries, atomic checkout rollbacks, and verified purchase rules:

```bash
# Run all integration tests across all apps
uv run python manage.py test

# Run tests with verbose output
uv run python manage.py test -v 2

# Run tests reusing the test database for faster execution
uv run python manage.py test --keepdb

# Target specific app suites
uv run python manage.py test users
uv run python manage.py test products
uv run python manage.py test cart
uv run python manage.py test orders
uv run python manage.py test reviews

```

---

## License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.