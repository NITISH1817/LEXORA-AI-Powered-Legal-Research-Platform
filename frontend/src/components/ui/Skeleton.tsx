import React from 'react';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'rectangular' | 'circular';
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width,
  height,
  className = '',
  style,
  ...props
}) => {
  const variants = {
    text: 'h-4 rounded',
    rectangular: 'rounded-xl',
    circular: 'rounded-full',
  };

  return (
    <div
      className={`animate-pulse bg-slate-800/60 ${variants[variant]} ${className}`}
      style={{
        width: width !== undefined ? width : undefined,
        height: height !== undefined ? height : undefined,
        ...style,
      }}
      aria-hidden="true"
      {...props}
    />
  );
};

export const CardSkeleton: React.FC<{ rows?: number }> = ({ rows = 3 }) => (
  <div className="p-5 bg-slate-900/40 rounded-xl border border-slate-800 space-y-3">
    <Skeleton variant="text" className="w-1/3 h-5 mb-4" />
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} variant="text" className={`h-3 ${i === rows - 1 ? 'w-2/3' : 'w-full'}`} />
    ))}
  </div>
);

export default Skeleton;
