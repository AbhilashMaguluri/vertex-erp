# API Documentation — Reach Out (SRM Hub) Endpoints

## Base Path: `/api/v1/reach-out`

### 1. Student Endpoints

#### `GET /api/v1/reach-out/my-counsellor`
- **Description**: Returns active assigned counsellor contact profile for logged in student.
- **RBAC**: Requires `STUDENT` role.
- **Response `200 OK` (Assigned)**:
  ```json
  {
    "assigned": true,
    "profile": {
      "id": "uuid",
      "counsellor_id": "uuid",
      "full_name": "Dr. Ravendra Sagu",
      "designation": "Student Counsellor",
      "department_name": "Artificial Intelligence & Data Science",
      "years_experience": 12,
      "building": "Block B",
      "floor": "3rd Floor",
      "cabin_number": "Room 302",
      "office_phone": "+91 863 2288200",
      "office_status": "AVAILABLE",
      "structured_schedule": { ... }
    }
  }
  ```
- **Response `200 OK` (Unassigned)**:
  ```json
  {
    "assigned": false,
    "message": "No counsellor has been assigned yet."
  }
  ```

#### `GET /api/v1/reach-out/emergency-contacts`
- **Description**: Returns dynamic campus emergency hotline contact directory.
- **RBAC**: Public / All authenticated users.

#### `POST /api/v1/reach-out/appointments`
- **Description**: Create a meeting request.
- **Request Body**:
  ```json
  {
    "request_type": "COUNSELLING",
    "preferred_date": "2026-07-28",
    "preferred_time_slot": "10:30 AM - 11:30 AM",
    "reason": "Attendance recovery guidance"
  }
  ```

---

### 2. Counsellor & HOD Endpoints

#### `GET /api/v1/reach-out/caseload`
- **Description**: Retrieve assigned student caseload with database SRM metrics.
- **Query Params**: `counsellor_id` (Optional, Admin/HOD only).
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "uuid",
      "name": "Student Name",
      "roll_number": "23BQ1A5480",
      "communication_health": {
        "has_data": true,
        "score_stars": 5.0,
        "follow_up_compliance_pct": 100.0
      },
      "parent_engagement": {
        "has_data": false,
        "insufficient_data_reason": "Insufficient data."
      }
    }
  ]
  ```

#### `POST /api/v1/reach-out/caseload/{student_id}/timeline`
- **Description**: Log a communication event.
- **Request Body**:
  ```json
  {
    "channel": "WHATSAPP",
    "direction": "COUNSELLOR_TO_STUDENT",
    "summary": "Discussed attendance plan",
    "sentiment": "POSITIVE",
    "action_outcome": "RESOLVED",
    "duration_minutes": 15,
    "follow_up_required": false
  }
  ```

---

### 3. Admin Endpoints

#### `PUT /api/v1/reach-out/admin/counsellors/{counsellor_id}`
- **Description**: Configure counsellor profile, cabin, and meeting links.
- **Pydantic Validation**:
  - `office_phone` & `whatsapp_number`: Must match regex pattern (`^\+?[0-9\s\-\(\)]{7,20}$`).
  - URLs: Must start with `http://` or `https://`.
- **Response `422 Unprocessable Entity`**: Returned on invalid URL/phone format.
- **Audit Logging**: Automatically writes an entry to `reach_out_audit_logs`.

#### `POST /api/v1/reach-out/admin/emergency-contacts`
- **Description**: Add a new campus emergency hotline contact. Creates audit log entry.

#### `DELETE /api/v1/reach-out/admin/emergency-contacts/{contact_id}`
- **Description**: Delete campus emergency hotline contact. Creates audit log entry.

#### `GET /api/v1/reach-out/admin/audit-logs`
- **Description**: List admin configuration audit history entries.
