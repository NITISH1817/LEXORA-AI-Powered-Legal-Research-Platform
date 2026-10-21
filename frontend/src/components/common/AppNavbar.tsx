import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Scale, Search, FileText, Activity, LogOut,
  UserCircle, Menu, X, ShieldAlert, ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../hooks/useAuth';
import Badge from '../ui/Badge';

interface AppNavbarProps {
  onToggleSidebar?: () => void;
  showSidebarToggle?: boolean;
  isSidebarOpen?: boolean;
}

export const AppNavbar: React.FC<AppNavbarProps> = ({
  onToggleSidebar,
  showSidebarToggle = false,
  isSidebarOpen = false,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [prevPath, setPrevPath] = useState(location.pathname);
  if (prevPath !== location.pathname) {
    setPrevPath(location.pathname);
    setMobileMenuOpen(false);
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all select-none ${
      isActive
        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
    }`;

  const mobileNavItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
        : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
    }`;

  return (
    <>
      <header className="h-14 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-md sticky top-0 z-40 flex items-center justify-between px-4 lg:px-6">
        {/* Left: Brand & Mobile Sidebar Toggle */}
        <div className="flex items-center gap-3">
          {showSidebarToggle && (
            <button
              type="button"
              onClick={onToggleSidebar}
              className={`p-1.5 rounded-lg transition-colors border ${
                isSidebarOpen
                  ? 'bg-blue-600/20 text-blue-400 border-blue-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-850 border-slate-800'
              }`}
              title={isSidebarOpen ? 'Collapse Sessions Sidebar' : 'Expand Sessions Sidebar'}
              aria-label="Toggle Sessions Sidebar"
            >
              <Menu size={17} />
            </button>
          )}

          <NavLink to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-md shadow-blue-500/10 group-hover:shadow-blue-500/20 transition-all shrink-0">
              <Scale size={16} className="text-white" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="font-serif font-bold text-base tracking-widest text-white leading-none">
                  LEXORA
                </span>
                <Badge variant="pilot" size="sm">
                  Pilot
                </Badge>
              </div>
              <span className="text-[10px] text-slate-500 tracking-wider">AI Legal Intelligence</span>
            </div>
          </NavLink>
        </div>

        {/* Center: Desktop Navigation Links */}
        <nav
          aria-label="Primary Navigation"
          className="hidden md:flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800/80 shadow-inner"
        >
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

        {/* Right: User Menu & Mobile Drawer Toggle */}
        <div className="flex items-center gap-2.5">
          {user ? (
            <div className="flex items-center gap-2">
              {/* User badge */}
              <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs">
                <UserCircle size={15} className="text-blue-400 shrink-0" />
                <span className="font-medium text-slate-200 truncate max-w-[140px]">
                  {user.full_name || user.email}
                </span>
                <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">
                  {user.role}
                </span>
              </div>

              {/* Logout button */}
              <button
                type="button"
                onClick={handleLogout}
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 rounded-lg transition-colors border border-transparent hover:border-slate-800"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="text-xs px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
            >
              Sign In
            </NavLink>
          )}

          {/* Mobile hamburger menu toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-850 md:hidden border border-slate-800"
            aria-label="Open Navigation Menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer Navigation */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 md:hidden flex">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm"
              aria-hidden="true"
            />

            {/* Slide-out Drawer */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="relative ml-auto w-72 max-w-[85vw] h-full bg-slate-950 border-l border-slate-800 p-5 flex flex-col shadow-2xl z-10"
            >
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
                    <Scale size={14} className="text-white" />
                  </div>
                  <span className="font-serif font-bold text-white tracking-widest text-sm">
                    LEXORA
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-850"
                  aria-label="Close Navigation Menu"
                >
                  <X size={18} />
                </button>
              </div>

              {/* User profile card in drawer */}
              {user && (
                <div className="my-4 p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <UserCircle size={20} className="text-blue-400 shrink-0" />
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-white truncate">
                        {user.full_name || user.email}
                      </div>
                      <div className="text-[10px] text-slate-400 truncate">{user.email}</div>
                    </div>
                  </div>
                  <div className="mt-2.5 flex items-center justify-between text-[10px] pt-2 border-t border-slate-800/80">
                    <span className="text-slate-500 uppercase font-mono">Assigned Role:</span>
                    <Badge variant="info" size="sm">
                      {user.role}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Navigation links */}
              <nav className="flex-1 space-y-1.5 overflow-y-auto py-2">
                <NavLink to="/research" className={mobileNavItemClass}>
                  <div className="flex items-center gap-2.5">
                    <Search size={16} />
                    <span>Research Workspace</span>
                  </div>
                  <ChevronRight size={14} className="text-slate-600" />
                </NavLink>

                <NavLink to="/documents" className={mobileNavItemClass}>
                  <div className="flex items-center gap-2.5">
                    <FileText size={16} />
                    <span>Document Intelligence</span>
                  </div>
                  <ChevronRight size={14} className="text-slate-600" />
                </NavLink>

                {user?.role === 'ADMIN' && (
                  <NavLink to="/evaluation" className={mobileNavItemClass}>
                    <div className="flex items-center gap-2.5">
                      <Activity size={16} />
                      <span>Evaluation & Gates</span>
                    </div>
                    <ChevronRight size={14} className="text-slate-600" />
                  </NavLink>
                )}
              </nav>

              {/* Controlled pilot advisory in drawer */}
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] mb-4">
                <div className="flex items-center gap-1.5 font-semibold text-amber-200 mb-1">
                  <ShieldAlert size={13} />
                  <span>Supervised Pilot</span>
                </div>
                <p className="text-[10px] text-amber-200/80 leading-relaxed font-sans">
                  Outputs require independent verification by qualified counsel.
                </p>
              </div>

              {/* Sign out button */}
              {user && (
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full py-2.5 px-4 bg-slate-900 hover:bg-rose-500/10 hover:text-rose-400 border border-slate-800 hover:border-rose-500/20 rounded-xl text-xs font-semibold text-slate-300 transition-colors flex items-center justify-center gap-2"
                >
                  <LogOut size={14} />
                  <span>Sign Out</span>
                </button>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};

export default AppNavbar;
