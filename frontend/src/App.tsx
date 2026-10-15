import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { CallbackPage } from './pages/CallbackPage';
import { DashboardPage } from './pages/DashboardPage';
import { AnalysisListPage } from './pages/AnalysisListPage';
import { AnalysisDetailPage } from './pages/AnalysisDetailPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoadingScreen } from './components/LoadingScreen';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/callback" element={<CallbackPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/analyses" element={<AnalysisListPage />} />
                <Route path="/analyses/:id" element={<AnalysisDetailPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}