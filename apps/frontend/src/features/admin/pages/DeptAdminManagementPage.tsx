import * as React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ShieldCheck,
  Plus,
  Search,
  Building2,
  KeyRound,
  Edit2,
} from 'lucide-react';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { Modal } from '@/shared/components/ui/Modal';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { adminService, Department } from '@/features/admin/services/admin.service';
import { deptAdminService, DeptAdminUser } from '@/features/dept_admin/services/deptAdmin.service';

export function DeptAdminManagementPage() {
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = React.useState('');
  const [createModalOpen, setCreateModalOpen] = React.useState(false);
  const [editingUser, setEditingUser] = React.useState<DeptAdminUser | null>(null);
  const [tempPassword, setTempPassword] = React.useState<string | null>(null);

  // Form state
  const [email, setEmail] = React.useState('');
  const [firstName, setFirstName] = React.useState('');
  const [lastName, setLastName] = React.useState('');
  const [departmentId, setDepartmentId] = React.useState('');
  const [phone, setPhone] = React.useState('');
  const [formError, setFormError] = React.useState<string | null>(null);

  const { data: departments } = useQuery<Department[]>({
    queryKey: ['admin', 'departments'],
    queryFn: adminService.getDepartments,
  });

  const { data: deptAdmins, isLoading } = useQuery<DeptAdminUser[]>({
    queryKey: ['admin', 'dept-admins'],
    queryFn: deptAdminService.listDeptAdmins,
  });

  const openCreateModal = () => {
    setEditingUser(null);
    setEmail('');
    setFirstName('');
    setLastName('');
    setDepartmentId(departments?.[0]?.id || '');
    setPhone('');
    setFormError(null);
    setCreateModalOpen(true);
  };

  const openEditModal = (user: DeptAdminUser) => {
    setEditingUser(user);
    setEmail(user.email);
    setFirstName(user.first_name);
    setLastName(user.last_name);
    setDepartmentId(user.department_id || '');
    setPhone(user.phone || '');
    setFormError(null);
    setCreateModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!departmentId) {
      setFormError('Please select a department.');
      return;
    }

    try {
      if (editingUser) {
        await deptAdminService.updateDeptAdmin(editingUser.id, {
          first_name: firstName,
          last_name: lastName,
          department_id: departmentId,
          phone,
        });
      } else {
        await deptAdminService.createDeptAdmin({
          email,
          first_name: firstName,
          last_name: lastName,
          department_id: departmentId,
          phone,
        });
      }
      queryClient.invalidateQueries({ queryKey: ['admin', 'dept-admins'] });
      setCreateModalOpen(false);
    } catch (err: any) {
      setFormError(
        err?.response?.data?.error?.message ??
        err?.response?.data?.detail ??
        'Failed to save Department Administrator.'
      );
    }
  };

  const handleResetPassword = async (userId: string) => {
    try {
      const res = await deptAdminService.resetPassword(userId);
      setTempPassword(res.temporary_password);
    } catch (err: any) {
      alert('Password reset failed.');
    }
  };

  const filtered = deptAdmins?.filter(
    (u) =>
      u.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.department_name || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Administration' },
          { label: 'User Directory', href: '/admin/users' },
          { label: 'Department Administrators' },
        ]}
      />
      <PageHeader
        title="Department Administrators"
        subtitle="Manage department-scoped administrators. Each Department Admin has full control strictly isolated to their assigned academic department."
        actions={
          <Button size="sm" onClick={openCreateModal}>
            <Plus className="mr-1.5 h-4 w-4" /> Add Department Admin
          </Button>
        }
      />

      {tempPassword && (
        <div className="mb-6 flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <div className="flex items-center gap-3">
            <KeyRound className="h-5 w-5 text-emerald-600" />
            <div>
              <p className="text-sm font-bold text-foreground">Temporary Password Generated</p>
              <p className="font-mono text-xs font-bold text-emerald-700 dark:text-emerald-400">{tempPassword}</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => setTempPassword(null)}>
            Dismiss
          </Button>
        </div>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-base">Assigned Administrators</CardTitle>
              <CardDescription>
                Department Administrators and their department assignments.
              </CardDescription>
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search administrators…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="h-8 pl-8 text-xs"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-64 w-full rounded-2xl" />
          ) : !filtered || filtered.length === 0 ? (
            <EmptyState
              icon={ShieldCheck}
              title="No Department Administrators found"
              description="Click 'Add Department Admin' above to assign an administrator to a department."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Administrator</TableHead>
                  <TableHead>Assigned Department</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 font-bold text-primary">
                          {user.first_name[0]}{user.last_name[0]}
                        </div>
                        <div>
                          <p className="font-bold text-foreground">{user.full_name}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono">
                        <Building2 className="mr-1 h-3 w-3 text-primary" />
                        {user.department_code || 'Unassigned'} — {user.department_name || 'No Dept'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{user.phone || '—'}</TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? 'success' : 'secondary'} dot>
                        {user.is_active ? 'Active' : 'Disabled'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs"
                          onClick={() => handleResetPassword(user.id)}
                          title="Reset Password"
                        >
                          <KeyRound className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs"
                          onClick={() => openEditModal(user)}
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Modal */}
      <Modal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title={editingUser ? `Edit ${editingUser.full_name}` : 'Create Department Administrator'}
        description="Assign a dedicated administrator to an academic department."
        className="max-w-md"
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-foreground">First Name</label>
              <Input
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-foreground">Last Name</label>
              <Input
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
              />
            </div>
          </div>

          {!editingUser && (
            <div className="space-y-1">
              <label className="text-xs font-bold text-foreground">Email Address</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@vvit.net"
                required
              />
            </div>
          )}

          <div className="space-y-1">
            <label className="text-xs font-bold text-foreground">Assigned Department</label>
            <select
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
              className="h-10 w-full rounded-xl border border-input bg-background px-3 text-xs font-semibold"
              required
            >
              <option value="" disabled>Select department…</option>
              {departments?.map((d) => (
                <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-foreground">Phone (Optional)</label>
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 9876543210"
            />
          </div>

          {formError && (
            <p className="text-xs font-medium text-rose-600">{formError}</p>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t border-border">
            <Button type="button" variant="outline" size="sm" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">
              {editingUser ? 'Save Changes' : 'Create Admin Account'}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
