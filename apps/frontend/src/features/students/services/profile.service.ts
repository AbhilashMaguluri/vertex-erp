import { api } from '@/shared/lib/axios';

/** Institution-owned facts. Rendered read-only everywhere — no update call in
 *  this file accepts any of these fields. */
export interface ReadOnlyAcademicIdentity {
  student_id: string;
  roll_number: string;
  registration_number: string;
  full_name: string;
  college_email: string;
  department_id?: string | null;
  department_name?: string | null;
  program?: string | null;
  branch?: string | null;
  section_name?: string | null;
  study_year?: number | null;
  semester_name?: string | null;
  semester_number?: number | null;
  batch_year: number;
  admission_year?: number | null;
  status: string;
  risk_level: string;
  counsellor_name?: string | null;
  mentor_name?: string | null;
}

/** ERP-owned admission & scholarship facts. There is no student-facing write
 *  path for any of these — the workspace renders them read-only. */
export interface AcademicRecordBlock {
  admission_number?: string | null;
  admission_date?: string | null;
  admission_type?: string | null;
  abc_id?: string | null;
  joining_year?: number | null;
  academic_year?: string | null;
  ssc_percentage?: number | string | null;
  intermediate_percentage?: number | string | null;
  eamcet_rank?: number | null;
  jee_rank?: number | null;
  scholarship_name?: string | null;
  scholarship_status?: string | null;
  fee_reimbursement_status?: string | null;
  placement_status?: string | null;
  total_credits_required?: number | null;
}

export interface ProfileCompletionSection {
  key: string;
  label: string;
  completed_fields: number;
  total_fields: number;
  percentage: number;
  missing: string[];
}

export interface ProfileCompletion {
  percentage: number;
  completed_fields: number;
  total_fields: number;
  sections: ProfileCompletionSection[];
  top_missing: string[];
}

export interface StudentSelfProfile {
  identity: ReadOnlyAcademicIdentity;

  first_name: string;
  last_name: string;
  date_of_birth?: string | null;
  gender?: string | null;
  photo_url?: string | null;

  preferred_name?: string | null;
  blood_group?: string | null;
  aadhaar_number?: string | null;
  nationality?: string | null;
  category?: string | null;
  religion?: string | null;
  mother_tongue?: string | null;
  languages_known?: string[] | null;
  self_introduction?: string | null;

  support_areas?: string[] | null;
  support_areas_other?: string | null;

  father_name?: string | null;
  father_occupation?: string | null;
  father_qualification?: string | null;
  father_phone?: string | null;
  father_email?: string | null;
  mother_name?: string | null;
  mother_occupation?: string | null;
  mother_qualification?: string | null;
  mother_phone?: string | null;
  mother_email?: string | null;
  guardian_name?: string | null;
  guardian_relation?: string | null;
  guardian_phone?: string | null;
  guardian_email?: string | null;
  guardian_address?: string | null;
  annual_family_income?: number | string | null;

  mobile_number?: string | null;
  alternate_phone?: string | null;
  personal_email?: string | null;
  current_address?: string | null;
  city?: string | null;
  district?: string | null;
  state?: string | null;
  pin_code?: string | null;
  permanent_address?: string | null;
  permanent_city?: string | null;
  permanent_district?: string | null;
  permanent_state?: string | null;
  permanent_pin_code?: string | null;
  permanent_same_as_current: boolean;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact_relation?: string | null;

  hostel_type?: string | null;
  hostel_name?: string | null;
  hostel_block?: string | null;
  hostel_floor?: string | null;
  hostel_room_number?: string | null;
  preferred_communication_method?: string | null;
  preferred_call_time?: string | null;

  career_goal?: string | null;
  higher_studies_goal?: string | null;
  dream_company?: string | null;
  strengths?: string | null;
  weaknesses?: string | null;
  areas_to_improve?: string | null;

  technical_skills?: string[] | null;
  programming_languages?: string[] | null;
  soft_skills?: string[] | null;
  tools_technologies?: string[] | null;
  other_skills?: string[] | null;
  hobbies?: string[] | null;
  interests?: string[] | null;

  extracurricular_activities?: string[] | null;
  extracurricular_other?: string | null;
  extracurricular_achievements?: string | null;

  medical_conditions?: string | null;
  allergies?: string | null;
  disability?: string | null;
  current_medications?: string | null;
  health_notes?: string | null;

  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  leetcode_url?: string | null;
  codechef_url?: string | null;
  hackerrank_url?: string | null;
  codeforces_url?: string | null;
  other_coding_url?: string | null;
  resume_url?: string | null;

  notification_preferences?: Record<string, boolean> | null;
  share_contact_with_counsellor: boolean;

  academic: AcademicRecordBlock;
  completion: ProfileCompletion;
}

// ---- counsellor section (read-only for the student) ----

export interface CounsellingNoteEntry {
  session_id: string;
  session_date: string;
  session_type: string;
  mode: string;
  counsellor_name?: string | null;
  observations: string;
  recommendations?: string | null;
  student_commitments?: string | null;
  follow_up_required: boolean;
  follow_up_date?: string | null;
  student_acknowledged: boolean;
}

export interface CounsellingActionItemEntry {
  id: string;
  description: string;
  due_date?: string | null;
  status: string;
  is_overdue: boolean;
  session_date?: string | null;
}

export interface ParentInteractionEntry {
  id: string;
  communication_date: string;
  mode: string;
  parent_name: string;
  relation: string;
  summary: string;
  action_items?: string | null;
  outcome: string;
  follow_up_date?: string | null;
}

export interface StudentCounsellingSummary {
  risk_level: string;
  counsellor_name?: string | null;
  mentor_name?: string | null;
  total_sessions: number;
  last_session_date?: string | null;
  follow_up_required: boolean;
  notes: CounsellingNoteEntry[];
  action_items: CounsellingActionItemEntry[];
  parent_interactions: ParentInteractionEntry[];
}

export interface Internship {
  id: string;
  student_id: string;
  company: string;
  role: string;
  start_date?: string | null;
  end_date?: string | null;
  duration?: string | null;
  stipend?: number | string | null;
  technologies?: string[] | null;
  description?: string | null;
  status: string;
  certificate_document_id?: string | null;
  created_at: string;
}

export interface Interview {
  id: string;
  student_id: string;
  company: string;
  role: string;
  interview_date?: string | null;
  interview_type?: string | null;
  round_name?: string | null;
  result: string;
  feedback?: string | null;
  notes?: string | null;
  package_offered?: number | string | null;
  counsellor_observation?: string | null;
  counsellor_observed_by_name?: string | null;
  counsellor_observed_at?: string | null;
  offer_document_id?: string | null;
  created_at: string;
}

export interface Achievement {
  id: string;
  student_id: string;
  category: string;
  title: string;
  description?: string | null;
  issuer?: string | null;
  achieved_on?: string | null;
  position?: string | null;
  credential_url?: string | null;
  proof_document_id?: string | null;
  created_at: string;
}

export interface StudentDocument {
  id: string;
  student_id: string;
  document_type: string;
  title?: string | null;
  original_filename: string;
  file_url?: string | null;
  content_type: string;
  size_bytes: number;
  version?: number;
  verification_status?: string;
  uploaded_by_name?: string | null;
  created_at: string;
}

/** Document slots offered on the Documents card, in the order the college
 *  asks for them. Labels are what the student sees; the value is what the API
 *  stores (core.enums.DocumentType). */
export const DOCUMENT_TYPES = [
  { value: 'PHOTO', label: 'Passport Size Photograph' },
  { value: 'RESUME', label: 'Resume' },
  { value: 'AADHAAR', label: 'Aadhaar Card' },
  { value: 'SSC_MEMO', label: 'SSC Marks Memo' },
  { value: 'INTERMEDIATE_MEMO', label: 'Intermediate Marks Memo' },
  { value: 'INCOME_CERTIFICATE', label: 'Income Certificate' },
  { value: 'CASTE_CERTIFICATE', label: 'Caste Certificate' },
  { value: 'BONAFIDE', label: 'Bonafide Certificate' },
  { value: 'CERTIFICATE', label: 'Course / Skill Certificate' },
  { value: 'INTERNSHIP_LETTER', label: 'Internship Letter' },
  { value: 'OFFER_LETTER', label: 'Offer Letter' },
  { value: 'ACHIEVEMENT_PROOF', label: 'Achievement Proof' },
  { value: 'PAN', label: 'PAN Card' },
  { value: 'PASSPORT', label: 'Passport' },
  { value: 'OTHER', label: 'Other Supporting Document' },
] as const;

export const SUPPORT_AREAS = [
  { value: 'ACADEMICS', label: 'Academics' },
  { value: 'COMMUNICATION_SKILLS', label: 'Communication Skills' },
  { value: 'FINANCIAL_SUPPORT', label: 'Financial Support' },
  { value: 'HIGHER_STUDIES', label: 'Higher Studies' },
  { value: 'PLACEMENTS', label: 'Placements' },
  { value: 'TIME_MANAGEMENT', label: 'Time Management' },
  { value: 'MENTAL_WELLBEING', label: 'Mental Wellbeing' },
  { value: 'PERSONAL_ISSUES', label: 'Personal Issues' },
  { value: 'ENTREPRENEURSHIP', label: 'Entrepreneurship' },
  { value: 'COMPETITIVE_EXAMS', label: 'Competitive Exams' },
  { value: 'OTHER', label: 'Other' },
] as const;

export const EXTRACURRICULAR_ACTIVITIES = [
  { value: 'NCC', label: 'NCC' },
  { value: 'NSS', label: 'NSS' },
  { value: 'SPORTS', label: 'Sports' },
  { value: 'CULTURAL', label: 'Cultural Activities' },
  { value: 'CLUBS', label: 'Clubs' },
  { value: 'TECHNICAL_CLUBS', label: 'Technical Clubs' },
  { value: 'HACKATHONS', label: 'Hackathons' },
  { value: 'VOLUNTEERING', label: 'Volunteering' },
  { value: 'EVENT_ORGANIZING', label: 'Event Organizing' },
  { value: 'OTHER', label: 'Other Activities' },
] as const;

export const ADMISSION_TYPE_LABELS: Record<string, string> = {
  CONVENOR: 'Convenor',
  MANAGEMENT: 'Management',
  LATERAL_ENTRY: 'Lateral Entry',
};

export const GENDERS = ['MALE', 'FEMALE', 'OTHER'] as const;

export const ACHIEVEMENT_CATEGORIES = [
  'HACKATHON',
  'CERTIFICATION',
  'COMPETITION',
  'PUBLICATION',
  'AWARD',
  'SPORTS',
  'CLUB',
  'NSS_NCC',
  'VOLUNTEER',
  'OTHER',
] as const;

export const INTERVIEW_TYPES = [
  'ON_CAMPUS',
  'OFF_CAMPUS',
  'VIRTUAL',
  'TELEPHONIC',
  'TECHNICAL',
  'HR',
  'GROUP_DISCUSSION',
  'APTITUDE',
] as const;

export const INTERVIEW_RESULTS = ['PENDING', 'SELECTED', 'REJECTED', 'ON_HOLD', 'WITHDRAWN'] as const;
export const INTERNSHIP_STATUSES = ['APPLIED', 'ONGOING', 'COMPLETED', 'CANCELLED'] as const;
export const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;

export const profileService = {
  // ---- own profile ----
  getMyProfile: async (): Promise<StudentSelfProfile> => {
    const res = await api.get<StudentSelfProfile>('/students/me/profile');
    return res.data;
  },
  getSelfProfile: async (): Promise<StudentSelfProfile> => {
    const res = await api.get<StudentSelfProfile>('/students/me/profile');
    return res.data;
  },

  updatePersonal: async (data: Record<string, unknown>): Promise<StudentSelfProfile> => {
    const res = await api.patch<StudentSelfProfile>('/students/me/profile/personal', data);
    return res.data;
  },

  updateFamily: async (data: Record<string, unknown>): Promise<StudentSelfProfile> => {
    const res = await api.patch<StudentSelfProfile>('/students/me/profile/family', data);
    return res.data;
  },

  updateContact: async (data: Record<string, unknown>): Promise<StudentSelfProfile> => {
    const res = await api.patch<StudentSelfProfile>('/students/me/profile/contact', data);
    return res.data;
  },

  updateSkills: async (data: Record<string, unknown>): Promise<StudentSelfProfile> => {
    const res = await api.patch<StudentSelfProfile>('/students/me/profile/skills', data);
    return res.data;
  },

  updateHealth: async (data: Record<string, unknown>): Promise<StudentSelfProfile> => {
    const res = await api.patch<StudentSelfProfile>('/students/me/profile/health', data);
    return res.data;
  },

  updateExtracurricular: async (data: Record<string, unknown>): Promise<StudentSelfProfile> => {
    const res = await api.patch<StudentSelfProfile>('/students/me/profile/extracurricular', data);
    return res.data;
  },

  updatePreferences: async (data: Record<string, unknown>): Promise<StudentSelfProfile> => {
    const res = await api.patch<StudentSelfProfile>('/students/me/profile/preferences', data);
    return res.data;
  },

  /** Uploads the cropped square produced by PhotoUploadDialog. The response
   *  carries the refreshed profile, so photo_url is never guessed client-side. */
  uploadPhoto: async (file: File): Promise<StudentSelfProfile> => {
    const form = new FormData();
    form.append('file', file);
    const res = await api.post<StudentSelfProfile>('/students/me/profile/photo', form);
    return res.data;
  },

  // ---- counsellor section (read-only) ----
  getMyCounsellingSummary: async (): Promise<StudentCounsellingSummary> => {
    const res = await api.get<StudentCounsellingSummary>('/students/me/counselling-summary');
    return res.data;
  },

  getStudentCounsellingSummary: async (studentId: string): Promise<StudentCounsellingSummary> => {
    const res = await api.get<StudentCounsellingSummary>(`/students/${studentId}/counselling-summary`);
    return res.data;
  },

  // ---- internships ----
  listInternships: async (): Promise<Internship[]> => {
    const res = await api.get<Internship[]>('/students/me/internships');
    return res.data;
  },
  createInternship: async (data: Record<string, unknown>): Promise<Internship> => {
    const res = await api.post<Internship>('/students/me/internships', data);
    return res.data;
  },
  updateInternship: async (id: string, data: Record<string, unknown>): Promise<Internship> => {
    const res = await api.patch<Internship>(`/students/me/internships/${id}`, data);
    return res.data;
  },
  deleteInternship: async (id: string): Promise<void> => {
    await api.delete(`/students/me/internships/${id}`);
  },

  // ---- interviews ----
  listInterviews: async (): Promise<Interview[]> => {
    const res = await api.get<Interview[]>('/students/me/interviews');
    return res.data;
  },
  createInterview: async (data: Record<string, unknown>): Promise<Interview> => {
    const res = await api.post<Interview>('/students/me/interviews', data);
    return res.data;
  },
  updateInterview: async (id: string, data: Record<string, unknown>): Promise<Interview> => {
    const res = await api.patch<Interview>(`/students/me/interviews/${id}`, data);
    return res.data;
  },
  deleteInterview: async (id: string): Promise<void> => {
    await api.delete(`/students/me/interviews/${id}`);
  },

  // ---- achievements ----
  listAchievements: async (): Promise<Achievement[]> => {
    const res = await api.get<Achievement[]>('/students/me/achievements');
    return res.data;
  },
  createAchievement: async (data: Record<string, unknown>): Promise<Achievement> => {
    const res = await api.post<Achievement>('/students/me/achievements', data);
    return res.data;
  },
  updateAchievement: async (id: string, data: Record<string, unknown>): Promise<Achievement> => {
    const res = await api.patch<Achievement>(`/students/me/achievements/${id}`, data);
    return res.data;
  },
  deleteAchievement: async (id: string): Promise<void> => {
    await api.delete(`/students/me/achievements/${id}`);
  },

  // ---- documents ----
  listDocuments: async (): Promise<StudentDocument[]> => {
    const res = await api.get<StudentDocument[]>('/students/me/documents');
    return res.data;
  },
  uploadDocument: async (
    file: File,
    documentType: string,
    title?: string
  ): Promise<StudentDocument> => {
    const form = new FormData();
    form.append('file', file);
    form.append('document_type', documentType);
    if (title) form.append('title', title);
    const res = await api.post<StudentDocument>('/students/me/documents', form);
    return res.data;
  },
  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/students/me/documents/${id}`);
  },

  /** Downloads or opens a document.  If the document has a Cloudinary
   *  ``file_url``, open it directly in a new tab.  Otherwise fall back to the
   *  authenticated blob-download path (302 redirect from the backend). */
  downloadDocument: async (studentId: string, documentId: string, filename: string, fileUrl?: string | null): Promise<void> => {
    if (fileUrl) {
      window.open(fileUrl, '_blank', 'noopener,noreferrer');
      return;
    }
    // Fallback: the backend redirects to Cloudinary, but for cases where
    // the browser doesn't follow the redirect automatically (e.g. blob
    // download), we fetch and save manually.
    const res = await api.get(`/students/${studentId}/documents/${documentId}/download`, {
      responseType: 'blob',
    });
    const url = URL.createObjectURL(res.data as Blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  // ---- staff read of a specific student ----
  getStudentProfile: async (studentId: string): Promise<StudentSelfProfile> => {
    const res = await api.get<StudentSelfProfile>(`/students/${studentId}/profile`);
    return res.data;
  },
  listStudentInternships: async (studentId: string): Promise<Internship[]> => {
    const res = await api.get<Internship[]>(`/students/${studentId}/internships`);
    return res.data;
  },
  listStudentInterviews: async (studentId: string): Promise<Interview[]> => {
    const res = await api.get<Interview[]>(`/students/${studentId}/interviews`);
    return res.data;
  },
  listStudentAchievements: async (studentId: string): Promise<Achievement[]> => {
    const res = await api.get<Achievement[]>(`/students/${studentId}/achievements`);
    return res.data;
  },
  listStudentDocuments: async (studentId: string): Promise<StudentDocument[]> => {
    const res = await api.get<StudentDocument[]>(`/students/${studentId}/documents`);
    return res.data;
  },
  setInterviewObservation: async (
    studentId: string,
    interviewId: string,
    observation: string
  ): Promise<Interview> => {
    const res = await api.put<Interview>(
      `/students/${studentId}/interviews/${interviewId}/observation`,
      { counsellor_observation: observation }
    );
    return res.data;
  },
};
