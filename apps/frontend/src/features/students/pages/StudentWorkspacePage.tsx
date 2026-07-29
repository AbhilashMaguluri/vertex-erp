import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { studentService, Student360Data } from '../services/student.service';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { User } from 'lucide-react';
import { StudentWorkspaceView } from '../components/StudentWorkspaceView';

/** Staff case-management view — counsellors/faculty/HOD/admins looking up
 * a specific student's Student 360 record. Never rendered for the student
 * themself; see MyWorkspacePage for the self-service equivalent. */
export function StudentWorkspacePage() {
  const { studentId } = useParams<{ studentId: string }>();

  const { data: workspaceData, isLoading, error } = useQuery<Student360Data>({
    queryKey: ['students', studentId, 'workspace'],
    queryFn: () => studentService.getStudent360(studentId!),
    enabled: !!studentId,
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
        icon={User}
        title="Student Record Not Found"
        description="Unable to retrieve workspace data for this student."
      />
    );
  }

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Assigned Students', href: '/students' },
          { label: workspaceData.profile.full_name },
        ]}
      />
      <StudentWorkspaceView workspaceData={workspaceData} mode="staff" />
    </>
  );
}
