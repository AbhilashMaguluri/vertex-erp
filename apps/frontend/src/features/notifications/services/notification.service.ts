import { api } from '@/shared/lib/axios';

export const NOTIFICATION_CATEGORIES = [
  'ACADEMIC',
  'COUNSELLING',
  'ATTENDANCE',
  'PARENT_COMMUNICATION',
  'PLACEMENT',
  'SYSTEM',
] as const;

export type NotificationCategory = (typeof NOTIFICATION_CATEGORIES)[number];

export const CATEGORY_LABELS: Record<string, string> = {
  ACADEMIC: 'Academic',
  COUNSELLING: 'Counselling',
  ATTENDANCE: 'Attendance',
  PARENT_COMMUNICATION: 'Parent',
  PLACEMENT: 'Placement',
  SYSTEM: 'System',
};

export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  category: string;
  priority: string; // LOW, NORMAL, HIGH, URGENT
  title: string;
  message: string;
  action_url?: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface CategoryCount {
  category: string;
  total: number;
  unread: number;
}

export interface NotificationSummary {
  unread_count: number;
  total_count: number;
  categories: CategoryCount[];
}

export const notificationService = {
  getNotifications: async (unreadOnly = false, category?: string): Promise<NotificationItem[]> => {
    const res = await api.get<NotificationItem[]>('/notifications', {
      params: { unread_only: unreadOnly, category },
    });
    return res.data;
  },

  getSummary: async (): Promise<NotificationSummary> => {
    const res = await api.get<NotificationSummary>('/notifications/summary');
    return res.data;
  },

  getUnreadCount: async (): Promise<number> => {
    const res = await api.get<{ unread_count: number }>('/notifications/unread-count');
    return res.data.unread_count;
  },

  markAsRead: async (notificationId: string): Promise<NotificationItem> => {
    const res = await api.patch<NotificationItem>(`/notifications/${notificationId}/read`);
    return res.data;
  },

  markAllAsRead: async (): Promise<void> => {
    await api.patch('/notifications/read-all');
  },
};
