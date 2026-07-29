import { useState } from 'react';
import {
  Building2,
  MapPin,
  Clock,
  Phone,
  Mail,
  ExternalLink,
  MessageSquare,
  Linkedin,
  Video,
  Send,
  QrCode,
  Calendar,
  Sparkles,
  Info,
  ChevronDown,
  ChevronUp,
  GraduationCap,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';
import { CounsellorContactProfile, InstitutionalChannelPolicy } from '../types/reachOut';
import { cn } from '@/shared/utils/cn';

interface CounsellorPersonaCardProps {
  counsellor: CounsellorContactProfile;
  policy?: InstitutionalChannelPolicy;
  onOpenAppointmentModal: (type: string) => void;
  onOpenPrivacyModal?: () => void;
}

export function CounsellorPersonaCard({
  counsellor,
  policy,
  onOpenAppointmentModal,
  onOpenPrivacyModal,
}: CounsellorPersonaCardProps) {
  const [showSchedule, setShowSchedule] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return { label: 'Available Today', bg: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20', dot: 'bg-emerald-500 animate-pulse' };
      case 'BUSY':
        return { label: 'Busy', bg: 'bg-amber-500/10 text-amber-600 border-amber-500/20', dot: 'bg-amber-500' };
      case 'IN_SESSION':
        return { label: 'In Session', bg: 'bg-rose-500/10 text-rose-600 border-rose-500/20', dot: 'bg-rose-500 animate-pulse' };
      case 'ON_LEAVE':
        return { label: 'On Leave', bg: 'bg-purple-500/10 text-purple-600 border-purple-500/20', dot: 'bg-purple-500' };
      case 'OFFLINE':
      default:
        return { label: 'Offline', bg: 'bg-slate-500/10 text-slate-600 border-slate-500/20', dot: 'bg-slate-400' };
    }
  };

  const statusInfo = getStatusBadge(counsellor.office_status);
  const dynamicQrUrl = `${window.location.origin}/reach-out?counsellor_id=${counsellor.counsellor_id}`;

  const hasStructuredSchedule =
    counsellor.structured_schedule &&
    Object.values(counsellor.structured_schedule).some((d) => d.is_available && d.slots && d.slots.length > 0);

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border/80 bg-card/90 shadow-xl backdrop-blur-xl transition-all duration-300">
      {/* Header Banner Background */}
      <div className="h-36 w-full bg-gradient-to-r from-brand-700 via-brand-600 to-indigo-700 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.15),transparent_70%)]" />
        <div className="absolute top-4 right-4 flex items-center gap-2">
          {onOpenPrivacyModal && (
            <button
              onClick={onOpenPrivacyModal}
              className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-white backdrop-blur-md hover:bg-white/20 transition-all cursor-pointer"
            >
              <ShieldCheck className="h-3.5 w-3.5" /> My Sharing Privacy
            </button>
          )}
          <button
            onClick={() => setShowQrModal(true)}
            className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-white backdrop-blur-md hover:bg-white/20 transition-all cursor-pointer"
          >
            <QrCode className="h-3.5 w-3.5" /> Counsellor QR
          </button>
        </div>
      </div>

      {/* Main Profile Info Section */}
      <div className="px-6 pb-6 pt-0 relative">
        <div className="flex flex-col md:flex-row md:items-end justify-between -mt-16 mb-4 gap-4">
          <div className="flex flex-col md:flex-row items-center md:items-end gap-5 text-center md:text-left">
            <div className="relative h-28 w-28 rounded-2xl ring-4 ring-card shadow-xl overflow-hidden bg-brand-500/10 text-brand-600 font-black text-3xl flex items-center justify-center shrink-0">
              {counsellor.photo_url ? (
                <img
                  src={counsellor.photo_url}
                  alt={counsellor.full_name}
                  className="h-full w-full object-cover"
                />
              ) : (
                counsellor.full_name.charAt(0)
              )}
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2 justify-center md:justify-start">
                <h2 className="text-2xl font-black tracking-tight text-foreground">{counsellor.full_name}</h2>
                <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border', statusInfo.bg)}>
                  <span className={cn('h-2 w-2 rounded-full', statusInfo.dot)} />
                  {statusInfo.label}
                </span>
              </div>
              <p className="text-sm font-semibold text-brand-600 dark:text-brand-400 mt-0.5">
                {counsellor.designation} • {counsellor.department_name}
              </p>
              <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1 justify-center md:justify-start">
                <span className="font-semibold">{counsellor.years_experience} Years Experience</span>
                <span>•</span>
                <span className="truncate">{counsellor.status_message || 'No status message'}</span>
              </div>
            </div>
          </div>

          {/* Quick Action Buttons Header */}
          <div className="flex flex-wrap items-center justify-center md:justify-end gap-2">
            <button
              onClick={() => onOpenAppointmentModal('APPOINTMENT')}
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-black text-white shadow-md shadow-brand-600/25 hover:bg-brand-700 transition-all cursor-pointer"
            >
              <Calendar className="h-4 w-4" /> Book Appointment
            </button>
            <button
              onClick={() => onOpenAppointmentModal('COUNSELLING')}
              className="inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-xs font-bold text-foreground hover:bg-accent/80 transition-all cursor-pointer border border-border/60"
            >
              <Sparkles className="h-4 w-4 text-brand-600" /> Request Counselling
            </button>
          </div>
        </div>

        {/* Languages & Specializations Badges */}
        {(counsellor.languages_spoken.length > 0 || counsellor.specializations.length > 0) && (
          <div className="flex flex-wrap items-center gap-1.5 mb-3">
            {counsellor.languages_spoken.map((lang) => (
              <span key={lang} className="rounded-md bg-blue-500/10 px-2 py-0.5 text-[10px] font-bold text-blue-600">
                🗣️ {lang}
              </span>
            ))}
            {counsellor.specializations.map((spec) => (
              <span key={spec} className="rounded-md bg-brand-500/10 px-2 py-0.5 text-[10px] font-bold text-brand-600">
                🎯 {spec}
              </span>
            ))}
          </div>
        )}

        {/* Bio */}
        {counsellor.about_me && (
          <p className="text-xs text-muted-foreground leading-relaxed mb-4 bg-muted/30 p-3 rounded-xl border border-border/40">
            {counsellor.about_me}
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 py-3 border-y border-border/60">
          {/* Cabin Details */}
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 shrink-0">
              <Building2 className="h-4 w-4" />
            </div>
            <div>
              <span className="text-[10px] font-black uppercase text-muted-foreground tracking-wider">Cabin & Location</span>
              <p className="text-xs font-extrabold text-foreground mt-0.5">
                {counsellor.building}, {counsellor.floor}, {counsellor.cabin_number}
              </p>
              {counsellor.maps_url && (
                <a
                  href={counsellor.maps_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] font-bold text-brand-600 hover:underline mt-1"
                >
                  <MapPin className="h-3 w-3" /> View Google Maps <ExternalLink className="h-2.5 w-2.5" />
                </a>
              )}
            </div>
          </div>

          {/* Office Hours & Schedule Toggle */}
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 shrink-0">
              <Clock className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <span className="text-[10px] font-black uppercase text-muted-foreground tracking-wider">Office Hours</span>
              <p className="text-xs font-extrabold text-foreground mt-0.5">
                {hasStructuredSchedule ? 'Weekly Timetable Configured' : 'Schedule not configured.'}
              </p>
              {hasStructuredSchedule && (
                <button
                  onClick={() => setShowSchedule(!showSchedule)}
                  className="inline-flex items-center gap-1 text-[11px] font-bold text-brand-600 hover:underline mt-1 cursor-pointer"
                >
                  {showSchedule ? 'Hide Full Schedule' : 'View Timetable'}
                  {showSchedule ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>
              )}
            </div>
          </div>

          {/* Direct Office Contacts */}
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 shrink-0">
              <Phone className="h-4 w-4" />
            </div>
            <div>
              <span className="text-[10px] font-black uppercase text-muted-foreground tracking-wider">Official Contacts</span>
              <div className="flex flex-col gap-0.5 mt-0.5">
                {counsellor.college_email && (
                  <a href={`mailto:${counsellor.college_email}`} className="text-xs font-bold text-foreground hover:text-brand-600 truncate flex items-center gap-1">
                    <Mail className="h-3 w-3 text-muted-foreground" /> {counsellor.college_email}
                  </a>
                )}
                {counsellor.office_phone && (
                  <a href={`tel:${counsellor.office_phone}`} className="text-xs font-bold text-foreground hover:text-brand-600 flex items-center gap-1">
                    <Phone className="h-3 w-3 text-muted-foreground" /> {counsellor.office_phone}
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Structured Weekly Schedule Timetable Drawer */}
        {showSchedule && counsellor.structured_schedule && (
          <div className="mt-4 rounded-2xl bg-muted/40 p-4 border border-border/60 animate-in fade-in duration-200">
            <h4 className="text-xs font-black uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-brand-600" /> Weekly Availability Timetable
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {Object.entries(counsellor.structured_schedule).map(([day, val]) => (
                <div key={day} className="rounded-xl bg-card p-2.5 border border-border/50 text-center">
                  <span className="text-[11px] font-black capitalize text-foreground">{day}</span>
                  {val.is_available && val.slots.length > 0 ? (
                    <div className="mt-1 space-y-1">
                      {val.slots.map((s, idx) => (
                        <span key={idx} className="block text-[10px] font-bold text-emerald-600 bg-emerald-500/10 rounded-md py-0.5 px-1">
                          {s.start} - {s.end}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="block text-[10px] font-extrabold text-muted-foreground/60 mt-1">Unavailable</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Direct One-Click Communication Launchers */}
        <div className="mt-5">
          <span className="text-[10px] font-black uppercase text-muted-foreground tracking-widest block mb-2">
            Approved One-Click Communication Channels
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {counsellor.whatsapp_number && (policy?.whatsapp_enabled ?? true) && (
              <a
                href={`https://wa.me/${counsellor.whatsapp_number.replace(/[^0-9]/g, '')}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-emerald-600/10 text-emerald-600 px-3 py-2 text-xs font-bold hover:bg-emerald-600 hover:text-white transition-all border border-emerald-500/20 shadow-sm"
              >
                <MessageSquare className="h-3.5 w-3.5" /> WhatsApp
              </a>
            )}

            {counsellor.college_email && (policy?.email_enabled ?? true) && (
              <a
                href={`mailto:${counsellor.college_email}`}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600/10 text-blue-600 px-3 py-2 text-xs font-bold hover:bg-blue-600 hover:text-white transition-all border border-blue-500/20 shadow-sm"
              >
                <Mail className="h-3.5 w-3.5" /> Send Email
              </a>
            )}

            {counsellor.teams_url && (policy?.teams_enabled ?? true) && (
              <a
                href={counsellor.teams_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600/10 text-indigo-600 px-3 py-2 text-xs font-bold hover:bg-indigo-600 hover:text-white transition-all border border-indigo-500/20 shadow-sm"
              >
                <Video className="h-3.5 w-3.5" /> MS Teams
              </a>
            )}

            {counsellor.google_meet_url && (policy?.google_meet_enabled ?? true) && (
              <a
                href={counsellor.google_meet_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-red-600/10 text-red-600 px-3 py-2 text-xs font-bold hover:bg-red-600 hover:text-white transition-all border border-red-500/20 shadow-sm"
              >
                <Video className="h-3.5 w-3.5" /> Google Meet
              </a>
            )}

            {counsellor.linkedin_url && (policy?.linkedin_enabled ?? true) && (
              <a
                href={counsellor.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-sky-600/10 text-sky-600 px-3 py-2 text-xs font-bold hover:bg-sky-600 hover:text-white transition-all border border-sky-500/20 shadow-sm"
              >
                <Linkedin className="h-3.5 w-3.5" /> LinkedIn Profile
              </a>
            )}

            {counsellor.telegram_url && (policy?.telegram_enabled ?? true) && (
              <a
                href={counsellor.telegram_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-sky-500/10 text-sky-500 px-3 py-2 text-xs font-bold hover:bg-sky-500 hover:text-white transition-all border border-sky-500/20 shadow-sm"
              >
                <Send className="h-3.5 w-3.5" /> Telegram
              </a>
            )}
          </div>
        </div>

        {/* Extended Guidance Request Actions */}
        <div className="mt-4 pt-4 border-t border-border/60 flex flex-wrap gap-2">
          <button
            onClick={() => onOpenAppointmentModal('CAREER_GUIDANCE')}
            className="inline-flex items-center gap-1.5 rounded-lg bg-muted px-3 py-1.5 text-xs font-bold text-foreground hover:bg-accent transition-all cursor-pointer border border-border/40"
          >
            <GraduationCap className="h-3.5 w-3.5 text-brand-600" /> Career Guidance Request
          </button>
          <button
            onClick={() => onOpenAppointmentModal('ACADEMIC_GUIDANCE')}
            className="inline-flex items-center gap-1.5 rounded-lg bg-muted px-3 py-1.5 text-xs font-bold text-foreground hover:bg-accent transition-all cursor-pointer border border-border/40"
          >
            <Info className="h-3.5 w-3.5 text-brand-600" /> Academic Guidance Request
          </button>
          <button
            onClick={() => onOpenAppointmentModal('PARENT_MEETING')}
            className="inline-flex items-center gap-1.5 rounded-lg bg-muted px-3 py-1.5 text-xs font-bold text-foreground hover:bg-accent transition-all cursor-pointer border border-border/40"
          >
            <UserCheck className="h-3.5 w-3.5 text-brand-600" /> Request Parent Meeting
          </button>
        </div>
      </div>

      {/* QR Code Generator Modal */}
      {showQrModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-sm rounded-3xl bg-card p-6 shadow-2xl border border-border/80 text-center">
            <h3 className="text-lg font-black text-foreground">Counsellor Contact QR</h3>
            <p className="text-xs text-muted-foreground mt-1">
              Scan with your mobile camera to open {counsellor.full_name}'s profile & book appointments.
            </p>
            <div className="my-6 mx-auto flex h-48 w-48 items-center justify-center rounded-2xl bg-white p-3 ring-4 ring-brand-500/20 shadow-inner">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(dynamicQrUrl)}`}
                alt="QR Code"
                className="h-full w-full object-contain"
              />
            </div>
            <button
              onClick={() => setShowQrModal(false)}
              className="w-full rounded-xl bg-brand-600 py-2.5 text-xs font-bold text-white hover:bg-brand-700 transition-all cursor-pointer shadow-md"
            >
              Close QR Code
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
