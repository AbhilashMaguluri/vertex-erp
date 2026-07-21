import { api } from '@/shared/lib/axios';

export interface SystemSetting {
  section: string;
  key: string;
  value: Record<string, any>;
  updated_at?: string;
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  user_id?: string;
  user_email?: string;
  user_role?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  changes_json?: Record<string, any>;
  ip_address?: string;
  request_id?: string;
}

export const settingsService = {
  getSettingsSection: async (section: string): Promise<SystemSetting[]> => {
    const res = await api.get<SystemSetting[]>(`/settings/${section}`);
    return res.data;
  },

  updateSetting: async (section: string, key: string, value: Record<string, any>): Promise<SystemSetting> => {
    const res = await api.put<SystemSetting>(`/settings/${section}/${key}`, { value });
    return res.data;
  },

  getAuditLogs: async (action?: string, entityType?: string): Promise<AuditLogItem[]> => {
    const res = await api.get<AuditLogItem[]>('/admin/audit-logs', {
      params: { action, entity_type: entityType },
    });
    return res.data;
  },
};
