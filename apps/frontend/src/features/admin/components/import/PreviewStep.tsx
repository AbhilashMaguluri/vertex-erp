import * as React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Columns3,
  CopyX,
  GraduationCap,
  ListChecks,
  UserCheck,
  UserPlus,
  Users,
  XCircle,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { cn } from '@/shared/utils/cn';
import type { ImportPreview } from '../../services/import.service';

interface PreviewStepProps {
  preview: ImportPreview;
  onBack: () => void;
  onContinue: () => void;
}

export function PreviewStep({ preview, onBack, onContinue }: PreviewStepProps) {
  const [tab, setTab] = React.useState<'ranges' | 'counsellors' | 'duplicates' | 'issues'>('ranges');

  const issueCount = preview.errors.length + preview.warnings.length;
  const nothingToImport = preview.importable_students === 0;

  const tabs = [
    { key: 'ranges' as const, label: 'Roll number ranges', count: preview.ranges.length },
    { key: 'counsellors' as const, label: 'Counsellors', count: preview.counsellors.length },
    { key: 'duplicates' as const, label: 'Duplicates', count: preview.duplicates.length },
    { key: 'issues' as const, label: 'Warnings & errors', count: issueCount },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Students detected"
          value={preview.students_detected}
          icon={GraduationCap}
          description={`Expanded from ${preview.total_rows} row${preview.total_rows === 1 ? '' : 's'} in the file`}
        />
        <StatCard
          title="Will be created"
          value={preview.importable_students}
          icon={UserPlus}
          trend={preview.importable_students > 0 ? 'up' : 'neutral'}
          change={preview.importable_students > 0 ? 'New' : 'None'}
          description={
            preview.duplicate_students > 0
              ? `${preview.duplicate_students} already exist and will be skipped`
              : 'No duplicates found'
          }
        />
        <StatCard
          title="Counsellors"
          value={preview.counsellors_detected}
          icon={Users}
          description={`${preview.new_counsellors} new · ${preview.existing_counsellors} reused`}
        />
        <StatCard
          title="Warnings & errors"
          value={issueCount}
          icon={AlertTriangle}
          trend={preview.errors.length > 0 ? 'down' : 'neutral'}
          change={preview.errors.length > 0 ? `${preview.errors.length} error` : 'Clean'}
          description={preview.errors.length > 0 ? 'Rows with errors are skipped' : 'Nothing blocking the import'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Columns3 className="h-4 w-4 text-primary" />
            Columns understood
          </CardTitle>
          <CardDescription>
            Read from sheet <span className="font-semibold text-foreground">“{preview.sheet_name}”</span>, header
            found on row {preview.header_row_number}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {preview.detected_columns.map((column) => (
              <div
                key={column.field}
                className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5"
              >
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span className="text-[11px] font-bold text-emerald-800 dark:text-emerald-200">{column.label}</span>
                <span className="font-mono text-[10px] text-emerald-700/70 dark:text-emerald-300/70">
                  ← “{column.source_header}”
                </span>
              </div>
            ))}
          </div>

          {preview.ignored_columns.length > 0 && (
            <p className="text-[11px] font-medium leading-relaxed text-muted-foreground">
              Ignored:{' '}
              {preview.ignored_columns.map((name, index) => (
                <React.Fragment key={name}>
                  {index > 0 && ', '}
                  <span className="font-mono text-foreground/70">“{name}”</span>
                </React.Fragment>
              ))}
              . These columns carry nothing the system needs.
            </p>
          )}
        </CardContent>
      </Card>

      <div>
        <div className="mb-4 flex gap-1 overflow-x-auto border-b border-border/80 pb-2 select-none">
          {tabs.map((entry) => (
            <button
              key={entry.key}
              onClick={() => setTab(entry.key)}
              className={cn(
                'flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-xs font-bold transition-all cursor-pointer',
                tab === entry.key
                  ? 'bg-brand-600 text-white font-black shadow-md shadow-brand-600/25'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              )}
            >
              {entry.label}
              <span
                className={cn(
                  'rounded-full px-1.5 py-0.5 text-[10px] font-black',
                  tab === entry.key ? 'bg-white/20' : 'bg-muted'
                )}
              >
                {entry.count}
              </span>
            </button>
          ))}
        </div>

        {tab === 'ranges' && <RangesTable preview={preview} />}
        {tab === 'counsellors' && <CounsellorsTable preview={preview} />}
        {tab === 'duplicates' && <DuplicatesTable preview={preview} />}
        {tab === 'issues' && <IssuesList preview={preview} />}
      </div>

      {nothingToImport && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <div className="text-xs leading-relaxed text-amber-800 dark:text-amber-200">
            <p className="font-bold">There is nothing new to import.</p>
            <p className="mt-0.5 font-medium">
              Every roll number in this file already has an account. Continuing will create no students — it will
              only reconcile counsellor accounts.
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/80 pt-5">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          Upload a different file
        </Button>
        <Button size="lg" onClick={onContinue}>
          Continue to configure
          <ArrowRight className="ml-1.5 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function RangesTable({ preview }: { preview: ImportPreview }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-16">Row</TableHead>
          <TableHead>As written</TableHead>
          <TableHead>Understood as</TableHead>
          <TableHead className="w-24 text-right">Students</TableHead>
          <TableHead>Counsellor</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {preview.ranges.map((range) => (
          <TableRow key={range.row_number}>
            <TableCell className="font-mono text-muted-foreground">{range.row_number}</TableCell>
            <TableCell className="font-mono text-muted-foreground">{range.raw_text || '—'}</TableCell>
            <TableCell>
              {range.errors.length > 0 ? (
                <span className="flex items-center gap-1.5 font-semibold text-rose-600 dark:text-rose-400">
                  <XCircle className="h-3.5 w-3.5 shrink-0" />
                  {range.errors[0]}
                </span>
              ) : (
                <span className="font-mono font-semibold text-foreground">{range.description}</span>
              )}
            </TableCell>
            <TableCell className="text-right">
              <Badge variant={range.student_count > 0 ? 'default' : 'destructive'}>{range.student_count}</Badge>
            </TableCell>
            <TableCell>
              {range.counsellor_name ? (
                <div className="flex flex-col">
                  <span className="font-semibold text-foreground">{range.counsellor_name}</span>
                  {range.counsellor_phone && (
                    <span className="font-mono text-[10px] text-muted-foreground">{range.counsellor_phone}</span>
                  )}
                </div>
              ) : (
                <span className="text-muted-foreground">—</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function CounsellorsTable({ preview }: { preview: ImportPreview }) {
  if (preview.counsellors.length === 0) {
    return <EmptyPanel icon={Users} message="No counsellor column was recognised in this file." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>As written on the sheet</TableHead>
          <TableHead>Account</TableHead>
          <TableHead>Username</TableHead>
          <TableHead>Phone</TableHead>
          <TableHead className="text-right">Students</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {preview.counsellors.map((counsellor) => (
          <TableRow key={counsellor.key}>
            <TableCell>
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    'flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-[10px] font-black text-white',
                    counsellor.status === 'NEW'
                      ? 'bg-gradient-to-tr from-brand-500 to-brand-600'
                      : 'bg-gradient-to-tr from-emerald-500 to-emerald-600'
                  )}
                >
                  {counsellor.display_name.substring(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <span className="block text-xs font-bold text-foreground">{counsellor.name_as_written}</span>
                  <span className="text-[10px] text-muted-foreground">will be stored as {counsellor.display_name}</span>
                </div>
              </div>
            </TableCell>
            <TableCell>
              {counsellor.status === 'NEW' ? (
                <Badge variant="default" className="gap-1">
                  <UserPlus className="h-3 w-3" /> New account
                </Badge>
              ) : (
                <Badge variant="success" className="gap-1">
                  <UserCheck className="h-3 w-3" /> Reused
                  {counsellor.matched_on ? ` · matched on ${counsellor.matched_on}` : ''}
                </Badge>
              )}
            </TableCell>
            <TableCell className="font-mono text-muted-foreground">{counsellor.proposed_username ?? '—'}</TableCell>
            <TableCell className="font-mono text-muted-foreground">{counsellor.phone ?? '—'}</TableCell>
            <TableCell className="text-right">
              <Badge variant="outline">{counsellor.student_count}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function DuplicatesTable({ preview }: { preview: ImportPreview }) {
  if (preview.duplicates.length === 0) {
    return (
      <EmptyPanel
        icon={CheckCircle2}
        message="No duplicates. Every roll number in this file is new to the system and appears only once."
      />
    );
  }

  return (
    <>
      <div className="mb-3 flex items-start gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3.5">
        <CopyX className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <p className="text-xs font-medium leading-relaxed text-amber-800 dark:text-amber-200">
          These are skipped, never overwritten. An existing student keeps their account, their history and their
          current counsellor.
        </p>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Roll number</TableHead>
            <TableHead>Existing student</TableHead>
            <TableHead>Why it is skipped</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {preview.duplicates.map((duplicate) => (
            <TableRow key={`${duplicate.roll_number}-${duplicate.row_numbers.join('-')}`}>
              <TableCell className="font-mono font-bold text-foreground">{duplicate.roll_number}</TableCell>
              <TableCell className="text-muted-foreground">{duplicate.existing_name ?? '—'}</TableCell>
              <TableCell className="text-muted-foreground">{duplicate.reason}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}

function IssuesList({ preview }: { preview: ImportPreview }) {
  if (preview.errors.length === 0 && preview.warnings.length === 0) {
    return <EmptyPanel icon={ListChecks} message="The file parsed cleanly. No warnings and no errors." />;
  }

  return (
    <div className="space-y-2">
      {preview.errors.map((message) => (
        <div
          key={`error-${message}`}
          className="flex items-start gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5"
        >
          <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
          <div className="min-w-0 text-xs leading-relaxed">
            <span className="font-black uppercase tracking-wider text-rose-700 dark:text-rose-300">Error</span>
            <p className="font-medium text-rose-800 dark:text-rose-200">{message}</p>
          </div>
        </div>
      ))}
      {preview.warnings.map((message) => (
        <div
          key={`warning-${message}`}
          className="flex items-start gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3.5"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <div className="min-w-0 text-xs leading-relaxed">
            <span className="font-black uppercase tracking-wider text-amber-700 dark:text-amber-300">Warning</span>
            <p className="font-medium text-amber-800 dark:text-amber-200">{message}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyPanel({ icon: Icon, message }: { icon: React.ElementType; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border/80 bg-card/50 p-10 text-center shadow-xs">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 ring-8 ring-emerald-500/5">
        <Icon className="h-5 w-5" />
      </div>
      <p className="max-w-md text-xs font-medium leading-relaxed text-muted-foreground">{message}</p>
    </div>
  );
}
