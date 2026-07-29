import React, { useState } from 'react';
import { Calendar, X, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { useCreateAppointment } from '../api/reachOutApi';

interface AppointmentRequestModalProps {
  initialType?: string;
  onClose: () => void;
}

export function AppointmentRequestModal({ initialType = 'APPOINTMENT', onClose }: AppointmentRequestModalProps) {
  const [requestType, setRequestType] = useState(initialType);
  const [date, setDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  });
  const [timeSlot, setTimeSlot] = useState('10:30 AM - 11:30 AM');
  const [reason, setReason] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const createMutation = useCreateAppointment();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(
      {
        request_type: requestType,
        preferred_date: date,
        preferred_time_slot: timeSlot,
        reason,
      },
      {
        onSuccess: () => {
          setSubmitted(true);
        },
      }
    );
  };

  const timeSlots = [
    '09:30 AM - 10:30 AM',
    '10:30 AM - 11:30 AM',
    '11:30 AM - 12:30 PM',
    '02:00 PM - 03:00 PM',
    '03:00 PM - 04:00 PM',
    '04:00 PM - 05:00 PM',
  ];

  const types = [
    { id: 'APPOINTMENT', label: 'Book General Appointment' },
    { id: 'COUNSELLING', label: 'Request Counselling Session' },
    { id: 'PARENT_MEETING', label: 'Request Parent Meeting' },
    { id: 'CAREER_GUIDANCE', label: 'Career Guidance Session' },
    { id: 'ACADEMIC_GUIDANCE', label: 'Academic & Backlog Guidance' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-3xl bg-card p-6 shadow-2xl border border-border/80 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 flex h-8 w-8 items-center justify-center rounded-full bg-muted text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
        >
          <X className="h-4 w-4" />
        </button>

        {submitted ? (
          <div className="py-8 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 ring-8 ring-emerald-500/10">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <h3 className="text-xl font-black text-foreground mt-4">Request Submitted Successfully</h3>
            <p className="text-xs text-muted-foreground mt-2 max-w-xs mx-auto">
              Your appointment request has been sent to Dr. Ravendra Sagu. You will receive a notification once confirmed.
            </p>
            <button
              onClick={onClose}
              className="mt-6 rounded-xl bg-brand-600 px-6 py-2.5 text-xs font-bold text-white shadow-md hover:bg-brand-700 transition-all cursor-pointer"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <h3 className="text-lg font-black text-foreground flex items-center gap-2">
                <Calendar className="h-5 w-5 text-brand-600" /> Book Counsellor Meeting
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Select your preferred date, time slot, and guidance topic for Dr. Ravendra Sagu.
              </p>
            </div>

            {/* Request Type Selector */}
            <div>
              <label className="text-xs font-bold text-foreground block mb-1">Select Purpose / Topic</label>
              <div className="grid grid-cols-1 gap-1.5">
                {types.map((t) => (
                  <button
                    type="button"
                    key={t.id}
                    onClick={() => setRequestType(t.id)}
                    className={`flex items-center justify-between p-2.5 rounded-xl text-xs font-bold text-left transition-all border ${
                      requestType === t.id
                        ? 'bg-brand-600/10 border-brand-600 text-brand-600'
                        : 'bg-muted/40 border-border/40 text-foreground hover:bg-accent'
                    }`}
                  >
                    <span>{t.label}</span>
                    {requestType === t.id && <Sparkles className="h-3.5 w-3.5 text-brand-600" />}
                  </button>
                ))}
              </div>
            </div>

            {/* Date & Time Slot */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-foreground block mb-1">Preferred Date</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  required
                  className="w-full rounded-xl bg-muted/50 p-2.5 text-xs font-bold text-foreground border border-border/60 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-foreground block mb-1">Preferred Time Slot</label>
                <select
                  value={timeSlot}
                  onChange={(e) => setTimeSlot(e.target.value)}
                  className="w-full rounded-xl bg-muted/50 p-2.5 text-xs font-bold text-foreground border border-border/60 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {timeSlots.map((slot) => (
                    <option key={slot} value={slot}>
                      {slot}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Reason Notes */}
            <div>
              <label className="text-xs font-bold text-foreground block mb-1">Reason / Discussion Points (Optional)</label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Briefly state what you'd like to discuss (e.g. attendance recovery, career guidance, personal stress)..."
                rows={3}
                className="w-full rounded-xl bg-muted/50 p-2.5 text-xs font-medium text-foreground border border-border/60 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
              />
            </div>

            {createMutation.isError && (
              <div className="p-3 rounded-xl bg-rose-500/10 text-rose-600 text-xs font-semibold flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" /> Failed to submit appointment request. Please try again.
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl px-4 py-2.5 text-xs font-bold text-muted-foreground hover:bg-accent transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="rounded-xl bg-brand-600 px-6 py-2.5 text-xs font-bold text-white shadow-md shadow-brand-600/25 hover:bg-brand-700 transition-all cursor-pointer"
              >
                {createMutation.isPending ? 'Submitting...' : 'Submit Meeting Request'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
