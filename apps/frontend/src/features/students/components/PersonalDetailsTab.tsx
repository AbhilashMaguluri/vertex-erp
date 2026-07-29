/**
 * Section 1 of the Student 360° Workspace — Personal Details.
 *
 * This is the student-owned half of the profile: ten collapsible cards, each
 * autosaving its own section independently, so a student can fill in what
 * they know now and come back later without ever pressing Save.
 *
 * The same component serves the counsellor's read-only view (`editable`
 * omitted). Read-only mode renders values, never disabled inputs — a greyed
 * out form reads as broken rather than as someone else's data.
 *
 * Everything institution-owned (roll number, branch, semester, marks) lives
 * in AcademicDetailsTab and is not editable from anywhere on this page.
 */
import * as React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  Braces,
  Camera,
  Download,
  FileText,
  Globe,
  HeartPulse,
  Lightbulb,
  Loader2,
  Lock,
  MapPin,
  Plus,
  Trash2,
  Trophy,
  UserRound,
  Users,
} from 'lucide-react';
import {
  Achievement,
  DOCUMENT_TYPES,
  EXTRACURRICULAR_ACTIVITIES,
  GENDERS,
  StudentSelfProfile,
  SUPPORT_AREAS,
  BLOOD_GROUPS,
  profileService,
} from '../services/profile.service';
import { StudentAvatar } from './StudentPresentation';
import { TagInput, TagList, ValueField, extractApiError } from './ProfileForm';
import {
  AuthedImage,
  AutoInput,
  AutoSelect,
  AutoTextArea,
  ChipList,
  CollapsibleCard,
  FieldShell,
  FilledBadge,
  LockedValue,
  MultiSelectChips,
  PhotoUploadDialog,
  useSectionAutosave,
  validators,
} from './ProfileWorkspaceKit';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { cn } from '@/shared/utils/cn';

const PROFILE_QUERY_KEY = ['students', 'me', 'profile'];

interface PersonalDetailsTabProps {
  profile: StudentSelfProfile;
  /** True only on the student's own /my-profile page. */
  editable?: boolean;
  /** Legacy prop from the counsellor workspace; kept so existing call sites
   *  keep compiling. It never grants edit rights on its own. */
  isStudentMode?: boolean;
}

// ---------------------------------------------------------------------------
// Shared field slot
// ---------------------------------------------------------------------------

function Slot({
  label,
  required,
  hint,
  error,
  editable,
  value,
  display,
  className,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string | null;
  editable: boolean;
  /** Read-only rendering for plain values. */
  value?: string | number | null;
  /** Read-only rendering for anything richer (chips, links). */
  display?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}) {
  if (!editable) {
    return (
      <div className={className}>
        {display ? (
          <div className="space-y-1">
            <div className="text-[10px] font-black uppercase tracking-wider text-muted-foreground">{label}</div>
            {display}
          </div>
        ) : (
          <ValueField label={label} value={value} />
        )}
      </div>
    );
  }
  return (
    <div className={className}>
      <FieldShell label={label} required={required} hint={hint} error={error}>
        {children}
      </FieldShell>
    </div>
  );
}

function Grid({ children, cols = 2 }: { children: React.ReactNode; cols?: 2 | 3 }) {
  return (
    <div className={cn('grid grid-cols-1 gap-4', cols === 3 ? 'sm:grid-cols-2 lg:grid-cols-3' : 'sm:grid-cols-2')}>
      {children}
    </div>
  );
}

function countFilled(values: unknown[]): number {
  return values.filter((v) => {
    if (v === null || v === undefined) return false;
    if (typeof v === 'string') return v.trim().length > 0;
    if (Array.isArray(v)) return v.length > 0;
    return true;
  }).length;
}

/** Wires one card's autosave to the cached profile, so the completion ring
 *  and every other card update from the response of the save itself. */
function useProfileSection<T extends Record<string, any>>(
  initial: T,
  save: (patch: Record<string, unknown>) => Promise<StudentSelfProfile>,
  fieldValidators?: Partial<Record<keyof T, (v: unknown) => string | null>>
) {
  const queryClient = useQueryClient();
  const onSave = React.useCallback(
    async (patch: Partial<T>) => {
      const updated = await save(patch as Record<string, unknown>);
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
      return updated;
    },
    [queryClient, save]
  );
  return useSectionAutosave<T>({ initial, onSave, validators: fieldValidators });
}

// ---------------------------------------------------------------------------
// A. Profile information
// ---------------------------------------------------------------------------

function ProfileInformationCard({
  profile,
  editable,
}: {
  profile: StudentSelfProfile;
  editable: boolean;
}) {
  const queryClient = useQueryClient();
  const [photoOpen, setPhotoOpen] = React.useState(false);

  const section = useProfileSection(
    {
      first_name: profile.first_name ?? '',
      last_name: profile.last_name ?? '',
      preferred_name: profile.preferred_name ?? '',
      date_of_birth: profile.date_of_birth ?? '',
      gender: profile.gender ?? '',
      blood_group: profile.blood_group ?? '',
      aadhaar_number: profile.aadhaar_number ?? '',
      mother_tongue: profile.mother_tongue ?? '',
      languages_known: profile.languages_known ?? [],
    },
    profileService.updatePersonal,
    {
      date_of_birth: validators.pastDate,
      aadhaar_number: validators.aadhaar,
    }
  );

  const contact = useProfileSection(
    {
      mobile_number: profile.mobile_number ?? '',
      personal_email: profile.personal_email ?? '',
    },
    profileService.updateContact,
    { mobile_number: validators.phone, personal_email: validators.email }
  );

  const uploadPhoto = async (file: File) => {
    const updated = await profileService.uploadPhoto(file);
    queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
    // The blob for the previous photo is keyed by its URL, so a new upload
    // fetches fresh bytes rather than showing the old crop.
    queryClient.invalidateQueries({ queryKey: ['authed-image'] });
  };

  const { draft, setField, status, error, fieldErrors } = section;
  const filled = countFilled([
    profile.photo_url,
    profile.date_of_birth,
    profile.gender,
    profile.blood_group,
    profile.mobile_number,
    profile.personal_email,
    profile.aadhaar_number,
    profile.mother_tongue,
    profile.languages_known,
  ]);

  const maskedAadhaar = profile.aadhaar_number
    ? `XXXX XXXX ${profile.aadhaar_number.slice(-4)}`
    : null;

  return (
    <CollapsibleCard
      id="profile-info"
      title="A. Profile Information"
      description="Photo, name, date of birth and how we reach you"
      icon={UserRound}
      accent="brand"
      defaultOpen
      status={status === 'idle' ? contact.status : status}
      error={error ?? contact.error}
      badge={<FilledBadge filled={filled} total={9} />}
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative">
            <AuthedImage
              src={profile.photo_url}
              alt={profile.identity.full_name}
              className="h-20 w-20 rounded-2xl object-cover ring-1 ring-border"
              fallback={<StudentAvatar name={profile.identity.full_name} size="lg" />}
            />
            {editable && (
              <button
                type="button"
                onClick={() => setPhotoOpen(true)}
                className="absolute -bottom-1 -right-1 rounded-full bg-brand-600 p-2 text-white shadow-md hover:bg-brand-700"
                title="Upload or replace photo"
              >
                <Camera className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-black text-foreground">{profile.identity.full_name}</p>
            <p className="font-mono text-xs font-bold text-brand-600">{profile.identity.roll_number}</p>
            <p className="text-[11px] text-muted-foreground">
              {profile.photo_url ? 'Passport size photograph on file' : 'No photograph uploaded yet'}
            </p>
          </div>
        </div>

        <Grid cols={3}>
          <Slot label="First name" required editable={editable} value={profile.first_name} error={fieldErrors.first_name}>
            <AutoInput value={draft.first_name} onCommit={(v) => setField('first_name', v)} />
          </Slot>
          <Slot label="Last name" required editable={editable} value={profile.last_name} error={fieldErrors.last_name}>
            <AutoInput value={draft.last_name} onCommit={(v) => setField('last_name', v)} />
          </Slot>
          <Slot
            label="Preferred name"
            editable={editable}
            value={profile.preferred_name}
            hint="What you would like to be called"
          >
            <AutoInput value={draft.preferred_name} onCommit={(v) => setField('preferred_name', v)} />
          </Slot>

          <Slot
            label="Date of birth"
            required
            editable={editable}
            value={profile.date_of_birth}
            error={fieldErrors.date_of_birth}
          >
            <AutoInput type="date" value={draft.date_of_birth} onCommit={(v) => setField('date_of_birth', v)} />
          </Slot>
          <Slot label="Gender" required editable={editable} value={profile.gender}>
            <AutoSelect value={draft.gender} onCommit={(v) => setField('gender', v)} options={GENDERS} />
          </Slot>
          <Slot label="Blood group" required editable={editable} value={profile.blood_group}>
            <AutoSelect value={draft.blood_group} onCommit={(v) => setField('blood_group', v)} options={BLOOD_GROUPS} />
          </Slot>

          <Slot
            label="Aadhaar number"
            editable={editable}
            value={maskedAadhaar}
            error={fieldErrors.aadhaar_number}
            hint="Stored securely; shown masked to staff"
          >
            <AutoInput
              inputMode="numeric"
              maxLength={12}
              placeholder="12 digits"
              value={draft.aadhaar_number}
              onCommit={(v) => setField('aadhaar_number', v.replace(/\D/g, ''))}
              error={fieldErrors.aadhaar_number}
            />
          </Slot>
          <Slot
            label="Mobile number"
            required
            editable={editable}
            value={profile.mobile_number}
            error={contact.fieldErrors.mobile_number}
          >
            <AutoInput
              inputMode="tel"
              value={contact.draft.mobile_number}
              onCommit={(v) => contact.setField('mobile_number', v)}
              error={contact.fieldErrors.mobile_number}
            />
          </Slot>
          <Slot
            label="Personal email"
            required
            editable={editable}
            value={profile.personal_email}
            error={contact.fieldErrors.personal_email}
          >
            <AutoInput
              type="email"
              value={contact.draft.personal_email}
              onCommit={(v) => contact.setField('personal_email', v)}
              error={contact.fieldErrors.personal_email}
            />
          </Slot>
        </Grid>

        <Grid cols={3}>
          <LockedValue
            label="College email"
            value={profile.identity.college_email}
            reason="Issued by the institution"
          />
          <Slot label="Mother tongue" editable={editable} value={profile.mother_tongue}>
            <AutoInput value={draft.mother_tongue} onCommit={(v) => setField('mother_tongue', v)} />
          </Slot>
          <Slot
            label="Languages known"
            editable={editable}
            display={<TagList value={profile.languages_known} />}
          >
            <TagInput
              value={draft.languages_known}
              onChange={(next) => setField('languages_known', next)}
              placeholder="Telugu, English…"
            />
          </Slot>
        </Grid>
      </div>

      <PhotoUploadDialog open={photoOpen} onClose={() => setPhotoOpen(false)} onUpload={uploadPhoto} />
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// B. Personal information
// ---------------------------------------------------------------------------

function PersonalInformationCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const { draft, setField, status, error } = useProfileSection(
    {
      strengths: profile.strengths ?? '',
      weaknesses: profile.weaknesses ?? '',
      career_goal: profile.career_goal ?? '',
      self_introduction: profile.self_introduction ?? '',
      support_areas: profile.support_areas ?? [],
      support_areas_other: profile.support_areas_other ?? '',
    },
    profileService.updateSkills
  );

  const showOther = (draft.support_areas ?? []).includes('OTHER');
  const filled = countFilled([
    profile.strengths,
    profile.weaknesses,
    profile.career_goal,
    profile.support_areas,
    profile.self_introduction,
  ]);

  return (
    <CollapsibleCard
      id="personal-info"
      title="B. Personal Information"
      description="Strengths, goals and the support you would like"
      icon={Lightbulb}
      accent="purple"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={5} />}
    >
      <div className="space-y-5">
        <Grid>
          <Slot label="Strengths" required editable={editable} value={profile.strengths}>
            <AutoTextArea value={draft.strengths} onCommit={(v) => setField('strengths', v)} />
          </Slot>
          <Slot label="Weaknesses" required editable={editable} value={profile.weaknesses}>
            <AutoTextArea value={draft.weaknesses} onCommit={(v) => setField('weaknesses', v)} />
          </Slot>
          <Slot label="Career goal" required editable={editable} value={profile.career_goal}>
            <AutoTextArea value={draft.career_goal} onCommit={(v) => setField('career_goal', v)} />
          </Slot>
          <Slot
            label="Short self introduction"
            editable={editable}
            value={profile.self_introduction}
            hint="A few lines your counsellor reads before your first session"
          >
            <AutoTextArea value={draft.self_introduction} onCommit={(v) => setField('self_introduction', v)} />
          </Slot>
        </Grid>

        <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
          <Slot
            label="Areas where support is required"
            required
            editable={editable}
            display={<ChipList value={profile.support_areas} options={SUPPORT_AREAS} empty="None selected" />}
            hint="Select everything that applies — this is what your counsellor acts on first"
          >
            <MultiSelectChips
              options={SUPPORT_AREAS}
              value={draft.support_areas ?? []}
              onChange={(next) => setField('support_areas', next)}
            />
          </Slot>

          {(editable ? showOther : !!profile.support_areas_other) && (
            <div className="mt-4">
              <Slot label="Please specify" editable={editable} value={profile.support_areas_other}>
                <AutoInput
                  value={draft.support_areas_other}
                  onCommit={(v) => setField('support_areas_other', v)}
                  placeholder="Tell us what kind of support you need"
                />
              </Slot>
            </div>
          )}
        </div>
      </div>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// C. Skills
// ---------------------------------------------------------------------------

function SkillsCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const { draft, setField, status, error } = useProfileSection(
    {
      programming_languages: profile.programming_languages ?? [],
      technical_skills: profile.technical_skills ?? [],
      soft_skills: profile.soft_skills ?? [],
      tools_technologies: profile.tools_technologies ?? [],
      other_skills: profile.other_skills ?? [],
    },
    profileService.updateSkills
  );

  const filled = countFilled([
    profile.programming_languages,
    profile.technical_skills,
    profile.soft_skills,
    profile.tools_technologies,
  ]);

  const lists: [keyof typeof draft, string, string][] = [
    ['programming_languages', 'Programming languages', 'Python, Java, C++…'],
    ['technical_skills', 'Technical skills', 'Data structures, DBMS…'],
    ['soft_skills', 'Soft skills', 'Teamwork, public speaking…'],
    ['tools_technologies', 'Tools & technologies', 'Git, Docker, Figma…'],
    ['other_skills', 'Other skills', 'Anything else you know'],
  ];

  return (
    <CollapsibleCard
      id="skills"
      title="C. Skills"
      description="Tagged so your counsellor can match you to opportunities"
      icon={Braces}
      accent="sky"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={4} />}
    >
      <div className="space-y-5">
        <Grid>
          {lists.map(([key, label, placeholder]) => (
            <Slot
              key={key}
              label={label}
              editable={editable}
              display={<TagList value={profile[key as keyof StudentSelfProfile] as string[] | null} />}
            >
              <TagInput
                value={(draft[key] as string[]) ?? []}
                onChange={(next) => setField(key, next as never)}
                placeholder={placeholder}
              />
            </Slot>
          ))}
        </Grid>

        <CertificationsPanel studentId={profile.identity.student_id} editable={editable} />
      </div>
    </CollapsibleCard>
  );
}

/** Certifications are stored as achievements with category CERTIFICATION —
 *  the same records the counsellor already sees, rather than a parallel list
 *  that could disagree with them. */
function CertificationsPanel({ studentId, editable }: { studentId: string; editable: boolean }) {
  const queryClient = useQueryClient();
  const [adding, setAdding] = React.useState(false);
  const [form, setForm] = React.useState({ title: '', issuer: '', achieved_on: '', credential_url: '' });
  const [formError, setFormError] = React.useState<string | null>(null);

  const { data, isLoading } = useQuery<Achievement[]>({
    queryKey: ['students', studentId, 'achievements'],
    queryFn: () => (editable ? profileService.listAchievements() : profileService.listStudentAchievements(studentId)),
  });

  const certifications = (data ?? []).filter((a) => a.category === 'CERTIFICATION');

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['students', studentId, 'achievements'] });

  const create = useMutation({
    mutationFn: () =>
      profileService.createAchievement({
        category: 'CERTIFICATION',
        title: form.title,
        issuer: form.issuer || undefined,
        achieved_on: form.achieved_on || undefined,
        credential_url: form.credential_url || undefined,
      }),
    onSuccess: () => {
      setForm({ title: '', issuer: '', achieved_on: '', credential_url: '' });
      setAdding(false);
      setFormError(null);
      invalidate();
    },
    onError: (err) => setFormError(extractApiError(err, 'Could not add that certification.')),
  });

  const remove = useMutation({
    mutationFn: (id: string) => profileService.deleteAchievement(id),
    onSuccess: invalidate,
  });

  return (
    <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-black text-foreground">Certifications</p>
          <p className="text-[11px] text-muted-foreground">Courses and credentials you have earned</p>
        </div>
        {editable && !adding && (
          <Button variant="outline" size="sm" onClick={() => setAdding(true)}>
            <Plus className="mr-1 h-3.5 w-3.5" /> Add
          </Button>
        )}
      </div>

      {formError && <p className="mb-3 text-[11px] font-semibold text-rose-600">{formError}</p>}

      {adding && (
        <div className="mb-3 space-y-3 rounded-xl border border-border/60 bg-card p-3">
          <Grid>
            <FieldShell label="Certification name" required>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </FieldShell>
            <FieldShell label="Issuing organisation">
              <Input value={form.issuer} onChange={(e) => setForm({ ...form, issuer: e.target.value })} />
            </FieldShell>
            <FieldShell label="Issued on">
              <Input
                type="date"
                value={form.achieved_on}
                onChange={(e) => setForm({ ...form, achieved_on: e.target.value })}
              />
            </FieldShell>
            <FieldShell label="Credential URL">
              <Input
                placeholder="https://…"
                value={form.credential_url}
                onChange={(e) => setForm({ ...form, credential_url: e.target.value })}
              />
            </FieldShell>
          </Grid>
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setAdding(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={() => create.mutate()}
              disabled={!form.title.trim()}
              isLoading={create.isPending}
            >
              Save certification
            </Button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="text-[11px] text-muted-foreground">Loading…</p>
      ) : certifications.length === 0 ? (
        <p className="text-[11px] italic text-muted-foreground/60">No certifications added yet.</p>
      ) : (
        <ul className="space-y-2">
          {certifications.map((c) => (
            <li
              key={c.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-border/50 bg-card p-3"
            >
              <div className="min-w-0">
                <p className="truncate text-xs font-bold text-foreground">{c.title}</p>
                <p className="truncate text-[11px] text-muted-foreground">
                  {[c.issuer, c.achieved_on].filter(Boolean).join(' • ') || 'No issuer recorded'}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {c.credential_url && (
                  <a
                    href={c.credential_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-bold text-brand-600 hover:underline"
                  >
                    View
                  </a>
                )}
                {editable && (
                  <button
                    type="button"
                    onClick={() => remove.mutate(c.id)}
                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-rose-500/10 hover:text-rose-600"
                    aria-label={`Remove ${c.title}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// D. Extracurricular activities
// ---------------------------------------------------------------------------

function ExtracurricularCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const { draft, setField, status, error } = useProfileSection(
    {
      activities: profile.extracurricular_activities ?? [],
      extracurricular_other: profile.extracurricular_other ?? '',
      extracurricular_achievements: profile.extracurricular_achievements ?? '',
    },
    profileService.updateExtracurricular
  );

  const showOther = (draft.activities ?? []).includes('OTHER');
  const filled = countFilled([profile.extracurricular_activities, profile.extracurricular_achievements]);

  return (
    <CollapsibleCard
      id="extracurricular"
      title="D. Extracurricular Activities"
      description="NCC, NSS, sports, clubs and everything beyond the classroom"
      icon={Trophy}
      accent="amber"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={2} />}
    >
      <div className="space-y-5">
        <Slot
          label="Activities you take part in"
          editable={editable}
          display={
            <ChipList
              value={profile.extracurricular_activities}
              options={EXTRACURRICULAR_ACTIVITIES}
              empty="None selected"
            />
          }
        >
          <MultiSelectChips
            options={EXTRACURRICULAR_ACTIVITIES}
            value={draft.activities ?? []}
            onChange={(next) => setField('activities', next)}
          />
        </Slot>

        {(editable ? showOther : !!profile.extracurricular_other) && (
          <Slot label="Other activities" editable={editable} value={profile.extracurricular_other}>
            <AutoInput
              value={draft.extracurricular_other}
              onCommit={(v) => setField('extracurricular_other', v)}
            />
          </Slot>
        )}

        <Slot
          label="Achievements & positions held"
          editable={editable}
          value={profile.extracurricular_achievements}
          hint="Captaincies, office bearer roles, prizes, event leadership"
        >
          <AutoTextArea
            rows={4}
            value={draft.extracurricular_achievements}
            onCommit={(v) => setField('extracurricular_achievements', v)}
          />
        </Slot>
      </div>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// E. Family details
// ---------------------------------------------------------------------------

function FamilyCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const { draft, setField, status, error, fieldErrors } = useProfileSection(
    {
      father_name: profile.father_name ?? '',
      father_occupation: profile.father_occupation ?? '',
      father_phone: profile.father_phone ?? '',
      mother_name: profile.mother_name ?? '',
      mother_occupation: profile.mother_occupation ?? '',
      mother_phone: profile.mother_phone ?? '',
      guardian_name: profile.guardian_name ?? '',
      guardian_relation: profile.guardian_relation ?? '',
      guardian_phone: profile.guardian_phone ?? '',
    },
    profileService.updateFamily,
    {
      father_phone: validators.phone,
      mother_phone: validators.phone,
      guardian_phone: validators.phone,
    }
  );

  const filled = countFilled([
    profile.father_name,
    profile.father_occupation,
    profile.father_phone,
    profile.mother_name,
    profile.mother_occupation,
    profile.mother_phone,
  ]);

  const block = (
    who: 'father' | 'mother' | 'guardian',
    heading: string,
    required: boolean,
    middleLabel: string
  ) => {
    const middleKey = (who === 'guardian' ? 'guardian_relation' : `${who}_occupation`) as keyof typeof draft;
    return (
      <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
        <p className="mb-3 text-xs font-black text-foreground">{heading}</p>
        <Grid cols={3}>
          <Slot label="Name" required={required} editable={editable} value={profile[`${who}_name`]}>
            <AutoInput
              value={draft[`${who}_name` as keyof typeof draft] as string}
              onCommit={(v) => setField(`${who}_name` as keyof typeof draft, v)}
            />
          </Slot>
          <Slot label={middleLabel} required={false} editable={editable} value={profile[middleKey]}>
            <AutoInput
              value={draft[middleKey] as string}
              onCommit={(v) => setField(middleKey, v)}
            />
          </Slot>
          <Slot
            label="Mobile number"
            required={required}
            editable={editable}
            value={profile[`${who}_phone`]}
            error={fieldErrors[`${who}_phone` as keyof typeof draft]}
          >
            <AutoInput
              inputMode="tel"
              value={draft[`${who}_phone` as keyof typeof draft] as string}
              onCommit={(v) => setField(`${who}_phone` as keyof typeof draft, v)}
              error={fieldErrors[`${who}_phone` as keyof typeof draft]}
            />
          </Slot>
        </Grid>
      </div>
    );
  };

  return (
    <CollapsibleCard
      id="family"
      title="E. Family Details"
      description="Parents and, if applicable, your guardian"
      icon={Users}
      accent="emerald"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={6} />}
    >
      <div className="space-y-4">
        {block('father', 'Father', true, 'Occupation')}
        {block('mother', 'Mother', true, 'Occupation')}
        {block('guardian', 'Guardian (optional)', false, 'Relationship')}
      </div>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// F. Contact details
// ---------------------------------------------------------------------------

function ContactCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const { draft, setField, status, error, fieldErrors } = useProfileSection(
    {
      current_address: profile.current_address ?? '',
      city: profile.city ?? '',
      district: profile.district ?? '',
      state: profile.state ?? '',
      pin_code: profile.pin_code ?? '',
      permanent_address: profile.permanent_address ?? '',
      permanent_city: profile.permanent_city ?? '',
      permanent_district: profile.permanent_district ?? '',
      permanent_state: profile.permanent_state ?? '',
      permanent_pin_code: profile.permanent_pin_code ?? '',
      permanent_same_as_current: profile.permanent_same_as_current ?? false,
    },
    profileService.updateContact,
    { pin_code: validators.pin, permanent_pin_code: validators.pin }
  );

  const sameAsCurrent = !!draft.permanent_same_as_current;
  const filled = countFilled([
    profile.current_address,
    profile.city,
    profile.state,
    profile.pin_code,
    profile.permanent_address,
  ]);

  return (
    <CollapsibleCard
      id="contact"
      title="F. Contact Details"
      description="Where you live now and your permanent address"
      icon={MapPin}
      accent="indigo"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={5} />}
    >
      <div className="space-y-4">
        <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
          <p className="mb-3 text-xs font-black text-foreground">Current address</p>
          <div className="space-y-4">
            <Slot label="Address line" required editable={editable} value={profile.current_address}>
              <AutoTextArea rows={2} value={draft.current_address} onCommit={(v) => setField('current_address', v)} />
            </Slot>
            <Grid cols={3}>
              <Slot label="City" required editable={editable} value={profile.city}>
                <AutoInput value={draft.city} onCommit={(v) => setField('city', v)} />
              </Slot>
              <Slot label="District" editable={editable} value={profile.district}>
                <AutoInput value={draft.district} onCommit={(v) => setField('district', v)} />
              </Slot>
              <Slot label="State" required editable={editable} value={profile.state}>
                <AutoInput value={draft.state} onCommit={(v) => setField('state', v)} />
              </Slot>
              <Slot
                label="PIN code"
                required
                editable={editable}
                value={profile.pin_code}
                error={fieldErrors.pin_code}
              >
                <AutoInput
                  inputMode="numeric"
                  maxLength={6}
                  value={draft.pin_code}
                  onCommit={(v) => setField('pin_code', v.replace(/\D/g, ''))}
                  error={fieldErrors.pin_code}
                />
              </Slot>
            </Grid>
          </div>
        </div>

        <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs font-black text-foreground">Permanent address</p>
            {editable ? (
              <label className="flex cursor-pointer items-center gap-2 text-[11px] font-bold text-muted-foreground">
                <input
                  type="checkbox"
                  className="h-3.5 w-3.5 accent-brand-600"
                  checked={sameAsCurrent}
                  onChange={(e) => setField('permanent_same_as_current', e.target.checked)}
                />
                Same as current address
              </label>
            ) : (
              profile.permanent_same_as_current && (
                <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-extrabold text-muted-foreground">
                  Same as current
                </span>
              )
            )}
          </div>

          {sameAsCurrent && editable ? (
            <p className="text-[11px] text-muted-foreground">
              Your permanent address will be kept in step with your current address.
            </p>
          ) : (
            <div className="space-y-4">
              <Slot label="Address line" required editable={editable} value={profile.permanent_address}>
                <AutoTextArea
                  rows={2}
                  value={draft.permanent_address}
                  onCommit={(v) => setField('permanent_address', v)}
                />
              </Slot>
              <Grid cols={3}>
                <Slot label="City" editable={editable} value={profile.permanent_city}>
                  <AutoInput value={draft.permanent_city} onCommit={(v) => setField('permanent_city', v)} />
                </Slot>
                <Slot label="District" editable={editable} value={profile.permanent_district}>
                  <AutoInput value={draft.permanent_district} onCommit={(v) => setField('permanent_district', v)} />
                </Slot>
                <Slot label="State" editable={editable} value={profile.permanent_state}>
                  <AutoInput value={draft.permanent_state} onCommit={(v) => setField('permanent_state', v)} />
                </Slot>
                <Slot
                  label="PIN code"
                  editable={editable}
                  value={profile.permanent_pin_code}
                  error={fieldErrors.permanent_pin_code}
                >
                  <AutoInput
                    inputMode="numeric"
                    maxLength={6}
                    value={draft.permanent_pin_code}
                    onCommit={(v) => setField('permanent_pin_code', v.replace(/\D/g, ''))}
                    error={fieldErrors.permanent_pin_code}
                  />
                </Slot>
              </Grid>
            </div>
          )}
        </div>
      </div>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// G. Emergency contact
// ---------------------------------------------------------------------------

function EmergencyCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const { draft, setField, status, error, fieldErrors } = useProfileSection(
    {
      emergency_contact_name: profile.emergency_contact_name ?? '',
      emergency_contact_relation: profile.emergency_contact_relation ?? '',
      emergency_contact_phone: profile.emergency_contact_phone ?? '',
    },
    profileService.updateContact,
    { emergency_contact_phone: validators.phone }
  );

  const filled = countFilled([
    profile.emergency_contact_name,
    profile.emergency_contact_relation,
    profile.emergency_contact_phone,
  ]);

  return (
    <CollapsibleCard
      id="emergency"
      title="G. Emergency Contact"
      description="Who the college calls first in an emergency"
      icon={AlertTriangle}
      accent="rose"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={3} />}
    >
      <Grid cols={3}>
        <Slot label="Contact name" required editable={editable} value={profile.emergency_contact_name}>
          <AutoInput
            value={draft.emergency_contact_name}
            onCommit={(v) => setField('emergency_contact_name', v)}
          />
        </Slot>
        <Slot label="Relationship" required editable={editable} value={profile.emergency_contact_relation}>
          <AutoInput
            value={draft.emergency_contact_relation}
            onCommit={(v) => setField('emergency_contact_relation', v)}
          />
        </Slot>
        <Slot
          label="Phone number"
          required
          editable={editable}
          value={profile.emergency_contact_phone}
          error={fieldErrors.emergency_contact_phone}
        >
          <AutoInput
            inputMode="tel"
            value={draft.emergency_contact_phone}
            onCommit={(v) => setField('emergency_contact_phone', v)}
            error={fieldErrors.emergency_contact_phone}
          />
        </Slot>
      </Grid>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// H. Health information
// ---------------------------------------------------------------------------

function HealthCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const { draft, setField, status, error } = useProfileSection(
    {
      medical_conditions: profile.medical_conditions ?? '',
      allergies: profile.allergies ?? '',
      disability: profile.disability ?? '',
      current_medications: profile.current_medications ?? '',
      health_notes: profile.health_notes ?? '',
    },
    profileService.updateHealth
  );

  const filled = countFilled([profile.medical_conditions, profile.allergies]);

  return (
    <CollapsibleCard
      id="health"
      title="H. Health Information"
      description="Shared with your counsellor only while contact sharing is on"
      icon={HeartPulse}
      accent="rose"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={2} />}
    >
      <div className="space-y-4">
        <p className="rounded-xl border border-border/60 bg-muted/30 p-3 text-[11px] text-muted-foreground">
          Everything here is optional. It is visible to your counsellor only while you allow contact details to be
          shared, and to nobody else.
        </p>
        <Grid>
          <Slot label="Existing medical conditions" editable={editable} value={profile.medical_conditions}>
            <AutoTextArea value={draft.medical_conditions} onCommit={(v) => setField('medical_conditions', v)} />
          </Slot>
          <Slot label="Allergies" editable={editable} value={profile.allergies}>
            <AutoTextArea value={draft.allergies} onCommit={(v) => setField('allergies', v)} />
          </Slot>
          <Slot label="Disability (if applicable)" editable={editable} value={profile.disability}>
            <AutoTextArea value={draft.disability} onCommit={(v) => setField('disability', v)} />
          </Slot>
          <Slot label="Current medications" editable={editable} value={profile.current_medications}>
            <AutoTextArea value={draft.current_medications} onCommit={(v) => setField('current_medications', v)} />
          </Slot>
        </Grid>
        <Slot label="Other health notes" editable={editable} value={profile.health_notes}>
          <AutoTextArea value={draft.health_notes} onCommit={(v) => setField('health_notes', v)} />
        </Slot>
      </div>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// I. Professional links
// ---------------------------------------------------------------------------

const LINK_FIELDS: { key: keyof StudentSelfProfile; label: string; placeholder: string }[] = [
  { key: 'linkedin_url', label: 'LinkedIn profile', placeholder: 'https://linkedin.com/in/…' },
  { key: 'github_url', label: 'GitHub', placeholder: 'https://github.com/…' },
  { key: 'portfolio_url', label: 'Portfolio website', placeholder: 'https://…' },
  { key: 'leetcode_url', label: 'LeetCode', placeholder: 'https://leetcode.com/…' },
  { key: 'codechef_url', label: 'CodeChef', placeholder: 'https://codechef.com/users/…' },
  { key: 'hackerrank_url', label: 'HackerRank', placeholder: 'https://hackerrank.com/…' },
  { key: 'codeforces_url', label: 'Codeforces', placeholder: 'https://codeforces.com/profile/…' },
  { key: 'other_coding_url', label: 'Other coding profile', placeholder: 'https://…' },
];

function LinksCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const initial = Object.fromEntries(
    LINK_FIELDS.map((f) => [f.key, (profile[f.key] as string | null) ?? ''])
  ) as Record<string, string>;

  const { draft, setField, status, error, fieldErrors } = useProfileSection(
    initial,
    profileService.updateSkills,
    Object.fromEntries(LINK_FIELDS.map((f) => [f.key, validators.url]))
  );

  const filled = countFilled([profile.linkedin_url, profile.github_url, profile.resume_url]);

  return (
    <CollapsibleCard
      id="links"
      title="I. Professional Links"
      description="Portfolio and coding profiles recruiters look at"
      icon={Globe}
      accent="sky"
      status={status}
      error={error}
      badge={<FilledBadge filled={filled} total={3} />}
    >
      <Grid>
        {LINK_FIELDS.map((f) => {
          const saved = profile[f.key] as string | null;
          return (
            <Slot
              key={f.key as string}
              label={f.label}
              editable={editable}
              error={fieldErrors[f.key as string]}
              display={
                saved ? (
                  <a
                    href={saved}
                    target="_blank"
                    rel="noreferrer"
                    className="break-all text-xs font-bold text-brand-600 hover:underline"
                  >
                    {saved}
                  </a>
                ) : (
                  <span className="text-xs italic text-muted-foreground/50">Not provided</span>
                )
              }
            >
              <AutoInput
                placeholder={f.placeholder}
                value={draft[f.key as string]}
                onCommit={(v) => setField(f.key as string, v)}
                error={fieldErrors[f.key as string]}
              />
            </Slot>
          );
        })}
      </Grid>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// J. Documents
// ---------------------------------------------------------------------------

const MAX_UPLOAD_MB = 10;

function DocumentsCard({ profile, editable }: { profile: StudentSelfProfile; editable: boolean }) {
  const studentId = profile.identity.student_id;
  const queryClient = useQueryClient();
  const [docType, setDocType] = React.useState<string>(DOCUMENT_TYPES[1].value);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const fileRef = React.useRef<HTMLInputElement | null>(null);

  const { data: documents, isLoading } = useQuery({
    queryKey: ['students', studentId, 'documents'],
    queryFn: () => (editable ? profileService.listDocuments() : profileService.listStudentDocuments(studentId)),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['students', studentId, 'documents'] });

  const upload = useMutation({
    mutationFn: (file: File) => profileService.uploadDocument(file, docType),
    onSuccess: () => {
      setUploadError(null);
      invalidate();
    },
    onError: (err) => setUploadError(extractApiError(err, 'Upload failed.')),
  });

  const remove = useMutation({
    mutationFn: (id: string) => profileService.deleteDocument(id),
    onSuccess: invalidate,
  });

  const handleFile = (file?: File) => {
    if (!file) return;
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setUploadError(`That file is larger than ${MAX_UPLOAD_MB}MB.`);
      return;
    }
    upload.mutate(file);
  };

  const labelFor = (value: string) =>
    DOCUMENT_TYPES.find((d) => d.value === value)?.label ?? value.replace(/_/g, ' ');

  return (
    <CollapsibleCard
      id="documents"
      title="J. Documents"
      description="Certificates and memos your counsellor may need"
      icon={FileText}
      accent="indigo"
      badge={
        <span className="hidden rounded-full bg-muted px-2 py-0.5 text-[10px] font-extrabold text-muted-foreground sm:inline-flex">
          {documents?.length ?? 0} uploaded
        </span>
      }
    >
      <div className="space-y-4">
        {editable && (
          <div className="flex flex-wrap items-end gap-3 rounded-2xl border border-border/60 bg-muted/20 p-4">
            <div className="min-w-[200px] flex-1">
              <FieldShell label="Document type" required>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="h-10 w-full rounded-xl border border-input bg-background px-3 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {DOCUMENT_TYPES.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </FieldShell>
            </div>
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
              onChange={(e) => {
                handleFile(e.target.files?.[0]);
                e.target.value = '';
              }}
            />
            <Button onClick={() => fileRef.current?.click()} isLoading={upload.isPending} size="sm">
              <Plus className="mr-1 h-3.5 w-3.5" /> Upload
            </Button>
            <p className="w-full text-[11px] text-muted-foreground">
              PDF, JPG, PNG, WEBP, DOC or DOCX — up to {MAX_UPLOAD_MB}MB each.
            </p>
          </div>
        )}

        {uploadError && <p className="text-[11px] font-semibold text-rose-600">{uploadError}</p>}

        {isLoading ? (
          <p className="flex items-center gap-2 text-[11px] text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" /> Loading documents…
          </p>
        ) : !documents?.length ? (
          <p className="text-[11px] italic text-muted-foreground/60">No documents uploaded yet.</p>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-border/50 bg-card p-3"
              >
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-foreground">
                    {doc.title || doc.original_filename}
                  </p>
                  <p className="truncate text-[11px] text-muted-foreground">
                    {labelFor(doc.document_type)} • {(doc.size_bytes / 1024).toFixed(0)} KB
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() =>
                      profileService.downloadDocument(studentId, doc.id, doc.original_filename, doc.file_url)
                    }
                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                    aria-label={`Download ${doc.original_filename}`}
                  >
                    <Download className="h-3.5 w-3.5" />
                  </button>
                  {editable && (
                    <button
                      type="button"
                      onClick={() => remove.mutate(doc.id)}
                      className="rounded-lg p-1.5 text-muted-foreground hover:bg-rose-500/10 hover:text-rose-600"
                      aria-label={`Delete ${doc.original_filename}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </CollapsibleCard>
  );
}

// ---------------------------------------------------------------------------
// Section 1
// ---------------------------------------------------------------------------

export function PersonalDetailsTab({ profile, editable = false }: PersonalDetailsTabProps) {
  return (
    <div className="space-y-3">
      {editable && (
        <p className="flex items-center gap-2 rounded-2xl border border-border/60 bg-muted/20 px-4 py-2.5 text-[11px] font-medium text-muted-foreground">
          <Activity className="h-3.5 w-3.5 shrink-0 text-brand-600" />
          Changes save automatically as you type. Fields marked
          <span className="font-black text-rose-500">*</span> are required.
        </p>
      )}

      <ProfileInformationCard profile={profile} editable={editable} />
      <PersonalInformationCard profile={profile} editable={editable} />
      <SkillsCard profile={profile} editable={editable} />
      <ExtracurricularCard profile={profile} editable={editable} />
      <FamilyCard profile={profile} editable={editable} />
      <ContactCard profile={profile} editable={editable} />
      <EmergencyCard profile={profile} editable={editable} />
      <HealthCard profile={profile} editable={editable} />
      <LinksCard profile={profile} editable={editable} />
      <DocumentsCard profile={profile} editable={editable} />

      {!editable && (
        <p className="flex items-center gap-2 px-1 pt-2 text-[11px] text-muted-foreground">
          <Lock className="h-3.5 w-3.5 shrink-0" />
          Student-maintained information. Only the student can change it.
        </p>
      )}
    </div>
  );
}
