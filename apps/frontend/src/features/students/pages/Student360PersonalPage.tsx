import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { profileService, StudentSelfProfile } from '../services/profile.service';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { AuthedImage } from '../components/ProfileWorkspaceKit';
import { StudentAvatar } from '../components/StudentPresentation';
import {
  UserRound,
  Contact,
  MapPin,
  Users,
  HeartPulse,
  Building,
  FileText,
  Globe,
  Braces,
  ArrowRight,
  Lock,
} from 'lucide-react';

export function Student360PersonalPage() {
  const navigate = useNavigate();

  const {
    data: profile,
    isLoading,
    error,
  } = useQuery<StudentSelfProfile>({
    queryKey: ['students', 'me', 'profile'],
    queryFn: profileService.getSelfProfile,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-44 rounded-3xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-64 rounded-3xl" />
          <Skeleton className="h-64 rounded-3xl" />
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <EmptyState
        icon={UserRound}
        title="Unable to load Student 360 Profile"
        description="Could not retrieve your record from the central database."
      />
    );
  }

  const { identity } = profile;
  const maskedAadhaar = profile.aadhaar_number
    ? `XXXX XXXX ${profile.aadhaar_number.slice(-4)}`
    : 'Not provided';

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Student 360 Portal', to: '/student-360/personal' }, { label: 'Personal Details' }]} />

      {/* READ-ONLY WORKSPACE BANNER */}
      <div className="relative overflow-hidden rounded-3xl border border-border/80 bg-gradient-to-r from-card via-muted/30 to-card p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <AuthedImage
              src={profile.photo_url}
              alt={identity.full_name}
              className="h-20 w-20 rounded-2xl object-cover ring-2 ring-brand-500/20"
              fallback={<StudentAvatar name={identity.full_name} size="lg" />}
            />
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-black text-foreground">{identity.full_name}</h1>
                <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600 font-bold">
                  {identity.status}
                </Badge>
                <Badge variant="outline" className="border-brand-500/30 bg-brand-500/10 text-brand-600 font-bold">
                  {identity.department_name || 'Department'}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground font-mono">
                <span>Roll: <strong className="text-foreground">{identity.roll_number}</strong></span>
                <span>Reg: <strong className="text-foreground">{identity.registration_number}</strong></span>
                <span>Batch: <strong className="text-foreground">{identity.batch_year}</strong></span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-xs text-amber-700">
            <Lock className="h-4 w-4 text-amber-600 shrink-0" />
            <span>
              <strong>Read-Only Workspace:</strong> To edit personal information, navigate to <strong className="underline">My Profile</strong>.
            </span>
          </div>
        </div>
      </div>

      {/* CARDS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* A. Profile & Personal Info */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <UserRound className="h-4 w-4 text-brand-500" /> Personal Information
              </CardTitle>
              <CardDescription className="text-xs">Identity and core personal details</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/personal')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <GridRow label="Full Name" value={identity.full_name} />
            <GridRow label="Preferred Name" value={profile.preferred_name} />
            <GridRow label="Date of Birth" value={profile.date_of_birth} />
            <GridRow label="Gender" value={profile.gender} />
            <GridRow label="Blood Group" value={profile.blood_group} />
            <GridRow label="Mother Tongue" value={profile.mother_tongue} />
            <GridRow label="Languages Known" value={profile.languages_known?.join(', ')} />
            <GridRow label="Self Introduction" value={profile.self_introduction} fullWidth />
          </CardContent>
        </Card>

        {/* B. Contact Details */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Contact className="h-4 w-4 text-brand-500" /> Contact Details
              </CardTitle>
              <CardDescription className="text-xs">Mobile numbers and email addresses</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/contact')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <GridRow label="Mobile Number" value={profile.mobile_number} />
            <GridRow label="Personal Email" value={profile.personal_email} />
            <GridRow label="College Email" value={identity.college_email} />
            <GridRow label="Alternate Phone" value={profile.alternate_phone} />
            <GridRow label="Preferred Contact" value={profile.preferred_communication_method} />
            <GridRow label="Preferred Call Time" value={profile.preferred_call_time} />
          </CardContent>
        </Card>

        {/* C. Address Details */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <MapPin className="h-4 w-4 text-brand-500" /> Address Details
              </CardTitle>
              <CardDescription className="text-xs">Current and permanent residence</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/address')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <GridRow
              label="Current Address"
              value={[profile.current_address, profile.city, profile.district, profile.state, profile.pin_code]
                .filter(Boolean)
                .join(', ')}
              fullWidth
            />
            <GridRow
              label="Permanent Address"
              value={
                profile.permanent_same_as_current
                  ? 'Same as Current Address'
                  : [profile.permanent_address, profile.permanent_city, profile.permanent_district, profile.permanent_state, profile.permanent_pin_code]
                      .filter(Boolean)
                      .join(', ')
              }
              fullWidth
            />
          </CardContent>
        </Card>

        {/* D. Parent & Guardian Information */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Users className="h-4 w-4 text-brand-500" /> Parent &amp; Guardian Information
              </CardTitle>
              <CardDescription className="text-xs">Family contacts and occupations</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/family')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <GridRow label="Father's Name" value={profile.father_name} />
            <GridRow label="Father's Phone" value={profile.father_phone} />
            <GridRow label="Mother's Name" value={profile.mother_name} />
            <GridRow label="Mother's Phone" value={profile.mother_phone} />
            <GridRow label="Guardian Name" value={profile.guardian_name} />
            <GridRow label="Guardian Phone" value={profile.guardian_phone} />
            <GridRow label="Emergency Contact" value={profile.emergency_contact_name ? `${profile.emergency_contact_name} (${profile.emergency_contact_phone || ''})` : null} fullWidth />
          </CardContent>
        </Card>

        {/* E. Medical & Health */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <HeartPulse className="h-4 w-4 text-brand-500" /> Medical &amp; Health Information
              </CardTitle>
              <CardDescription className="text-xs">Health background on file</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/medical')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <GridRow label="Medical Conditions" value={profile.medical_conditions} />
            <GridRow label="Allergies" value={profile.allergies} />
            <GridRow label="Disability Details" value={profile.disability} />
            <GridRow label="Current Medications" value={profile.current_medications} />
          </CardContent>
        </Card>

        {/* F. Hostel / Residence */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Building className="h-4 w-4 text-brand-500" /> Hostel &amp; Residence
              </CardTitle>
              <CardDescription className="text-xs">Day scholar or hostel accommodation</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/personal')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <GridRow label="Residence Type" value={profile.hostel_type ? profile.hostel_type.replace('_', ' ') : 'Day Scholar'} />
            <GridRow label="Hostel Name" value={profile.hostel_name} />
            <GridRow label="Block / Room" value={[profile.hostel_block, profile.hostel_room_number].filter(Boolean).join(' - ')} />
          </CardContent>
        </Card>

        {/* G. Government Documents */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <FileText className="h-4 w-4 text-brand-500" /> Government Identity Documents
              </CardTitle>
              <CardDescription className="text-xs">Official document records (Masked for privacy)</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/documents')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <GridRow label="Aadhaar Number" value={maskedAadhaar} />
            <GridRow label="Category" value={profile.category} />
            <GridRow label="Nationality" value={profile.nationality} />
            <GridRow label="Religion" value={profile.religion} />
          </CardContent>
        </Card>

        {/* H. Professional & Coding Links */}
        <Card className="rounded-3xl border-border/80 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Globe className="h-4 w-4 text-brand-500" /> Professional Links
              </CardTitle>
              <CardDescription className="text-xs">LinkedIn, GitHub &amp; coding profiles</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/links')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <LinkGridRow label="LinkedIn" url={profile.linkedin_url} />
            <LinkGridRow label="GitHub" url={profile.github_url} />
            <LinkGridRow label="Portfolio" url={profile.portfolio_url} />
            <LinkGridRow label="LeetCode" url={profile.leetcode_url} />
            <LinkGridRow label="CodeChef" url={profile.codechef_url} />
          </CardContent>
        </Card>

        {/* I. Skills & Extracurriculars */}
        <Card className="rounded-3xl border-border/80 shadow-md md:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Braces className="h-4 w-4 text-brand-500" /> Skills &amp; Extracurricular Activities
              </CardTitle>
              <CardDescription className="text-xs">Technical skills and extracurricular achievements</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-xs font-bold text-brand-600 border-brand-500/30 hover:bg-brand-500/10"
              onClick={() => navigate('/my-profile/personal')}
            >
              Edit <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <TagRow label="Programming Languages" tags={profile.programming_languages} />
            <TagRow label="Technical Skills" tags={profile.technical_skills} />
            <TagRow label="Tools & Technologies" tags={profile.tools_technologies} />
            <TagRow label="Soft Skills" tags={profile.soft_skills} />
            <TagRow label="Extracurricular Activities" tags={profile.extracurricular_activities} />
            <GridRow label="Extracurricular Achievements" value={profile.extracurricular_achievements} fullWidth />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function GridRow({ label, value, fullWidth }: { label: string; value?: string | number | null; fullWidth?: boolean }) {
  return (
    <div className={fullWidth ? 'col-span-full' : ''}>
      <span className="text-[10px] font-black uppercase text-muted-foreground block">{label}</span>
      <span className="text-xs font-bold text-foreground mt-0.5 block">
        {value ? String(value) : <span className="text-muted-foreground/60 italic">Not provided</span>}
      </span>
    </div>
  );
}

function LinkGridRow({ label, url }: { label: string; url?: string | null }) {
  return (
    <div>
      <span className="text-[10px] font-black uppercase text-muted-foreground block">{label}</span>
      {url ? (
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-bold text-brand-600 hover:underline truncate block"
        >
          {url}
        </a>
      ) : (
        <span className="text-xs text-muted-foreground/60 italic">Not provided</span>
      )}
    </div>
  );
}

function TagRow({ label, tags }: { label: string; tags?: string[] | null }) {
  return (
    <div>
      <span className="text-[10px] font-black uppercase text-muted-foreground block mb-1">{label}</span>
      {tags && tags.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((t, idx) => (
            <Badge key={idx} variant="secondary" className="text-xs font-semibold">
              {t}
            </Badge>
          ))}
        </div>
      ) : (
        <span className="text-xs text-muted-foreground/60 italic">None listed</span>
      )}
    </div>
  );
}
