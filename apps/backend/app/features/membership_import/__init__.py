"""Membership Import — bulk-import counsellor assignments from a simple
three-column Excel sheet (Start Roll, End Roll, Counselor Email).

The module is intentionally separate from the existing Office Import
(``features/imports``), which provisions student accounts.  This module
is concerned solely with *assigning* existing students to existing
counsellors.  It follows the same staged approach — parse → validate →
preview → confirm → execute — but owns its own services, schemas, and
router so the two import domains stay clean and maintainable.
"""
