import React, { useState } from 'react';
import { Shield, X, Eye, EyeOff, Save } from 'lucide-react';
import { useMyPrivacySettings, useUpdatePrivacySettings } from '../api/reachOutApi';

interface StudentPrivacySettingsModalProps {
  onClose: () => void;
}

export function StudentPrivacySettingsModal({ onClose }: StudentPrivacySettingsModalProps) {
  const { data: privacy, isLoading } = useMyPrivacySettings();
  const updateMutation = useUpdatePrivacySettings();

  const [form, setForm] = useState(() => ({
    share_phone: privacy?.share_phone ?? true,
    share_personal_email: privacy?.share_personal_email ?? true,
    share_linkedin: privacy?.share_linkedin ?? true,
    share_github: privacy?.share_github ?? true,
    share_portfolio: privacy?.share_portfolio ?? true,
    share_leetcode: privacy?.share_leetcode ?? true,
    share_codechef: privacy?.share_codechef ?? true,
    share_hackerrank: privacy?.share_hackerrank ?? true,
    preferred_parent_contact: privacy?.preferred_parent_contact ?? 'FATHER',
    best_time_to_call: privacy?.best_time_to_call ?? 'Evening 5:00 PM - 7:00 PM',
    preferred_language: privacy?.preferred_language ?? 'Telugu',
  }));

  React.useEffect(() => {
    if (privacy) {
      setForm({
        share_phone: privacy.share_phone,
        share_personal_email: privacy.share_personal_email,
        share_linkedin: privacy.share_linkedin,
        share_github: privacy.share_github,
        share_portfolio: privacy.share_portfolio,
        share_leetcode: privacy.share_leetcode,
        share_codechef: privacy.share_codechef,
        share_hackerrank: privacy.share_hackerrank,
        preferred_parent_contact: privacy.preferred_parent_contact,
        best_time_to_call: privacy.best_time_to_call || 'Evening 5:00 PM - 7:00 PM',
        preferred_language: privacy.preferred_language || 'Telugu',
      });
    }
  }, [privacy]);

  const handleToggle = (key: keyof typeof form) => {
    setForm((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(form, {
      onSuccess: () => {
        onClose();
      },
    });
  };

  const platforms = [
    { key: 'share_phone', label: 'Personal Mobile Phone Number' },
    { key: 'share_personal_email', label: 'Personal Email Address' },
    { key: 'share_linkedin', label: 'LinkedIn Profile Handle' },
    { key: 'share_github', label: 'GitHub Repository Profile' },
    { key: 'share_leetcode', label: 'LeetCode Profile' },
    { key: 'share_portfolio', label: 'Portfolio Website' },
    { key: 'share_codechef', label: 'CodeChef Handle' },
    { key: 'share_hackerrank', label: 'HackerRank Profile' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-md rounded-3xl bg-card p-6 shadow-2xl border border-border/80 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 flex h-8 w-8 items-center justify-center rounded-full bg-muted text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 ring-4 ring-brand-500/10">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-lg font-black text-foreground">Reach Out Privacy Settings</h3>
            <p className="text-xs text-muted-foreground">Manage handles visible to your assigned counsellor.</p>
          </div>
        </div>

        {isLoading ? (
          <div className="py-8 text-center text-xs font-bold text-muted-foreground">Loading privacy preferences...</div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <span className="text-[10px] font-black uppercase text-muted-foreground tracking-wider block">
                Platform Handle Sharing Controls
              </span>
              {platforms.map((p) => {
                const val = Boolean(form[p.key as keyof typeof form]);
                return (
                  <div
                    key={p.key}
                    onClick={() => handleToggle(p.key as keyof typeof form)}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-muted/40 border border-border/40 hover:border-brand-500/40 transition-all cursor-pointer select-none"
                  >
                    <span className="text-xs font-bold text-foreground">{p.label}</span>
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-black transition-all ${val ? 'bg-emerald-500/10 text-emerald-600' : 'bg-slate-500/10 text-slate-500'}`}>
                      {val ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
                      {val ? 'Visible' : 'Hidden'}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="space-y-2 pt-2 border-t border-border/60">
              <span className="text-[10px] font-black uppercase text-muted-foreground tracking-wider block">
                Parent Reach Out Preferences
              </span>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground block mb-1">Preferred Parent Contact</label>
                  <select
                    value={form.preferred_parent_contact}
                    onChange={(e) => setForm({ ...form, preferred_parent_contact: e.target.value })}
                    className="w-full rounded-xl bg-muted/50 p-2 text-xs font-bold text-foreground border border-border/60"
                  >
                    <option value="FATHER">Father</option>
                    <option value="MOTHER">Mother</option>
                    <option value="GUARDIAN">Guardian</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-muted-foreground block mb-1">Preferred Language</label>
                  <input
                    type="text"
                    value={form.preferred_language}
                    onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}
                    className="w-full rounded-xl bg-muted/50 p-2 text-xs font-bold text-foreground border border-border/60"
                  />
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl px-4 py-2 text-xs font-bold text-muted-foreground hover:bg-accent"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-5 py-2 text-xs font-bold text-white shadow-md hover:bg-brand-700 cursor-pointer"
              >
                <Save className="h-3.5 w-3.5" />
                {updateMutation.isPending ? 'Saving...' : 'Save Privacy Controls'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
