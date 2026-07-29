// ---------------------------------------------------------------------------
// SuggestedPrompts — Role-aware welcome screen with personalized greeting
// ---------------------------------------------------------------------------

import {
  Sparkles,
  LogIn,
  KeyRound,
  Info,
  Phone,
  MapPin,
  HelpCircle,
  CalendarDays,
  GraduationCap,
  BookOpen,
  ClipboardList,
  Users,
  BarChart3,
  FileText,
  Mail,
  AlertTriangle,
  Shield,
  Settings,
  Activity,
  Building2,
} from 'lucide-react';
import type { VertexMode, SuggestedPrompt } from '../types/vertex';

// ---------------------------------------------------------------------------
// Icons lookup (lucide components by string key)
// ---------------------------------------------------------------------------
const ICONS: Record<string, React.ElementType> = {
  LogIn, KeyRound, Info, Phone, MapPin, HelpCircle,
  CalendarDays, GraduationCap, BookOpen, ClipboardList,
  Users, BarChart3, FileText, Mail, AlertTriangle,
  Shield, Settings, Activity, Building2, Sparkles,
};

// ---------------------------------------------------------------------------
// Role-specific prompt card sets
// ---------------------------------------------------------------------------
const PROMPTS_BY_MODE: Record<VertexMode, SuggestedPrompt[]> = {
  guest: [
    { icon: 'LogIn', label: 'Login Help', prompt: 'How do I log in to VertexERP?' },
    { icon: 'KeyRound', label: 'Password Reset', prompt: 'How do I reset my password?' },
    { icon: 'Info', label: 'About VertexERP', prompt: 'What is VertexERP and what can it do?' },
    { icon: 'Phone', label: 'Contact Info', prompt: 'How can I contact the administration?' },
    { icon: 'MapPin', label: 'Campus Navigation', prompt: 'Help me navigate the campus facilities.' },
    { icon: 'HelpCircle', label: 'FAQs', prompt: 'What are the most frequently asked questions?' },
  ],
  student: [
    { icon: 'ClipboardList', label: 'My Attendance', prompt: 'Show me my attendance summary.' },
    { icon: 'CalendarDays', label: "Today's Timetable", prompt: "What's my timetable for today?" },
    { icon: 'GraduationCap', label: 'My Grades', prompt: 'How are my grades this semester?' },
    { icon: 'Users', label: 'Counselling Info', prompt: 'How can I book a counselling session?' },
    { icon: 'BookOpen', label: 'Exam Schedule', prompt: 'When are my upcoming exams?' },
    { icon: 'HelpCircle', label: 'Campus Help', prompt: 'Help me with campus-related information.' },
  ],
  counsellor: [
    { icon: 'Users', label: 'My Students', prompt: 'Give me an overview of my assigned students.' },
    { icon: 'CalendarDays', label: "Today's Sessions", prompt: 'What counselling sessions do I have today?' },
    { icon: 'FileText', label: 'Generate Report', prompt: 'Help me generate a student report.' },
    { icon: 'Mail', label: 'Parent Communication', prompt: 'Draft a parent communication email.' },
    { icon: 'AlertTriangle', label: 'At-Risk Students', prompt: 'Which students are at risk and need attention?' },
    { icon: 'BarChart3', label: 'Quick Analytics', prompt: 'Show me a quick analytics summary.' },
  ],
  faculty: [
    { icon: 'ClipboardList', label: 'Record Attendance', prompt: 'Help me record attendance for my class.' },
    { icon: 'GraduationCap', label: 'Enter Marks', prompt: 'Guide me through marks entry.' },
    { icon: 'CalendarDays', label: 'My Schedule', prompt: "What's my schedule for today?" },
    { icon: 'Users', label: 'Student Lookup', prompt: 'Help me look up a student.' },
    { icon: 'Building2', label: 'Department Info', prompt: 'Tell me about my department.' },
    { icon: 'HelpCircle', label: 'Help', prompt: 'What can Vertex help me with?' },
  ],
  hod: [
    { icon: 'BarChart3', label: 'Department Analytics', prompt: 'Show me department-wide analytics.' },
    { icon: 'Users', label: 'Counsellor Overview', prompt: 'Give me an overview of counsellors in my department.' },
    { icon: 'FileText', label: 'Generate Report', prompt: 'Help me generate a department report.' },
    { icon: 'ClipboardList', label: 'Attendance Summary', prompt: 'Show me the attendance summary for my department.' },
    { icon: 'GraduationCap', label: 'Student Stats', prompt: 'What are the student statistics for my department?' },
    { icon: 'Settings', label: 'Settings', prompt: 'Help me with department settings.' },
  ],
  admin: [
    { icon: 'Activity', label: 'System Analytics', prompt: 'Show me system-wide analytics.' },
    { icon: 'Shield', label: 'User Management', prompt: 'Help me manage users.' },
    { icon: 'Building2', label: 'Department Overview', prompt: 'Give me an overview of all departments.' },
    { icon: 'FileText', label: 'Generate Report', prompt: 'Help me generate a system report.' },
    { icon: 'BookOpen', label: 'Audit Logs', prompt: 'Show me recent audit logs.' },
    { icon: 'Activity', label: 'System Health', prompt: 'How is the system performing?' },
  ],
};

// ---------------------------------------------------------------------------
// Time-aware greeting
// ---------------------------------------------------------------------------
function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good Morning';
  if (hour < 17) return 'Good Afternoon';
  return 'Good Evening';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
interface SuggestedPromptsProps {
  mode: VertexMode;
  userName: string | null;
  onPromptClick: (prompt: string) => void;
}

export function SuggestedPrompts({ mode, userName, onPromptClick }: SuggestedPromptsProps) {
  const prompts = PROMPTS_BY_MODE[mode] || PROMPTS_BY_MODE.guest;
  const greeting = getGreeting();

  // Extract first name
  const firstName = userName ? userName.split(' ')[0] : null;

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-5 py-6">
      {/* Branding */}
      <div className="mb-1 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-md shadow-brand-600/20">
          <Sparkles className="h-4.5 w-4.5 text-white" />
        </div>
        <div>
          <h2 className="text-base font-bold text-foreground leading-tight">Vertex</h2>
          <p className="text-[10px] font-medium text-muted-foreground leading-tight">
            AI Agent &amp; Chatbot for VertexERP
          </p>
        </div>
      </div>

      {/* Divider */}
      <div className="my-4 h-px w-16 bg-border/60" />

      {/* Greeting */}
      <div className="mb-5 text-center">
        {firstName ? (
          <>
            <p className="text-lg font-semibold text-foreground">
              {greeting}, {firstName}.
            </p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              How can I assist you today?
            </p>
          </>
        ) : (
          <>
            <p className="text-lg font-semibold text-foreground">
              {greeting} 👋
            </p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              How can I help you today?
            </p>
          </>
        )}
      </div>

      {/* Prompt cards */}
      <div className="grid w-full max-w-sm grid-cols-2 gap-2">
        {prompts.map((p) => {
          const IconComponent = ICONS[p.icon] || HelpCircle;
          return (
            <button
              key={p.label}
              onClick={() => onPromptClick(p.prompt)}
              className="group flex items-center gap-2.5 rounded-xl border border-border/60 bg-card/80 px-3 py-2.5 text-left transition-all duration-150 hover:border-brand-300 hover:bg-brand-50/50 hover:shadow-sm active:scale-[0.98] dark:hover:bg-brand-950/20 dark:hover:border-brand-700/50 cursor-pointer"
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-muted/80 transition-colors group-hover:bg-brand-100 dark:group-hover:bg-brand-900/30">
                <IconComponent className="h-3.5 w-3.5 text-muted-foreground transition-colors group-hover:text-brand-600 dark:group-hover:text-brand-400" />
              </div>
              <span className="text-xs font-medium text-foreground/80 transition-colors group-hover:text-foreground">
                {p.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
