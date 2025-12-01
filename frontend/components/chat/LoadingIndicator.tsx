'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface LoadingIndicatorProps {
  className?: string;
  text?: string;
}

export function LoadingIndicator({ 
  className,
  text = 'Thinking...'
}: LoadingIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 bg-blue-500 rounded-full"
            animate={{
              y: [0, -8, 0],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.15,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>
      <span className="text-sm text-slate-500 dark:text-slate-400">
        {text}
      </span>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-2">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-1.5 h-1.5 bg-slate-400 dark:bg-slate-500 rounded-full"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.4, 1, 0.4],
          }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.2,
          }}
        />
      ))}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <motion.div
      className={cn(
        'w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full',
        className
      )}
      animate={{ rotate: 360 }}
      transition={{
        duration: 1,
        repeat: Infinity,
        ease: 'linear',
      }}
    />
  );
}

export default LoadingIndicator;
