import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ResearchWorkspace from './components/ResearchWorkspace';
import EvaluationDashboard from './components/EvaluationDashboard';
import DocumentIntelligence from './components/DocumentIntelligence';
import DocumentDetail from './components/DocumentDetail';
import DocumentSourceViewer from './components/DocumentSourceViewer';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import { AuthProvider, useAuth } from './context/AuthContext';
import { UserCircle, LogOut } from 'lucide-react';

function ProtectedRoute({ children, adminOnly = false }: { children: React.ReactNode, adminOnly?: boolean }) {
  const { isAuthenticated, user, logout } = useAuth();
  
  if (!isAuthenticated) return <Navigate to="/login" />;
  
  if (!user) {
    return <div className="h-screen w-screen bg-[#0b0f19] flex items-center justify-center text-slate-500">Loading workspace...</div>;
  }

  if (adminOnly && user.role !== 'ADMIN') {
    return <div className="h-screen w-screen bg-[#0b0f19] flex items-center justify-center text-red-500">403 Forbidden: Admin Access Required</div>;
  }

  return (
    <div className="relative">
      <div className="absolute top-4 right-4 z-50 flex items-center gap-4 bg-slate-900/80 px-4 py-2 rounded-full border border-slate-800 shadow-xl backdrop-blur-sm">
        <div className="flex items-center gap-2">
            <UserCircle className="text-blue-500" size={18} />
            <div className="flex flex-col">
                <span className="text-xs font-bold text-slate-200 leading-tight">{user.full_name || "User"}</span>
                <span className="text-[10px] text-slate-500 leading-tight">{user.role}</span>
            </div>
        </div>
        <div className="w-px h-6 bg-slate-700"></div>
        <button onClick={logout} className="text-slate-400 hover:text-white transition-colors" title="Logout">
            <LogOut size={16} />
        </button>
      </div>
      {children}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Main App Routes */}
          <Route path="/" element={<ProtectedRoute><ResearchWorkspace /></ProtectedRoute>} />
          <Route path="/research" element={<ProtectedRoute><ResearchWorkspace /></ProtectedRoute>} />
          <Route path="/evaluation" element={<ProtectedRoute adminOnly><EvaluationDashboard /></ProtectedRoute>} />
          
          {/* Document Intelligence Routes (Phase 10) */}
          <Route path="/documents" element={<ProtectedRoute><DocumentIntelligence /></ProtectedRoute>} />
          <Route path="/documents/:id" element={<ProtectedRoute><DocumentDetail /></ProtectedRoute>} />
          <Route path="/documents/:id/source" element={<ProtectedRoute><DocumentSourceViewer /></ProtectedRoute>} />
          
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;