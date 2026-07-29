import { Sparkles, CheckSquare, MessageCircle, X, Clock } from 'lucide-react';
import { useAIMeetingBriefing } from '../api/reachOutApi';

interface AIMeetingPrepModalProps {
  studentId: string;
  studentName: string;
  onClose: () => void;
}

export function AIMeetingPrepModal({ studentId, studentName, onClose }: AIMeetingPrepModalProps) {
  const { data: briefing, isLoading } = useAIMeetingBriefing(studentId, true);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-xl rounded-3xl bg-card p-6 shadow-2xl border border-border/80 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 flex h-8 w-8 items-center justify-center rounded-full bg-muted text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 ring-4 ring-brand-500/10">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-lg font-black text-foreground">AI Pre-Meeting Briefing</h3>
            <p className="text-xs text-muted-foreground">Automated briefing for {studentName}</p>
          </div>
        </div>

        {isLoading ? (
          <div className="py-12 text-center text-xs font-bold text-muted-foreground flex items-center justify-center gap-2">
            <Sparkles className="h-4 w-4 text-brand-600 animate-spin" /> Generating AI briefing snapshot...
          </div>
        ) : briefing ? (
          <div className="space-y-4">
            {/* Student Snapshot Banner */}
            <div className="grid grid-cols-4 gap-2 rounded-2xl bg-muted/40 p-3 border border-border/50 text-center">
              <div>
                <span className="text-[10px] font-black uppercase text-muted-foreground block">CGPA</span>
                <span className="text-sm font-black text-foreground">{briefing.cgpa ?? '7.8'}</span>
              </div>
              <div>
                <span className="text-[10px] font-black uppercase text-muted-foreground block">Attendance</span>
                <span className={`text-sm font-black ${(briefing.attendance_pct ?? 75) < 75 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {briefing.attendance_pct}%
                </span>
              </div>
              <div>
                <span className="text-[10px] font-black uppercase text-muted-foreground block">Backlogs</span>
                <span className="text-sm font-black text-foreground">{briefing.backlogs_count}</span>
              </div>
              <div>
                <span className="text-[10px] font-black uppercase text-muted-foreground block">Risk Level</span>
                <span className="text-xs font-black uppercase text-brand-600 bg-brand-500/10 px-2 py-0.5 rounded-full inline-block mt-0.5">
                  {briefing.risk_level}
                </span>
              </div>
            </div>

            {/* Last Session Context */}
            {briefing.last_session_summary && (
              <div className="rounded-2xl bg-indigo-500/5 p-4 border border-indigo-500/20">
                <h4 className="text-xs font-black uppercase text-indigo-600 flex items-center gap-1.5 mb-1">
                  <Clock className="h-3.5 w-3.5" /> Previous Session Context ({briefing.last_session_date || 'Recent'})
                </h4>
                <p className="text-xs text-foreground/90 font-medium leading-relaxed">
                  {briefing.last_session_summary}
                </p>
              </div>
            )}

            {/* Pending Tasks & Commitments */}
            <div>
              <h4 className="text-xs font-black uppercase text-muted-foreground tracking-wider mb-2 flex items-center gap-1.5">
                <CheckSquare className="h-3.5 w-3.5 text-amber-600" /> Pending Action Items
              </h4>
              <div className="space-y-1.5">
                {briefing.pending_tasks.map((task, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2.5 rounded-xl bg-card border border-border/60 text-xs font-semibold text-foreground">
                    <span className="h-2 w-2 rounded-full bg-amber-500" />
                    <span>{task}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Suggested Discussion Topics */}
            <div>
              <h4 className="text-xs font-black uppercase text-muted-foreground tracking-wider mb-2 flex items-center gap-1.5">
                <MessageCircle className="h-3.5 w-3.5 text-brand-600" /> AI Suggested Discussion Agenda
              </h4>
              <div className="space-y-1.5">
                {briefing.suggested_discussion_topics.map((topic, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-2.5 rounded-xl bg-brand-500/5 border border-brand-500/20 text-xs font-bold text-foreground">
                    <Sparkles className="h-3.5 w-3.5 text-brand-600 shrink-0 mt-0.5" />
                    <span>{topic}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={onClose}
                className="rounded-xl bg-brand-600 px-6 py-2 text-xs font-bold text-white shadow-md hover:bg-brand-700 transition-all cursor-pointer"
              >
                Proceed to Meeting
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
