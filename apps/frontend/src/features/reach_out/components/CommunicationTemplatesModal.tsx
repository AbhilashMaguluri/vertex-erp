import React from 'react';
import { MessageSquare, Mail, Copy, X, Check } from 'lucide-react';
import { useCommunicationTemplates } from '../api/reachOutApi';

interface CommunicationTemplatesModalProps {
  studentName: string;
  onSelectTemplate: (body: string, subject?: string) => void;
  onClose: () => void;
}

export function CommunicationTemplatesModal({
  studentName,
  onSelectTemplate,
  onClose,
}: CommunicationTemplatesModalProps) {
  const { data: templates, isLoading } = useCommunicationTemplates();
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const formatText = (text: string) => {
    return text.replace('{student_name}', studentName).replace('{attendance_pct}', '72');
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(formatText(text));
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-3xl bg-card p-6 shadow-2xl border border-border/80 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 flex h-8 w-8 items-center justify-center rounded-full bg-muted text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 ring-4 ring-brand-500/10">
            <MessageSquare className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-lg font-black text-foreground">One-Click Quick Templates</h3>
            <p className="text-xs text-muted-foreground">Select a pre-formatted message template for {studentName}</p>
          </div>
        </div>

        {isLoading ? (
          <div className="py-8 text-center text-xs font-bold text-muted-foreground">Loading templates...</div>
        ) : (
          <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
            {templates?.map((t) => {
              const formattedBody = formatText(t.body_template);
              return (
                <div
                  key={t.id}
                  className="rounded-2xl border border-border/60 bg-muted/30 p-4 hover:border-brand-500/40 transition-all space-y-2 group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-foreground flex items-center gap-2">
                      {t.channel === 'EMAIL' ? <Mail className="h-3.5 w-3.5 text-blue-600" /> : <MessageSquare className="h-3.5 w-3.5 text-emerald-600" />}
                      {t.title}
                    </span>
                    <span className="text-[10px] font-extrabold uppercase bg-brand-500/10 text-brand-600 px-2 py-0.5 rounded-full">
                      {t.category}
                    </span>
                  </div>

                  {t.subject_template && (
                    <p className="text-[11px] font-bold text-brand-600">Subj: {formatText(t.subject_template)}</p>
                  )}

                  <p className="text-xs text-muted-foreground font-medium bg-card p-2.5 rounded-xl border border-border/40 whitespace-pre-wrap">
                    {formattedBody}
                  </p>

                  <div className="flex items-center justify-end gap-2 pt-1">
                    <button
                      onClick={() => handleCopy(t.id, t.body_template)}
                      className="inline-flex items-center gap-1 text-xs font-bold text-muted-foreground hover:text-foreground p-1.5 rounded-lg hover:bg-accent transition-all"
                    >
                      {copiedId === t.id ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                      {copiedId === t.id ? 'Copied' : 'Copy'}
                    </button>
                    <button
                      onClick={() => {
                        onSelectTemplate(formattedBody, t.subject_template ? formatText(t.subject_template) : undefined);
                        onClose();
                      }}
                      className="inline-flex items-center gap-1 text-xs font-bold text-white bg-brand-600 px-3 py-1.5 rounded-xl hover:bg-brand-700 transition-all shadow-sm cursor-pointer"
                    >
                      Use Template
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
