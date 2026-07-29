import { useState } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { UserRole } from '@scms/types';
import {
  useMyCounsellor,
  useAssignedStudentsCaseload,
  useCampusEmergencyContacts,
  useInstitutionalChannelPolicy,
  useCounsellors,
} from '../api/reachOutApi';
import { CounsellorPersonaCard } from '../components/CounsellorPersonaCard';
import { CampusEmergencyCard } from '../components/CampusEmergencyCard';
import { AppointmentRequestModal } from '../components/AppointmentRequestModal';
import { CounsellorCaseloadGrid } from '../components/CounsellorCaseloadGrid';
import { EnrichedStudentModal } from '../components/EnrichedStudentModal';
import { AIMeetingPrepModal } from '../components/AIMeetingPrepModal';
import { CommunicationTemplatesModal } from '../components/CommunicationTemplatesModal';
import { StudentPrivacySettingsModal } from '../components/StudentPrivacySettingsModal';
import { AdminReachOutConfigView } from '../components/AdminReachOutConfigView';
import { AssignedStudentContact, CounsellorContactProfile } from '../types/reachOut';
import { PhoneCall, Sparkles, UserCheck } from 'lucide-react';

export function ReachOutPage() {
  const { user } = useAuth();
  const roleNames = user?.roles || [];

  const isStudent = roleNames.includes(UserRole.STUDENT);
  const isCounsellor = roleNames.includes(UserRole.COUNSELLOR) && !roleNames.includes(UserRole.ADMIN);
  const isHod = roleNames.includes(UserRole.HOD);
  const isAdmin = roleNames.includes(UserRole.ADMIN) || roleNames.includes(UserRole.SUPER_ADMIN);

  // Queries
  const { data: counsellorRes, isLoading: isCounsellorLoading } = useMyCounsellor();
  const { data: caseload, isLoading: isCaseloadLoading } = useAssignedStudentsCaseload();
  const { data: emergencyContacts } = useCampusEmergencyContacts();
  const { data: policy } = useInstitutionalChannelPolicy();

  // HOD View Queries
  const { data: deptCounsellors } = useCounsellors((user as any)?.department_id || undefined);
  const [selectedHodCounsellor, setSelectedHodCounsellor] = useState<CounsellorContactProfile | null>(null);

  // Modals state
  const [appointmentModalType, setAppointmentModalType] = useState<string | null>(null);
  const [selectedStudentForModal, setSelectedStudentForModal] = useState<AssignedStudentContact | null>(null);
  const [aiBriefingStudent, setAiBriefingStudent] = useState<AssignedStudentContact | null>(null);
  const [templateStudent, setTemplateStudent] = useState<AssignedStudentContact | null>(null);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-foreground">Reach Out</h1>
            <span className="inline-flex items-center gap-1 rounded-full bg-brand-600/10 px-3 py-0.5 text-xs font-black text-brand-600 border border-brand-600/20">
              <PhoneCall className="h-3.5 w-3.5" /> SRM & Reach Out Hub
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {isStudent
              ? 'One-click direct access to your assigned counsellor, cabin location, office hours, and emergency hotlines.'
              : isCounsellor
              ? 'Caseload relationship desk: view student contact profiles, parent details, timeline history, and AI briefings.'
              : isHod
              ? 'Department HOD view: monitor counsellor profiles and student relationship health across department.'
              : 'Admin management: configure counsellor cabin profiles, office hours, emergency hotlines, and channel policies.'}
          </p>
        </div>
      </div>

      {/* STUDENT VIEW */}
      {isStudent && (
        <div className="space-y-6">
          {isCounsellorLoading ? (
            <div className="py-12 text-center text-xs font-bold text-muted-foreground flex items-center justify-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-600 animate-spin" /> Loading assigned counsellor profile...
            </div>
          ) : counsellorRes?.assigned && counsellorRes.profile ? (
            <CounsellorPersonaCard
              counsellor={counsellorRes.profile}
              policy={policy}
              onOpenAppointmentModal={(type) => setAppointmentModalType(type)}
              onOpenPrivacyModal={() => setShowPrivacyModal(true)}
            />
          ) : (
            <div className="p-12 text-center rounded-3xl bg-card border border-border/80 shadow-md">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 ring-4 ring-amber-500/10 mb-4">
                <UserCheck className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-black text-foreground">No counsellor has been assigned yet.</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                Your academic record is not currently assigned to a counsellor. Please contact your department administration for assistance.
              </p>
            </div>
          )}

          <CampusEmergencyCard contacts={emergencyContacts || []} />
        </div>
      )}

      {/* COUNSELLOR VIEW */}
      {isCounsellor && (
        <div className="space-y-6">
          {isCaseloadLoading ? (
            <div className="py-12 text-center text-xs font-bold text-muted-foreground flex items-center justify-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-600 animate-spin" /> Loading assigned student caseload...
            </div>
          ) : (
            <CounsellorCaseloadGrid
              students={caseload || []}
              policy={policy}
              onSelectStudentModal={(student) => setSelectedStudentForModal(student)}
              onOpenAiBriefing={(student) => setAiBriefingStudent(student)}
              onOpenTemplates={(student) => setTemplateStudent(student)}
            />
          )}

          <CampusEmergencyCard contacts={emergencyContacts || []} />
        </div>
      )}

      {/* HOD VIEW */}
      {isHod && !isAdmin && (
        <div className="space-y-6">
          <div className="p-4 rounded-3xl bg-card border border-border/80 shadow-md flex items-center justify-between">
            <h3 className="text-xs font-black uppercase text-muted-foreground">Department Counsellors Supervision</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-foreground">Select Counsellor:</span>
              <select
                value={selectedHodCounsellor?.counsellor_id || ''}
                onChange={(e) => {
                  const found = deptCounsellors?.find((c) => c.counsellor_id === e.target.value);
                  setSelectedHodCounsellor(found || null);
                }}
                className="rounded-xl bg-muted p-2 text-xs font-bold border"
              >
                <option value="">-- All Counsellors --</option>
                {deptCounsellors?.map((c) => (
                  <option key={c.id} value={c.counsellor_id}>
                    {c.full_name} ({c.department_name})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {selectedHodCounsellor && (
            <CounsellorPersonaCard
              counsellor={selectedHodCounsellor}
              policy={policy}
              onOpenAppointmentModal={(type) => setAppointmentModalType(type)}
            />
          )}

          <CounsellorCaseloadGrid
            students={caseload || []}
            policy={policy}
            onSelectStudentModal={(student) => setSelectedStudentForModal(student)}
            onOpenAiBriefing={(student) => setAiBriefingStudent(student)}
            onOpenTemplates={(student) => setTemplateStudent(student)}
          />

          <CampusEmergencyCard contacts={emergencyContacts || []} />
        </div>
      )}

      {/* ADMIN VIEW */}
      {isAdmin && (
        <div className="space-y-6">
          <AdminReachOutConfigView />
          <CampusEmergencyCard contacts={emergencyContacts || []} />
        </div>
      )}

      {/* MODALS */}
      {appointmentModalType && (
        <AppointmentRequestModal
          initialType={appointmentModalType}
          onClose={() => setAppointmentModalType(null)}
        />
      )}

      {selectedStudentForModal && (
        <EnrichedStudentModal
          student={selectedStudentForModal}
          onClose={() => setSelectedStudentForModal(null)}
        />
      )}

      {aiBriefingStudent && (
        <AIMeetingPrepModal
          studentId={aiBriefingStudent.id}
          studentName={aiBriefingStudent.name}
          onClose={() => setAiBriefingStudent(null)}
        />
      )}

      {templateStudent && (
        <CommunicationTemplatesModal
          studentName={templateStudent.name}
          onSelectTemplate={(body) => {
            if (templateStudent.whatsapp_number) {
              window.open(`https://wa.me/${templateStudent.whatsapp_number.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(body)}`, '_blank');
            }
          }}
          onClose={() => setTemplateStudent(null)}
        />
      )}

      {showPrivacyModal && (
        <StudentPrivacySettingsModal onClose={() => setShowPrivacyModal(false)} />
      )}
    </div>
  );
}
