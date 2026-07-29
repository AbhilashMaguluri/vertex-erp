import * as React from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import {
  studentService,
  CaseloadFilters,
  CaseloadStudent,
} from '../services/student.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { Pagination } from '@/shared/components/ui/Pagination';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/components/ui/Table';
import {
  AttendanceCell,
  GpaCell,
  RiskBadge,
  StudentAvatar,
  formatSessionDate,
  yearLabel,
} from '../components/StudentPresentation';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { cn } from '@/shared/utils/cn';
import {
  Users,
  Search,
  SlidersHorizontal,
  X,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  MessageSquarePlus,
  ExternalLink,
  AlertTriangle,
  PhoneCall,
  NotebookPen,
} from 'lucide-react';

const PER_PAGE = 25;

/** Quick filters expressed as the API params they set — one click replaces
 *  hunting through four dropdowns for the three cohorts a counsellor actually
 *  chases day to day. */
const QUICK_FILTERS: { key: string; label: string; params: CaseloadFilters }[] = [
  { key: 'high-risk', label: 'High risk', params: { risk_level: 'HIGH' } },
  { key: 'low-attendance', label: `Attendance below 75%`, params: { max_attendance: 74.9 } },
  { key: 'backlogs', label: 'Has backlogs', params: { has_backlogs: true } },
];

export function MyStudentsPage() {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const canCreateSession = hasPermission('counselling.create');
  const canReadParentComms = hasPermission('parent_communication.read');

  const [searchInput, setSearchInput] = React.useState(searchParams.get('search') ?? '');
  const [showFilters, setShowFilters] = React.useState(false);
  const searchRef = React.useRef<HTMLInputElement>(null);

  // The workspace's "Search student" quick action lands here with ?focus=search
  // so one click puts the cursor in the box rather than on the page.
  React.useEffect(() => {
    if (searchParams.get('focus') !== 'search') return;
    searchRef.current?.focus();
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete('focus');
        return next;
      },
      { replace: true }
    );
  }, [searchParams, setSearchParams]);

  // Debounce typing so each keystroke doesn't become a request.
  React.useEffect(() => {
    const t = setTimeout(() => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (searchInput) next.set('search', searchInput);
        else next.delete('search');
        next.delete('page');
        return next;
      });
    }, 350);
    return () => clearTimeout(t);
  }, [searchInput, setSearchParams]);

  // URL is the single source of truth for filter state, so a filtered caseload
  // is shareable and survives a refresh or a trip into a student workspace.
  const filters: CaseloadFilters = React.useMemo(() => {
    const get = (k: string) => searchParams.get(k) ?? undefined;
    const num = (k: string) => (get(k) ? Number(get(k)) : undefined);
    return {
      search: get('search'),
      year: num('year'),
      section_id: get('section_id'),
      semester_id: get('semester_id'),
      department_id: get('department_id'),
      batch_year: num('batch_year'),
      risk_level: get('risk_level'),
      status: get('status'),
      min_attendance: num('min_attendance'),
      max_attendance: num('max_attendance'),
      min_cgpa: num('min_cgpa'),
      max_cgpa: num('max_cgpa'),
      has_backlogs: get('has_backlogs') ? get('has_backlogs') === 'true' : undefined,
      sort_by: get('sort_by') ?? 'roll_number',
      sort_dir: (get('sort_dir') as 'asc' | 'desc') ?? 'asc',
      page: num('page') ?? 1,
      per_page: PER_PAGE,
    };
  }, [searchParams]);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['students', 'caseload', filters],
    queryFn: () => studentService.getCaseload(filters),
    placeholderData: keepPreviousData,
  });

  const { data: facets } = useQuery({
    queryKey: ['students', 'caseload', 'facets'],
    queryFn: studentService.getCaseloadFacets,
    staleTime: 5 * 60_000,
  });

  const setParam = (key: string, value?: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value === undefined || value === '') next.delete(key);
      else next.set(key, value);
      if (key !== 'page') next.delete('page');
      return next;
    });
  };

  const toggleSort = (field: string) => {
    const isCurrent = filters.sort_by === field;
    const nextDir = isCurrent && filters.sort_dir === 'asc' ? 'desc' : 'asc';
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('sort_by', field);
      next.set('sort_dir', nextDir);
      next.delete('page');
      return next;
    });
  };

  const applyQuickFilter = (params: CaseloadFilters) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      Object.entries(params).forEach(([k, v]) => next.set(k, String(v)));
      next.delete('page');
      return next;
    });
  };

  const clearFilters = () => {
    setSearchInput('');
    setSearchParams(new URLSearchParams());
  };

  const activeFilterCount = [
    'year', 'section_id', 'semester_id', 'department_id', 'batch_year', 'risk_level', 'status',
    'min_attendance', 'max_attendance', 'min_cgpa', 'max_cgpa', 'has_backlogs',
  ].filter((k) => searchParams.get(k)).length;

  const students = data?.data ?? [];
  const pagination = data?.pagination;

  const SortHeader = ({ field, children, className }: { field: string; children: React.ReactNode; className?: string }) => {
    const active = filters.sort_by === field;
    const Icon = !active ? ArrowUpDown : filters.sort_dir === 'asc' ? ArrowUp : ArrowDown;
    return (
      <TableHead className={className}>
        <button
          type="button"
          onClick={() => toggleSort(field)}
          className={cn(
            'inline-flex items-center gap-1.5 uppercase tracking-wider transition-colors hover:text-foreground cursor-pointer',
            active && 'text-foreground'
          )}
        >
          {children}
          <Icon className="h-3 w-3" />
        </button>
      </TableHead>
    );
  };

  return (
    <>
      <Breadcrumbs items={[{ label: 'Assigned Students' }]} />

      <PageHeader
        title="Assigned Students"
        subtitle="Your caseload — open a student to see their full record, or start a session directly"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant={showFilters || activeFilterCount ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowFilters((v) => !v)}
            >
              <SlidersHorizontal className="mr-1.5 h-3.5 w-3.5" />
              Filters
              {activeFilterCount > 0 && (
                <span className="ml-1.5 rounded-full bg-white/20 px-1.5 text-[10px] font-black">
                  {activeFilterCount}
                </span>
              )}
            </Button>
          </div>
        }
      />

      <div className="mt-6 space-y-4">
        {/* Search + quick filters */}
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              ref={searchRef}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Roll number, name, phone, email, branch or section…"
              className="pl-9"
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => setSearchInput('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {QUICK_FILTERS.map((q) => (
              <Button key={q.key} variant="outline" size="sm" onClick={() => applyQuickFilter(q.params)}>
                {q.label}
              </Button>
            ))}
            {(activeFilterCount > 0 || searchInput) && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="mr-1 h-3.5 w-3.5" /> Clear
              </Button>
            )}
          </div>
        </div>

        {/* Filter panel — options come from the caller's own caseload, so a
            selection can never return an empty table by construction. */}
        {showFilters && (
          <Card>
            <CardContent className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
              <FilterSelect
                label="Year"
                value={searchParams.get('year') ?? ''}
                onChange={(v) => setParam('year', v)}
                options={(facets?.years ?? []).map((y) => ({ value: String(y), label: `${yearLabel(y)} Year` }))}
              />
              <FilterSelect
                label="Section"
                value={searchParams.get('section_id') ?? ''}
                onChange={(v) => setParam('section_id', v)}
                options={(facets?.sections ?? []).map((s) => ({ value: s.id, label: `Section ${s.label}` }))}
              />
              <FilterSelect
                label="Semester"
                value={searchParams.get('semester_id') ?? ''}
                onChange={(v) => setParam('semester_id', v)}
                options={(facets?.semesters ?? []).map((s) => ({ value: s.id, label: s.label }))}
              />
              <FilterSelect
                label="Branch"
                value={searchParams.get('department_id') ?? ''}
                onChange={(v) => setParam('department_id', v)}
                options={(facets?.departments ?? []).map((d) => ({ value: d.id, label: d.label }))}
              />
              <FilterSelect
                label="Batch"
                value={searchParams.get('batch_year') ?? ''}
                onChange={(v) => setParam('batch_year', v)}
                options={(facets?.batch_years ?? []).map((b) => ({ value: String(b), label: `${b} Batch` }))}
              />
              <FilterSelect
                label="Risk level"
                value={searchParams.get('risk_level') ?? ''}
                onChange={(v) => setParam('risk_level', v)}
                options={(facets?.risk_levels ?? []).map((r) => ({ value: r, label: r }))}
              />
              <FilterSelect
                label="Status"
                value={searchParams.get('status') ?? ''}
                onChange={(v) => setParam('status', v)}
                options={(facets?.statuses ?? []).map((s) => ({ value: s, label: s }))}
              />
              <FilterSelect
                label="Backlogs"
                value={searchParams.get('has_backlogs') ?? ''}
                onChange={(v) => setParam('has_backlogs', v)}
                options={[
                  { value: 'true', label: 'Has active backlogs' },
                  { value: 'false', label: 'No backlogs' },
                ]}
              />
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                  Attendance range (%)
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    placeholder="Min"
                    value={searchParams.get('min_attendance') ?? ''}
                    onChange={(e) => setParam('min_attendance', e.target.value)}
                  />
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    placeholder="Max"
                    value={searchParams.get('max_attendance') ?? ''}
                    onChange={(e) => setParam('max_attendance', e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Table */}
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : isError ? (
          <EmptyState
            icon={AlertTriangle}
            title="Could not load your caseload"
            description={
              (error as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ??
              'Something went wrong fetching assigned students. Please retry.'
            }
          />
        ) : students.length === 0 ? (
          <EmptyState
            icon={Users}
            title={activeFilterCount || searchInput ? 'No students match these filters' : 'No students assigned yet'}
            description={
              activeFilterCount || searchInput
                ? 'Try widening or clearing the filters to see more of your caseload.'
                : 'An administrator assigns students to counsellors. Once you have a caseload it appears here.'
            }
            actionLabel={activeFilterCount || searchInput ? 'Clear filters' : undefined}
            onAction={activeFilterCount || searchInput ? clearFilters : undefined}
          />
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <SortHeader field="roll_number">Student</SortHeader>
                  <TableHead>Branch</TableHead>
                  <TableHead>Year / Section</TableHead>
                  <SortHeader field="attendance">Attendance</SortHeader>
                  <SortHeader field="cgpa">CGPA</SortHeader>
                  <TableHead>Backlogs</TableHead>
                  <SortHeader field="risk">Risk</SortHeader>
                  <SortHeader field="last_session">Last session</SortHeader>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {students.map((s: CaseloadStudent) => (
                  <TableRow key={s.id} className="group">
                    <TableCell>
                      <Link to={`/students/${s.id}`} className="flex items-center gap-3">
                        <StudentAvatar name={s.full_name} photoUrl={s.photo_url} />
                        <div className="min-w-0">
                          <div className="truncate font-bold text-foreground group-hover:text-primary transition-colors">
                            {s.full_name}
                          </div>
                          <div className="truncate font-mono text-[11px] text-muted-foreground">
                            {s.roll_number}
                          </div>
                        </div>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-foreground">
                        {s.department_code ?? s.department_name ?? '—'}
                      </div>
                      {s.department_code && s.department_name && (
                        <div className="truncate text-[11px] text-muted-foreground">{s.department_name}</div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="font-semibold text-foreground">{yearLabel(s.study_year)} Year</div>
                      <div className="text-[11px] text-muted-foreground">
                        {s.section_name ? `Section ${s.section_name}` : 'No section'}
                        {s.semester_name ? ` • ${s.semester_name}` : ''}
                      </div>
                    </TableCell>
                    <TableCell>
                      <AttendanceCell value={s.attendance_percentage} />
                    </TableCell>
                    <TableCell>
                      <GpaCell value={s.cgpa} />
                    </TableCell>
                    <TableCell>
                      {s.active_backlogs > 0 ? (
                        <Badge variant="warning">{s.active_backlogs}</Badge>
                      ) : (
                        <span className="text-muted-foreground/60">None</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <RiskBadge level={s.risk_level} />
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          'font-medium',
                          s.last_session_date ? 'text-foreground' : 'text-amber-600 dark:text-amber-400'
                        )}
                      >
                        {formatSessionDate(s.last_session_date)}
                      </span>
                      {s.session_count > 0 && (
                        <div className="text-[11px] text-muted-foreground">{s.session_count} total</div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1.5">
                        {canCreateSession && (
                          <Button
                            size="sm"
                            variant="outline"
                            title="Record a counselling session"
                            onClick={() => navigate(`/counselling/new?studentId=${s.id}`)}
                          >
                            <MessageSquarePlus className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        {canReadParentComms && (
                          <Button
                            size="sm"
                            variant="outline"
                            title="Parent communication log"
                            onClick={() => navigate(`/students/${s.id}?tab=parents`)}
                          >
                            <PhoneCall className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          title="Counselling notes & history"
                          onClick={() => navigate(`/students/${s.id}?tab=counselling`)}
                        >
                          <NotebookPen className="h-3.5 w-3.5" />
                        </Button>
                        <Button size="sm" title="Open Student 360" onClick={() => navigate(`/students/${s.id}`)}>
                          <ExternalLink className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {pagination && pagination.total_pages > 1 && (
              <Pagination
                currentPage={pagination.page}
                totalPages={pagination.total_pages}
                totalCount={pagination.total}
                onPageChange={(p) => setParam('page', String(p))}
              />
            )}
          </>
        )}
      </div>
    </>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 w-full rounded-lg border border-input bg-background px-3 text-xs font-semibold focus:ring-2 focus:ring-ring"
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
