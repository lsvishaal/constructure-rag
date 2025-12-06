'use client';

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '@/lib/hooks/useChat';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { MessageSquare } from 'lucide-react';

interface ChatContainerProps {
  className?: string;
}

export function ChatContainer({ className }: ChatContainerProps) {
  const { messages, isLoading, sendMessage } = useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Messages area */}
      <ScrollArea className="flex-1 px-4" ref={scrollRef}>
        <div className="max-w-4xl mx-auto py-6">
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            <AnimatePresence mode="popLayout">
              {messages.map((message, index) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  index={index}
                />
              ))}
            </AnimatePresence>
          )}
        </div>
      </ScrollArea>

      {/* Input area */}
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}

function EmptyState() {
  const suggestions = [
    'What is the wage rate for an Electrician?',
    'What is the General Decision Number?',
    'What state does this cover?',
    'What is the Executive Order 14026 minimum wage?',
  ];

  const { sendMessage } = useChatStore();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 px-4"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="w-16 h-16 rounded-2xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-6"
      >
        <MessageSquare className="w-8 h-8 text-blue-600 dark:text-blue-400" />
      </motion.div>

      <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
        Project Brain
      </h2>
      <p className="text-slate-500 dark:text-slate-400 text-center mb-8 max-w-md">
        Ask questions about your construction documents. I can help with wage
        determinations, door schedules, and more.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {suggestions.map((suggestion, idx) => (
          <motion.button
            key={suggestion}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + idx * 0.05 }}
            onClick={() => sendMessage(suggestion)}
            className={cn(
              'p-3 rounded-xl text-left text-sm',
              'bg-slate-100 dark:bg-slate-800',
              'hover:bg-slate-200 dark:hover:bg-slate-700',
              'text-slate-700 dark:text-slate-300',
              'border border-slate-200 dark:border-slate-700',
              'transition-colors duration-150'
            )}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {suggestion}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

export default ChatContainer;
