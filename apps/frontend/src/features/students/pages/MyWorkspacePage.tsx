import { useQuery } from '@tanstack/react-query';
import { studentService, Student360Data } from '../services/student.service';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { GraduationCap } from 'lucide-react';
import { StudentWorkspaceView } from '../components/StudentWorkspaceView';

/** Self-service student portal — the logged-in student's own academic
 * snapshot. Uses the "self" mode of StudentWorkspaceView, which strips every
 * case-management control (risk flagging, new-session, internal notes) and
 * uses first-person terminology. */
export function MyWorkspacePage() {
  const { data: workspaceData, isLoading, error } = useQuery<Student360Data>({
    queryKey: ['students', 'me', 'workspace'],
    queryFn: studentService.getMyWorkspace,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-48 rounded-2xl" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (error || !workspaceData) {
    return (
      <EmptyState
        icon={GraduationCap}
        title="No student record linked"
        description="Your account isn't linked to an active student record. Contact your institutional administrator."
      />
    );
  }

  return (
    <>
      <Breadcrumbs items={[{ label: 'My Portal' }]} />
      <StudentWorkspaceView workspaceData={workspaceData} mode="self" />
    </>
  );
}
