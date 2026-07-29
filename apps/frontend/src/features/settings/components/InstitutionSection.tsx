import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsService } from '../services/settings.service';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Skeleton } from '@/shared/components/ui/Skeleton';

const SECTION = 'institution';
const KEY = 'profile';

interface InstitutionProfile {
  name: string;
  address: string;
  contact_email: string;
  contact_phone: string;
}

const EMPTY: InstitutionProfile = { name: '', address: '', contact_email: '', contact_phone: '' };

/** Real, functional admin panel backed by the generic system_settings
 * key-value store (GET/PUT /settings/institution). No mock data. */
export function InstitutionSection() {
  const queryClient = useQueryClient();
  const [form, setForm] = React.useState<InstitutionProfile>(EMPTY);
  const [saved, setSaved] = React.useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['settings', SECTION],
    queryFn: () => settingsService.getSettingsSection(SECTION),
  });

  React.useEffect(() => {
    const row = data?.find((s) => s.key === KEY);
    if (row) setForm({ ...EMPTY, ...(row.value as Partial<InstitutionProfile>) });
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () => settingsService.updateSetting(SECTION, KEY, form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', SECTION] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
  });

  const set = (k: keyof InstitutionProfile) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  if (isLoading) return <Skeleton className="h-72 rounded-xl max-w-xl" />;

  return (
    <form
      className="space-y-6 max-w-xl"
      onSubmit={(e) => {
        e.preventDefault();
        saveMutation.mutate();
      }}
    >
      <div>
        <h3 className="text-base font-bold text-foreground">Institution Info</h3>
        <p className="text-xs text-muted-foreground">Institutional identity shown across the portal.</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground">Institution Name</label>
          <Input value={form.name} onChange={set('name')} placeholder="VVIT University" />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground">Address</label>
          <Input value={form.address} onChange={set('address')} placeholder="Nambur, Guntur, Andhra Pradesh" />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground">Contact Email</label>
          <Input type="email" value={form.contact_email} onChange={set('contact_email')} placeholder="info@vvit.net" />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground">Contact Phone</label>
          <Input value={form.contact_phone} onChange={set('contact_phone')} placeholder="+91 00000 00000" />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button type="submit" size="sm" isLoading={saveMutation.isPending}>
          Save Changes
        </Button>
        {saved && <span className="text-xs font-semibold text-emerald-600">Saved</span>}
        {saveMutation.isError && <span className="text-xs font-semibold text-rose-600">Could not save. Try again.</span>}
      </div>
    </form>
  );
}
