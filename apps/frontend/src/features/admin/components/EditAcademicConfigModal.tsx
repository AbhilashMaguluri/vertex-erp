import * as React from 'react';
import { Modal } from '@/shared/components/ui/Modal';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import { adminService, Department, AcademicYear, Subject, Section } from '../services/admin.service';
import { AcademicConfigKind } from './AddAcademicConfigModal';
import { STUDY_YEARS, STUDY_YEAR_LABELS } from '../schemas/academicConfig.schema';
import { AlertCircle } from 'lucide-react';

const selectClass =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50';

export type AcademicConfigRecord = Department | AcademicYear | Subject | Section;

interface EditAcademicConfigModalProps {
  open: boolean;
  kind: AcademicConfigKind;
  record: AcademicConfigRecord | null;
  onClose: () => void;
  onSaved: () => void;
}

const TITLES: Record<AcademicConfigKind, string> = {
  departments: 'Edit Department',
  'academic-years': 'Edit Academic Year',
  subjects: 'Edit Subject',
  sections: 'Edit Section',
};

export function EditAcademicConfigModal({ open, kind, record, onClose, onSaved }: EditAcademicConfigModalProps) {
  const [departments, setDepartments] = React.useState<Department[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const [deptForm, setDeptForm] = React.useState({ code: '', name: '', description: '' });
  const [ayForm, setAyForm] = React.useState({ name: '', start_date: '', end_date: '', is_current: false });
  const [subjectForm, setSubjectForm] = React.useState({
    department_id: '',
    code: '',
    name: '',
    credits: 3,
    max_mid_marks: 30,
    max_internal_marks: 20,
    max_external_marks: 50,
  });
  const [sectionForm, setSectionForm] = React.useState({ department_id: '', year: 1, name: '', batch_year: new Date().getFullYear() });

  React.useEffect(() => {
    if (!open) return;
    setError(null);
    if (kind === 'subjects' || kind === 'sections') {
      adminService.getDepartments().then(setDepartments).catch(() => setDepartments([]));
    }
  }, [open, kind]);

  // Re-hydrate the form from the selected record every time it changes so the
  // dialog always opens pre-filled with the latest values, never stale input.
  React.useEffect(() => {
    if (!open || !record) return;
    if (kind === 'departments') {
      const d = record as Department;
      setDeptForm({ code: d.code, name: d.name, description: d.description || '' });
    } else if (kind === 'academic-years') {
      const a = record as AcademicYear;
      setAyForm({ name: a.name, start_date: a.start_date, end_date: a.end_date, is_current: a.is_current });
    } else if (kind === 'sections') {
      const s = record as Section;
      setSectionForm({ department_id: s.department_id, year: s.year ?? 1, name: s.name, batch_year: s.batch_year });
    } else {
      const s = record as Subject;
      setSubjectForm({
        department_id: s.department_id,
        code: s.code,
        name: s.name,
        credits: s.credits,
        max_mid_marks: s.max_mid_marks,
        max_internal_marks: s.max_internal_marks,
        max_external_marks: s.max_external_marks,
      });
    }
  }, [open, record, kind]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!record) return;
    setError(null);
    setIsSubmitting(true);
    try {
      if (kind === 'departments') {
        await adminService.updateDepartment(record.id, {
          name: deptForm.name,
          description: deptForm.description || undefined,
        });
      } else if (kind === 'academic-years') {
        await adminService.updateAcademicYear(record.id, {
          name: ayForm.name,
          start_date: ayForm.start_date,
          end_date: ayForm.end_date,
          is_current: ayForm.is_current,
        });
      } else if (kind === 'sections') {
        await adminService.updateSection(record.id, sectionForm);
      } else {
        await adminService.updateSubject(record.id, subjectForm);
      }
      onSaved();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Could not save changes. Check the fields and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!record) return null;

  return (
    <Modal open={open} onClose={onClose} title={TITLES[kind]}>
      <form onSubmit={handleSubmit} className="space-y-3">
        {error && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs font-medium text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {kind === 'departments' && (
          <>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Department Code</label>
              <Input value={deptForm.code} disabled />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Department Name</label>
              <Input
                value={deptForm.name}
                onChange={(e) => setDeptForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Computer Science & Engineering"
                required
                minLength={2}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Description (optional)</label>
              <Input
                value={deptForm.description}
                onChange={(e) => setDeptForm((f) => ({ ...f, description: e.target.value }))}
              />
            </div>
          </>
        )}

        {kind === 'academic-years' && (
          <>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Academic Year Name</label>
              <Input
                value={ayForm.name}
                onChange={(e) => setAyForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="2026-2027"
                required
                minLength={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Start Date</label>
                <Input
                  type="date"
                  value={ayForm.start_date}
                  onChange={(e) => setAyForm((f) => ({ ...f, start_date: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">End Date</label>
                <Input
                  type="date"
                  value={ayForm.end_date}
                  onChange={(e) => setAyForm((f) => ({ ...f, end_date: e.target.value }))}
                  required
                />
              </div>
            </div>
            <label className="flex items-center gap-2 text-xs font-medium text-foreground pt-1 cursor-pointer">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={ayForm.is_current}
                onChange={(e) => setAyForm((f) => ({ ...f, is_current: e.target.checked }))}
              />
              Set as the current active academic year
            </label>
          </>
        )}

        {kind === 'sections' && (
          <>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Department</label>
              <select
                className={selectClass}
                value={sectionForm.department_id}
                onChange={(e) => setSectionForm((f) => ({ ...f, department_id: e.target.value }))}
                required
              >
                <option value="">Select a department...</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Study Year</label>
                <select
                  className={selectClass}
                  value={sectionForm.year}
                  onChange={(e) => setSectionForm((f) => ({ ...f, year: Number(e.target.value) }))}
                  required
                >
                  {STUDY_YEARS.map((yr) => (
                    <option key={yr} value={yr}>{STUDY_YEAR_LABELS[yr]}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Section Name</label>
                <Input
                  value={sectionForm.name}
                  onChange={(e) => setSectionForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="A"
                  required
                  maxLength={20}
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Admission Batch Year</label>
              <Input
                type="number"
                value={sectionForm.batch_year}
                onChange={(e) => setSectionForm((f) => ({ ...f, batch_year: Number(e.target.value) }))}
                min={2000}
                max={2100}
                required
              />
            </div>
          </>
        )}

        {kind === 'subjects' && (
          <>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Department</label>
              <select
                className={selectClass}
                value={subjectForm.department_id}
                onChange={(e) => setSubjectForm((f) => ({ ...f, department_id: e.target.value }))}
                required
              >
                <option value="">Select a department...</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Course Code</label>
                <Input
                  value={subjectForm.code}
                  onChange={(e) => setSubjectForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
                  placeholder="CS301"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Credits</label>
                <Input
                  type="number"
                  min={1}
                  max={10}
                  value={subjectForm.credits}
                  onChange={(e) => setSubjectForm((f) => ({ ...f, credits: Number(e.target.value) }))}
                  required
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Subject Title</label>
              <Input
                value={subjectForm.name}
                onChange={(e) => setSubjectForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Data Structures & Algorithms"
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Marks Weightage (Mid / Internal / External)</label>
              <div className="grid grid-cols-3 gap-3">
                <Input
                  type="number"
                  min={0}
                  value={subjectForm.max_mid_marks}
                  onChange={(e) => setSubjectForm((f) => ({ ...f, max_mid_marks: Number(e.target.value) }))}
                  required
                />
                <Input
                  type="number"
                  min={0}
                  value={subjectForm.max_internal_marks}
                  onChange={(e) => setSubjectForm((f) => ({ ...f, max_internal_marks: Number(e.target.value) }))}
                  required
                />
                <Input
                  type="number"
                  min={0}
                  value={subjectForm.max_external_marks}
                  onChange={(e) => setSubjectForm((f) => ({ ...f, max_external_marks: Number(e.target.value) }))}
                  required
                />
              </div>
            </div>
          </>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting} isLoading={isSubmitting}>
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  );
}
