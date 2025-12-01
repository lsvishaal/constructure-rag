'use client';

import { motion } from 'framer-motion';
import { useAuthStore } from '@/lib/hooks/useAuth';
import { useChatStore } from '@/lib/hooks/useChat';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Brain,
  User,
  LogOut,
  Trash2,
  Settings,
  MessageSquare,
  FileText,
} from 'lucide-react';
import Link from 'next/link';
import { ChatMode } from '@/types/chat';

interface HeaderProps {
  className?: string;
}

export function Header({ className }: HeaderProps) {
  const { user, logout, isAuthenticated } = useAuthStore();
  const { mode, setMode, clearMessages, messages } = useChatStore();

  const modes: { value: ChatMode; label: string; icon: React.ReactNode }[] = [
    { value: 'qa', label: 'Q&A', icon: <MessageSquare className="w-4 h-4" /> },
    { value: 'extraction', label: 'Extract', icon: <FileText className="w-4 h-4" /> },
    { value: 'sources_only', label: 'Sources', icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'sticky top-0 z-50 w-full',
        'border-b border-slate-200 dark:border-slate-800',
        'bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg',
        className
      )}
    >
      <div className="container flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <motion.div
            whileHover={{ rotate: 10 }}
            className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center"
          >
            <Brain className="w-5 h-5 text-white" />
          </motion.div>
          <span className="font-bold text-lg text-slate-900 dark:text-slate-100">
            Project Brain
          </span>
        </Link>

        {/* Center: Mode selector */}
        {isAuthenticated && (
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-800">
            {modes.map((m) => (
              <motion.button
                key={m.value}
                onClick={() => setMode(m.value)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  mode === m.value
                    ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                )}
              >
                {m.icon}
                <span className="hidden sm:inline">{m.label}</span>
              </motion.button>
            ))}
          </div>
        )}

        {/* Right: User menu */}
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              {/* Message count */}
              {messages.length > 0 && (
                <Badge variant="secondary" className="hidden sm:flex">
                  {messages.length} messages
                </Badge>
              )}

              {/* Clear chat */}
              {messages.length > 0 && (
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearMessages}
                    className="text-slate-500 hover:text-red-500"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </motion.div>
              )}

              {/* User dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="flex items-center gap-2 px-2"
                  >
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                      <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <span className="hidden sm:inline text-sm font-medium max-w-[150px] truncate">
                      {user?.email}
                    </span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuItem className="text-slate-500">
                    <User className="w-4 h-4 mr-2" />
                    {user?.email}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <Settings className="w-4 h-4 mr-2" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={logout}
                    className="text-red-600 dark:text-red-400"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <Link href="/login">
              <Button>Sign In</Button>
            </Link>
          )}
        </div>
      </div>
    </motion.header>
  );
}

export default Header;
