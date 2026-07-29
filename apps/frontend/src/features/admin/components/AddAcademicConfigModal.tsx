import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal } from '@/shared/components/ui/Modal';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import { adminService, Department, Section, Subject, AcademicYear } from '../services/admin.service';
import {
  departmentSchema, DepartmentFormData,
  academicYearSchema, AcademicYearFormData,
  subjectSchema, SubjectFormData,
  sectionSchema, SectionFormData,
  STUDY_YEARS, STUDY_YEAR_LABELS,
} from '../schemas/academicConfig.schema';
import { applyServerFieldErrors } from '@/shared/lib/apiErrors';
import { AlertCircle, CheckCircle2, Layers, Plus, ArrowRight, BookOpen, PartyPopper } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

const selectClass =
  'flex h-10 w-full rounded-xl border border-input bg-background/60 px-3.5 py-2 text-xs font-medium shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50';

export type AcademicConfigKind = 'departments' | 'academic-years' | 'subjects' | 'sections';

interface AddAcademicConfigModalProps {
  open: boolean;
  kind: AcademicConfigKind;
  onClose: () => void;
  onCreated: () => void;
  /** Pre-loaded lists from the parent, used for instant client-side duplicate checks. */
  departments?: Department[];
  sections?: Section[];
  subjects?: Subject[];
  academicYears?: AcademicYear[];
  /** Standalone "sections" add (e.g. the "+" on a specific year group) starts pre-scoped. */
  presetDepartmentId?: string;
  presetYear?: number;
}

const TITLES: Record<AcademicConfigKind, string> = {
  departments: 'Create Department',
  'academic-years': 'Add Academic Year',
  subjects: 'Add Subject',
  sections: 'Add Section',
};

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p className="text-[11px] text-rose-500 font-medium mt-1 flex items-center gap-1">
      <AlertCircle className="h-3 w-3 shrink-0" /> {message}
    </p>
  );
}

function WizardSteps({ step }: { step: 0 | 1 | 2 }) {
  const labels = ['Department', 'Years & Sections', 'Subjects'];
  return (
    <div className="flex items-center gap-1.5 mb-4">
      {labels.map((label, idx) => (
        <React.Fragment key={label}>
          <div className={cn('flex items-center gap-1.5 text-[10px] font-bold', idx <= step ? 'text-primary' : 'text-muted-foreground/50')}>
            <span
              className={cn(
                'flex h-5 w-5 items-center justify-center rounded-full border text-[10px]',
                idx < step ? 'bg-primary border-primary text-primary-foreground' : idx === step ? 'border-primary text-primary' : 'border-border'
              )}
            >
              {idx < step ? <CheckCircle2 className="h-3 w-3" /> : idx + 1}
            </span>
            <span className="hidden sm:inline">{label}</span>
          </div>
          {idx < labels.length - 1 && <div className={cn('h-px flex-1', idx < step ? 'bg-primary' : 'bg-border')} />}
        </React.Fragment>
      ))}
    </div>
  );
}

const currentYear = new Date().getFullYear();

export function AddAcademicConfigModal({
  open, kind, onClose, onCreated,
  departments: departmentsProp, sections: sectionsProp, subjects: subjectsProp, academicYears: academicYearsProp,
  presetDepartmentId, presetYear,
}: AddAcademicConfigModalProps) {
  const [departments, setDepartments] = React.useState<Department[]>(departmentsProp ?? []);
  const [generalError, setGeneralError] = React.useState<string | null>(null);

  // Guided wizard state (kind === 'departments' only): create dept, then
  // configure its years/sections, then seed its subject catalog, then finish
  // — administrators never have to hunt across separate pages for one setup.
  const [wizardStep, setWizardStep] = React.useState<0 | 1 | 2>(0);
  const [createdDepartment, setCreatedDepartment] = React.useState<Department | null>(null);
  const [addedSections, setAddedSections] = React.useState<Section[]>([]);
  const [addedSubjects, setAddedSubjects] = React.useState<Subject[]>([]);
  const [activeYearTab, setActiveYearTab] = React.useState<number>(1);

  const deptForm = useForm<DepartmentFormData>({
    resolver: zodResolver(departmentSchema),
    defaultValues: { code: '', name: '', description: '' },
  });
  const ayForm = useForm<AcademicYearFormData>({
    resolver: zodResolver(academicYearSchema),
    defaultValues: { name: '', start_date: '', end_date: '', is_current: false },
  });
  const subjectForm = useForm<SubjectFormData>({
    resolver: zodResolver(subjectSchema),
    defaultValues: {
      department_id: '', code: '', name: '',
      credits: 3, max_mid_marks: 30, max_internal_marks: 20, max_external_marks: 50,
    },
  });
  const sectionForm = useForm<SectionFormData>({
    resolver: zodResolver(sectionSchema),
    defaultValues: { department_id: '', year: 1, name: '', batch_year: currentYear },
  });

  React.useEffect(() => {
    if (!open) return;
    setGeneralError(null);
    setWizardStep(0);
    setCreatedDepartment(null);
    setAddedSections([]);
    setAddedSubjects([]);
    setActiveYearTab(presetYear ?? 1);
    deptForm.reset({ code: '', name: '', description: '' });
    ayForm.reset({ name: '', start_date: '', end_date: '', is_current: false });
    subjectForm.reset({
      department_id: presetDepartmentId ?? '', code: '', name: '',
      credits: 3, max_mid_marks: 30, max_internal_marks: 20, max_external_marks: 50,
    });
    sectionForm.reset({ department_id: presetDepartmentId ?? '', year: presetYear ?? 1, name: '', batch_year: currentYear });
    if (kind === 'subjects' || kind === 'sections') {
      if (departmentsProp) setDepartments(departmentsProp);
      else adminService.getDepartments().then(setDepartments).catch(() => setDepartments([]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, kind, presetDepartmentId, presetYear]);

  const onSubmitDepartment = async (data: DepartmentFormData) => {
    setGeneralError(null);
    const codeUpper = data.code.toUpperCase();
    const dupCode = (departmentsProp ?? departments).find((d) => d.code.toUpperCase() === codeUpper);
    if (dupCode) {
      deptForm.setError('code', { type: 'manual', message: `A department with code '${codeUpper}' already exists.` });
      return;
    }
    const dupName = (departmentsProp ?? departments).find((d) => d.name.trim().toLowerCase() === data.name.trim().toLowerCase());
    if (dupName) {
      deptForm.setError('name', { type: 'manual', message: 'A department with this name already exists.' });
      return;
    }
    try {
      const dept = await adminService.createDepartment({
        code: codeUpper,
        name: data.name,
        description: data.description || undefined,
      });
      setCreatedDepartment(dept);
      sectionForm.reset({ department_id: dept.id, year: 1, name: '', batch_year: currentYear });
      subjectForm.reset({
        department_id: dept.id, code: '', name: '',
        credits: 3, max_mid_marks: 30, max_internal_marks: 20, max_external_marks: 50,
      });
      setActiveYearTab(1);
      setWizardStep(1);
    } catch (err: any) {
      const msg = applyServerFieldErrors<DepartmentFormData>(err, deptForm.setError);
      if (msg) setGeneralError(msg);
    }
  };

  const onSubmitAcademicYear = async (data: AcademicYearFormData) => {
    setGeneralError(null);
    const dup = (academicYearsProp ?? []).find((a) => a.name.trim().toLowerCase() === data.name.trim().toLowerCase());
    if (dup) {
      ayForm.setError('name', { type: 'manual', message: `Academic year '${data.name}' already exists.` });
      return;
    }
    try {
      await adminService.createAcademicYear(data);
      onCreated();
    } catch (err: any) {
      const msg = applyServerFieldErrors<AcademicYearFormData>(err, ayForm.setError);
      if (msg) setGeneralError(msg);
    }
  };

  const onSubmitSubject = async (data: SubjectFormData, opts?: { standalone?: boolean }) => {
    setGeneralError(null);
    const codeUpper = data.code.toUpperCase();
    const pool = opts?.standalone ? (subjectsProp ?? []) : [...(subjectsProp ?? []), ...addedSubjects];
    const dup = pool.find((s) => s.code.toUpperCase() === codeUpper);
    if (dup) {
      subjectForm.setError('code', { type: 'manual', message: `Subject code '${codeUpper}' already exists.` });
      return;
    }
    try {
      const created = await adminService.createSubject({ ...data, code: codeUpper });
      if (opts?.standalone) {
        onCreated();
      } else {
        setAddedSubjects((prev) => [...prev, created]);
        subjectForm.reset({
          department_id: data.department_id, code: '', name: '',
          credits: 3, max_mid_marks: 30, max_internal_marks: 20, max_external_marks: 50,
        });
      }
    } catch (err: any) {
      const msg = applyServerFieldErrors<SubjectFormData>(err, subjectForm.setError);
      if (msg) setGeneralError(msg);
    }
  };

  const onSubmitSection = async (data: SectionFormData, opts?: { standalone?: boolean }) => {
    setGeneralError(null);
    const pool = opts?.standalone ? (sectionsProp ?? []) : [...(sectionsProp ?? []), ...addedSections];
    const dup = pool.find(
      (s) => s.department_id === data.department_id && s.year === data.year && s.name.trim().toLowerCase() === data.name.trim().toLowerCase()
    );
    if (dup) {
      sectionForm.setError('name', { type: 'manual', message: `Section '${data.name}' already exists for ${STUDY_YEAR_LABELS[data.year]}.` });
      return;
    }
    try {
      const section = await adminService.createSection(data);
      if (opts?.standalone) {
        onCreated();
      } else {
        setAddedSections((prev) => [...prev, section]);
        sectionForm.reset({ department_id: data.department_id, year: data.year, name: '', batch_year: data.batch_year });
      }
    } catch (err: any) {
      const msg = applyServerFieldErrors<SectionFormData>(err, sectionForm.setError);
      if (msg) setGeneralError(msg);
    }
  };

  const finishWizard = () => onCreated();

  // --- Guided wizard (kind === 'departments') ---
  if (kind === 'departments' && createdDepartment) {
    const sectionsForActiveYear = addedSections.filter((s) => s.year === activeYearTab);

    return (
      <Modal
        open={open}
        onClose={finishWizard}
        title={wizardStep === 1 ? 'Configure Years & Sections' : 'Assign Subjects'}
        description={`Continue setting up '${createdDepartment.name}'.`}
        className="max-w-xl"
      >
        <WizardSteps step={wizardStep} />

        <div className="flex items-center gap-2 rounded-md bg-emerald-50 dark:bg-emerald-950 p-3 text-xs font-medium text-emerald-700 dark:text-emerald-300 mb-4">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>
            Department <strong>{createdDepartment.code}</strong> — {createdDepartment.name} created successfully.
          </span>
        </div>

        {generalError && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs font-medium text-destructive mb-4">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{generalError}</span>
          </div>
        )}

        {wizardStep === 1 && (
          <div className="space-y-4">
            {/* Study year tabs */}
            <div className="flex gap-1.5">
              {STUDY_YEARS.map((yr) => (
                <button
                  key={yr}
                  type="button"
                  onClick={() => {
                    setActiveYearTab(yr);
                    sectionForm.setValue('year', yr);
                  }}
                  className={cn(
                    'flex-1 rounded-lg px-2 py-2 text-[11px] font-bold transition-all',
                    activeYearTab === yr ? 'bg-primary text-primary-foreground shadow-xs' : 'bg-muted/50 text-muted-foreground hover:bg-accent'
                  )}
                >
                  {STUDY_YEAR_LABELS[yr]}
                  {addedSections.some((s) => s.year === yr) && (
                    <span className="ml-1.5 opacity-80">({addedSections.filter((s) => s.year === yr).length})</span>
                  )}
                </button>
              ))}
            </div>

            {sectionsForActiveYear.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {sectionsForActiveYear.map((s) => (
                  <span
                    key={s.id}
                    className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/50 px-2.5 py-1 text-[11px] font-semibold text-foreground"
                  >
                    <Layers className="h-3 w-3 text-muted-foreground" /> Section {s.name}
                  </span>
                ))}
              </div>
            )}

            <form
              onSubmit={sectionForm.handleSubmit((data) => onSubmitSection(data))}
              className="space-y-3 rounded-md border border-dashed border-border p-3"
            >
              <p className="text-xs font-semibold text-muted-foreground">
                Add a Section to {STUDY_YEAR_LABELS[activeYearTab]}
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Section Name</label>
                  <Input {...sectionForm.register('name')} placeholder="A" error={!!sectionForm.formState.errors.name} />
                  <FieldError message={sectionForm.formState.errors.name?.message} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Admission Batch Year</label>
                  <Input type="number" {...sectionForm.register('batch_year')} error={!!sectionForm.formState.errors.batch_year} />
                  <FieldError message={sectionForm.formState.errors.batch_year?.message} />
                </div>
              </div>
              <div className="flex justify-end">
                <Button type="submit" size="sm" variant="outline" isLoading={sectionForm.formState.isSubmitting}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Section
                </Button>
              </div>
            </form>

            <div className="flex justify-between gap-2 pt-2 border-t border-border">
              <Button type="button" variant="outline" onClick={() => setWizardStep(2)}>
                Skip
              </Button>
              <Button type="button" onClick={() => setWizardStep(2)}>
                Continue to Subjects <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}

        {wizardStep === 2 && (
          <div className="space-y-4">
            {addedSubjects.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {addedSubjects.map((s) => (
                  <span
                    key={s.id}
                    className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/50 px-2.5 py-1 text-[11px] font-semibold text-foreground"
                  >
                    <BookOpen className="h-3 w-3 text-muted-foreground" /> {s.code} · {s.name}
                  </span>
                ))}
              </div>
            )}

            <form onSubmit={subjectForm.handleSubmit((data) => onSubmitSubject(data))} className="space-y-3 rounded-md border border-dashed border-border p-3">
              <p className="text-xs font-semibold text-muted-foreground">Add a Subject to the Catalog</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Course Code</label>
                  <Input {...subjectForm.register('code')} placeholder="CS301" className="uppercase" error={!!subjectForm.formState.errors.code} />
                  <FieldError message={subjectForm.formState.errors.code?.message} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Credits</label>
                  <Input type="number" min={1} max={10} {...subjectForm.register('credits')} error={!!subjectForm.formState.errors.credits} />
                  <FieldError message={subjectForm.formState.errors.credits?.message} />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Subject Title</label>
                <Input {...subjectForm.register('name')} placeholder="Data Structures & Algorithms" error={!!subjectForm.formState.errors.name} />
                <FieldError message={subjectForm.formState.errors.name?.message} />
              </div>
              <div className="flex justify-end">
                <Button type="submit" size="sm" variant="outline" isLoading={subjectForm.formState.isSubmitting}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Subject
                </Button>
              </div>
            </form>

            <div className="flex justify-between gap-2 pt-2 border-t border-border">
              <Button type="button" variant="outline" onClick={() => setWizardStep(1)}>
                Back
              </Button>
              <Button type="button" onClick={finishWizard}>
                <PartyPopper className="mr-1.5 h-3.5 w-3.5" /> Finish Setup
              </Button>
            </div>
          </div>
        )}
      </Modal>
    );
  }

  return (
    <Modal open={open} onClose={onClose} title={TITLES[kind]}>
      {kind === 'departments' && <WizardSteps step={0} />}

      {generalError && (
        <div className="mb-3 flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs font-medium text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{generalError}</span>
        </div>
      )}

      {kind === 'departments' && (
        <form onSubmit={deptForm.handleSubmit(onSubmitDepartment)} className="space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Department Code</label>
            <Input
              {...deptForm.register('code')}
              placeholder="CSE"
              className="uppercase"
              error={!!deptForm.formState.errors.code}
            />
            <FieldError message={deptForm.formState.errors.code?.message} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Department Name</label>
            <Input
              {...deptForm.register('name')}
              placeholder="Computer Science & Engineering"
              error={!!deptForm.formState.errors.name}
            />
            <FieldError message={deptForm.formState.errors.name?.message} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Description (optional)</label>
            <Input {...deptForm.register('description')} />
            <FieldError message={deptForm.formState.errors.description?.message} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={deptForm.formState.isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={deptForm.formState.isSubmitting} isLoading={deptForm.formState.isSubmitting}>
              Create & Continue <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
            </Button>
          </div>
        </form>
      )}

      {kind === 'academic-years' && (
        <form onSubmit={ayForm.handleSubmit(onSubmitAcademicYear)} className="space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Academic Year Code</label>
            <Input
              {...ayForm.register('name')}
              placeholder="2026-2027"
              error={!!ayForm.formState.errors.name}
            />
            <FieldError message={ayForm.formState.errors.name?.message} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Start Date</label>
              <Input type="date" {...ayForm.register('start_date')} error={!!ayForm.formState.errors.start_date} />
              <FieldError message={ayForm.formState.errors.start_date?.message} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">End Date</label>
              <Input type="date" {...ayForm.register('end_date')} error={!!ayForm.formState.errors.end_date} />
              <FieldError message={ayForm.formState.errors.end_date?.message} />
            </div>
          </div>
          <label className="flex items-center gap-2 text-xs font-medium text-foreground pt-1 cursor-pointer">
            <input type="checkbox" className="h-4 w-4 rounded border-input" {...ayForm.register('is_current')} />
            Set as the current active academic year
          </label>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={ayForm.formState.isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={ayForm.formState.isSubmitting} isLoading={ayForm.formState.isSubmitting}>
              Save
            </Button>
          </div>
        </form>
      )}

      {kind === 'subjects' && (
        <form onSubmit={subjectForm.handleSubmit((data) => onSubmitSubject(data, { standalone: true }))} className="space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Department</label>
            <select className={selectClass} {...subjectForm.register('department_id')} disabled={!!presetDepartmentId}>
              <option value="">Select a department...</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            <FieldError message={subjectForm.formState.errors.department_id?.message} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Course Code</label>
              <Input
                {...subjectForm.register('code')}
                placeholder="CS301"
                className="uppercase"
                error={!!subjectForm.formState.errors.code}
              />
              <FieldError message={subjectForm.formState.errors.code?.message} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Credits</label>
              <Input type="number" min={1} max={10} {...subjectForm.register('credits')} error={!!subjectForm.formState.errors.credits} />
              <FieldError message={subjectForm.formState.errors.credits?.message} />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Subject Title</label>
            <Input
              {...subjectForm.register('name')}
              placeholder="Data Structures & Algorithms"
              error={!!subjectForm.formState.errors.name}
            />
            <FieldError message={subjectForm.formState.errors.name?.message} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Marks Weightage (Mid / Internal / External)</label>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Input type="number" min={0} {...subjectForm.register('max_mid_marks')} error={!!subjectForm.formState.errors.max_mid_marks} />
                <FieldError message={subjectForm.formState.errors.max_mid_marks?.message} />
              </div>
              <div>
                <Input type="number" min={0} {...subjectForm.register('max_internal_marks')} error={!!subjectForm.formState.errors.max_internal_marks} />
                <FieldError message={subjectForm.formState.errors.max_internal_marks?.message} />
              </div>
              <div>
                <Input type="number" min={0} {...subjectForm.register('max_external_marks')} error={!!subjectForm.formState.errors.max_external_marks} />
                <FieldError message={subjectForm.formState.errors.max_external_marks?.message} />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={subjectForm.formState.isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={subjectForm.formState.isSubmitting} isLoading={subjectForm.formState.isSubmitting}>
              Save
            </Button>
          </div>
        </form>
      )}

      {kind === 'sections' && (
        <form onSubmit={sectionForm.handleSubmit((data) => onSubmitSection(data, { standalone: true }))} className="space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Department</label>
            <select className={selectClass} {...sectionForm.register('department_id')} disabled={!!presetDepartmentId}>
              <option value="">Select a department...</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            <FieldError message={sectionForm.formState.errors.department_id?.message} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Study Year</label>
              <select className={selectClass} {...sectionForm.register('year', { valueAsNumber: true })}>
                {STUDY_YEARS.map((yr) => (
                  <option key={yr} value={yr}>{STUDY_YEAR_LABELS[yr]}</option>
                ))}
              </select>
              <FieldError message={sectionForm.formState.errors.year?.message} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Section Name</label>
              <Input {...sectionForm.register('name')} placeholder="A" error={!!sectionForm.formState.errors.name} />
              <FieldError message={sectionForm.formState.errors.name?.message} />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Admission Batch Year</label>
            <Input type="number" {...sectionForm.register('batch_year')} error={!!sectionForm.formState.errors.batch_year} />
            <FieldError message={sectionForm.formState.errors.batch_year?.message} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={sectionForm.formState.isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={sectionForm.formState.isSubmitting} isLoading={sectionForm.formState.isSubmitting}>
              Save
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
