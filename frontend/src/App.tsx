import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import ResearchWorkspace from './components/ResearchWorkspace';
import EvaluationDashboard from './components/EvaluationDashboard';
import DocumentIntelligence from './components/DocumentIntelligence';
import DocumentDetail from './components/DocumentDetail';
import DocumentSourceViewer from './components/DocumentSourceViewer';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import NotFound from './components/common/NotFound';
import { useAuth } from './hooks/useAuth';
import { ToastProvider } from './context/ToastContext';
import { Loader2, ShieldAlert } from 'lucide-react';

export function ProtectedRoute({ children, adminOnly = false }: { children: React.ReactNode; adminOnly?: boolean }) {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-[#080c14] flex flex-col items-center justify-center text-slate-400 gap-3 font-sans">
        <Loader2 className="animate-spin text-blue-500" size={32} />
        <span className="text-xs font-medium tracking-wide">Initializing secure legal workspace...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user?.role !== 'ADMIN') {
    return (
      <div className="h-screen w-screen bg-[#080c14] flex flex-col items-center justify-center text-slate-300 gap-4 font-sans p-6 text-center">
        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center shadow-lg">
          <ShieldAlert size={24} />
        </div>
        <h2 className="text-xl font-bold text-white">403 Forbidden: Administrator Role Required</h2>
        <p className="text-xs text-slate-400 max-w-md leading-relaxed">
          The requested administrative evaluation console and release gates are restricted strictly to verified institutional administrators.
        </p>
        <Link
          to="/"
          className="mt-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition-colors border border-slate-700"
        >
          Return to Research Workspace
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}

export function App() {
  return (
    <ToastProvider>
      <Router>
        <Routes>
          {/* Authentication Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Main Research Workspace Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <ResearchWorkspace />
              </ProtectedRoute>
            }
          />
          <Route
            path="/research"
            element={
              <ProtectedRoute>
                <ResearchWorkspace />
              </ProtectedRoute>
            }
          />

          {/* Evaluation and Gate Monitoring (Admin Only) */}
          <Route
            path="/evaluation"
            element={
              <ProtectedRoute adminOnly>
                <EvaluationDashboard />
              </ProtectedRoute>
            }
          />

          {/* Document Intelligence Suite */}
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <DocumentIntelligence />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents/:id"
            element={
              <ProtectedRoute>
                <DocumentDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents/:id/source"
            element={
              <ProtectedRoute>
                <DocumentSourceViewer />
              </ProtectedRoute>
            }
          />

          {/* 404 Catch-All Route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </ToastProvider>
  );
}

export default App;