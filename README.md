# Salom CRM — Educational Agency Multi-Tenant Platform

> Enterprise-grade CRM architecture built with **Python + Django REST Framework + PostgreSQL + Redis** on the backend, and **Vue 3 + TypeScript + Vite + Pinia + TanStack Query + Tailwind CSS** on the frontend.

---

## 🌟 Architectural Highlights

- **Strict Server-Side Multi-Tenancy**: Complete tenant data isolation. Each query is automatically scoped by the user's tenant context. Tenant A can never read or write Tenant B records.
- **Platform Super Admin Hierarchy**: Global visibility and switching between tenant scopes via the header switcher.
- **Transactional Financial Ledger**:
  - `Balance = (Total Payments + Total Discounts) - Tariff Price`
  - Dynamic tariff pricing (e.g. `E-VISA` with language certificate is 16,000,000 UZS vs 24,000,000 UZS without).
  - Atomic recalculation and rollbacks on payment edits, deletions, and fund withdrawals.
  - Live thousands formatted input masking.
  - Native Excel export (`/api/payments/export/excel/`).
- **Alphanumeric ID Ordering**: Custom sorting grouping alphanumeric prefixes and ordering numeric components numerically (`UB1`, `UB2`, `UB10`).
- **Status & Urgency Engine**: Real-time KDB deposit countdowns (`OVERDUE`, `CRITICAL`, `URGENT`, `NORMAL`) and Embassy sponsorship drawer.
- **Interactive OpenAPI Documentation**: Built with `drf-spectacular` at `/api/docs/` (Swagger UI) and `/api/redoc/`.

---

## 🚀 Quick Start & Local Development

### 1. Backend Setup

```bash
# Navigate to project root and create Python virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows

# Install Python requirements
pip install -r backend/requirements.txt

# Run migrations and seed sample database
python backend/manage.py migrate
python backend/manage.py seed_data

# Run automated backend test suite
python backend/manage.py test apps.tenants.tests apps.payments.tests apps.students.tests

# Start Django backend dev server
python backend/manage.py runserver 127.0.0.1:8000
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run frontend dev server
npm run dev
# Opens at http://localhost:3000
```

---

## 🐳 Docker Deployment

To launch the complete containerized stack (PostgreSQL 16, Redis 7, Django Gunicorn backend, Vue 3 Nginx frontend):

```bash
docker-compose up --build -d
```

- **Frontend App**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000/api/`
- **Swagger Documentation**: `http://localhost:8000/api/docs/`
- **Django Admin**: `http://localhost:8000/admin/`

---

## 🔑 Demo Login Accounts

| Role | Email | Password | Scope |
|---|---|---|---|
| **Platform Super Admin** | `admin@uniapp.com` | `admin123456` | Global (All Tenants) |
| **Unibridge Head Manager** | `abdurazzakov_97@mail.ru` | `robocode2023@` | Unibridge Agency |

---

## 📁 Repository Structure

```
Uniapp3/
├── backend/
│   ├── config/              # Django settings, WSGI, URLs, drf-spectacular
│   ├── apps/
│   │   ├── core/            # TenantAwareModel, permissions, pagination, seed_data
│   │   ├── authentication/  # Custom User model, JWT auth, Me endpoint
│   │   ├── tenants/         # Multi-tenant models, middleware, ViewSets
│   │   ├── students/        # Student model, alphanumeric sorting, folders, options
│   │   ├── payments/        # Ledger engine, payment/withdraw services, Excel export
│   │   ├── status_board/    # KDB urgency engine, Embassy sponsorship drawer
│   │   └── audit/           # AuditLog model and event tracker
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios client, auth, students, payments, status, tenants
│   │   ├── stores/          # Pinia auth and UI theme/toast stores
│   │   ├── composables/     # useCurrency (live masking), useAlphanumericSort
│   │   ├── components/      # Common modals, drawers, AppSidebar, AppHeader
│   │   ├── modules/
│   │   │   ├── auth/        # LoginPage with quick-fill demo buttons
│   │   │   ├── students/    # StudentsPage, StudentTable, StudentDetailDrawer, Modals
│   │   │   ├── payments/    # PaymentsPage, StudentOverview, History, Withdraw
│   │   │   ├── status/      # StatusPage, General View, KDB View, Embassy Drawer
│   │   │   └── tenants/     # TenantsPage, CreateTenantModal (Super Admin)
│   │   ├── router/          # Vue Router with navigation guards
│   │   └── style.css        # Tailwind CSS & theme tokens
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
└── README.md
```
