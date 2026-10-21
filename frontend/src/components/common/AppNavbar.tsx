import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Scale, Search, FileText, Activity, LogOut, UserCircle, Menu, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface AppNavbarProps {
  onToggleSidebar?: () => void;
  showSidebarToggle?: boolean;
}

export const AppNavbar: React.FC<AppNavbarProps> = ({ onToggleSidebar, showSidebarToggle = false }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
      isActive
        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
    }`;

  return (
    <header className="h-14 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 flex items-center justify-between px-4 lg:px-6">
      {/* Brand & Workspace Name */}
      <div className="flex items-center gap-3">
        {showSidebarToggle && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800/80 transition-colors lg:hidden"
            title="Toggle Sessions Sidebar"
            aria-label="Toggle Sessions Sidebar"
          >
            <Menu size={18} />
          </button>
        )}

        <NavLink to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-md shadow-blue-500/10 group-hover:shadow-blue-500/20 transition-all">
            <Scale size={16} className="text-white" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-serif font-bold text-base tracking-widest text-white leading-none">
                LEXORA
              </span>
              <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono font-semibold">
                Pilot
              </span>
            </div>
            <span className="text-[10px] text-slate-500 tracking-wider">AI Legal Intelligence</span>
          </div>
        </NavLink>
      </div>

      {/* Center Nav Links (Desktop) */}
      <nav className="hidden md:flex items-center gap-1 bg-slate-900/60 p-1 rounded-lg border border-slate-800/60">
        <NavLink to="/research" className={navItemClass}>
          <Search size={14} />
          <span>Research Workspace</span>
        </NavLink>

        <NavLink to="/documents" className={navItemClass}>
          <FileText size={14} />
          <span>Document Intelligence</span>
        </NavLink>

        {user?.role === 'ADMIN' && (
          <NavLink to="/evaluation" className={navItemClass}>
            <Activity size={14} />
            <span>Evaluation & Gates</span>
          </NavLink>
        )}
      </nav>

      {/* Right Controls: User Profile & Logout */}
      <div className="flex items-center gap-3">
        {user ? (
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800">
              <UserCircle size={15} className="text-blue-400" />
              <div className="flex items-center gap-1.5 text-xs">
                <span className="font-medium text-slate-200">{user.full_name || user.email}</span>
                <span className="text-[9px] uppercase font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                  {user.role}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-md transition-colors"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <NavLink
              to="/login"
              className="px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
            >
              Sign In
            </NavLink>
            <NavLink
              to="/register"
              className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-md transition-colors"
            >
              Register
            </NavLink>
          </div>
        )}

        {/* Mobile menu button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 text-slate-400 hover:text-white rounded-md md:hidden hover:bg-slate-800"
          aria-label="Toggle Menu"
        >
          {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {/* Mobile navigation dropdown */}
      {mobileMenuOpen && (
        <div className="absolute top-14 left-0 w-full bg-slate-950 border-b border-slate-800 p-4 flex flex-col gap-2 md:hidden z-50 shadow-2xl">
          <NavLink
            to="/research"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:bg-slate-900 text-sm"
          >
            <Search size={16} className="text-blue-400" />
            <span>Research Workspace</span>
          </NavLink>
          <NavLink
            to="/documents"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:bg-slate-900 text-sm"
          >
            <FileText size={16} className="text-blue-400" />
            <span>Document Intelligence</span>
          </NavLink>
          {user?.role === 'ADMIN' && (
            <NavLink
              to="/evaluation"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-2 p-2 rounded-lg text-slate-300 hover:bg-slate-900 text-sm"
            >
              <Activity size={16} className="text-blue-400" />
              <span>Evaluation & Metrics</span>
            </NavLink>
          )}
          {user && (
            <div className="pt-2 mt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Signed in as {user.email}</span>
              <button
                type="button"
                onClick={handleLogout}
                className="text-rose-400 hover:underline flex items-center gap-1"
              >
                <LogOut size={14} /> Sign Out
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
};

export default AppNavbar;
