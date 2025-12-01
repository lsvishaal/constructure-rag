'use client';

import { motion } from 'framer-motion';
import { Source } from '@/types/chat';
import { cn } from '@/lib/utils';
import { FileText, Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface SourceCitationProps {
  source: Source;
  compact?: boolean;
}

export function SourceCitation({ source, compact = false }: SourceCitationProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(
      `${source.filename} - Page ${source.page}\n${source.content}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (compact) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
        <FileText className="w-3 h-3" />
        {source.filename} p.{source.page}
      </span>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        'group flex items-start gap-2 p-2 rounded-lg',
        'bg-slate-50 dark:bg-slate-800/50',
        'border border-slate-200 dark:border-slate-700',
        'hover:bg-slate-100 dark:hover:bg-slate-800',
        'transition-colors duration-150'
      )}
    >
      <div className="flex-shrink-0 mt-0.5">
        <FileText className="w-4 h-4 text-blue-500" />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-sm text-slate-900 dark:text-slate-100 truncate">
            {source.filename}
          </span>
          <span className="flex-shrink-0 px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">
            Page {source.page}
          </span>
          {source.score && (
            <span className="flex-shrink-0 text-xs text-slate-500">
              {(source.score * 100).toFixed(0)}% match
            </span>
          )}
        </div>
        
        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
          {source.content}
        </p>
      </div>
      
      <motion.button
        onClick={handleCopy}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className={cn(
          'flex-shrink-0 p-1.5 rounded',
          'opacity-0 group-hover:opacity-100',
          'hover:bg-slate-200 dark:hover:bg-slate-700',
          'transition-all duration-150'
        )}
        aria-label="Copy citation"
      >
        {copied ? (
          <Check className="w-3.5 h-3.5 text-green-500" />
        ) : (
          <Copy className="w-3.5 h-3.5 text-slate-500" />
        )}
      </motion.button>
    </motion.div>
  );
}

export default SourceCitation;
