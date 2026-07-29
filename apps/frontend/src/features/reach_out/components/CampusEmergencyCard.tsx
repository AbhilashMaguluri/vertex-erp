import { PhoneCall, ShieldAlert, HeartPulse, Building, Lock, Mail, Phone } from 'lucide-react';
import { CampusEmergencyContact } from '../types/reachOut';

interface CampusEmergencyCardProps {
  contacts: CampusEmergencyContact[];
}

export function CampusEmergencyCard({ contacts }: CampusEmergencyCardProps) {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'COUNSELLING':
        return <PhoneCall className="h-4 w-4 text-emerald-500" />;
      case 'SAFETY':
      case 'HEPLINE':
        return <ShieldAlert className="h-4 w-4 text-rose-500" />;
      case 'MEDICAL':
        return <HeartPulse className="h-4 w-4 text-red-500" />;
      case 'SECURITY':
        return <Lock className="h-4 w-4 text-amber-500" />;
      default:
        return <Building className="h-4 w-4 text-brand-500" />;
    }
  };

  return (
    <div className="rounded-3xl border border-rose-500/20 bg-rose-500/5 p-6 backdrop-blur-xl shadow-lg relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-600 ring-1 ring-rose-500/20">
            <ShieldAlert className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-base font-black text-foreground">Campus Emergency Hotlines</h3>
            <p className="text-xs text-muted-foreground">
              Instant 1-click access to official campus safety, medical, and grievance helplines.
            </p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-3 py-1 text-[10px] font-black uppercase text-rose-600 border border-rose-500/20">
          24/7 Available
        </span>
      </div>

      {contacts.length === 0 ? (
        <div className="py-6 text-center text-xs font-bold text-muted-foreground">
          No emergency contacts configured.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {contacts.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between p-3 rounded-2xl bg-card border border-border/60 hover:border-rose-500/30 transition-all shadow-sm group"
            >
              <div className="flex items-center gap-3 truncate">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-muted group-hover:scale-110 transition-transform">
                  {getCategoryIcon(item.category)}
                </div>
                <div className="truncate">
                  <span className="text-xs font-black text-foreground block truncate">{item.name}</span>
                  <span className="text-[10px] text-muted-foreground font-semibold block truncate">
                    {item.location || item.category}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <a
                  href={`tel:${item.phone.replace(/[^0-9+]/g, '')}`}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-rose-500/10 text-rose-600 hover:bg-rose-600 hover:text-white transition-all"
                  title={`Call ${item.phone}`}
                >
                  <Phone className="h-3.5 w-3.5" />
                </a>
                {item.email && (
                  <a
                    href={`mailto:${item.email}`}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-muted text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
                    title={`Email ${item.email}`}
                  >
                    <Mail className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
