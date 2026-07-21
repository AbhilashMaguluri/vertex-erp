import * as React from 'react';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import {
  User,
  Palette,
  Bell,
  Shield,
  Building,
  GraduationCap,
  Building2,
  Users,
  HardDrive,
  Activity,
  Layers,
  Sliders,
  CheckCircle2,
} from 'lucide-react';

export function SettingsPage() {
  const [activeSection, setActiveSection] = React.useState<
    'profile' | 'appearance' | 'notifications' | 'security' | 'institution' | 'academic' | 'departments' | 'users' | 'storage' | 'audit' | 'integrations' | 'system'
  >('profile');

  const [savedMsg, setSavedMsg] = React.useState<string | null>(null);

  const sections = [
    { key: 'profile', label: 'Profile', icon: User, adminOnly: false },
    { key: 'appearance', label: 'Appearance', icon: Palette, adminOnly: false },
    { key: 'notifications', label: 'Notifications', icon: Bell, adminOnly: false },
    { key: 'security', label: 'Security', icon: Shield, adminOnly: false },
    { key: 'institution', label: 'Institution', icon: Building, adminOnly: true },
    { key: 'academic', label: 'Academic', icon: GraduationCap, adminOnly: true },
    { key: 'departments', label: 'Departments', icon: Building2, adminOnly: true },
    { key: 'users', label: 'Users & Roles', icon: Users, adminOnly: true },
    { key: 'storage', label: 'Storage & Quotas', icon: HardDrive, adminOnly: true },
    { key: 'audit', label: 'Audit Policy', icon: Activity, adminOnly: true },
    { key: 'integrations', label: 'Integrations', icon: Layers, adminOnly: true },
    { key: 'system', label: 'System Flags', icon: Sliders, adminOnly: true },
  ];

  const handleSave = () => {
    setSavedMsg(`Settings for '${activeSection.toUpperCase()}' saved successfully.`);
    setTimeout(() => setSavedMsg(null), 3000);
  };

  return (
    <AppShell userRole="ADMIN" userName="System Admin">
      <Breadcrumbs items={[{ label: 'Settings Architecture' }]} />

      <PageHeader
        title="Settings Architecture"
        subtitle="Organized into 12 structured sections (User-level & System-level) (§23)"
      />

      <div className="mt-6 flex flex-col md:flex-row gap-6 border rounded-lg bg-card shadow-2xs">
        {/* Sidebar-within-sidebar (VS Code style) */}
        <div className="w-full md:w-56 border-b md:border-b-0 md:border-r border-border p-2 space-y-1">
          {sections.map((sec) => {
            const Icon = sec.icon;
            return (
              <button
                key={sec.key}
                onClick={() => setActiveSection(sec.key as any)}
                className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-md transition-colors ${
                  activeSection === sec.key
                    ? 'bg-primary text-primary-foreground font-semibold'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className="h-3.5 w-3.5" />
                  <span>{sec.label}</span>
                </div>
                {sec.adminOnly && (
                  <span className="text-[9px] font-bold uppercase tracking-wider px-1 bg-muted rounded">Admin</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Settings Panel Content */}
        <div className="flex-1 p-6">
          {savedMsg && (
            <div className="mb-4 flex items-center gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-3 text-xs font-medium text-emerald-800">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{savedMsg}</span>
            </div>
          )}

          <div className="space-y-4 max-w-xl">
            <h3 className="text-base font-semibold capitalize flex items-center gap-2">
              Configuration: {activeSection}
            </h3>

            {activeSection === 'profile' && (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold">Full Name</label>
                  <Input defaultValue="System Administrator" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold">Email Address</label>
                  <Input defaultValue="admin@scms.edu" disabled />
                </div>
              </div>
            )}

            {activeSection === 'institution' && (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold">Institution Full Name</label>
                  <Input defaultValue="National Institute of Technology" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold">Institutional Code</label>
                  <Input defaultValue="NIT-2026" />
                </div>
              </div>
            )}

            {activeSection !== 'profile' && activeSection !== 'institution' && (
              <div className="py-6 text-sm text-muted-foreground">
                Configurable parameters for <span className="font-semibold text-foreground">{activeSection}</span> section.
              </div>
            )}

            <div className="pt-4 border-t">
              <Button size="sm" onClick={handleSave}>
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
