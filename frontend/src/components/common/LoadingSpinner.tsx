import React from 'react';
import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className,
  text 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div className="flex flex-col items-center space-y-2">
        <div 
          className={clsx(
            'animate-spin rounded-full border-2 border-gray-300 border-t-medical-600',
            sizeClasses[size]
          )}
        />
        {text && (
          <p className="text-sm text-gray-600 animate-pulse">{text}</p>
        )}
      </div>
    </div>
  );
};

export const LoadingSkeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={clsx('animate-pulse bg-gray-200 rounded', className)} />
  );
};

export const LoadingCard: React.FC = () => {
  return (
    <div className="card animate-pulse">
      <div className="flex items-center space-x-4">
        <LoadingSkeleton className="w-12 h-12 rounded-lg" />
        <div className="flex-1">
          <LoadingSkeleton className="h-4 w-3/4 mb-2" />
          <LoadingSkeleton className="h-3 w-1/2" />
        </div>
      </div>
      <div className="mt-4 space-y-2">
        <LoadingSkeleton className="h-3 w-full" />
        <LoadingSkeleton className="h-3 w-2/3" />
      </div>
    </div>
  );
};
