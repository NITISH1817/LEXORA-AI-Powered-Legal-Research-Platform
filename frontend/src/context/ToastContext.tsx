import React, { useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import { ToastContext, type ToastItem } from './toast-types';

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    ({ type, title, message, duration = 3500 }: Omit<ToastItem, 'id'>) => {
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const newToast: ToastItem = { id, type, title, message, duration };

      setToasts((prev) => [...prev.slice(-4), newToast]); // keep max 5 toasts

      if (duration > 0) {
        setTimeout(() => {
          dismiss(id);
        }, duration);
      }
    },
    [dismiss]
  );

  const success = useCallback(
    (message: string, title?: string) => toast({ type: 'success', title, message }),
    [toast]
  );
  const error = useCallback(
    (message: string, title?: string) => toast({ type: 'error', title, message, duration: 5000 }),
    [toast]
  );
  const info = useCallback(
    (message: string, title?: string) => toast({ type: 'info', title, message }),
    [toast]
  );
  const warning = useCallback(
    (message: string, title?: string) => toast({ type: 'warning', title, message, duration: 4500 }),
    [toast]
  );

  return (
    <ToastContext.Provider value={{ toast, success, error, info, warning, dismiss }}>
      {children}
      {/* Toast Notification Container */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      >
        <AnimatePresence>
          {toasts.map((t) => {
            const icons = {
              success: <CheckCircle2 size={16} className="text-emerald-400 shrink-0 mt-0.5" />,
              error: <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />,
              warning: <AlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />,
              info: <Info size={16} className="text-blue-400 shrink-0 mt-0.5" />,
            };

            const borderColors = {
              success: 'border-emerald-500/30 bg-slate-900/95 text-slate-100',
              error: 'border-rose-500/30 bg-slate-900/95 text-slate-100',
              warning: 'border-amber-500/30 bg-slate-900/95 text-slate-100',
              info: 'border-blue-500/30 bg-slate-900/95 text-slate-100',
            };

            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 15, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
                className={`pointer-events-auto p-3.5 rounded-xl border shadow-2xl backdrop-blur-md flex items-start gap-3 text-xs font-sans ${
                  borderColors[t.type]
                }`}
                role="status"
              >
                {icons[t.type]}
                <div className="flex-1 min-w-0">
                  {t.title && <div className="font-semibold text-white mb-0.5">{t.title}</div>}
                  <div className="text-slate-300 leading-relaxed font-sans">{t.message}</div>
                </div>
                <button
                  type="button"
                  onClick={() => dismiss(t.id)}
                  className="p-1 text-slate-400 hover:text-white rounded transition-colors"
                  aria-label="Dismiss notification"
                >
                  <X size={14} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export default ToastProvider;
