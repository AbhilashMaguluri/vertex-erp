// ---------------------------------------------------------------------------
// Vertex — Type definitions
// ---------------------------------------------------------------------------

// Message primitives
export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageStatus = 'streaming' | 'complete' | 'error';

export interface VertexMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  status: MessageStatus;
  responseType?: ResponseType;
}

// Response types — drives the frontend renderer
export type ResponseType =
  | 'text'
  | 'markdown'
  | 'table'
  | 'card'
  | 'list'
  | 'error'
  | 'loading'
  | 'action';

// Rich context
export interface UserContext {
  id?: string;
  name?: string;
  role?: string;
  department?: string;
  permissions?: string[];
}

export interface PageContext {
  page: string;
  studentId?: string;
  params?: Record<string, string>;
}

export type VertexMode =
  | 'guest'
  | 'student'
  | 'counsellor'
  | 'faculty'
  | 'hod'
  | 'admin';

export interface VertexContext {
  user: UserContext;
  page: PageContext;
  mode: VertexMode;
  timestamp?: string;
}

// Suggested prompts
export interface SuggestedPrompt {
  icon: string;
  label: string;
  prompt: string;
  description?: string;
}

// API request format (mirrors backend VertexRequest)
export interface VertexRequest {
  messages: { role: MessageRole; content: string }[];
  context: VertexContext;
  metadata?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// UI Action types — commands Vertex sends to the frontend to execute
// ---------------------------------------------------------------------------

export type UIActionType =
  | 'navigate'
  | 'setTheme'
  | 'showToast'
  | 'logout'
  | 'openDialog'
  | 'closeDialog';

export interface UIAction {
  type: UIActionType;
  route?: string;
  mode?: string;
  message?: string;
  variant?: string;
  dialog?: string;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// SSE event types from the backend
// ---------------------------------------------------------------------------

export interface VertexSSEToken {
  type: 'token';
  content: string;
}

export interface VertexSSEDone {
  type: 'done';
}

export interface VertexSSEError {
  type: 'error';
  content: string;
}

export interface VertexSSEAction {
  type: 'action';
  action: UIAction;
}

export type VertexSSEvent =
  | VertexSSEToken
  | VertexSSEDone
  | VertexSSEError
  | VertexSSEAction;

// ---------------------------------------------------------------------------
// Dual Window Mode State persistence (Compact Floating vs Docked Right Sidebar Workspace)
// ---------------------------------------------------------------------------
export interface VertexWindowState {
  isOpen: boolean;
  isDocked: boolean; // right-docked AI sidebar workspace mode
  compactWidth: number;
  compactHeight: number;
  dockedWidth: number; // width when docked as sidebar (min 420px, max 700px)
}
