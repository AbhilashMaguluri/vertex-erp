# Roadmap & Known Operational Boundaries

This document documents planned roadmap enhancements and explicitly outlines current system operational boundaries.

---

## 1. Planned Roadmap Features

These items reflect TODO items and planned features noted in the codebase:

- [ ] **External Message Queue Integration**: Migrate the in-process `EventBus` (`app/core/events.py`) to an external message queue (e.g. RabbitMQ or Redis Pub/Sub) for multi-worker notification scaling.
- [ ] **Persistent Event Timeline Table**: Add a database persistence subscriber to store and query student domain timeline events across semesters.
- [ ] **Name-to-ID Spreadsheet Resolution**: Add automatic fuzzy text matching in the Office Import engine to map human-readable department names (e.g. "CSE") to internal UUIDs.
- [ ] **Institutional Document PDF Layouts**: Add customizable institutional header and footer templates to generated PDF reports.
- [ ] **Self-Service Profile Edit Endpoint**: Expand student self-service profile APIs with direct profile editing routes (`PATCH /api/v1/auth/me`).

---

## 2. Known Operational Boundaries

1. **In-Process Pub/Sub Event Bus**: `app/core/events.py` runs in-process. Events published to `EventBus` trigger active in-memory listeners.
2. **Institutional Account Provisioning**: SCMS is a closed institutional application. Public self-registration APIs are intentionally omitted; accounts must be created by an Administrator.
3. **Counselling Note Immutability**: Counselling session summaries are append-only. Once logged, observations cannot be edited or soft-deleted, ensuring an audit trail.
