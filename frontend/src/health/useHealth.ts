import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    refetchInterval: 5000,
    retry: false,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/health');
      if (response.status === 200 && data) return data;
      if (response.status === 503 && error) return error;
      throw new Error(`Unexpected status ${response.status}`);
    },
  });
};
