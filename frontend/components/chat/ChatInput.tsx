"use client";

import { motion } from "framer-motion";
import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Send, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

// Get initial value synchronously to avoid effect-based setState
function getInitialDraft(): string {
  if (typeof window === "undefined") return "";
  try {
    return localStorage.getItem("chat-draft") || "";
  } catch {
    return "";
  }
}

export function ChatInput({
  onSend,
  isLoading = false,
  placeholder = "Ask about construction documents... (Ctrl+Enter to send)",
  disabled = false,
}: ChatInputProps) {
  // Initialize with localStorage value directly (no useEffect needed)
  const [input, setInput] = useState(getInitialDraft);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        150
      )}px`;
    }
  }, [input]);

  // Save draft to localStorage (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      try {
        if (input) {
          localStorage.setItem("chat-draft", input);
        } else {
          localStorage.removeItem("chat-draft");
        }
      } catch {
        // Ignore localStorage errors
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [input]);

  const handleSend = useCallback(() => {
    if (input.trim() && !isLoading && !disabled) {
      onSend(input.trim());
      setInput("");
      localStorage.removeItem("chat-draft");
    }
  }, [input, isLoading, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const canSend = input.trim() && !isLoading && !disabled;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.3 }}
      className="sticky bottom-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 p-4"
    >
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              className={cn(
                "w-full px-4 py-3 rounded-2xl border resize-none",
                "bg-slate-50 dark:bg-slate-800",
                "border-slate-200 dark:border-slate-700",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder:text-slate-400 dark:placeholder:text-slate-500",
                "text-sm text-slate-900 dark:text-slate-100",
                "transition-shadow duration-200",
                disabled && "opacity-50 cursor-not-allowed"
              )}
              rows={1}
            />

            {/* Character count */}
            {input.length > 200 && (
              <span className="absolute bottom-2 right-14 text-xs text-slate-400">
                {input.length}/1000
              </span>
            )}
          </div>

          <motion.div
            whileHover={canSend ? { scale: 1.05 } : {}}
            whileTap={canSend ? { scale: 0.95 } : {}}
          >
            <Button
              onClick={handleSend}
              disabled={!canSend}
              size="lg"
              className={cn(
                "px-4 h-12 rounded-2xl transition-all duration-200",
                canSend
                  ? "bg-blue-500 hover:bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                  : "bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed"
              )}
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </motion.div>
        </div>

        {/* Helper text */}
        <p className="mt-2 text-xs text-slate-400 dark:text-slate-500 text-center">
          Press{" "}
          <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs">
            Ctrl
          </kbd>
          +
          <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs">
            Enter
          </kbd>{" "}
          to send
        </p>
      </div>
    </motion.div>
  );
}

export default ChatInput;
