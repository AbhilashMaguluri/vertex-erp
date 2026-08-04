import * as React from 'react';
import {
  Users,
  GraduationCap,
  Link2,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  ArrowRight,
  Download,
  Search,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardHeader } from '@/shared/components/ui/Card';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { Input } from '@/shared/components/ui/Input';
import type { MembershipImportPreview } from '../../services/membershipImport.service';
import { membershipImportService } from '../../services/membershipImport.service';

type TabId = 'students' | 'counselors' | 'memberships';

interface MembershipPreviewStepProps {
  preview: MembershipImportPreview;
  onBack: () => void;
  onContinue: () => void;
}

export function MembershipPreviewStep({ preview, onBack, onContinue }: MembershipPreviewStepProps) {
  const [activeTab, setActiveTab] = React.useState<TabId>('students');
  const [searchTerm, setSearchTerm] = React.useState('');
  const { summary, tables, validation_errors } = preview;

  const hasErrors = summary.errors > 0 || summary.missing_counselors > 0;
  const hasWarnings = summary.warnings > 0;

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-6">
        <StatCard
          title="Total Students"
          value={summary.total_students}
          icon={GraduationCap}
          description={`${summary.new_student_accounts} new accounts needed`}
        />
        <StatCard
          title="Existing Students"
          value={summary.existing_student_accounts}
          icon={CheckCircle2}
          description="Already in the system"
        />
        <StatCard
          title="New Accounts"
          value={summary.new_student_accounts}
          icon={Users}
          description="Will be created"
        />
        <StatCard
          title="Counselors Found"
          value={summary.existing_counselor_accounts}
          icon={Users}
          description={`${summary.missing_counselors} missing`}
        />
        <StatCard
          title="New Memberships"
          value={summary.new_memberships}
          icon={Link2}
          description={`${summary.existing_memberships} already exist`}
        />
        <StatCard
          title="Errors"
          value={summary.errors}
          icon={AlertCircle}
          description={`${summary.warnings} warnings`}
        />
      </div>

      {/* Alerts */}
      {hasErrors && (
        <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400" />
          <div>
            <p className="text-sm font-bold text-rose-700 dark:text-rose-300">
              {summary.errors} error{summary.errors !== 1 ? 's' : ''} found
            </p>
            <p className="mt-0.5 text-xs text-rose-600/80 dark:text-rose-400/80">
              {summary.missing_counselors > 0 &&
                `${summary.missing_counselors} counselor${summary.missing_counselors !== 1 ? 's' : ''} not found in the system. `}
              Rows with errors will be skipped during import.
              {validation_errors.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-2 h-6 text-xs"
                  onClick={() => membershipImportService.downloadErrorReport(preview.batch_id)}
                >
                  <Download className="mr-1 h-3 w-3" />
                  Download Import_Errors.xlsx
                </Button>
              )}
            </p>
          </div>
        </div>
      )}
      {hasWarnings && !hasErrors && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
          <p className="text-sm text-amber-700 dark:text-amber-300">
            {summary.warnings} warning{summary.warnings !== 1 ? 's' : ''} — import can proceed, but review them.
          </p>
        </div>
      )}

      {/* Tab navigation */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex gap-1 rounded-xl bg-muted/50 p-1">
              {([
                { id: 'students' as TabId, label: 'Students', icon: GraduationCap, count: tables.students.length },
                { id: 'counselors' as TabId, label: 'Counselors', icon: Users, count: tables.counselors.length },
                { id: 'memberships' as TabId, label: 'Memberships', icon: Link2, count: tables.memberships.length },
              ]).map(tab => (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setSearchTerm(''); }}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                    activeTab === tab.id
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <tab.icon className="h-3.5 w-3.5" />
                  {tab.label}
                  <Badge variant="secondary" className="ml-1 text-[10px]">{tab.count}</Badge>
                </button>
              ))}
            </div>

            <div className="relative w-56">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="h-8 pl-8 text-xs"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {activeTab === 'students' && (
            <StudentTable rows={tables.students} search={searchTerm} />
          )}
          {activeTab === 'counselors' && (
            <CounselorTable rows={tables.counselors} search={searchTerm} />
          )}
          {activeTab === 'memberships' && (
            <MembershipTable rows={tables.memberships} search={searchTerm} />
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="mr-1.5 h-4 w-4" /> Back
        </Button>
        <Button onClick={onContinue}>
          Configure & Import <ArrowRight className="ml-1.5 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// --- Sub-tables ---------------------------------------------------------

function StudentTable({ rows, search }: { rows: MembershipImportPreview['tables']['students']; search: string }) {
  const filtered = rows.filter(r =>
    !search || r.roll_number.toLowerCase().includes(search.toLowerCase()) ||
    (r.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (r.email_used || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-h-[420px] overflow-auto rounded-lg border border-border/30">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Roll Number</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.length === 0 ? (
            <TableRow><TableCell colSpan={5} className="py-8 text-center text-muted-foreground">No students to show.</TableCell></TableRow>
          ) : filtered.slice(0, 200).map((r) => (
            <TableRow key={r.roll_number}>
              <TableCell className="font-mono text-xs font-bold">{r.roll_number}</TableCell>
              <TableCell className="text-xs text-muted-foreground">{r.email_used || '—'}</TableCell>
              <TableCell className="text-xs">{r.name || '—'}</TableCell>
              <TableCell>
                <Badge variant={r.status === 'Existing' ? 'success' : 'warning'} dot>{r.status}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant={r.action === 'Reuse' ? 'info' : 'secondary'}>{r.action}</Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {filtered.length > 200 && (
        <p className="py-2 text-center text-xs text-muted-foreground">
          Showing first 200 of {filtered.length} students
        </p>
      )}
    </div>
  );
}

function CounselorTable({ rows, search }: { rows: MembershipImportPreview['tables']['counselors']; search: string }) {
  const filtered = rows.filter(r =>
    !search || r.email.toLowerCase().includes(search.toLowerCase()) ||
    (r.name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-h-[420px] overflow-auto rounded-lg border border-border/30">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Action</TableHead>
            <TableHead className="text-right">Students</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.length === 0 ? (
            <TableRow><TableCell colSpan={5} className="py-8 text-center text-muted-foreground">No counselors to show.</TableCell></TableRow>
          ) : filtered.map((r) => (
            <TableRow key={r.email}>
              <TableCell className="text-xs font-semibold">{r.email}</TableCell>
              <TableCell className="text-xs">{r.name || '—'}</TableCell>
              <TableCell>
                <Badge variant={r.status === 'Found' ? 'success' : 'destructive'} dot>{r.status}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant={r.action === 'Reuse' ? 'info' : 'destructive'}>{r.action}</Badge>
              </TableCell>
              <TableCell className="text-right font-bold">{r.student_count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function MembershipTable({ rows, search }: { rows: MembershipImportPreview['tables']['memberships']; search: string }) {
  const filtered = rows.filter(r =>
    !search || r.student_roll.toLowerCase().includes(search.toLowerCase()) ||
    r.counselor_email.toLowerCase().includes(search.toLowerCase()) ||
    (r.student_name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-h-[420px] overflow-auto rounded-lg border border-border/30">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Student Roll</TableHead>
            <TableHead>Student Name</TableHead>
            <TableHead>Counselor</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.length === 0 ? (
            <TableRow><TableCell colSpan={5} className="py-8 text-center text-muted-foreground">No memberships to show.</TableCell></TableRow>
          ) : filtered.slice(0, 200).map((r, i) => (
            <TableRow key={`${r.student_roll}-${r.counselor_email}-${i}`}>
              <TableCell className="font-mono text-xs font-bold">{r.student_roll}</TableCell>
              <TableCell className="text-xs">{r.student_name || '—'}</TableCell>
              <TableCell className="text-xs">
                <div>{r.counselor_email}</div>
                {r.counselor_name && (
                  <div className="text-muted-foreground">{r.counselor_name}</div>
                )}
              </TableCell>
              <TableCell>
                <Badge
                  variant={
                    r.status === 'New' ? 'success' :
                    r.status === 'Existing' ? 'info' :
                    'secondary'
                  }
                  dot
                >
                  {r.status}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge
                  variant={
                    r.action === 'Create' ? 'success' :
                    r.action === 'Update' ? 'warning' :
                    r.action === 'Error' ? 'destructive' :
                    'secondary'
                  }
                >
                  {r.action}
                </Badge>
                {r.error && (
                  <p className="mt-0.5 text-[10px] text-rose-600 dark:text-rose-400">{r.error}</p>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {filtered.length > 200 && (
        <p className="py-2 text-center text-xs text-muted-foreground">
          Showing first 200 of {filtered.length} memberships
        </p>
      )}
    </div>
  );
}
