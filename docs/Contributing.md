# Developer Contribution Guidelines

This document outlines contribution workflows, code quality rules, and the 15-point Definition of Done (DoD) for developers contributing to SCMS.

---

## 1. Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL 16+

### Setup Local Workspace

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Backend Virtual Environment**:
   ```bash
   cd apps/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   Copy `apps/backend/.env.example` to `apps/backend/.env` and fill in required values (`DATABASE_URL`, `JWT_SECRET_KEY`, `CLOUDINARY_*`, `RESEND_API_KEY`, `EMAIL_FROM`).

4. **Migrations & Seeding**:
   ```bash
   alembic upgrade head
   python -m app.scripts.seed
   ```

---

## 2. Definition of Done (15-Point DoD)

Every pull request or feature branch must meet the 15-point Definition of Done:

1. **UI Implementation**: Matches design system components and Tailwind CSS tokens.
2. **Backend API Documentation**: OpenAPI tags, return types, and Pydantic schemas defined.
3. **Dual Validation**: Validated on both client (Zod) and server (Pydantic).
4. **Authorization Rules**: Access enforced via `require_permission()` dependencies.
5. **Audit Logging**: Mutations logged via `record_audit_log()`.
6. **Domain Events**: Emitted to `EventBus` where appropriate.
7. **Page States Covered**: Loading, empty, error, success, no-results, unauthorized, forbidden.
8. **Loading Skeletons**: Provided for data fetches.
9. **Empty States**: Rendered with action call-to-actions (CTAs).
10. **Automated Testing**: Unit and integration tests written and passing (`pytest`).
11. **Documentation Updated**: Relevant files in `/docs` updated.
12. **Responsive Design**: Verified on desktop, tablet, and mobile breakpoints.
13. **Accessibility**: Keyboard navigable and contrast checked.
14. **Performance Budgets**: Caching and pagination rules respected.
15. **Feature Flags**: Checked if feature is gated by `app/core/feature_flags.py`.
