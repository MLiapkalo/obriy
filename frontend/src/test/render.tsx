import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';

export function renderWithQueryClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(ui, {
    wrapper: ({ children }) => {
      return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
    },
  });
}
