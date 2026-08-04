import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  SlidersHorizontal,
  Plus,
  Trash2,
  Save,
  Award,
} from 'lucide-react';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Modal } from '@/shared/components/ui/Modal';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { adminService, Subject, Department } from '@/features/admin/services/admin.service';
import {
  marksImportService,
  AssessmentTemplate,
  AssessmentComponent,
} from '@/features/academics/services/marksImport.service';

export function AssessmentConfigPage() {
  const queryClient = useQueryClient();

  const [selectedSubjectId, setSelectedSubjectId] = React.useState('');
  const [departmentId, setDepartmentId] = React.useState('');
  const [editModalOpen, setEditModalOpen] = React.useState(false);
  const [editingTemplate, setEditingTemplate] = React.useState<AssessmentTemplate | null>(null);

  // Form state
  const [formCode, setFormCode] = React.useState('');
  const [formName, setFormName] = React.useState('');
  const [formTotalMax, setFormTotalMax] = React.useState('30');
  const [formDesc, setFormDesc] = React.useState('');
  const [formComponents, setFormComponents] = React.useState<AssessmentComponent[]>([]);

  const { data: departments } = useQuery<Department[]>({
    queryKey: ['admin', 'departments'],
    queryFn: adminService.getDepartments,
  });

  const { data: subjects } = useQuery<Subject[]>({
    queryKey: ['admin', 'subjects', departmentId],
    queryFn: () => adminService.getSubjects(departmentId || undefined),
  });

  const { data: templates, isLoading } = useQuery<AssessmentTemplate[]>({
    queryKey: ['admin', 'assessment-templates', selectedSubjectId],
    queryFn: () => marksImportService.getTemplates(selectedSubjectId || undefined),
  });

  const openCreateModal = () => {
    setEditingTemplate(null);
    setFormCode('MID_WRITTEN_2');
    setFormName('Mid Written Exam 2');
    setFormTotalMax('30');
    setFormDesc('Configurable Mid Exam');
    setFormComponents([
      { key: 'A', label: 'Question A', max_marks: 6 },
      { key: 'B', label: 'Question B', max_marks: 6 },
      { key: 'C', label: 'Question C', max_marks: 6 },
      { key: 'D', label: 'Question D', max_marks: 12 },
    ]);
    setEditModalOpen(true);
  };

  const openEditModal = (tmpl: AssessmentTemplate) => {
    setEditingTemplate(tmpl);
    setFormCode(tmpl.assessment_code);
    setFormName(tmpl.assessment_name);
    setFormTotalMax(String(tmpl.total_max_marks));
    setFormDesc(tmpl.description || '');
    setFormComponents(tmpl.components ? [...tmpl.components] : []);
    setEditModalOpen(true);
  };

  const addComponent = () => {
    const nextChar = String.fromCharCode(65 + formComponents.length);
    setFormComponents([
      ...formComponents,
      { key: nextChar, label: `Question ${nextChar}`, max_marks: 5 },
    ]);
  };

  const removeComponent = (idx: number) => {
    setFormComponents(formComponents.filter((_, i) => i !== idx));
  };

  const updateComponent = (idx: number, field: keyof AssessmentComponent, value: any) => {
    const updated = [...formComponents];
    updated[idx] = { ...updated[idx], [field]: value };
    setFormComponents(updated);
  };

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        subject_id: selectedSubjectId || undefined,
        assessment_code: formCode,
        assessment_name: formName,
        total_max_marks: parseFloat(formTotalMax) || 30,
        components: formComponents,
        description: formDesc,
      };

      if (editingTemplate) {
        return marksImportService.updateTemplate(editingTemplate.id, payload);
      }
      return marksImportService.createTemplate(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'assessment-templates'] });
      setEditModalOpen(false);
    },
  });

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Administration' },
          { label: 'Academic Config', href: '/admin/academic-config' },
          { label: 'Assessment Configuration' },
        ]}
      />
      <PageHeader
        title="Assessment Structure Configuration"
        subtitle="Configure assessment types, max total marks, and question breakdown structures for exams without modifying code."
        actions={
          <Button size="sm" onClick={openCreateModal}>
            <Plus className="mr-1.5 h-4 w-4" /> Add Assessment Template
          </Button>
        }
      />

      <div className="space-y-6">
        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Subject Scope Filter</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">Department</label>
              <select
                value={departmentId}
                onChange={(e) => {
                  setDepartmentId(e.target.value);
                  setSelectedSubjectId('');
                }}
                className="h-10 w-full rounded-xl border border-input bg-background px-3 text-xs font-semibold"
              >
                <option value="">All Departments (Global Templates)</option>
                {departments?.map((d) => (
                  <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">Subject Specific Override</label>
              <select
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(e.target.value)}
                className="h-10 w-full rounded-xl border border-input bg-background px-3 text-xs font-semibold"
              >
                <option value="">(Global Defaults)</option>
                {subjects?.map((s) => (
                  <option key={s.id} value={s.id}>{s.code} — {s.name}</option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Templates Grid */}
        {isLoading ? (
          <Skeleton className="h-64 w-full rounded-2xl" />
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            {templates?.map((tmpl) => (
              <Card key={tmpl.id} className="flex flex-col justify-between">
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Award className="h-5 w-5 text-primary shrink-0" />
                      <div>
                        <CardTitle className="text-base">{tmpl.assessment_name}</CardTitle>
                        <p className="text-xs font-mono text-muted-foreground">{tmpl.assessment_code}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className="font-mono text-xs">
                      Max {tmpl.total_max_marks}m
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-xs text-muted-foreground">{tmpl.description || 'No description provided.'}</p>

                  <div className="rounded-lg border border-border/40 bg-muted/20 p-3">
                    <p className="mb-1.5 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                      Question Structure
                    </p>
                    {tmpl.components && tmpl.components.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {tmpl.components.map((c) => (
                          <Badge key={c.key} variant="secondary" className="text-xs">
                            {c.key}: {c.max_marks}m
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs font-medium text-foreground">Single Overall Marks Entry ({tmpl.total_max_marks} Marks)</p>
                    )}
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="outline" size="sm" onClick={() => openEditModal(tmpl)}>
                      <SlidersHorizontal className="mr-1.5 h-3.5 w-3.5" /> Edit Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Add / Edit Modal */}
      <Modal
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title={editingTemplate ? `Edit Assessment: ${editingTemplate.assessment_name}` : 'New Assessment Template'}
        description="Define maximum marks and question components."
        className="max-w-lg"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-foreground">Assessment Code</label>
              <Input
                value={formCode}
                onChange={(e) => setFormCode(e.target.value.toUpperCase())}
                placeholder="e.g. MID_WRITTEN_1"
                disabled={Boolean(editingTemplate)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-foreground">Max Total Marks</label>
              <Input
                type="number"
                value={formTotalMax}
                onChange={(e) => setFormTotalMax(e.target.value)}
                placeholder="30"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-foreground">Display Name</label>
            <Input
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder="e.g. Mid Written Exam 1"
            />
          </div>

          {/* Question components */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-foreground">Question Components (Optional)</label>
              <Button type="button" variant="ghost" size="sm" onClick={addComponent} className="h-6 text-xs">
                <Plus className="mr-1 h-3 w-3" /> Add Question
              </Button>
            </div>

            {formComponents.length === 0 ? (
              <p className="rounded-lg border border-dashed p-3 text-center text-xs text-muted-foreground">
                No questions defined — will use single total marks column.
              </p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-auto">
                {formComponents.map((comp, idx) => (
                  <div key={idx} className="flex items-center gap-2 rounded-lg border border-border p-2">
                    <Input
                      value={comp.key}
                      onChange={(e) => updateComponent(idx, 'key', e.target.value.toUpperCase())}
                      placeholder="Key (A)"
                      className="h-8 w-16 text-xs font-bold"
                    />
                    <Input
                      value={comp.label}
                      onChange={(e) => updateComponent(idx, 'label', e.target.value)}
                      placeholder="Label (Question A)"
                      className="h-8 flex-1 text-xs"
                    />
                    <Input
                      type="number"
                      value={comp.max_marks}
                      onChange={(e) => updateComponent(idx, 'max_marks', parseFloat(e.target.value) || 0)}
                      placeholder="Max"
                      className="h-8 w-20 text-xs font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => removeComponent(idx)}
                      className="p-1 text-muted-foreground hover:text-rose-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-border">
            <Button variant="outline" size="sm" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
              <Save className="mr-1.5 h-3.5 w-3.5" /> Save Template
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
