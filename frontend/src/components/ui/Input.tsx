import React, { forwardRef, useId } from 'react';
import { AlertCircle } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
  rightElement?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, icon, rightElement, className = '', id, ...props }, ref) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5"
          >
            {label}
            {props.required && <span className="text-rose-400 ml-1">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          {icon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              {icon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            className={`w-full bg-slate-950/80 border text-slate-100 placeholder-slate-500 text-xs sm:text-sm rounded-lg py-2.5 transition-all outline-none ${
              icon ? 'pl-9' : 'pl-3'
            } ${rightElement ? 'pr-10' : 'pr-3'} ${
              error
                ? 'border-rose-500/80 focus:border-rose-500 focus:ring-1 focus:ring-rose-500'
                : 'border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
            } ${className}`}
            {...props}
          />

          {rightElement && (
            <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center">
              {rightElement}
            </div>
          )}
        </div>

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

Input.displayName = 'Input';
export default Input;
