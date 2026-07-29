import * as React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { UserRole } from '@scms/types';
import { api } from '@/shared/lib/axios';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  PhoneCall,
  FileText,
  Calendar,
  Award,
  Shield,
  BookOpen,
  Activity,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  GraduationCap,
  Sparkles,
  UserCheck,
  FileCheck,
} from 'lucide-react';
import { cn } from '@/shared/utils/cn';

interface SidebarProps {
  role: UserRole | string;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavSubItem {
  label: string;
  to: string;
}

interface NavItem {
  label: string;
  to: string;
  icon: React.ElementType;
  badge?: string;
  children?: NavSubItem[];
}

interface NavGroup {
  groupLabel: string;
  items: NavItem[];
}

export function Sidebar({ role, isCollapsed, onToggleCollapse }: SidebarProps) {
  const location = useLocation();
  const [openGroups, setOpenGroups] = React.useState<Record<string, boolean>>({
    '/my-profile': true,
    '/student-360': true,
  });

  const toggleGroup = (key: string) => {
    setOpenGroups((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const { data: isHealthy } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: async () => {
      const res = await api.get('/health/ready');
      return res.data?.status === 'healthy';
    },
    retry: false,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const getNavGroups = (): NavGroup[] => {
    switch (role) {
      case UserRole.STUDENT:
        return [
          {
            groupLabel: 'My Portal',
            items: [
              { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
              {
                label: 'My Profile',
                to: '/my-profile/personal',
                icon: GraduationCap,
                children: [
                  { label: 'Personal Information', to: '/my-profile/personal' },
                  { label: 'Contact', to: '/my-profile/contact' },
                  { label: 'Address', to: '/my-profile/address' },
                  { label: 'Parent & Guardian', to: '/my-profile/family' },
                  { label: 'Medical', to: '/my-profile/medical' },
                  { label: 'Documents', to: '/my-profile/documents' },
                  { label: 'Professional Links', to: '/my-profile/links' },
                ],
              },
              {
                label: 'Student 360 Portal',
                to: '/student-360/personal',
                icon: UserCheck,
                children: [
                  { label: 'Personal Details', to: '/student-360/personal' },
                  { label: 'Academic Details', to: '/student-360/academic' },
                  { label: 'Correction Requests', to: '/student-360/corrections' },
                ],
              },
              { label: 'Contact & Reach Out', to: '/reach-out', icon: PhoneCall },
            ],
          },
        ];

      case UserRole.COUNSELLOR:
        return [
          {
            groupLabel: 'My Caseload',
            items: [
              { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
              { label: 'Assigned Students', to: '/students', icon: Users },
              { label: 'Correction Requests', to: '/student-360/corrections', icon: FileCheck },
              { label: 'Contact & Reach Out', to: '/reach-out', icon: PhoneCall },
            ],
          },
          {
            groupLabel: 'Counselling',
            items: [
              { label: 'Session History', to: '/counselling/sessions', icon: MessageSquare },
              { label: 'Record Session', to: '/counselling/new', icon: Sparkles },
              { label: 'Parent Interactions', to: '/parent-communication', icon: PhoneCall },
            ],
          },
          {
            groupLabel: 'Insights',
            items: [{ label: 'Reports', to: '/reports', icon: FileText }],
          },
        ];

      case UserRole.FACULTY:
        return [
          {
            groupLabel: 'Faculty Desk',
            items: [
              { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
              { label: 'Record Attendance', to: '/attendance', icon: Calendar },
              { label: 'Faculty Marks Entry', to: '/academics/marks', icon: Award },
            ],
          },
        ];

      case UserRole.HOD:
        return [
          {
            groupLabel: 'Department Desk',
            items: [
              { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
              { label: 'Students', to: '/students', icon: Users },
              { label: 'Correction Requests', to: '/student-360/corrections', icon: FileCheck },
              { label: 'Reach-Out Config', to: '/reach-out', icon: PhoneCall },
              { label: 'Reports Catalog', to: '/reports', icon: FileText },
            ],
          },
        ];

      case UserRole.ADMIN:
      case UserRole.SUPER_ADMIN:
      default:
        return [
          {
            groupLabel: 'Overview',
            items: [{ label: 'Executive Dashboard', to: '/dashboard', icon: LayoutDashboard }],
          },
          {
            groupLabel: 'Administration',
            items: [
              { label: 'Students', to: '/students', icon: GraduationCap },
              { label: 'Correction Requests', to: '/student-360/corrections', icon: FileCheck },
              { label: 'User Directory', to: '/admin/users', icon: Users },
              { label: 'Academic Config', to: '/admin/academic-config', icon: BookOpen },
              { label: 'Counsellor Reach-Out', to: '/reach-out', icon: PhoneCall },
              { label: 'Office Import', to: '/admin/imports', icon: FileSpreadsheet },
              { label: 'Reports Catalog', to: '/reports', icon: FileText },
              { label: 'Security Audit Logs', to: '/admin/audit-logs', icon: Activity },
            ],
          },
        ];
    }
  };

  const navGroups = getNavGroups();

  return (
    <aside
      className={cn(
        'relative z-30 flex flex-col border-r border-border/80 bg-card/90 backdrop-blur-xl transition-all duration-300 select-none shadow-sm',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Sidebar Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border/60">
        {!isCollapsed ? (
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 shrink-0 items-center rounded-xl bg-white px-2 ring-1 ring-border/70 shadow-sm">
              <img src="/vvit-logo.png" alt="VVIT University" className="h-6 w-auto object-contain" />
            </div>
            <div className="flex flex-col truncate">
              <span className="text-[13px] font-black tracking-tight text-foreground leading-none truncate" title="VVIT Counselling Portal">
                VVIT Counselling Portal
              </span>
              <span className="text-[10px] font-extrabold text-muted-foreground uppercase tracking-widest mt-1 truncate">
                {role.replace('_', ' ')}
              </span>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-xl bg-white ring-1 ring-border/70 shadow-sm overflow-hidden">
            <img src="/vvit-logo.png" alt="VVIT" className="h-8 w-8 object-contain p-0.5" />
          </div>
        )}

        <button
          onClick={onToggleCollapse}
          className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/80 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors shrink-0 cursor-pointer"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* Nav List Groups */}
      <nav className="flex-1 space-y-4 p-3 overflow-y-auto">
        {navGroups.map((group, groupIdx) => (
          <div key={groupIdx} className="space-y-1">
            {!isCollapsed && (
              <div className="px-3 py-1 text-[10px] font-extrabold text-muted-foreground/60 uppercase tracking-widest">
                {group.groupLabel}
              </div>
            )}
            {group.items.map((item) => {
              const prefixKey = item.to.split('/')[1] ? `/${item.to.split('/')[1]}` : item.to;
              const hasChildren = Boolean(item.children && item.children.length > 0);
              const isParentActive = location.pathname.startsWith(prefixKey);
              const isOpen = openGroups[prefixKey] ?? isParentActive;

              if (hasChildren && !isCollapsed) {
                return (
                  <div key={item.to} className="space-y-1">
                    <button
                      type="button"
                      onClick={() => toggleGroup(prefixKey)}
                      className={cn(
                        'w-full group relative flex items-center justify-between rounded-xl px-3 py-2 text-xs font-bold transition-all duration-150 cursor-pointer',
                        isParentActive
                          ? 'bg-brand-600/10 text-brand-600 font-black'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <item.icon className="h-4 w-4 shrink-0 transition-transform duration-150 group-hover:scale-110" />
                        <span className="truncate">{item.label}</span>
                      </div>
                      <ChevronDown
                        className={cn(
                          'h-3.5 w-3.5 shrink-0 transition-transform duration-200',
                          isOpen ? 'rotate-180' : ''
                        )}
                      />
                    </button>

                    {isOpen && (
                      <div className="ml-4 pl-3 border-l border-border/60 space-y-1 my-1">
                        {item.children?.map((sub) => (
                          <NavLink
                            key={sub.to}
                            to={sub.to}
                            className={({ isActive }) =>
                              cn(
                                'flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[11px] font-bold transition-all duration-150',
                                isActive
                                  ? 'bg-brand-600 text-white font-black shadow-xs'
                                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                              )
                            }
                          >
                            <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
                            <span className="truncate">{sub.label}</span>
                          </NavLink>
                        ))}
                      </div>
                    )}
                  </div>
                );
              }

              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      'group relative flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-bold transition-all duration-150',
                      isActive
                        ? 'bg-brand-600 text-white font-black shadow-md shadow-brand-600/25'
                        : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                      isCollapsed && 'justify-center px-0'
                    )
                  }
                  title={isCollapsed ? item.label : undefined}
                >
                  {({ isActive }) => (
                    <>
                      <item.icon
                        className={cn(
                          'h-4 w-4 shrink-0 transition-transform duration-150 group-hover:scale-110',
                          isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'
                        )}
                      />
                      {!isCollapsed && <span className="truncate">{item.label}</span>}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Sidebar Footer */}
      {!isCollapsed && (
        <div className="p-3 border-t border-border/60">
          <div className="rounded-xl bg-muted/40 p-3 flex items-center justify-between border border-border/40">
            <div className="flex items-center gap-2.5 truncate">
              <div
                className={cn(
                  'flex h-7 w-7 items-center justify-center rounded-lg shrink-0',
                  isHealthy === false ? 'bg-rose-500/10 text-rose-600' : 'bg-emerald-500/10 text-emerald-600'
                )}
              >
                <Shield className="h-4 w-4" />
              </div>
              <div className="flex flex-col truncate">
                <span className="text-[11px] font-bold text-foreground truncate">
                  System Status
                </span>
                {isHealthy === undefined ? (
                  <span className="text-[9px] text-muted-foreground font-bold flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50" /> Checking...
                  </span>
                ) : isHealthy ? (
                  <span className="text-[9px] text-emerald-600 font-bold flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" /> Operational
                  </span>
                ) : (
                  <span className="text-[9px] text-rose-600 font-bold flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-500" /> Degraded
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
