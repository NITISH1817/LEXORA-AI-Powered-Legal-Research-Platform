import React, { forwardRef, useId } from 'react';
import { AlertCircle } from 'lucide-react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  shortcutHint?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, helperText, shortcutHint, className = '', id, ...props }, ref) => {
    const generatedId = useId();
    const textareaId = id || generatedId;
    const errorId = `${textareaId}-error`;
    const helperId = `${textareaId}-helper`;

    return (
      <div className="w-full">
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <label
              htmlFor={textareaId}
              className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
            >
              {label}
              {props.required && <span className="text-rose-400 ml-1">*</span>}
            </label>
          )}
          {shortcutHint && (
            <span className="text-[10px] text-slate-500 font-mono">{shortcutHint}</span>
          )}
        </div>

        <textarea
          ref={ref}
          id={textareaId}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : helperText ? helperId : undefined}
          className={`w-full bg-slate-950/80 border text-slate-100 placeholder-slate-500 text-xs sm:text-sm rounded-xl p-3 transition-all outline-none resize-y min-h-[80px] ${
            error
              ? 'border-rose-500/80 focus:border-rose-500 focus:ring-1 focus:ring-rose-500'
              : 'border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
          } ${className}`}
          {...props}
        />

        {error && (
          <p id={errorId} className="mt-1.5 text-xs text-rose-400 flex items-center gap-1 font-sans">
            <AlertCircle size={13} className="shrink-0" />
            <span>{error}</span>
          </p>
        )}

        {!error && helperText && (
          <p id={helperId} className="mt-1 text-[11px] text-slate-500 font-sans">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
export default Textarea;
