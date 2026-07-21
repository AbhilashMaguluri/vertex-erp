import * as React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentService, Student360Data } from '../services/student.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Timeline, TimelineEventItem } from '@/shared/components/ui/Timeline';
import {
  LayoutDashboard,
  Clock,
  Calendar,
  Award,
  MessageSquare,
  PhoneCall,
  FileText,
  FileCheck,
  Activity,
  Plus,
  Flag,
  AlertTriangle,
} from 'lucide-react';

export function StudentWorkspacePage() {
  const { studentId = 'demo-id' } = useParams();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = React.useState<
    'overview' | 'timeline' | 'attendance' | 'academics' | 'counselling' | 'parents' | 'documents' | 'reports' | 'analytics'
  >('overview');

  const [isRiskModalOpen, setIsRiskModalOpen] = React.useState(false);
  const [selectedRisk, setSelectedRisk] = React.useState('HIGH');
  const [riskReason, setRiskReason] = React.useState('');

  const { data, isLoading, isError } = useQuery<Student360Data>({
    queryKey: ['students', studentId, 'workspace'],
    queryFn: () => studentService.getStudent360(studentId),
  });

  const riskMutation = useMutation({
    mutationFn: () => studentService.updateRiskFlag(studentId, selectedRisk, riskReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students', studentId, 'workspace'] });
      setIsRiskModalOpen(false);
      setRiskReason('');
    },
  });

  const profile = data?.profile;

  const mockTimelineEvents: TimelineEventItem[] = [
    {
      id: '1',
      event_type: 'ATTENDANCE_BELOW_THRESHOLD',
      title: 'Attendance dropped below threshold (75%)',
      description: 'Mathematics attendance is currently at 68.4%',
      created_at: new Date().toISOString(),
      actor_name: 'System',
    },
    {
      id: '2',
      event_type: 'SESSION_CONDUCTED',
      title: 'Academic & Personal Counselling Session',
      description: 'Discussed mid-term exam performance and study timetable',
      created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
      actor_name: 'Dr. Priya Sharma',
    },
    {
      id: '3',
      event_type: 'PARENT_COMMUNICATION',
      title: 'Parent Call Logged',
      description: 'Spoke with Arjun’s father regarding attendance progress',
      created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
      actor_name: 'Dr. Priya Sharma',
    },
  ];

  if (isLoading) {
    return (
      <AppShell userRole="COUNSELLOR" userName="Dr. Priya Sharma">
        <Skeleton className="h-6 w-48 mb-4" />
        <Skeleton className="h-16 w-full mb-6" />
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      </AppShell>
    );
  }

  if (isError || !profile) {
    return (
      <AppShell userRole="COUNSELLOR" userName="Dr. Priya Sharma">
        <EmptyState
          icon={AlertTriangle}
          title="Student Not Found"
          description="The requested student workspace could not be loaded or you do not have permission."
          actionLabel="Return to Roster"
          onAction={() => window.history.back()}
        />
      </AppShell>
    );
  }

  return (
    <AppShell userRole="COUNSELLOR" userName="Dr. Priya Sharma">
      <Breadcrumbs
        items={[
          { label: 'My Students', href: '/students' },
          { label: profile.full_name },
        ]}
      />

      {/* Signature Persistent Action Bar */}
      <PageHeader
        title={profile.full_name}
        subtitle={`Roll: ${profile.roll_number} • Dept: ${profile.department_name || 'CSE'} • Counsellor: ${profile.counsellor_name || 'Dr. Priya'}`}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant={profile.risk_level === 'CRITICAL' || profile.risk_level === 'HIGH' ? 'danger' : 'warning'}>
              Risk: {profile.risk_level}
            </Badge>
            <Button size="sm" variant="outline" onClick={() => setIsRiskModalOpen(true)}>
              <Flag className="mr-1.5 h-3.5 w-3.5 text-amber-500" /> Flag Risk
            </Button>
            <Button size="sm" variant="outline">
              <PhoneCall className="mr-1.5 h-3.5 w-3.5 text-teal-600" /> Log Parent Call
            </Button>
            <Button size="sm">
              <Plus className="mr-1.5 h-3.5 w-3.5" /> New Session
            </Button>
          </div>
        }
      />

      {/* 9 Workspace Tabs */}
      <div className="flex border-b border-border my-6 overflow-x-auto gap-4 text-xs font-medium scrollbar-none">
        {[
          { key: 'overview', label: 'Overview', icon: LayoutDashboard },
          { key: 'timeline', label: 'Timeline', icon: Clock },
          { key: 'attendance', label: 'Attendance', icon: Calendar },
          { key: 'academics', label: 'Academics', icon: Award },
          { key: 'counselling', label: 'Counselling', icon: MessageSquare },
          { key: 'parents', label: 'Parent Calls', icon: PhoneCall },
          { key: 'documents', label: 'Documents', icon: FileText },
          { key: 'reports', label: 'Reports', icon: FileCheck },
          { key: 'analytics', label: 'Analytics', icon: Activity },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`pb-3 whitespace-nowrap flex items-center gap-1.5 border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Attention Required Banner */}
          {data.attention_items.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40 p-4 text-amber-900 dark:text-amber-200">
              <div className="flex items-center gap-2 font-semibold text-sm mb-1">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <span>Attention Required</span>
              </div>
              <ul className="list-disc list-inside text-xs space-y-1">
                {data.attention_items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.stats.map((stat, idx) => (
              <StatCard
                key={idx}
                title={stat.title}
                value={stat.value}
                change={stat.change}
                trend={stat.trend as any}
                description={stat.description}
              />
            ))}
          </div>

          {/* Recent Timeline Feed Preview */}
          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" /> Recent Student Activity
            </h3>
            <Timeline events={mockTimelineEvents} />
          </div>
        </div>
      )}

      {/* Tab 2: Timeline */}
      {activeTab === 'timeline' && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-base font-semibold mb-4">Universal Student History Timeline</h3>
          <Timeline events={mockTimelineEvents} />
        </div>
      )}

      {/* Other Tabs Stub */}
      {['attendance', 'academics', 'counselling', 'parents', 'documents', 'reports', 'analytics'].includes(activeTab) && (
        <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
          {activeTab.toUpperCase()} module data loaded for {profile.full_name}.
        </div>
      )}

      {/* Flag Risk Modal */}
      {isRiskModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-semibold">Flag Student Risk Level</h3>
            <div className="space-y-2">
              <label className="text-xs font-semibold">Risk Severity Level</label>
              <select
                value={selectedRisk}
                onChange={(e) => setSelectedRisk(e.target.value)}
                className="w-full h-9 rounded-md border bg-transparent px-3 text-sm"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold">Reason for Risk Flag</label>
              <textarea
                value={riskReason}
                onChange={(e) => setRiskReason(e.target.value)}
                placeholder="Detailed reason for changing risk severity..."
                rows={3}
                className="w-full rounded-md border bg-transparent p-2 text-sm"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsRiskModalOpen(false)}>
                Cancel
              </Button>
              <Button size="sm" onClick={() => riskMutation.mutate()} disabled={riskMutation.isPending}>
                {riskMutation.isPending ? 'Updating...' : 'Update Risk Flag'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
