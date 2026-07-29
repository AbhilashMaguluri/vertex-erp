import * as React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { ProfileSection } from '../components/ProfileSection';
import { SecuritySection } from '../components/SecuritySection';
import { AppearanceSection } from '../components/AppearanceSection';
import { InstitutionSection } from '../components/InstitutionSection';
import {
  User, Palette, Shield, Building, Building2, Users, Activity,
} from 'lucide-react';
import { cn } from '@/shared/utils/cn';

type SectionKey =
  | 'profile' | 'security' | 'appearance'
  | 'institution' | 'departments' | 'users' | 'audit';

interface SectionDef {
  key: SectionKey;
  label: string;
  icon: React.ElementType;
  /** Permission gate — omitted means every authenticated user sees it. */
  permission?: string;
}

// Order here is the display order. Each section is only shown when the user
// actually holds its permission, so no role ever sees a section it cannot use.
const ALL_SECTIONS: SectionDef[] = [
  { key: 'profile', label: 'Profile', icon: User },
  { key: 'security', label: 'Security & Account', icon: Shield },
  { key: 'appearance', label: 'Appearance', icon: Palette },
  { key: 'institution', label: 'Institution Info', icon: Building, permission: 'settings.manage' },
  { key: 'departments', label: 'Departments & Academics', icon: Building2, permission: 'department.manage' },
  { key: 'users', label: 'User Directory', icon: Users, permission: 'user.manage' },
  { key: 'audit', label: 'Audit Logs', icon: Activity, permission: 'audit.read' },
];

/** Admin link-out sections point at the dedicated management pages rather
 * than duplicating them — one source of truth, no dead placeholder panes. */
function ManagementLink({ title, description, to, cta }: { title: string; description: string; to: string; cta: string }) {
  const navigate = useNavigate();
  return (
    <div className="space-y-4 max-w-xl">
      <div>
        <h3 className="text-base font-bold text-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
      </div>
      <Button size="sm" onClick={() => navigate(to)}>{cta}</Button>
    </div>
  );
}

export function SettingsPage() {
  const location = useLocation();
  const { hasPermission } = useAuth();

  const sections = React.useMemo(
    () => ALL_SECTIONS.filter((s) => !s.permission || hasPermission(s.permission)),
    [hasPermission]
  );

  const requestedSection = (location.state as { section?: SectionKey } | null)?.section;
  const isVisible = (k: SectionKey | undefined): k is SectionKey => !!k && sections.some((s) => s.key === k);

  const [activeSection, setActiveSection] = React.useState<SectionKey>(
    isVisible(requestedSection) ? requestedSection : 'profile'
  );

  // Header dropdown deep-links here with a target section in route state.
  React.useEffect(() => {
    if (isVisible(requestedSection)) setActiveSection(requestedSection);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestedSection]);

  return (
    <>
      <Breadcrumbs items={[{ label: 'Settings' }]} />
      <PageHeader title="Settings" subtitle="Manage your profile, security, and preferences" />

      <div className="mt-6 flex flex-col md:flex-row gap-6">
        {/* Section nav */}
        <Card className="w-full md:w-64 shrink-0 h-fit">
          <CardContent className="p-2 space-y-1">
            <div className="px-3 py-2 text-[10px] font-bold text-muted-foreground/70 uppercase tracking-widest">
              Settings Menu
            </div>
            {sections.map((sec) => {
              const Icon = sec.icon;
              const isActive = activeSection === sec.key;
              return (
                <button
                  key={sec.key}
                  onClick={() => setActiveSection(sec.key)}
                  className={cn(
                    'w-full flex items-center gap-2.5 px-3 py-2.5 text-xs font-semibold rounded-lg transition-all duration-150 cursor-pointer select-none',
                    isActive
                      ? 'bg-primary text-primary-foreground font-bold shadow-xs'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{sec.label}</span>
                </button>
              );
            })}
          </CardContent>
        </Card>

        {/* Content pane */}
        <Card className="flex-1">
          <CardContent className="p-6 md:p-8">
            {activeSection === 'profile' && <ProfileSection />}
            {activeSection === 'security' && <SecuritySection />}
            {activeSection === 'appearance' && <AppearanceSection />}
            {activeSection === 'institution' && <InstitutionSection />}
            {activeSection === 'departments' && (
              <ManagementLink
                title="Departments & Academics"
                description="Configure departments, sections, subjects, and academic years."
                to="/admin/academic-config"
                cta="Open Academic Config"
              />
            )}
            {activeSection === 'users' && (
              <ManagementLink
                title="User Directory & Access Control"
                description="Provision and manage HOD, Counsellor, Faculty, and Student accounts."
                to="/admin/users"
                cta="Open User Directory"
              />
            )}
            {activeSection === 'audit' && (
              <ManagementLink
                title="Security Audit Trail"
                description="Review system event logs, authentication attempts, and privilege changes."
                to="/admin/audit-logs"
                cta="Open Audit Logs"
              />
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
