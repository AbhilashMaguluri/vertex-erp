import React, { useState } from 'react';
import {
  X,
  Phone,
  Mail,
  MessageSquare,
  Linkedin,
  Github,
  Globe,
  Code2,
  Plus,
  Sparkles,
  ExternalLink,
  UserCheck,
} from 'lucide-react';
import { AssignedStudentContact } from '../types/reachOut';
import { useStudentTimeline, useLogCommunication } from '../api/reachOutApi';

interface EnrichedStudentModalProps {
  student: AssignedStudentContact;
  onClose: () => void;
}

export function EnrichedStudentModal({ student, onClose }: EnrichedStudentModalProps) {
  const [activeTab, setActiveTab] = useState<'CONTACT' | 'PARENT' | 'TIMELINE'>('CONTACT');
  const [showLogForm, setShowLogForm] = useState(false);

  const { data: timelineLogs, isLoading: isTimelineLoading } = useStudentTimeline(student.id, activeTab === 'TIMELINE');
  const logMutation = useLogCommunication();

  // Log form state
  const [channel, setChannel] = useState('WHATSAPP');
  const [direction, setDirection] = useState('COUNSELLOR_TO_STUDENT');
  const [summary, setSummary] = useState('');
  const [sentiment] = useState('POSITIVE');
  const [actionOutcome, setActionOutcome] = useState('RESOLVED');
  const [duration, setDuration] = useState<number | undefined>(15);
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [followUpDate] = useState('');

  const handleLogSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    logMutation.mutate(
      {
        studentId: student.id,
        data: {
          channel,
          direction,
          summary,
          sentiment,
          action_outcome: actionOutcome,
          duration_minutes: duration,
          follow_up_required: followUpRequired,
          follow_up_date: followUpDate || undefined,
        },
      },
      {
        onSuccess: () => {
          setShowLogForm(false);
          setSummary('');
        },
      }
    );
  };

  const parents = student.parent_contacts;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-3xl rounded-3xl bg-card shadow-2xl border border-border/80 relative overflow-hidden max-h-[92vh] flex flex-col">
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-brand-700 via-brand-600 to-indigo-700 p-6 text-white relative shrink-0">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-all cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>

          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-2xl ring-4 ring-white/20 bg-white/10 text-white font-black flex items-center justify-center text-xl overflow-hidden shrink-0">
              {student.photo_url ? (
                <img src={student.photo_url} alt={student.name} className="h-full w-full object-cover" />
              ) : (
                student.name.charAt(0)
              )}
            </div>

            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-black">{student.name}</h3>
                <span className="text-xs font-mono font-bold bg-white/20 px-2 py-0.5 rounded-full">
                  {student.roll_number}
                </span>
              </div>
              <p className="text-xs text-white/80 font-medium">
                {student.department_name} • {student.current_semester || 'Semester VI'} • Batch {student.batch_year}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-md">
                  {student.cgpa ? `${student.cgpa} CGPA` : '7.8 CGPA'}
                </span>
                <span className="text-[10px] font-black uppercase bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded-md">
                  {student.attendance_pct}% Attendance
                </span>
                <span className="text-[10px] font-black uppercase bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded-md">
                  Risk: {student.risk_level}
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 mt-6 border-b border-white/20 pb-0">
            <button
              onClick={() => setActiveTab('CONTACT')}
              className={`px-4 py-2 text-xs font-extrabold rounded-t-xl transition-all ${
                activeTab === 'CONTACT' ? 'bg-card text-foreground shadow-md' : 'text-white/80 hover:bg-white/10'
              }`}
            >
              Student Handles
            </button>
            <button
              onClick={() => setActiveTab('PARENT')}
              className={`px-4 py-2 text-xs font-extrabold rounded-t-xl transition-all ${
                activeTab === 'PARENT' ? 'bg-card text-foreground shadow-md' : 'text-white/80 hover:bg-white/10'
              }`}
            >
              Parent & Family Contacts
            </button>
            <button
              onClick={() => setActiveTab('TIMELINE')}
              className={`px-4 py-2 text-xs font-extrabold rounded-t-xl transition-all ${
                activeTab === 'TIMELINE' ? 'bg-card text-foreground shadow-md' : 'text-white/80 hover:bg-white/10'
              }`}
            >
              Communication History & Timeline
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {/* TAB 1: STUDENT HANDLES */}
          {activeTab === 'CONTACT' && (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-black uppercase text-muted-foreground tracking-wider mb-3">
                  Direct One-Click Reach Out
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {student.phone && (
                    <a
                      href={`tel:${student.phone}`}
                      className="flex items-center gap-3 p-3 rounded-2xl bg-purple-500/10 text-purple-600 border border-purple-500/20 hover:bg-purple-600 hover:text-white transition-all shadow-sm"
                    >
                      <Phone className="h-4 w-4" />
                      <div>
                        <span className="text-[10px] font-black uppercase tracking-wider block opacity-80">Phone Call</span>
                        <span className="text-xs font-extrabold">{student.phone}</span>
                      </div>
                    </a>
                  )}

                  {student.whatsapp_number && (
                    <a
                      href={`https://wa.me/${student.whatsapp_number.replace(/[^0-9]/g, '')}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-3 p-3 rounded-2xl bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 hover:bg-emerald-600 hover:text-white transition-all shadow-sm"
                    >
                      <MessageSquare className="h-4 w-4" />
                      <div>
                        <span className="text-[10px] font-black uppercase tracking-wider block opacity-80">WhatsApp Chat</span>
                        <span className="text-xs font-extrabold">{student.whatsapp_number}</span>
                      </div>
                    </a>
                  )}

                  {student.college_email && (
                    <a
                      href={`mailto:${student.college_email}`}
                      className="flex items-center gap-3 p-3 rounded-2xl bg-blue-500/10 text-blue-600 border border-blue-500/20 hover:bg-blue-600 hover:text-white transition-all shadow-sm"
                    >
                      <Mail className="h-4 w-4" />
                      <div>
                        <span className="text-[10px] font-black uppercase tracking-wider block opacity-80">College Email</span>
                        <span className="text-xs font-extrabold truncate">{student.college_email}</span>
                      </div>
                    </a>
                  )}
                </div>
              </div>

              {/* Shared Platform Links */}
              <div>
                <h4 className="text-xs font-black uppercase text-muted-foreground tracking-wider mb-3">
                  Student Professional & Coding Profiles
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {student.linkedin_url && (
                    <a
                      href={student.linkedin_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between p-2.5 rounded-xl bg-card border border-border/60 hover:border-sky-500 transition-all"
                    >
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Linkedin className="h-3.5 w-3.5 text-sky-600" /> LinkedIn
                      </span>
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    </a>
                  )}

                  {student.github_url && (
                    <a
                      href={student.github_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between p-2.5 rounded-xl bg-card border border-border/60 hover:border-slate-800 transition-all"
                    >
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Github className="h-3.5 w-3.5 text-slate-700" /> GitHub
                      </span>
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    </a>
                  )}

                  {student.leetcode_url && (
                    <a
                      href={student.leetcode_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between p-2.5 rounded-xl bg-card border border-border/60 hover:border-amber-500 transition-all"
                    >
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Code2 className="h-3.5 w-3.5 text-amber-500" /> LeetCode
                      </span>
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    </a>
                  )}

                  {student.portfolio_url && (
                    <a
                      href={student.portfolio_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between p-2.5 rounded-xl bg-card border border-border/60 hover:border-brand-500 transition-all"
                    >
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Globe className="h-3.5 w-3.5 text-brand-600" /> Portfolio
                      </span>
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PARENT & FAMILY CONTACTS */}
          {activeTab === 'PARENT' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-muted/40 p-3 rounded-2xl border border-border/40">
                <div className="flex items-center gap-2 text-xs font-bold text-foreground">
                  <UserCheck className="h-4 w-4 text-brand-600" />
                  <span>Preferred Parent Contact: <strong className="text-brand-600">{parents.preferred_parent_contact}</strong></span>
                </div>
                <span className="text-xs text-muted-foreground font-semibold">
                  Best Time: {parents.best_time_to_call || 'Evening 5–7 PM'} • Lang: {parents.preferred_language || 'Telugu'}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Father */}
                {parents.father_name && (
                  <div className="rounded-2xl bg-card p-4 border border-border/60 space-y-2">
                    <div className="flex items-center justify-between">
                      <h5 className="text-xs font-black uppercase tracking-wider text-foreground">Father</h5>
                      <span className="text-[10px] font-bold text-muted-foreground">{parents.father_occupation}</span>
                    </div>
                    <p className="text-sm font-extrabold text-foreground">{parents.father_name}</p>
                    <div className="flex items-center gap-2 pt-1">
                      {parents.father_phone && (
                        <a
                          href={`tel:${parents.father_phone}`}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-purple-500/10 text-purple-600 px-3 py-1.5 text-xs font-bold hover:bg-purple-600 hover:text-white transition-all"
                        >
                          <Phone className="h-3.5 w-3.5" /> Call
                        </a>
                      )}
                      {parents.father_phone && (
                        <a
                          href={`https://wa.me/${parents.father_phone.replace(/[^0-9]/g, '')}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/10 text-emerald-600 px-3 py-1.5 text-xs font-bold hover:bg-emerald-600 hover:text-white transition-all"
                        >
                          <MessageSquare className="h-3.5 w-3.5" /> WhatsApp
                        </a>
                      )}
                    </div>
                  </div>
                )}

                {/* Mother */}
                {parents.mother_name && (
                  <div className="rounded-2xl bg-card p-4 border border-border/60 space-y-2">
                    <div className="flex items-center justify-between">
                      <h5 className="text-xs font-black uppercase tracking-wider text-foreground">Mother</h5>
                      <span className="text-[10px] font-bold text-muted-foreground">{parents.mother_occupation}</span>
                    </div>
                    <p className="text-sm font-extrabold text-foreground">{parents.mother_name}</p>
                    <div className="flex items-center gap-2 pt-1">
                      {parents.mother_phone && (
                        <a
                          href={`tel:${parents.mother_phone}`}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-purple-500/10 text-purple-600 px-3 py-1.5 text-xs font-bold hover:bg-purple-600 hover:text-white transition-all"
                        >
                          <Phone className="h-3.5 w-3.5" /> Call
                        </a>
                      )}
                      {parents.mother_phone && (
                        <a
                          href={`https://wa.me/${parents.mother_phone.replace(/[^0-9]/g, '')}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/10 text-emerald-600 px-3 py-1.5 text-xs font-bold hover:bg-emerald-600 hover:text-white transition-all"
                        >
                          <MessageSquare className="h-3.5 w-3.5" /> WhatsApp
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: TIMELINE & LOG EVENT */}
          {activeTab === 'TIMELINE' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-black uppercase tracking-wider text-muted-foreground">
                  Communication History & Logs
                </h4>
                <button
                  onClick={() => setShowLogForm(!showLogForm)}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-3 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-brand-700 transition-all cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5" /> Log Communication
                </button>
              </div>

              {/* Log Communication Form Drawer */}
              {showLogForm && (
                <form onSubmit={handleLogSubmit} className="p-4 rounded-2xl bg-muted/40 border border-brand-500/30 space-y-3">
                  <h5 className="text-xs font-black text-foreground flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-brand-600" /> Log Communication Event
                  </h5>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <div>
                      <label className="text-[10px] font-bold text-muted-foreground block mb-1">Channel</label>
                      <select value={channel} onChange={(e) => setChannel(e.target.value)} className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/50">
                        <option value="WHATSAPP">WhatsApp</option>
                        <option value="PHONE_CALL">Phone Call</option>
                        <option value="EMAIL">Email</option>
                        <option value="PARENT_MEETING">Parent Meeting</option>
                        <option value="IN_PERSON">In-Person Office</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-muted-foreground block mb-1">Direction</label>
                      <select value={direction} onChange={(e) => setDirection(e.target.value)} className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/50">
                        <option value="COUNSELLOR_TO_STUDENT">Counsellor → Student</option>
                        <option value="COUNSELLOR_TO_PARENT">Counsellor → Parent</option>
                        <option value="STUDENT_TO_COUNSELLOR">Student → Counsellor</option>
                        <option value="PARENT_TO_COUNSELLOR">Parent → Counsellor</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-muted-foreground block mb-1">Action Outcome</label>
                      <select value={actionOutcome} onChange={(e) => setActionOutcome(e.target.value)} className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/50">
                        <option value="RESOLVED">Resolved</option>
                        <option value="ACTION_REQUIRED">Action Required</option>
                        <option value="ESCALATED">Escalated</option>
                        <option value="PARENT_INFORMED">Parent Informed</option>
                        <option value="FOLLOW_UP_SCHEDULED">Follow-up Scheduled</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-muted-foreground block mb-1">Duration (Mins)</label>
                      <input type="number" value={duration || ''} onChange={(e) => setDuration(Number(e.target.value))} className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/50" />
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold text-muted-foreground block mb-1">Summary / Notes</label>
                    <textarea value={summary} onChange={(e) => setSummary(e.target.value)} required placeholder="Summarize key discussion points and commitments..." rows={2} className="w-full rounded-xl bg-card p-2.5 text-xs font-medium border border-border/50 resize-none" />
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <label className="flex items-center gap-2 text-xs font-bold text-foreground cursor-pointer">
                      <input type="checkbox" checked={followUpRequired} onChange={(e) => setFollowUpRequired(e.target.checked)} className="rounded" />
                      Follow-up Required?
                    </label>
                    <button type="submit" disabled={logMutation.isPending} className="rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-brand-700">
                      {logMutation.isPending ? 'Logging...' : 'Save Timeline Log'}
                    </button>
                  </div>
                </form>
              )}

              {/* Timeline Items */}
              {isTimelineLoading ? (
                <div className="py-8 text-center text-xs font-bold text-muted-foreground">Loading timeline logs...</div>
              ) : (
                <div className="space-y-3">
                  {timelineLogs?.map((log) => (
                    <div key={log.id} className="p-4 rounded-2xl bg-card border border-border/60 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-black text-brand-600 bg-brand-500/10 px-2 py-0.5 rounded-full uppercase">
                            {log.channel}
                          </span>
                          <span className="text-xs font-bold text-muted-foreground">
                            {log.direction.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-muted-foreground">
                          {new Date(log.occurred_at).toLocaleDateString()}
                        </span>
                      </div>

                      <p className="text-xs text-foreground font-medium">{log.summary}</p>

                      <div className="flex items-center justify-between pt-1 text-[10px] font-bold text-muted-foreground">
                        <span>Logged by {log.counsellor_name}</span>
                        <span className="text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-md uppercase">
                          {log.action_outcome}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
