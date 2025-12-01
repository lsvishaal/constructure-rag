'use client';

import { motion } from 'framer-motion';
import { ChatMessage as ChatMessageType } from '@/types/chat';
import { SourceCitation } from './SourceCitation';
import { TypingIndicator } from './LoadingIndicator';
import { cn } from '@/lib/utils';
import { User, Bot, AlertCircle } from 'lucide-react';
import { EASING } from '@/lib/constants';

interface ChatMessageProps {
  message: ChatMessageType;
  index: number;
}

export function ChatMessage({ message, index }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;
  const hasError = !!message.error;

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: EASING.INTERACTIVE,
        delay: index * 0.05,
      },
    },
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className={cn(
        'flex gap-3 mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {/* Avatar for AI */}
      {!isUser && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20 }}
          className={cn(
            'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
            hasError
              ? 'bg-red-100 dark:bg-red-900/30'
              : 'bg-blue-100 dark:bg-blue-900/30'
          )}
        >
          {hasError ? (
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
          ) : (
            <Bot className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          )}
        </motion.div>
      )}

      {/* Message bubble */}
      <motion.div
        className={cn(
          'max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-xl px-4 py-3 rounded-2xl shadow-sm',
          isUser
            ? 'bg-blue-500 text-white rounded-br-sm'
            : hasError
              ? 'bg-red-50 dark:bg-red-900/20 text-red-900 dark:text-red-100 border border-red-200 dark:border-red-800 rounded-bl-sm'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-sm'
        )}
        whileHover={{
          scale: 1.01,
          transition: { duration: 0.15 },
        }}
      >
        {/* Message content */}
        {isStreaming && !message.content ? (
          <TypingIndicator />
        ) : (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        )}

        {/* Error message */}
        {hasError && (
          <p className="mt-2 text-xs text-red-600 dark:text-red-400">
            {message.error}
          </p>
        )}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ delay: 0.2, duration: 0.3 }}
            className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700 space-y-2"
          >
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
              📚 Sources:
            </p>
            {message.sources.map((source) => (
              <SourceCitation key={source.id} source={source} />
            ))}
          </motion.div>
        )}
      </motion.div>

      {/* Avatar for User */}
      {isUser && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20 }}
          className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center"
        >
          <User className="w-4 h-4 text-white" />
        </motion.div>
      )}
    </motion.div>
  );
}

export default ChatMessage;
