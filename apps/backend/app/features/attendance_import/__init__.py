"""Attendance Import — bulk import attendance records for today or past dates
using a two-column Excel sheet (Student Roll Number, Attendance Status).

The module is isolated under ``features/attendance_import/`` and handles
the complete workflow: Parse → Validate → Range/Roster Check → Preview →
Confirm → Execute (in transaction) → Downloadable Reports.
"""
