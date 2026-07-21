import * as React from 'react';
import { TimelineEventType } from '@scms/types';
import {
  UserPlus,
  RefreshCw,
  GraduationCap,
  Link,
  Calendar,
  AlertTriangle,
  AlertOctagon,
  FileSpreadsheet,
  BarChart2,
  XCircle,
  CheckCircle,
  MessageSquare,
  Check,
  ClipboardList,
  Clock,
  Phone,
  FileText,
  Flag,
  FileCheck,
} from 'lucide-react';
import { cn } from '@/shared/utils/cn';

export interface TimelineEventItem {
  id: string;
  event_type: TimelineEventType | string;
  title: string;
  description?: string;
  created_at: string;
  actor_name?: string;
  metadata?: Record<string, any>;
}

interface TimelineProps {
  events: TimelineEventItem[];
  onEventClick?: (event: TimelineEventItem) => void;
  className?: string;
}

const eventIcons: Record<string, React.ElementType> = {
  [TimelineEventType.STUDENT_REGISTERED]: UserPlus,
  [TimelineEventType.STUDENT_STATUS_CHANGED]: RefreshCw,
  [TimelineEventType.STUDENT_PROMOTED]: GraduationCap,
  [TimelineEventType.COUNSELLOR_ASSIGNED]: Link,
  [TimelineEventType.COUNSELLOR_REASSIGNED]: Link,
  [TimelineEventType.ATTENDANCE_UPDATED]: Calendar,
  [TimelineEventType.ATTENDANCE_BELOW_THRESHOLD]: AlertTriangle,
  [TimelineEventType.ATTENDANCE_CRITICAL]: AlertOctagon,
  [TimelineEventType.MARKS_UPDATED]: FileSpreadsheet,
  [TimelineEventType.SGPA_CALCULATED]: BarChart2,
  [TimelineEventType.BACKLOG_ADDED]: XCircle,
  [TimelineEventType.BACKLOG_CLEARED]: CheckCircle,
  [TimelineEventType.SESSION_CONDUCTED]: MessageSquare,
  [TimelineEventType.SESSION_ACKNOWLEDGED]: Check,
  [TimelineEventType.FOLLOW_UP_CREATED]: ClipboardList,
  [TimelineEventType.FOLLOW_UP_COMPLETED]: CheckCircle,
  [TimelineEventType.FOLLOW_UP_OVERDUE]: Clock,
  [TimelineEventType.PARENT_COMMUNICATION]: Phone,
  [TimelineEventType.DOCUMENT_UPLOADED]: FileText,
  [TimelineEventType.RISK_FLAG_CHANGED]: Flag,
  [TimelineEventType.REPORT_GENERATED]: FileCheck,
};

const eventColors: Record<string, string> = {
  [TimelineEventType.STUDENT_REGISTERED]: 'bg-blue-100 text-blue-700 border-blue-200',
  [TimelineEventType.ATTENDANCE_BELOW_THRESHOLD]: 'bg-amber-100 text-amber-700 border-amber-200',
  [TimelineEventType.ATTENDANCE_CRITICAL]: 'bg-red-100 text-red-700 border-red-200',
  [TimelineEventType.BACKLOG_ADDED]: 'bg-red-100 text-red-700 border-red-200',
  [TimelineEventType.BACKLOG_CLEARED]: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  [TimelineEventType.SESSION_CONDUCTED]: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  [TimelineEventType.PARENT_COMMUNICATION]: 'bg-teal-100 text-teal-700 border-teal-200',
  [TimelineEventType.RISK_FLAG_CHANGED]: 'bg-purple-100 text-purple-700 border-purple-200',
};

export function Timeline({ events, onEventClick, className }: TimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        No timeline events recorded yet.
      </div>
    );
  }

  return (
    <div className={cn('relative border-l border-muted ml-4 space-y-6 py-2', className)}>
      {events.map((event) => {
        const IconComponent = eventIcons[event.event_type] || Calendar;
        const colorClass = eventColors[event.event_type] || 'bg-muted text-muted-foreground border-border';
        const formattedDate = new Date(event.created_at).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });

        return (
          <div
            key={event.id}
            onClick={() => onEventClick && onEventClick(event)}
            className={cn(
              'relative pl-6 group transition-colors',
              onEventClick && 'cursor-pointer'
            )}
          >
            {/* Timeline icon node */}
            <span
              className={cn(
                'absolute -left-3 top-0.5 flex h-6 w-6 items-center justify-center rounded-full border text-xs shadow-xs',
                colorClass
              )}
            >
              <IconComponent className="h-3 w-3" />
            </span>

            {/* Event Content */}
            <div className="rounded-md border bg-card p-3 shadow-2xs group-hover:border-primary/50 transition-colors">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold">{event.title}</h4>
                <time className="text-xs text-muted-foreground">{formattedDate}</time>
              </div>
              {event.description && (
                <p className="mt-1 text-xs text-muted-foreground">{event.description}</p>
              )}
              {event.actor_name && (
                <p className="mt-2 text-[11px] text-muted-foreground font-medium">
                  By {event.actor_name}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
