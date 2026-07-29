import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal } from '@/shared/components/ui/Modal';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import { adminService, Department, Section, Semester } from '../services/admin.service';
import { userAdminService, UserCreatePayload } from '../services/admin.service';
import { createUserSchema, CreateUserFormData, ASSIGNABLE_ROLES } from '../schemas/createUser.schema';
import { applyServerFieldErrors } from '@/shared/lib/apiErrors';
import { AlertCircle, RotateCcw } from 'lucide-react';

const selectClass =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50';

interface CreateUserModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (result: { email: string; temporaryPassword: string; emailSent: boolean }) => void;
}

function defaultStudentPassword(rollNumber: string) {
  return rollNumber ? `${rollNumber.trim().toUpperCase()}@vvit.net` : '';
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="text-[11px] text-rose-500 font-medium mt-1">{message}</p>;
}

export function CreateUserModal({ open, onClose, onCreated }: CreateUserModalProps) {
  const [departments, setDepartments] = React.useState<Department[]>([]);
  const [sections, setSections] = React.useState<Section[]>([]);
  const [semesters, setSemesters] = React.useState<Semester[]>([]);
  const [generalError, setGeneralError] = React.useState<string | null>(null);
  const [passwordTouched, setPasswordTouched] = React.useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      first_name: '', last_name: '', email: '', phone: '', role: 'STUDENT', department_id: '',
      password: '', roll_number: '', registration_number: '', date_of_birth: '',
      batch_year: new Date().getFullYear(), section_id: '', semester_id: '',
    },
  });

  const role = watch('role');
  const departmentId = watch('department_id');
  const rollNumber = watch('roll_number');
  const isStudent = role === 'STUDENT';

  React.useEffect(() => {
    if (!open) return;
    setGeneralError(null);
    setPasswordTouched(false);
    reset({
      first_name: '', last_name: '', email: '', phone: '', role: 'STUDENT', department_id: '',
      password: '', roll_number: '', registration_number: '', date_of_birth: '',
      batch_year: new Date().getFullYear(), section_id: '', semester_id: '',
    });
    adminService.getDepartments().then(setDepartments).catch(() => setDepartments([]));
    adminService.getSemesters().then(setSemesters).catch(() => setSemesters([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  React.useEffect(() => {
    if (!departmentId) {
      setSections([]);
      return;
    }
    adminService.getSections(departmentId).then(setSections).catch(() => setSections([]));
  }, [departmentId]);

  // Keep the password field in sync with the Roll Number until the admin
  // edits it directly — at that point their override takes precedence.
  React.useEffect(() => {
    if (!isStudent || passwordTouched) return;
    setValue('password', defaultStudentPassword(rollNumber || ''));
  }, [rollNumber, isStudent, passwordTouched, setValue]);

  const resetToDefaultPassword = () => {
    setPasswordTouched(false);
    setValue('password', defaultStudentPassword(rollNumber || ''));
  };

  const onSubmit = async (data: CreateUserFormData) => {
    setGeneralError(null);
    try {
      const payload: UserCreatePayload = {
        email: data.email,
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone || undefined,
        role: data.role,
        department_id: data.department_id || undefined,
        password: data.password || undefined,
      };
      if (isStudent) {
        payload.student_details = {
          roll_number: data.roll_number!,
          registration_number: data.registration_number!,
          date_of_birth: data.date_of_birth!,
          batch_year: Number(data.batch_year),
          section_id: data.section_id!,
          semester_id: data.semester_id!,
        };
      }
      const result = await userAdminService.createUser(payload);
      onCreated({ email: result.user.email, temporaryPassword: result.temporary_password, emailSent: result.email_sent });
    } catch (err: any) {
      const msg = applyServerFieldErrors<CreateUserFormData>(err, setError, (field) =>
        field.startsWith('student_details.') ? field.slice('student_details.'.length) : field
      );
      if (msg) setGeneralError(msg);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create User" description="A default password is generated — the new user must change it on first login.">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        {generalError && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs font-medium text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{generalError}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">First Name</label>
            <Input {...register('first_name')} error={!!errors.first_name} />
            <FieldError message={errors.first_name?.message} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Last Name</label>
            <Input {...register('last_name')} error={!!errors.last_name} />
            <FieldError message={errors.last_name?.message} />
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-foreground">Email</label>
          <Input type="email" {...register('email')} error={!!errors.email} />
          <FieldError message={errors.email?.message} />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Phone (optional)</label>
            <Input {...register('phone')} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Role</label>
            <select className={selectClass} {...register('role')}>
              {ASSIGNABLE_ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-foreground">Department {isStudent && '(required)'}</label>
          <select className={selectClass} {...register('department_id')}>
            <option value="">Select a department...</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <FieldError message={errors.department_id?.message} />
        </div>

        {isStudent && (
          <div className="space-y-3 rounded-md border border-dashed border-border p-3">
            <p className="text-xs font-semibold text-muted-foreground">Student Enrollment Details</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Roll Number</label>
                <Input {...register('roll_number')} placeholder="23BQ1A0501" error={!!errors.roll_number} />
                <FieldError message={errors.roll_number?.message} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Registration Number</label>
                <Input {...register('registration_number')} error={!!errors.registration_number} />
                <FieldError message={errors.registration_number?.message} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Date of Birth</label>
                <Input type="date" {...register('date_of_birth')} error={!!errors.date_of_birth} />
                <FieldError message={errors.date_of_birth?.message} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Batch Year</label>
                <Input type="number" {...register('batch_year')} error={!!errors.batch_year} />
                <FieldError message={errors.batch_year?.message} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Section</label>
                <select className={selectClass} {...register('section_id')}>
                  <option value="">Select...</option>
                  {sections.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                <FieldError message={errors.section_id?.message} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Semester</label>
                <select className={selectClass} {...register('semester_id')}>
                  <option value="">Select...</option>
                  {semesters.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                <FieldError message={errors.semester_id?.message} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-foreground">Default Password</label>
                {passwordTouched && (
                  <button
                    type="button"
                    onClick={resetToDefaultPassword}
                    className="flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline"
                  >
                    <RotateCcw className="h-3 w-3" /> Reset to default
                  </button>
                )}
              </div>
              <Input
                {...register('password', { onChange: () => setPasswordTouched(true) })}
                placeholder="23BQ1A0501@vvit.net"
                error={!!errors.password}
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                Default password is generated as <code className="font-mono">&lt;RollNumber&gt;@vvit.net</code>. Administrators may override it above.
              </p>
              <FieldError message={errors.password?.message} />
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting} isLoading={isSubmitting}>
            Create User
          </Button>
        </div>
      </form>
    </Modal>
  );
}
