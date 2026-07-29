import * as React from 'react';
import { Modal } from '@/shared/components/ui/Modal';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import { adminService, Department } from '../services/admin.service';
import { userAdminService, UserListItem } from '../services/admin.service';
import { AlertCircle } from 'lucide-react';

const ASSIGNABLE_ROLES = ['HOD', 'COUNSELLOR', 'FACULTY', 'STUDENT'];

const selectClass =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50';

interface EditUserModalProps {
  open: boolean;
  onClose: () => void;
  user: UserListItem | null;
  onSaved: () => void;
}

export function EditUserModal({ open, onClose, user, onSaved }: EditUserModalProps) {
  const [departments, setDepartments] = React.useState<Department[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [form, setForm] = React.useState({ first_name: '', last_name: '', phone: '', department_id: '', role: '' });

  React.useEffect(() => {
    if (!open) return;
    adminService.getDepartments().then(setDepartments).catch(() => setDepartments([]));
  }, [open]);

  React.useEffect(() => {
    if (!user) return;
    const [first, ...rest] = user.full_name.split(' ');
    setForm({
      first_name: first || '',
      last_name: rest.join(' '),
      phone: '',
      department_id: user.department_id || '',
      role: user.roles[0] || 'STUDENT',
    });
  }, [user]);

  const update = (field: keyof typeof form, value: string) => setForm((f) => ({ ...f, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await userAdminService.updateUser(user.id, {
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone || undefined,
        department_id: form.department_id || undefined,
        role: form.role,
      });
      onSaved();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Could not update user.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) return null;

  return (
    <Modal open={open} onClose={onClose} title="Edit User" description={user.email}>
      <form onSubmit={handleSubmit} className="space-y-3">
        {error && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs font-medium text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">First Name</label>
            <Input value={form.first_name} onChange={(e) => update('first_name', e.target.value)} required />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Last Name</label>
            <Input value={form.last_name} onChange={(e) => update('last_name', e.target.value)} required />
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-semibold text-foreground">Phone</label>
          <Input value={form.phone} onChange={(e) => update('phone', e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Role</label>
            <select className={selectClass} value={form.role} onChange={(e) => update('role', e.target.value)}>
              {ASSIGNABLE_ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-foreground">Department</label>
            <select className={selectClass} value={form.department_id} onChange={(e) => update('department_id', e.target.value)}>
              <option value="">None</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>Cancel</Button>
          <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Saving...' : 'Save Changes'}</Button>
        </div>
      </form>
    </Modal>
  );
}
