import * as React from 'react';
import { Department, Section, Subject } from '../services/admin.service';
import { STUDY_YEARS, STUDY_YEAR_LABELS } from '../schemas/academicConfig.schema';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { ChevronDown, Pencil, Plus, Trash2, Layers, BookOpen, Building2 } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

interface DepartmentHierarchyCardProps {
  department: Department;
  sections: Section[];
  subjects: Subject[];
  canManageDepartment: boolean;
  canManageSection: boolean;
  canManageSubject: boolean;
  defaultExpanded?: boolean;
  onEditDepartment: () => void;
  onAddSection: (year: number) => void;
  onEditSection: (section: Section) => void;
  onDeleteSection: (section: Section) => void;
  onAddSubject: () => void;
  onEditSubject: (subject: Subject) => void;
}

export function DepartmentHierarchyCard({
  department, sections, subjects,
  canManageDepartment, canManageSection, canManageSubject,
  defaultExpanded = true,
  onEditDepartment, onAddSection, onEditSection, onDeleteSection, onAddSubject, onEditSubject,
}: DepartmentHierarchyCardProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  const totalSections = sections.length;

  return (
    <Card className="overflow-hidden">
      {/* Department Header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between gap-3 p-4 text-left cursor-pointer hover:bg-accent/40 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Building2 className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="default" className="font-mono font-bold">{department.code}</Badge>
              <h3 className="text-sm font-bold text-foreground truncate">{department.name}</h3>
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {totalSections} section{totalSections === 1 ? '' : 's'} · {subjects.length} subject{subjects.length === 1 ? '' : 's'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {canManageDepartment && (
            <span
              role="button"
              tabIndex={0}
              onClick={(e) => {
                e.stopPropagation();
                onEditDepartment();
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.stopPropagation();
                  onEditDepartment();
                }
              }}
              aria-label={`Edit ${department.name}`}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <Pencil className="h-3.5 w-3.5" />
            </span>
          )}
          <ChevronDown className={cn('h-4 w-4 text-muted-foreground transition-transform', expanded && 'rotate-180')} />
        </div>
      </button>

      {expanded && (
        <CardContent className="pt-0 pb-5 space-y-5 border-t border-border/60">
          {/* Years -> Sections */}
          <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {STUDY_YEARS.map((year) => {
              const yearSections = sections.filter((s) => s.year === year);
              return (
                <div key={year} className="rounded-xl border border-border/70 bg-muted/20 p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-extrabold uppercase tracking-wide text-muted-foreground">
                      {STUDY_YEAR_LABELS[year]}
                    </span>
                    {canManageSection && (
                      <button
                        onClick={() => onAddSection(year)}
                        className="flex h-6 w-6 items-center justify-center rounded-md text-primary hover:bg-primary/10"
                        title={`Add section to ${STUDY_YEAR_LABELS[year]}`}
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>

                  {yearSections.length === 0 ? (
                    <p className="text-[11px] text-muted-foreground/70 italic">No sections configured yet.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {yearSections.map((s) => (
                        <div
                          key={s.id}
                          className="group inline-flex items-center gap-1 rounded-full border border-border bg-card px-2.5 py-1 text-[11px] font-semibold text-foreground shadow-xs"
                        >
                          <Layers className="h-3 w-3 text-muted-foreground" />
                          Section {s.name}
                          <span className="text-muted-foreground/70 font-mono">· {s.batch_year}</span>
                          {canManageSection && (
                            <span className="flex items-center gap-0.5 ml-1">
                              <button
                                onClick={() => onEditSection(s)}
                                className="text-muted-foreground hover:text-foreground"
                                aria-label={`Edit Section ${s.name}`}
                              >
                                <Pencil className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => onDeleteSection(s)}
                                className="text-muted-foreground hover:text-rose-600"
                                aria-label={`Delete Section ${s.name}`}
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Legacy sections created before study-year tracking existed — surfaced
              so they're editable instead of silently vanishing from the tree. */}
          {sections.some((s) => !s.year) && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3">
              <span className="text-[11px] font-extrabold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                Unassigned Study Year
              </span>
              <p className="text-[11px] text-muted-foreground/80 mt-0.5 mb-2">
                These sections predate study-year tracking — edit each to place it under a year above.
              </p>
              <div className="flex flex-wrap gap-1.5">
                {sections.filter((s) => !s.year).map((s) => (
                  <div
                    key={s.id}
                    className="group inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-card px-2.5 py-1 text-[11px] font-semibold text-foreground shadow-xs"
                  >
                    <Layers className="h-3 w-3 text-muted-foreground" />
                    Section {s.name}
                    <span className="text-muted-foreground/70 font-mono">· {s.batch_year}</span>
                    {canManageSection && (
                      <span className="flex items-center gap-0.5 ml-1">
                        <button onClick={() => onEditSection(s)} className="text-muted-foreground hover:text-foreground" aria-label={`Edit Section ${s.name}`}>
                          <Pencil className="h-3 w-3" />
                        </button>
                        <button onClick={() => onDeleteSection(s)} className="text-muted-foreground hover:text-rose-600" aria-label={`Delete Section ${s.name}`}>
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Subjects */}
          <div className="rounded-xl border border-border/70 bg-muted/20 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-wide text-muted-foreground">
                <BookOpen className="h-3.5 w-3.5" /> Subjects Catalog
              </span>
              {canManageSubject && (
                <Button variant="ghost" size="sm" onClick={onAddSubject} className="h-6 px-2 text-[11px] text-primary hover:bg-primary/10">
                  <Plus className="mr-1 h-3 w-3" /> Add Subject
                </Button>
              )}
            </div>

            {subjects.length === 0 ? (
              <p className="text-[11px] text-muted-foreground/70 italic">No subjects configured yet.</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {subjects.map((sub) => (
                  <div
                    key={sub.id}
                    className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-[11px] font-semibold text-foreground shadow-xs"
                  >
                    <span className="font-mono font-bold text-primary">{sub.code}</span>
                    <span className="text-muted-foreground">{sub.name}</span>
                    <span className="text-muted-foreground/70">· {sub.credits} cr</span>
                    {canManageSubject && (
                      <button onClick={() => onEditSubject(sub)} className="text-muted-foreground hover:text-foreground ml-1" aria-label={`Edit ${sub.name}`}>
                        <Pencil className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
