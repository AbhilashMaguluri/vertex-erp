import * as React from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { profileService, StudentSelfProfile } from '../services/profile.service';
import { studentService, Student360Data } from '../services/student.service';
import { counsellingService } from '@/features/counselling/services/counselling.service';
import { notificationService } from '@/features/notifications/services/notification.service';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { PersonalDetailsTab } from '../components/PersonalDetailsTab';
import { AcademicDetailsTab } from '../components/AcademicDetailsTab';
import { CounsellorSectionTab } from '../components/CounsellorSectionTab';
import { AuthedImage } from '../components/ProfileWorkspaceKit';
import { StudentAvatar } from '../components/StudentPresentation';
import {
  User,
  GraduationCap,
  Award,
  CalendarCheck,
  AlertCircle,
  Bell,
  MessageSquare,
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '@/shared/utils/cn';

type MajorSection = 'personal' | 'academic' | 'counsellor';

const SECTIONS: { key: MajorSection; label: string; icon: React.ElementType }[] = [
  { key: 'personal', label: '1. Personal', icon: User },
  { key: 'academic', label: '2. Academic', icon: GraduationCap },
  { key: 'counsellor', label: '3. Counsellor', icon: ShieldCheck },
];

function statValue(workspace: Student360Data | undefined, title: string): string {
  const stat = workspace?.stats?.find((s) => s.title.toLowerCase() === title.toLowerCase());
  return stat?.value ?? 'No data';
}

function SummaryTile({
  label,
  value,
  icon: Icon,
  tone = 'default',
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  tone?: 'default' | 'good' | 'warn';
}) {
  const hasData = value !== 'No data';
  return (
    <div className="p-3 rounded-2xl bg-card border border-border/50 text-center">
      <span className="text-[10px] font-black uppercase text-muted-foreground block">{label}</span>
      <span
        className={cn(
          'text-xl font-black flex items-center justify-center gap-1',
          !hasData && 'text-muted-foreground/50 text-sm font-bold',
          hasData && tone === 'good' && 'text-emerald-600',
          hasData && tone === 'warn' && 'text-amber-600',
          hasData && tone === 'default' && 'text-foreground'
        )}
      >
        <Icon className="h-4 w-4 shrink-0" /> {value}
      </span>
    </div>
  );
}

function ProfileSummaryStrip({
  workspaceData,
  sessionCount,
  unreadCount,
  completionPercentage,
}: {
  workspaceData: Student360Data;
  sessionCount?: number;
  unreadCount?: number;
  completionPercentage: number;
}) {
  const sgpaStat = workspaceData.stats?.find((s) => s.title.toLowerCase() === 'current sgpa');
  const cgpaMatch = sgpaStat?.description?.match(/CGPA:\s*([\d.]+)/i);

  return (
    <div className="rounded-3xl border border-border/80 bg-gradient-to-r from-card via-muted/30 to-card p-6 shadow-xl relative overflow-hidden">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <SummaryTile label="Current CGPA" value={cgpaMatch ? cgpaMatch[1] : 'No data'} icon={Award} tone="good" />
        <SummaryTile
          label="Attendance"
          value={statValue(workspaceData, 'Overall Attendance')}
          icon={CalendarCheck}
        />
        <SummaryTile
          label="Open Backlogs"
          value={statValue(workspaceData, 'Active Backlogs')}
          icon={AlertCircle}
        />
        <SummaryTile
          label="Counselling Sessions"
          value={sessionCount === undefined ? 'No data' : sessionCount}
          icon={MessageSquare}
        />
        <SummaryTile
          label="Notifications"
          value={unreadCount === undefined ? 'No data' : `${unreadCount} unread`}
          icon={Bell}
        />
        <SummaryTile
          label="Completeness"
          value={`${completionPercentage}%`}
          icon={CheckCircle2}
          tone={completionPercentage >= 80 ? 'good' : 'warn'}
        />
      </div>
    </div>
  );
}

export function MyProfilePage() {
  const { section: routeSection } = useParams<{ section?: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const subSection = routeSection || searchParams.get('section') || 'personal';
  const isPersonalSubSection = ['personal', 'contact', 'address', 'family', 'medical', 'documents', 'links'].includes(
    subSection
  );

  const activeSection: MajorSection = isPersonalSubSection
    ? 'personal'
    : subSection === 'academic' || subSection === 'counsellor'
    ? (subSection as MajorSection)
    : 'personal';

  React.useEffect(() => {
    if (isPersonalSubSection && subSection !== 'personal') {
      const elementIdMap: Record<string, string> = {
        contact: 'profile-info',
        address: 'address-info',
        family: 'family-info',
        medical: 'medical-info',
        documents: 'documents-info',
        links: 'portfolio-info',
      };
      const targetId = elementIdMap[subSection];
      if (targetId) {
        setTimeout(() => {
          const el = document.getElementById(targetId);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 300);
      }
    }
  }, [subSection, isPersonalSubSection]);

  const setSection = (section: MajorSection) => {
    navigate(`/my-profile/${section}`);
  };


  // Fetch self-service personal profile
  const {
    data: profile,
    isLoading: isLoadingProfile,
    error: profileError,
  } = useQuery<StudentSelfProfile>({
    queryKey: ['students', 'me', 'profile'],
    queryFn: profileService.getSelfProfile,
  });

  // Fetch workspace academic data
  const {
    data: workspaceData,
    isLoading: isLoadingWorkspace,
    error: workspaceError,
  } = useQuery<Student360Data>({
    queryKey: ['students', 'me', 'workspace'],
    queryFn: studentService.getMyWorkspace,
  });

  // The summary strip reports real counts or says "No data" — it must never
  // show a placeholder figure, because a student reads these as their own
  // academic standing.
  const { data: mySessions } = useQuery({
    queryKey: ['counselling', 'my-sessions'],
    queryFn: counsellingService.getMySessions,
  });

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: notificationService.getUnreadCount,
  });

  const sessionCount = mySessions?.length;

  if (isLoadingProfile || isLoadingWorkspace) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-28 rounded-3xl" />
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <Skeleton className="h-96 rounded-3xl lg:col-span-1" />
          <Skeleton className="h-96 rounded-3xl lg:col-span-3" />
        </div>
      </div>
    );
  }

  if (profileError || workspaceError || !profile || !workspaceData) {
    return (
      <EmptyState
        icon={User}
        title="Unable to load Student 360 Profile"
        description="Could not retrieve your record from the central database."
      />
    );
  }

  const { identity, completion } = profile;

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Student 360° Workspace' }]} />

      {/* TOP DASHBOARD ACTIVITY OVERVIEW HEADER */}
      <ProfileSummaryStrip
        workspaceData={workspaceData}
        sessionCount={sessionCount}
        unreadCount={unreadCount}
        completionPercentage={completion.percentage}
      />

      {/* TWO MAJOR SECTION WORKSPACE LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

        {/* DESKTOP STICKY SUMMARY SIDEBAR */}
        <div className="lg:col-span-1 space-y-4">
          <div className="sticky top-6 rounded-3xl border border-border/80 bg-card p-6 shadow-xl text-center space-y-4">
            {/* Upload lives on the Profile Information card, which is where a
                student edits everything else about their photo. */}
            <div className="mx-auto inline-block">
              <AuthedImage
                src={profile.photo_url}
                alt={identity.full_name}
                className="h-16 w-16 rounded-2xl object-cover ring-1 ring-border/70"
                fallback={<StudentAvatar name={identity.full_name} size="lg" />}
              />
            </div>

            <div>
              <h2 className="text-lg font-black text-foreground">{identity.full_name}</h2>
              <p className="text-xs font-mono font-bold text-brand-600 mt-0.5">{identity.roll_number}</p>
              <div className="flex items-center justify-center gap-1.5 mt-2">
                <span className="inline-flex rounded-full bg-emerald-500/10 text-emerald-600 px-2.5 py-0.5 text-[10px] font-extrabold">
                  {identity.status}
                </span>
                <span className="inline-flex rounded-full bg-brand-500/10 text-brand-600 px-2.5 py-0.5 text-[10px] font-extrabold">
                  {identity.department_name || 'Department'}
                </span>
              </div>
            </div>

            {/* WEIGHTED PROFILE COMPLETENESS RING & CHECKLIST */}
            <div className="p-4 rounded-2xl bg-muted/30 border border-border/40 text-left space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black text-foreground">Profile Completion</span>
                <span className="text-xs font-black text-brand-600">{completion.percentage}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-emerald-500 transition-all duration-500"
                  style={{ width: `${completion.percentage}%` }}
                />
              </div>
              {completion?.top_missing && completion.top_missing.length > 0 && (
                <div className="mt-2 text-[10px] font-semibold text-muted-foreground space-y-1">
                  <span className="font-bold text-amber-600 block">Missing Information:</span>
                  <ul className="list-disc list-inside space-y-0.5">
                    {completion.top_missing.map((item, idx) => (
                      <li key={idx} className="truncate">{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* MAIN WORKSPACE VIEW (2 MAJOR SECTIONS) */}
        <div className="lg:col-span-3 space-y-6">

          {/* MAJOR SECTION TOGGLE */}
          <div
            role="tablist"
            aria-label="Profile sections"
            className="flex items-center gap-1 rounded-2xl border border-border/60 bg-muted/40 p-1.5"
          >
            {SECTIONS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                role="tab"
                aria-selected={activeSection === key}
                onClick={() => setSection(key)}
                className={cn(
                  'flex flex-1 items-center justify-center gap-1.5 rounded-xl px-3 py-2.5 text-[11px] font-black transition-all sm:text-xs',
                  activeSection === key
                    ? 'border border-border/80 bg-card text-foreground shadow-md'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="truncate">{label}</span>
              </button>
            ))}
          </div>

          {/* SECTION 1: PERSONAL DETAILS — student editable */}
          {activeSection === 'personal' && <PersonalDetailsTab profile={profile} editable />}

          {/* SECTION 2: ACADEMIC DETAILS — ERP owned, read-only */}
          {activeSection === 'academic' && (
            <AcademicDetailsTab workspaceData={workspaceData} profile={profile} isStudentMode />
          )}

          {/* SECTION 3: COUNSELLOR SECTION — staff authored, read-only */}
          {activeSection === 'counsellor' && <CounsellorSectionTab />}

        </div>
      </div>
    </div>
  );
}
