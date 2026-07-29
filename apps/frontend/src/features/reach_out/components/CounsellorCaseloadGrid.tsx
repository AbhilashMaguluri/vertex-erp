import { useState } from 'react';
import {
  Search,
  Star,
  MessageSquare,
  Mail,
  Phone,
  Linkedin,
  Github,
  Sparkles,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import { AssignedStudentContact, InstitutionalChannelPolicy } from '../types/reachOut';
import { useToggleFavoriteStudent } from '../api/reachOutApi';
import { Link } from 'react-router-dom';
import { cn } from '@/shared/utils/cn';

interface CounsellorCaseloadGridProps {
  students: AssignedStudentContact[];
  policy?: InstitutionalChannelPolicy;
  onSelectStudentModal: (student: AssignedStudentContact) => void;
  onOpenAiBriefing: (student: AssignedStudentContact) => void;
  onOpenTemplates: (student: AssignedStudentContact) => void;
}

export function CounsellorCaseloadGrid({
  students,
  policy,
  onSelectStudentModal,
  onOpenAiBriefing,
  onOpenTemplates,
}: CounsellorCaseloadGridProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const toggleFavoriteMutation = useToggleFavoriteStudent();

  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.roll_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFav = favoritesOnly ? s.is_favorite : true;
    return matchesSearch && matchesFav;
  });

  const favoriteStudents = students.filter((s) => s.is_favorite);

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
        return 'bg-rose-500/10 text-rose-600 border-rose-500/20';
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-600 border-amber-500/20';
      case 'MEDIUM':
        return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20';
      case 'LOW':
        return 'bg-blue-500/10 text-blue-600 border-blue-500/20';
      default:
        return 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20';
    }
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <Star
            key={i}
            className={`h-3 w-3 ${i <= Math.round(rating) ? 'text-amber-400 fill-amber-400' : 'text-muted-foreground/30'}`}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Pinned Favorite Students Bar */}
      {favoriteStudents.length > 0 && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-2 mb-3">
            <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
            <h3 className="text-xs font-black uppercase tracking-wider text-amber-700 dark:text-amber-300">
              ⭐ Pinned High-Touch Students ({favoriteStudents.length})
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {favoriteStudents.map((s) => (
              <button
                key={s.id}
                onClick={() => onSelectStudentModal(s)}
                className="inline-flex items-center gap-2 rounded-xl bg-card px-3 py-2 text-xs font-bold text-foreground border border-border/60 hover:border-amber-500/50 hover:shadow-md transition-all cursor-pointer"
              >
                <div className="h-6 w-6 rounded-full bg-brand-500/10 text-brand-600 font-extrabold flex items-center justify-center text-[10px] overflow-hidden">
                  {s.photo_url ? <img src={s.photo_url} alt="" className="h-full w-full object-cover" /> : s.name.charAt(0)}
                </div>
                <span>{s.name}</span>
                <span className="text-[10px] font-mono text-muted-foreground">({s.roll_number})</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filter and Search Toolbar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-card/80 p-3 rounded-2xl border border-border/60 backdrop-blur-md">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by student name or roll number..."
            className="w-full rounded-xl bg-muted/40 pl-9 pr-4 py-2 text-xs font-semibold text-foreground border border-border/40 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto justify-end">
          <button
            onClick={() => setFavoritesOnly(!favoritesOnly)}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold transition-all cursor-pointer border',
              favoritesOnly
                ? 'bg-amber-500 text-white border-amber-500 shadow-md'
                : 'bg-muted text-muted-foreground hover:bg-accent hover:text-foreground border-border/40'
            )}
          >
            <Star className={`h-3.5 w-3.5 ${favoritesOnly ? 'fill-white' : ''}`} />
            Starred Only
          </button>
          <span className="text-xs font-bold text-muted-foreground px-2">
            Showing {filteredStudents.length} Students
          </span>
        </div>
      </div>

      {/* Caseload Data Table */}
      <div className="overflow-hidden rounded-3xl border border-border/80 bg-card shadow-xl backdrop-blur-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border/60 bg-muted/40 text-[11px] font-black uppercase tracking-wider text-muted-foreground">
                <th className="py-3.5 px-4">Student Info</th>
                <th className="py-3.5 px-4">Academic Snapshot</th>
                <th className="py-3.5 px-4">Comm. Health</th>
                <th className="py-3.5 px-4">Parent Engagement</th>
                <th className="py-3.5 px-4">1-Click Launchers</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 text-xs">
              {filteredStudents.map((s) => (
                <tr key={s.id} className="hover:bg-muted/30 transition-colors group">
                  {/* Student Info */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => toggleFavoriteMutation.mutate({ studentId: s.id, isFavorite: s.is_favorite })}
                        className="text-muted-foreground hover:text-amber-400 transition-colors cursor-pointer"
                        title={s.is_favorite ? 'Unpin favorite' : 'Pin favorite'}
                      >
                        <Star className={`h-4 w-4 ${s.is_favorite ? 'text-amber-400 fill-amber-400' : ''}`} />
                      </button>

                      <div className="h-9 w-9 rounded-xl bg-brand-500/10 text-brand-600 font-extrabold flex items-center justify-center shrink-0 overflow-hidden ring-1 ring-border/50">
                        {s.photo_url ? (
                          <img src={s.photo_url} alt="" className="h-full w-full object-cover" />
                        ) : (
                          s.name.charAt(0)
                        )}
                      </div>

                      <div className="flex flex-col">
                        <button
                          onClick={() => onSelectStudentModal(s)}
                          className="font-black text-foreground hover:text-brand-600 text-left truncate flex items-center gap-1 group-hover:underline cursor-pointer"
                        >
                          {s.name}
                        </button>
                        <span className="text-[10px] font-mono font-bold text-muted-foreground">
                          {s.roll_number} • {s.department_name}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Academic Snapshot */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-foreground">{s.cgpa ? `${s.cgpa} CGPA` : 'N/A CGPA'}</span>
                      {s.attendance_pct != null ? (
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${
                            s.attendance_pct < 75 ? 'bg-rose-500/10 text-rose-600' : 'bg-emerald-500/10 text-emerald-600'
                          }`}
                        >
                          {s.attendance_pct}% Att.
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold text-muted-foreground">No Att.</span>
                      )}
                      <span className={cn('text-[9px] font-black uppercase px-2 py-0.5 rounded-full border', getRiskBadge(s.risk_level))}>
                        {s.risk_level}
                      </span>
                    </div>
                  </td>

                  {/* Communication Health */}
                  <td className="py-3.5 px-4">
                    {s.communication_health.has_data ? (
                      <div className="flex flex-col gap-0.5">
                        {renderStars(s.communication_health.score_stars)}
                        <span className="text-[10px] font-bold text-muted-foreground">
                          {s.communication_health.follow_up_compliance_pct}% Compliance
                        </span>
                      </div>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-muted-foreground/70 bg-muted px-2 py-1 rounded-md">
                        <AlertCircle className="h-3 w-3" /> Insufficient data.
                      </span>
                    )}
                  </td>

                  {/* Parent Engagement */}
                  <td className="py-3.5 px-4">
                    {s.parent_engagement.has_data ? (
                      <div className="flex flex-col gap-0.5">
                        {renderStars(s.parent_engagement.score_stars)}
                        <span className="text-[10px] font-bold text-muted-foreground">
                          {s.parent_engagement.total_calls} Calls • {s.parent_engagement.total_meetings} Meetings
                        </span>
                      </div>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-muted-foreground/70 bg-muted px-2 py-1 rounded-md">
                        <AlertCircle className="h-3 w-3" /> Insufficient data.
                      </span>
                    )}
                  </td>

                  {/* 1-Click Launchers */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1">
                      {s.whatsapp_number && (policy?.whatsapp_enabled ?? true) && (
                        <a
                          href={`https://wa.me/${s.whatsapp_number.replace(/[^0-9]/g, '')}`}
                          target="_blank"
                          rel="noreferrer"
                          className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 hover:bg-emerald-600 hover:text-white transition-all"
                          title="Open WhatsApp"
                        >
                          <MessageSquare className="h-3.5 w-3.5" />
                        </a>
                      )}

                      {s.college_email && (policy?.email_enabled ?? true) && (
                        <a
                          href={`mailto:${s.college_email}`}
                          className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 hover:bg-blue-600 hover:text-white transition-all"
                          title="Send Email"
                        >
                          <Mail className="h-3.5 w-3.5" />
                        </a>
                      )}

                      {s.phone && (policy?.phone_enabled ?? true) && (
                        <a
                          href={`tel:${s.phone}`}
                          className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/10 text-purple-600 hover:bg-purple-600 hover:text-white transition-all"
                          title="Call Phone"
                        >
                          <Phone className="h-3.5 w-3.5" />
                        </a>
                      )}

                      {s.linkedin_url && (policy?.linkedin_enabled ?? true) && (
                        <a
                          href={s.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex h-7 w-7 items-center justify-center rounded-lg bg-sky-500/10 text-sky-600 hover:bg-sky-600 hover:text-white transition-all"
                          title="View LinkedIn"
                        >
                          <Linkedin className="h-3.5 w-3.5" />
                        </a>
                      )}

                      {s.github_url && (
                        <a
                          href={s.github_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-500/10 text-slate-600 hover:bg-slate-800 hover:text-white transition-all"
                          title="View GitHub"
                        >
                          <Github className="h-3.5 w-3.5" />
                        </a>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => onOpenTemplates(s)}
                        className="inline-flex items-center gap-1 rounded-lg bg-muted px-2 py-1 text-[11px] font-bold text-foreground hover:bg-accent transition-all cursor-pointer border border-border/40"
                        title="Use Quick Template"
                      >
                        <MessageSquare className="h-3 w-3 text-emerald-600" /> Template
                      </button>
                      <button
                        onClick={() => onOpenAiBriefing(s)}
                        className="inline-flex items-center gap-1 rounded-lg bg-brand-500/10 px-2 py-1 text-[11px] font-bold text-brand-600 hover:bg-brand-500 hover:text-white transition-all cursor-pointer"
                        title="AI Pre-meeting Briefing"
                      >
                        <Sparkles className="h-3 w-3" /> AI Prep
                      </button>
                      <button
                        onClick={() => onSelectStudentModal(s)}
                        className="inline-flex items-center gap-1 rounded-lg bg-brand-600 px-2.5 py-1 text-[11px] font-bold text-white shadow-sm hover:bg-brand-700 transition-all cursor-pointer"
                      >
                        Contact Card
                      </button>
                      <Link
                        to={`/students/${s.id}`}
                        className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
                        title="Open Student 360"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}

              {filteredStudents.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs font-bold text-muted-foreground">
                    No students assigned or matching your search filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
