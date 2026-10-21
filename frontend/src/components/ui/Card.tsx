import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'glass';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variants = {
    default: 'bg-slate-900/60 border border-slate-800 shadow-lg',
    elevated: 'bg-slate-900/90 border border-slate-700/80 shadow-xl',
    glass: 'bg-slate-950/70 border border-slate-800/80 backdrop-blur-md shadow-2xl',
  };

  return (
    <div className={`rounded-xl p-5 ${variants[variant]} ${className}`} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <div className={`flex items-center justify-between pb-3 mb-4 border-b border-slate-800/80 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <h3 className={`text-xs font-bold uppercase tracking-widest text-slate-300 flex items-center gap-2 ${className}`} {...props}>
    {children}
  </h3>
);

export default Card;
