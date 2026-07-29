import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { userAdminService, UserListItem, PaginatedUsers } from '../services/admin.service';
import { CreateUserModal } from '../components/CreateUserModal';
import { EditUserModal } from '../components/EditUserModal';
import { TemporaryPasswordModal } from '../components/TemporaryPasswordModal';
import { UserSessionsModal } from '../components/UserSessionsModal';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/shared/components/ui/Table';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Users, Plus, Search, ShieldCheck, UserX, UserCheck, FileSpreadsheet, Sparkles, Pencil, KeyRound, Monitor } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

const ROLE_TABS = [
  { key: '', label: 'All Users' },
  { key: 'STUDENT', label: 'Students' },
  { key: 'FACULTY', label: 'Faculty' },
  { key: 'COUNSELLOR', label: 'Counsellors' },
  { key: 'HOD', label: 'HODs' },
  { key: 'ADMIN', label: 'Admins' },
];

export function UserManagementPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [roleFilter, setRoleFilter] = React.useState<string>('');
  const [statusFilter, setStatusFilter] = React.useState<string>('');
  const [searchQuery, setSearchQuery] = React.useState<string>('');

  const [isCreateOpen, setIsCreateOpen] = React.useState(false);
  const [editingUser, setEditingUser] = React.useState<UserListItem | null>(null);
  const [sessionsUser, setSessionsUser] = React.useState<UserListItem | null>(null);
  const [tempPasswordInfo, setTempPasswordInfo] = React.useState<{ email: string; temporaryPassword: string; emailSent: boolean } | null>(null);

  const { data: paginatedUsers, isLoading } = useQuery<PaginatedUsers>({
    queryKey: ['admin', 'users', roleFilter, statusFilter, searchQuery],
    queryFn: () =>
      userAdminService.listUsers({
        role: roleFilter || undefined,
        is_active: statusFilter === 'ACTIVE' ? true : statusFilter === 'DEACTIVATED' ? false : undefined,
        search: searchQuery || undefined,
      }),
  });

  const toggleStatusMutation = useMutation({
    mutationFn: (user: UserListItem) =>
      user.is_active ? userAdminService.deactivateUser(user.id) : userAdminService.activateUser(user.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });

  const resetPasswordMutation = useMutation({
    mutationFn: (user: UserListItem) => userAdminService.resetPassword(user.id).then((res) => ({ user, res })),
    onSuccess: ({ user, res }) => {
      setTempPasswordInfo({ email: user.email, temporaryPassword: res.temporary_password, emailSent: res.email_sent });
    },
  });

  const users = paginatedUsers?.data ?? [];
  const totalCount = paginatedUsers?.pagination?.total ?? users.length;
  const activeCount = users.filter((u) => u.is_active).length;
  const adminCount = users.filter((u) => u.roles.includes('ADMIN') || u.roles.includes('SUPER_ADMIN')).length;

  return (
    <>
      <Breadcrumbs items={[{ label: 'Administration' }, { label: 'User Directory & Access Control' }]} />

      <PageHeader
        title="User Accounts & Privilege Directory"
        subtitle="Manage HODs, Counsellors, Faculty, and Student access permissions across campus"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate('/admin/imports')}>
              <FileSpreadsheet className="mr-1.5 h-4 w-4" /> Office Import
            </Button>
            <Button size="sm" onClick={() => setIsCreateOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" /> Create User
            </Button>
          </div>
        }
      />

      {/* Top Executive Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 my-6">
        <StatCard title="Total Directory Users" value={totalCount} icon={Users} description="Registered system accounts" />
        <StatCard title="Active Operational Accounts" value={activeCount} icon={ShieldCheck} trend="up" change="Active" description="Cleared for system access" />
        <StatCard title="Administrative Directory" value={adminCount} icon={Sparkles} description="Admins & HOD personnel" />
      </div>

      {/* Advanced Filter Toolbar */}
      <div className="space-y-4 my-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl border border-border/80 bg-card shadow-xs">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/70" />
            <Input
              placeholder="Search by full name or email address..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-muted-foreground">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 rounded-xl border border-input bg-background px-3 text-xs font-semibold focus:ring-2 focus:ring-ring"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="DEACTIVATED">DEACTIVATED</option>
            </select>
          </div>
        </div>

        {/* Role Segmented Pills */}
        <div className="flex border-b border-border/80 gap-1 overflow-x-auto pb-2 select-none">
          {ROLE_TABS.map((tab) => {
            const isActive = roleFilter === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setRoleFilter(tab.key)}
                className={cn(
                  'rounded-xl px-4 py-2 text-xs font-bold transition-all cursor-pointer whitespace-nowrap',
                  isActive
                    ? 'bg-brand-600 text-white font-black shadow-md shadow-brand-600/25'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                )}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Directory Data Table */}
      <div>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
          </div>
        ) : users.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No Users Matched"
            description="No directory users found matching the selected filter criteria."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User Identity</TableHead>
                <TableHead>Assigned Roles</TableHead>
                <TableHead>Account Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((userItem) => (
                <TableRow key={userItem.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-500 to-brand-600 text-white font-black text-xs">
                        {userItem.full_name.substring(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-foreground block text-xs truncate">{userItem.full_name}</span>
                          {userItem.username && (
                            <Badge variant="secondary" className="font-mono text-[9px]">
                              {userItem.username}
                            </Badge>
                          )}
                        </div>
                        <span className="text-[11px] text-muted-foreground font-mono">{userItem.email}</span>
                      </div>
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-1 flex-wrap">
                      {userItem.roles.map((r) => (
                        <Badge key={r} variant="outline" className="font-mono text-[10px]">
                          {r}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>

                  <TableCell>
                    <Badge variant={userItem.is_active ? 'success' : 'destructive'} dot>
                      {userItem.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                    </Badge>
                  </TableCell>

                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setEditingUser(userItem)}
                        className="text-xs font-semibold text-muted-foreground hover:bg-accent"
                      >
                        <Pencil className="mr-1 h-3.5 w-3.5" /> Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => resetPasswordMutation.mutate(userItem)}
                        disabled={resetPasswordMutation.isPending}
                        className="text-xs font-semibold text-muted-foreground hover:bg-accent"
                      >
                        <KeyRound className="mr-1 h-3.5 w-3.5" /> Reset Password
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSessionsUser(userItem)}
                        className="text-xs font-semibold text-muted-foreground hover:bg-accent"
                      >
                        <Monitor className="mr-1 h-3.5 w-3.5" /> Sessions
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleStatusMutation.mutate(userItem)}
                        disabled={toggleStatusMutation.isPending}
                        className={cn(
                          'text-xs font-semibold',
                          userItem.is_active ? 'text-rose-600 hover:bg-rose-500/10' : 'text-emerald-600 hover:bg-emerald-500/10'
                        )}
                      >
                        {userItem.is_active ? (
                          <>
                            <UserX className="mr-1 h-3.5 w-3.5" /> Deactivate
                          </>
                        ) : (
                          <>
                            <UserCheck className="mr-1 h-3.5 w-3.5" /> Activate
                          </>
                        )}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <CreateUserModal
        open={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={(result) => {
          setIsCreateOpen(false);
          queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
          setTempPasswordInfo({ email: result.email, temporaryPassword: result.temporaryPassword, emailSent: result.emailSent });
        }}
      />

      <EditUserModal
        open={!!editingUser}
        user={editingUser}
        onClose={() => setEditingUser(null)}
        onSaved={() => {
          setEditingUser(null);
          queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
        }}
      />

      <UserSessionsModal
        open={!!sessionsUser}
        userId={sessionsUser?.id ?? null}
        userEmail={sessionsUser?.email ?? ''}
        onClose={() => setSessionsUser(null)}
      />

      {tempPasswordInfo && (
        <TemporaryPasswordModal
          open={!!tempPasswordInfo}
          email={tempPasswordInfo.email}
          temporaryPassword={tempPasswordInfo.temporaryPassword}
          emailSent={tempPasswordInfo.emailSent}
          onClose={() => setTempPasswordInfo(null)}
        />
      )}
    </>
  );
}
