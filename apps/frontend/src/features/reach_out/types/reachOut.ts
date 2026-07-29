export interface CounsellorContactProfile {
  id: string;
  counsellor_id: string;
  full_name: string;
  photo_url?: string | null;
  designation: string;
  department_name: string;
  years_experience: number;
  specializations: string[];
  languages_spoken: string[];
  about_me?: string | null;
  research_interests?: string | null;

  building: string;
  floor: string;
  cabin_number: string;
  office_phone?: string | null;
  emergency_alternate_phone?: string | null;
  office_image_url?: string | null;
  maps_url?: string | null;

  office_status: 'AVAILABLE' | 'BUSY' | 'IN_SESSION' | 'ON_LEAVE' | 'OFFLINE';
  status_message?: string | null;

  structured_schedule?: Record<string, { is_available: boolean; slots: { start: string; end: string }[] }> | null;
  channel_preferences?: Record<string, boolean> | null;

  whatsapp_number?: string | null;
  linkedin_url?: string | null;
  teams_url?: string | null;
  google_meet_url?: string | null;
  zoom_url?: string | null;
  telegram_url?: string | null;
  college_email?: string | null;
}

export interface StudentCommunicationHealth {
  has_data: boolean;
  insufficient_data_reason?: string | null;
  score_stars: number;
  last_response_time?: string | null;
  avg_response_time_hours: number;
  last_meeting_date?: string | null;
  follow_up_compliance_pct: number;
}

export interface ParentEngagementScore {
  has_data: boolean;
  insufficient_data_reason?: string | null;
  score_stars: number;
  total_calls: number;
  total_meetings: number;
  total_emails: number;
  last_contact_date?: string | null;
}

export interface ParentContactDetails {
  father_name?: string | null;
  father_phone?: string | null;
  father_email?: string | null;
  father_occupation?: string | null;

  mother_name?: string | null;
  mother_phone?: string | null;
  mother_email?: string | null;
  mother_occupation?: string | null;

  guardian_name?: string | null;
  guardian_relation?: string | null;
  guardian_phone?: string | null;
  guardian_email?: string | null;

  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact_relation?: string | null;

  preferred_parent_contact: string;
  best_time_to_call?: string | null;
  preferred_language?: string | null;
}

export interface StudentPrivacySettings {
  share_phone: boolean;
  share_personal_email: boolean;
  share_linkedin: boolean;
  share_github: boolean;
  share_portfolio: boolean;
  share_leetcode: boolean;
  share_codechef: boolean;
  share_hackerrank: boolean;

  preferred_parent_contact: string;
  best_time_to_call?: string | null;
  preferred_language?: string | null;
}

export interface AssignedStudentContact {
  id: string;
  user_id: string;
  name: string;
  roll_number: string;
  department_name: string;
  batch_year: number;
  current_semester?: string | null;
  photo_url?: string | null;

  cgpa?: number | null;
  attendance_pct?: number | null;
  risk_level: string;
  active_backlogs_count: number;

  phone?: string | null;
  personal_email?: string | null;
  college_email?: string | null;
  whatsapp_number?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  leetcode_url?: string | null;
  codechef_url?: string | null;
  hackerrank_url?: string | null;
  resume_url?: string | null;

  parent_contacts: ParentContactDetails;
  privacy_settings: StudentPrivacySettings;

  is_favorite: boolean;
  communication_health: StudentCommunicationHealth;
  parent_engagement: ParentEngagementScore;
  latest_communication_date?: string | null;
}

export interface AppointmentRequest {
  id: string;
  student_id: string;
  student_name: string;
  student_roll: string;
  counsellor_id: string;
  counsellor_name: string;
  request_type: string;
  preferred_date: string;
  preferred_time_slot: string;
  reason?: string | null;
  status: 'PENDING' | 'ACCEPTED' | 'DECLINED' | 'COMPLETED' | 'RESCHEDULED' | 'CANCELLED' | 'NO_SHOW' | 'EXPIRED';
  rescheduled_date?: string | null;
  rescheduled_slot?: string | null;
  counsellor_notes?: string | null;
  created_at: string;
}

export interface CommunicationTimelineLog {
  id: string;
  student_id: string;
  counsellor_id: string;
  counsellor_name: string;
  channel: string;
  direction: string;
  summary: string;
  sentiment: string;
  action_outcome: string;
  duration_minutes?: number | null;
  follow_up_required: boolean;
  follow_up_date?: string | null;
  attachments?: string[] | null;
  ai_summary?: {
    key_concerns?: string[];
    action_items?: string[];
    student_commitments?: string[];
    parent_commitments?: string[];
    recommended_risk_level?: string;
  } | null;
  occurred_at: string;
}

export interface AIMeetingBriefing {
  student_id: string;
  student_name: string;
  roll_number: string;
  department_name: string;
  cgpa?: number | null;
  attendance_pct?: number | null;
  backlogs_count: number;
  risk_level: string;
  last_session_date?: string | null;
  last_session_summary?: string | null;
  pending_tasks: string[];
  suggested_discussion_topics: string[];
}

export interface CommunicationTemplate {
  id: string;
  title: string;
  category: string;
  channel: string;
  subject_template?: string | null;
  body_template: string;
  is_system: boolean;
}

export interface InstitutionalChannelPolicy {
  whatsapp_enabled: boolean;
  linkedin_enabled: boolean;
  telegram_enabled: boolean;
  teams_enabled: boolean;
  google_meet_enabled: boolean;
  zoom_enabled: boolean;
  phone_enabled: boolean;
  email_enabled: boolean;
}

export interface CampusEmergencyContact {
  id: string;
  name: string;
  category: string;
  phone: string;
  email?: string | null;
  location?: string | null;
  is_24_7: boolean;
  display_order: number;
}

export interface ReachOutAuditLog {
  id: string;
  actor_id: string;
  actor_name: string;
  action: string;
  target_type: string;
  target_id?: string | null;
  old_values?: Record<string, any> | null;
  new_values?: Record<string, any> | null;
  created_at: string;
}
