import * as React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminService, Department, Section, Subject, AcademicYear } from '../services/admin.service';
import { AddAcademicConfigModal, AcademicConfigKind } from '../components/AddAcademicConfigModal';
import { EditAcademicConfigModal, AcademicConfigRecord } from '../components/EditAcademicConfigModal';
import { DepartmentHierarchyCard } from '../components/DepartmentHierarchyCard';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Modal } from '@/shared/components/ui/Modal';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { AlertCircle, AlertTriangle, Building2, Calendar, CheckCircle2, Pencil, Plus } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

export function AcademicConfigPage() {
  const [addModal, setAddModal] = React.useState<{ kind: AcademicConfigKind; presetDepartmentId?: string; presetYear?: number } | null>(null);
  const [editing, setEditing] = React.useState<{ kind: AcademicConfigKind; record: AcademicConfigRecord } | null>(null);
  const [deletingSection, setDeletingSection] = React.useState<Section | null>(null);
  const [deleteError, setDeleteError] = React.useState<string | null>(null);
  const [successMessage, setSuccessMessage] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { hasPermission } = useAuth();

  const canManageDepartment = hasPermission('department.manage');
  const canManageSection = hasPermission('section.manage');
  const canManageSubject = hasPermission('subject.manage');
  const canManageAcademicYear = hasPermission('academic.manage');

  React.useEffect(() => {
    if (!successMessage) return;
    const timer = setTimeout(() => setSuccessMessage(null), 4000);
    return () => clearTimeout(timer);
  }, [successMessage]);

  const { data: departments, isLoading: deptsLoading, isError: deptsError } = useQuery<Department[]>({
    queryKey: ['admin', 'departments'],
    queryFn: adminService.getDepartments,
  });

  const { data: sections } = useQuery<Section[]>({
    queryKey: ['admin', 'sections'],
    queryFn: () => adminService.getSections(),
  });

  const { data: subjects } = useQuery<Subject[]>({
    queryKey: ['admin', 'subjects'],
    queryFn: () => adminService.getSubjects(),
  });

  const { data: academicYears, isLoading: ayLoading } = useQuery<AcademicYear[]>({
    queryKey: ['admin', 'academic-years'],
    queryFn: adminService.getAcademicYears,
  });

  const deleteSectionMutation = useMutation({
    mutationFn: (id: string) => adminService.deleteSection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'sections'] });
      setDeletingSection(null);
      setDeleteError(null);
      setSuccessMessage('Section deleted successfully.');
    },
    onError: (err: any) => {
      setDeleteError(err?.response?.data?.error?.message || 'Could not delete this section. Please try again.');
    },
  });

  const successLabels: Record<AcademicConfigKind, string> = {
    departments: 'Department',
    'academic-years': 'Academic year',
    subjects: 'Subject',
    sections: 'Section',
  };

  const currentAcademicYear = academicYears?.find((a) => a.is_current) ?? academicYears?.[0];

  return (
    <>
      <Breadcrumbs items={[{ label: 'Administration' }, { label: 'Academic Configuration' }]} />

      <PageHeader
        title="Academic Configuration"
        subtitle="Configure the full academic structure — Academic Year, Departments, Study Years, Sections, and Subjects — in one guided hierarchy."
        actions={
          canManageDepartment && (
            <Button size="sm" onClick={() => setAddModal({ kind: 'departments' })}>
              <Plus className="mr-1.5 h-4 w-4" /> Add Department
            </Button>
          )
        }
      />

      {successMessage && (
        <div className="mb-4 flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3.5 text-xs font-semibold text-emerald-600">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {successMessage}
        </div>
      )}

      {/* --- Level 1: Academic Year --- */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            <h2 className="text-xs font-extrabold uppercase tracking-widest text-muted-foreground">Academic Year</h2>
          </div>
          {canManageAcademicYear && (
            <Button variant="ghost" size="sm" onClick={() => setAddModal({ kind: 'academic-years' })} className="h-7 px-2 text-[11px] text-primary hover:bg-primary/10">
              <Plus className="mr-1 h-3 w-3" /> Add Academic Year
            </Button>
          )}
        </div>

        {ayLoading ? (
          <Skeleton className="h-16 rounded-xl" />
        ) : !academicYears || academicYears.length === 0 ? (
          <EmptyState
            icon={Calendar}
            title="No Academic Years Configured"
            description="Create an academic year to anchor the department structure beneath it."
            actionLabel={canManageAcademicYear ? 'Add Academic Year' : undefined}
            onAction={canManageAcademicYear ? () => setAddModal({ kind: 'academic-years' }) : undefined}
          />
        ) : (
          <div className="flex gap-2.5 overflow-x-auto pb-1">
            {academicYears.map((ay) => (
              <div
                key={ay.id}
                className={cn(
                  'group flex shrink-0 items-center gap-2.5 rounded-xl border px-4 py-2.5 shadow-xs',
                  ay.is_current ? 'border-primary/40 bg-primary/5' : 'border-border/70 bg-card/80'
                )}
              >
                <div>
                  <p className="text-xs font-bold text-foreground">{ay.name}</p>
                  <p className="text-[10px] text-muted-foreground font-mono">{ay.start_date} → {ay.end_date}</p>
                </div>
                {ay.is_current && <Badge variant="success" dot className="text-[9px]">Current</Badge>}
                {canManageAcademicYear && (
                  <button
                    onClick={() => setEditing({ kind: 'academic-years', record: ay })}
                    className="text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label={`Edit ${ay.name}`}
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* --- Levels 2-5: Department -> Study Year -> Sections -> Subjects --- */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <Building2 className="h-4 w-4 text-primary" />
          <h2 className="text-xs font-extrabold uppercase tracking-widest text-muted-foreground">
            Department Structure {currentAcademicYear ? `· ${currentAcademicYear.name}` : ''}
          </h2>
        </div>

        {deptsLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-24 rounded-2xl" />
            <Skeleton className="h-24 rounded-2xl" />
            <Skeleton className="h-24 rounded-2xl" />
          </div>
        ) : deptsError ? (
          <div className="flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs font-semibold text-rose-600">
            Failed to load departments data.
          </div>
        ) : !departments || departments.length === 0 ? (
          <EmptyState
            icon={Building2}
            title="No Departments Configured"
            description="Create your first department to start building its years, sections, and subject catalog."
            actionLabel={canManageDepartment ? 'Add Department' : undefined}
            onAction={canManageDepartment ? () => setAddModal({ kind: 'departments' }) : undefined}
          />
        ) : (
          <div className="space-y-4">
            {departments.map((dept) => (
              <DepartmentHierarchyCard
                key={dept.id}
                department={dept}
                sections={(sections ?? []).filter((s) => s.department_id === dept.id)}
                subjects={(subjects ?? []).filter((s) => s.department_id === dept.id)}
                canManageDepartment={canManageDepartment}
                canManageSection={canManageSection}
                canManageSubject={canManageSubject}
                onEditDepartment={() => setEditing({ kind: 'departments', record: dept })}
                onAddSection={(year) => setAddModal({ kind: 'sections', presetDepartmentId: dept.id, presetYear: year })}
                onEditSection={(section) => setEditing({ kind: 'sections', record: section })}
                onDeleteSection={(section) => {
                  setDeleteError(null);
                  setDeletingSection(section);
                }}
                onAddSubject={() => setAddModal({ kind: 'subjects', presetDepartmentId: dept.id })}
                onEditSubject={(subject) => setEditing({ kind: 'subjects', record: subject })}
              />
            ))}
          </div>
        )}
      </section>

      <AddAcademicConfigModal
        open={!!addModal}
        kind={addModal?.kind ?? 'departments'}
        presetDepartmentId={addModal?.presetDepartmentId}
        presetYear={addModal?.presetYear}
        departments={departments}
        sections={sections}
        subjects={subjects}
        academicYears={academicYears}
        onClose={() => setAddModal(null)}
        onCreated={() => {
          const kind = addModal?.kind ?? 'departments';
          setAddModal(null);
          queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] });
          queryClient.invalidateQueries({ queryKey: ['admin', 'sections'] });
          queryClient.invalidateQueries({ queryKey: ['admin', 'subjects'] });
          queryClient.invalidateQueries({ queryKey: ['admin', 'academic-years'] });
          setSuccessMessage(`${successLabels[kind]} saved successfully.`);
        }}
      />

      <EditAcademicConfigModal
        open={!!editing}
        kind={editing?.kind ?? 'departments'}
        record={editing?.record ?? null}
        onClose={() => setEditing(null)}
        onSaved={() => {
          const kind = editing?.kind ?? 'departments';
          setEditing(null);
          queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] });
          queryClient.invalidateQueries({ queryKey: ['admin', 'sections'] });
          queryClient.invalidateQueries({ queryKey: ['admin', 'subjects'] });
          queryClient.invalidateQueries({ queryKey: ['admin', 'academic-years'] });
          setSuccessMessage(`${successLabels[kind]} updated successfully.`);
        }}
      />

      {deletingSection && (
        <Modal
          open={!!deletingSection}
          onClose={() => setDeletingSection(null)}
          title="Delete Section"
          description={`Section ${deletingSection.name} will be permanently removed from this department's structure.`}
        >
          {deleteError && (
            <div className="mb-3 flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs font-medium text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{deleteError}</span>
            </div>
          )}
          <div className="flex items-start gap-2.5 rounded-md border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-300">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>This cannot be undone. Sections with enrolled students cannot be deleted.</span>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setDeletingSection(null)} disabled={deleteSectionMutation.isPending}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={() => deleteSectionMutation.mutate(deletingSection.id)}
              isLoading={deleteSectionMutation.isPending}
            >
              Delete Section
            </Button>
          </div>
        </Modal>
      )}
    </>
  );
}
