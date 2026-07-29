import { api } from '@/shared/lib/axios';

export interface SearchResultItem {
  type: 'student' | 'user';
  id: string;
  title: string;
  subtitle?: string;
  url: string;
}

export const searchService = {
  search: async (q: string): Promise<SearchResultItem[]> => {
    const res = await api.get<SearchResultItem[]>('/search', { params: { q } });
    return res.data;
  },
};
