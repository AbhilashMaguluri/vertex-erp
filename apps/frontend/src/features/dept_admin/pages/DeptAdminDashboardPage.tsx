import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Building2,
  Users,
  GraduationCap,
  Award,
  Calendar,
  UploadCloud,
  FileText,
  BookOpen,
  SlidersHorizontal,
  MessageSquare,
  Activity,
  ArrowRight,
} from 'lucide-react';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { Badge } from '@/shared/components/ui/Badge';
import { deptAdminService, DeptDashboardMetrics } from '../services/deptAdmin.service';

export function DeptAdminDashboardPage() {
  const { data: metrics, isLoading } = useQuery<DeptDashboardMetrics>({
    queryKey: ['dept-admin', 'dashboard'],
    queryFn: deptAdminService.getDashboardMetrics,
  });

  if (isLoading || !metrics) {
    return <Skeleton className="h-96 w-full rounded-2xl" />;
  }

  return (
    <div className="space-y-6">
      {/* Banner */}
      <Card className="border-primary/30 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent">
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
              <Building2 className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono">{metrics.department_code}</Badge>
                <h1 className="text-xl font-bold text-foreground">{metrics.department_name} Department</h1>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Department Executive Control Desk — strictly scoped metrics and management.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 xl:grid-cols-8">
        <StatCard
          title="Students"
          value={metrics.total_students}
          icon={GraduationCap}
          description="In department"
        />
        <StatCard
          title="Faculty"
          value={metrics.faculty_count}
          icon={Users}
          description="Assigned faculty"
        />
        <StatCard
          title="Counselors"
          value={metrics.counselor_count}
          icon={MessageSquare}
          description="Active counselors"
        />
        <StatCard
          title="Attendance"
          value={`${metrics.attendance_percentage}%`}
          icon={Calendar}
          progress={metrics.attendance_percentage}
          description="Department average"
        />
        <StatCard
          title="Pending Sessions"
          value={metrics.pending_counseling_sessions}
          icon={Activity}
          description="Awaiting conduct"
        />
        <StatCard
          title="Subjects"
          value={metrics.subject_count}
          icon={BookOpen}
          description="Active subjects"
        />
        <StatCard
          title="Sections"
          value={metrics.section_count}
          icon={SlidersHorizontal}
          description="Department sections"
        />
        <StatCard
          title="Activity"
          value={metrics.recent_activity_count}
          icon={Award}
          description="Records tracked"
        />
      </div>

      {/* Quick Action Navigation */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card className="hover:border-primary/50 transition-all">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GraduationCap className="h-5 w-5 text-primary" />
              Student Directory
            </CardTitle>
            <CardDescription>View, search, and manage department students.</CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/students">
              <Button variant="outline" size="sm" className="w-full">
                Open Directory <ArrowRight className="ml-1.5 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-all">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <UploadCloud className="h-5 w-5 text-primary" />
              Department Imports
            </CardTitle>
            <CardDescription>Bulk import attendance, marks, and membership.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <Link to="/attendance/import">
              <Button variant="outline" size="sm" className="w-full justify-start text-xs">
                <Calendar className="mr-2 h-3.5 w-3.5 text-primary" /> Attendance Import
              </Button>
            </Link>
            <Link to="/academics/import-marks">
              <Button variant="outline" size="sm" className="w-full justify-start text-xs">
                <Award className="mr-2 h-3.5 w-3.5 text-primary" /> Marks Import
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-all">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-5 w-5 text-primary" />
              Department Reports
            </CardTitle>
            <CardDescription>Generate department performance & attendance reports.</CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/reports">
              <Button variant="outline" size="sm" className="w-full">
                View Reports <ArrowRight className="ml-1.5 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
