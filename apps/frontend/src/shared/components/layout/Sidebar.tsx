import * as React from 'react';
import { NavLink } from 'react-router-dom';
import { UserRole } from '@scms/types';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  PhoneCall,
  FileText,
  Calendar,
  Award,
  Bell,
  Settings,
  Shield,
  BookOpen,
  CheckSquare,
  Activity,
  Layers,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/shared/utils/cn';

interface SidebarProps {
  role: UserRole | string;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  label: string;
  to: string;
  icon: React.ElementType;
}

export function Sidebar({ role, isCollapsed, onToggleCollapse }: SidebarProps) {
  const getNavItems = (): NavItem[] => {
    switch (role) {
      case UserRole.STUDENT:
        return [
          { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
          { label: 'My Workspace', to: '/my-workspace', icon: Users },
          { label: 'Attendance', to: '/attendance', icon: Calendar },
          { label: 'Marks & GPA', to: '/academics', icon: Award },
          { label: 'Counselling', to: '/counselling', icon: MessageSquare },
          { label: 'Documents', to: '/documents', icon: FileText },
          { label: 'Notifications', to: '/notifications', icon: Bell },
          { label: 'Settings', to: '/settings', icon: Settings },
        ];

      case UserRole.COUNSELLOR:
        return [
          { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
          { label: 'My Students', to: '/students', icon: Users },
          { label: 'Sessions', to: '/counselling/sessions', icon: MessageSquare },
          { label: 'Parent Calls', to: '/parent-communication', icon: PhoneCall },
          { label: 'Reports', to: '/reports', icon: FileText },
          { label: 'Notifications', to: '/notifications', icon: Bell },
          { label: 'Settings', to: '/settings', icon: Settings },
        ];

      case UserRole.FACULTY:
        return [
          { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
          { label: 'Attendance', to: '/attendance', icon: Calendar },
          { label: 'Marks Entry', to: '/academics/marks', icon: Award },
          { label: 'Subject Analytics', to: '/analytics/subject', icon: Activity },
          { label: 'Notifications', to: '/notifications', icon: Bell },
          { label: 'Settings', to: '/settings', icon: Settings },
        ];

      case UserRole.HOD:
        return [
          { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
          { label: 'Department Overview', to: '/department', icon: Layers },
          { label: 'All Students', to: '/students', icon: Users },
          { label: 'Counsellors Compliance', to: '/counselling/compliance', icon: MessageSquare },
          { label: 'Approvals Queue', to: '/approvals', icon: CheckSquare },
          { label: 'Reports', to: '/reports', icon: FileText },
          { label: 'Notifications', to: '/notifications', icon: Bell },
          { label: 'Settings', to: '/settings', icon: Settings },
        ];

      case UserRole.ADMIN:
      case UserRole.SUPER_ADMIN:
      default:
        return [
          { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
          { label: 'User Management', to: '/admin/users', icon: Users },
          { label: 'Academic Config', to: '/admin/academic-config', icon: BookOpen },
          { label: 'Counsellor Assign', to: '/admin/assignments', icon: Layers },
          { label: 'Feature Flags', to: '/admin/feature-flags', icon: Shield },
          { label: 'Reports', to: '/reports', icon: FileText },
          { label: 'Audit Logs', to: '/admin/audit-logs', icon: Activity },
          { label: 'Notifications', to: '/notifications', icon: Bell },
          { label: 'System Settings', to: '/settings', icon: Settings },
        ];
    }
  };

  const navItems = getNavItems();

  return (
    <aside
      className={cn(
        'relative z-30 flex flex-col border-r border-border bg-card transition-all duration-300 select-none',
        isCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Sidebar Header / Collapse Button */}
      <div className="flex h-12 items-center justify-between px-3 border-b border-border">
        {!isCollapsed && (
          <span className="text-xs font-semibold text-muted-foreground tracking-wider uppercase px-2">
            Workspace
          </span>
        )}
        <button
          onClick={onToggleCollapse}
          className="ml-auto flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Nav List */}
      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground font-semibold shadow-2xs'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                isCollapsed && 'justify-center px-0'
              )
            }
            title={isCollapsed ? item.label : undefined}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!isCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
