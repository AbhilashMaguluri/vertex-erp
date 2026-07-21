# Developer Contribution Guidelines

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL 16+

### Setup Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Backend setup:
   ```bash
   cd apps/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Definition of Done (DoD)

Every pull request or feature branch must meet the 15-point Definition of Done specified in PRD §52:
1. **UI Implementation** matches design system components.
2. **Backend API** documented with Pydantic schemas and OpenAPI tags.
3. **Validation** on both client (Zod) and server (Pydantic).
4. **Authorization** enforced via `require_permission()`.
5. **Audit Logging** on all mutation endpoints.
6. **Domain Events** emitted for timeline, analytics, and notification subscribers.
7. **Page States** defined: loading, empty, error, success, no-results, unauthorized, forbidden.
8. **Loading Skeletons** provided for all data fetches.
9. **Empty States** provided with action CTA.
10. **Tests** written (unit + integration).
11. **Documentation** updated.
12. **Responsive Design** verified on desktop, tablet, and mobile.
13. **Accessibility** keyboard navigable and contrast checked.
14. **Performance** budgets respected.
15. **Feature Flags** checked if feature is conditional.
