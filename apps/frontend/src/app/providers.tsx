import * as React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/shared/lib/queryClient';
import { AuthProvider } from '@/features/auth/context/AuthContext';
import { ThemeProvider } from '@/shared/theme/ThemeContext';

interface AppProvidersProps {
  children: React.ReactNode;
}

// AppRouter (child) uses createBrowserRouter/RouterProvider, which manages
// its own history — do not also wrap this in <BrowserRouter>. AuthProvider
// sits above the router so every route element can call useAuth().
export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
