import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminService, Department, Subject, AcademicYear } from '../services/admin.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { BookOpen, Building2, Calendar, Plus } from 'lucide-react';

export function AcademicConfigPage() {
  const [activeTab, setActiveTab] = React.useState<'departments' | 'academic-years' | 'subjects'>('departments');

  const { data: departments, isLoading: deptsLoading, isError: deptsError } = useQuery<Department[]>({
    queryKey: ['admin', 'departments'],
    queryFn: adminService.getDepartments,
    enabled: activeTab === 'departments',
  });

  const { data: academicYears, isLoading: ayLoading } = useQuery<AcademicYear[]>({
    queryKey: ['admin', 'academic-years'],
    queryFn: adminService.getAcademicYears,
    enabled: activeTab === 'academic-years',
  });

  const { data: subjects, isLoading: subjectsLoading } = useQuery<Subject[]>({
    queryKey: ['admin', 'subjects'],
    queryFn: () => adminService.getSubjects(),
    enabled: activeTab === 'subjects',
  });

  return (
    <AppShell userRole="ADMIN" userName="System Admin">
      <Breadcrumbs items={[{ label: 'Administration', href: '/admin' }, { label: 'Academic Configuration' }]} />
      
      <PageHeader
        title="Academic Configuration"
        subtitle="Manage departments, sections, subjects, academic years, and semesters"
        actions={
          <Button size="sm">
            <Plus className="mr-1.5 h-4 w-4" /> Add {activeTab.slice(0, -1)}
          </Button>
        }
      />

      {/* Tabs */}
      <div className="flex border-b border-border my-6 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('departments')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'departments'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Building2 className="h-4 w-4" />
          Departments
        </button>

        <button
          onClick={() => setActiveTab('academic-years')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'academic-years'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Calendar className="h-4 w-4" />
          Academic Years
        </button>

        <button
          onClick={() => setActiveTab('subjects')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'subjects'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <BookOpen className="h-4 w-4" />
          Subjects
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'departments' && (
        <div>
          {deptsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
          ) : deptsError ? (
            <div className="p-6 text-center text-destructive text-sm">Failed to load departments.</div>
          ) : !departments || departments.length === 0 ? (
            <EmptyState
              icon={Building2}
              title="No Departments Found"
              description="Create departments to organize students, faculty, and subjects."
              actionLabel="Add Department"
              onAction={() => {}}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {departments.map((dept) => (
                <Card key={dept.id}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-primary/10 text-primary">
                        {dept.code}
                      </span>
                    </div>
                    <CardTitle className="text-base mt-2">{dept.name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground">
                      {dept.description || 'No description provided.'}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'academic-years' && (
        <div>
          {ayLoading ? (
            <Skeleton className="h-48" />
          ) : !academicYears || academicYears.length === 0 ? (
            <EmptyState
              icon={Calendar}
              title="No Academic Years Configured"
              description="Setup academic years to define semester schedules."
              actionLabel="Add Academic Year"
              onAction={() => {}}
            />
          ) : (
            <div className="space-y-3">
              {academicYears.map((ay) => (
                <div key={ay.id} className="flex items-center justify-between p-4 rounded-lg border bg-card">
                  <div>
                    <span className="font-semibold text-sm">{ay.name}</span>
                    <span className="text-xs text-muted-foreground ml-3">
                      ({ay.start_date} to {ay.end_date})
                    </span>
                  </div>
                  {ay.is_current && (
                    <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-700">
                      Active Year
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'subjects' && (
        <div>
          {subjectsLoading ? (
            <Skeleton className="h-48" />
          ) : !subjects || subjects.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="No Subjects Configured"
              description="Add course subjects with credits and exam grading schemes."
              actionLabel="Add Subject"
              onAction={() => {}}
            />
          ) : (
            <div className="rounded-md border bg-card divide-y">
              {subjects.map((sub) => (
                <div key={sub.id} className="p-4 flex items-center justify-between">
                  <div>
                    <span className="font-mono text-xs font-bold text-primary mr-2">{sub.code}</span>
                    <span className="font-medium text-sm">{sub.name}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Credits: <span className="font-semibold text-foreground">{sub.credits}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
