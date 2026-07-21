import { api } from '@/shared/lib/axios';

export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  priority: string; // LOW, NORMAL, HIGH, URGENT
  title: string;
  message: string;
  action_url?: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export const notificationService = {
  getNotifications: async (unreadOnly = false): Promise<NotificationItem[]> => {
    const res = await api.get<NotificationItem[]>('/notifications', {
      params: { unread_only: unreadOnly },
    });
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
