import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Shell from '@/components/layout/Shell';
import ProtectedRoute from '@/components/common/ProtectedRoute';
import ToastContainer from '@/components/common/ToastContainer';
import NotFound from '@/components/common/NotFound';
import ErrorBoundary from '@/components/common/ErrorBoundary';

// Lazy-loaded route components for optimized chunk size and code-splitting
const AuthPage = lazy(() => import('@/features/auth/AuthPage'));
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage'));
const DSATrackerPage = lazy(() => import('@/features/dsa/DSATrackerPage'));
const ResumeATSPage = lazy(() => import('@/features/resume/ResumeATSPage'));
const MockInterviewPage = lazy(() => import('@/features/interview/MockInterviewPage'));
const ProfilePage = lazy(() => import('@/features/profile/ProfilePage'));

const PageLoader = () => (
  <div className="min-h-[400px] flex flex-col items-center justify-center gap-3">
    <div className="w-8 h-8 border-2 border-[#4be277] border-t-transparent rounded-full animate-spin" />
    <div className="label-mono text-xs text-[#869585]">LOADING VIEW...</div>
  </div>
);

/**
 * Wraps route element with per-route ErrorBoundary and Suspense fallback.
 * @param {Object} props
 * @param {React.ComponentType} props.element
 */
const RouteBoundary = ({ element }) => (
  <ErrorBoundary>
    <Suspense fallback={<PageLoader />}>
      {React.createElement(element)}
    </Suspense>
  </ErrorBoundary>
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App = () => {
  return (
    <ErrorBoundary level="root" title="Placement Copilot Encountered an Error">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication */}
            <Route path="/login" element={<RouteBoundary element={AuthPage} />} />
            <Route path="/signup" element={<RouteBoundary element={AuthPage} />} />

            {/* Protected Application Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<Shell />}>
                <Route path="/" element={<RouteBoundary element={DashboardPage} />} />
                <Route path="/dsa" element={<RouteBoundary element={DSATrackerPage} />} />
                <Route path="/resume" element={<RouteBoundary element={ResumeATSPage} />} />
                <Route path="/interview" element={<RouteBoundary element={MockInterviewPage} />} />
                <Route path="/interview/:id" element={<RouteBoundary element={MockInterviewPage} />} />
                <Route path="/profile" element={<RouteBoundary element={ProfilePage} />} />
              </Route>
            </Route>

            {/* 404 & Redirects */}
            <Route path="/404" element={<NotFound />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
