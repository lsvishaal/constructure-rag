"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  User,
  LogOut,
  Moon,
  Sun,
  FileText,
  Copy,
  Check,
  Loader2,
  Menu,
  X,
  Plus,
  Upload,
  File,
  Sparkles,
  Zap,
  ChevronDown,
  Trash2,
  XCircle,
  Table,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/lib/hooks/useChat";
import { useAuthStore, useHasHydrated } from "@/lib/hooks/useAuth";
import { useThemeStore } from "@/lib/hooks/useTheme";
import { useStreamingUpload } from "@/lib/hooks/useStreamingUpload";
import { UploadProgress } from "@/components/upload";
import { WageTable } from "@/components/extraction";
import { apiClient } from "@/lib/api-client";
import { API_ENDPOINTS } from "@/lib/constants";
import { toast } from "sonner";
import {
  SPRING,
  TIMING,
  EASING,
  sidebarVariants,
  overlayVariants,
  expandVariants,
} from "@/lib/animations";
import type { ChatMessage as ChatMessageType, Source, WageEntry } from "@/types/chat";

// Source citation with premium styling
function SourceCitation({ source, index }: { source: Source; index: number }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(source.content);
    setCopied(true);
    toast.success("Copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        delay: index * 0.08,
        duration: TIMING.medium,
        ease: EASING.entrance,
      }}
      className="group relative flex items-start gap-3 p-3 rounded-xl bg-gradient-to-r from-muted/80 to-muted/40 hover:from-muted hover:to-muted/60 border border-border/50 transition-all duration-200"
    >
      {/* Glow effect on hover */}
      <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r from-primary/5 to-accent/5 pointer-events-none" />

      <motion.span
        whileHover={{ scale: 1.1 }}
        className="relative flex items-center justify-center w-6 h-6 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 text-primary text-xs font-bold shrink-0 border border-primary/20"
      >
        {index + 1}
      </motion.span>
      <div className="flex-1 min-w-0 relative">
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1.5">
          <FileText className="w-3 h-3" />
          <span className="font-semibold truncate text-foreground/70">
            {source.filename}
          </span>
          <span className="text-muted-foreground/50">•</span>
          <span className="font-mono">p.{source.page}</span>
          {source.score && (
            <>
              <span className="text-muted-foreground/50">•</span>
              <span className="px-1.5 py-0.5 rounded-full bg-primary/10 text-primary font-semibold">
                {(source.score * 100).toFixed(0)}%
              </span>
            </>
          )}
        </div>
        <p className="text-sm text-foreground/80 line-clamp-2 leading-relaxed">
          {source.content}
        </p>
      </div>
      <motion.button
        onClick={handleCopy}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="relative p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-background/80 transition-all duration-200"
      >
        {copied ? (
          <Check className="w-4 h-4 text-emerald-500" />
        ) : (
          <Copy className="w-4 h-4 text-muted-foreground" />
        )}
      </motion.button>
    </motion.div>
  );
}

// Premium chat message with animations
function ChatMessage({
  message,
  index,
}: {
  message: ChatMessageType;
  index: number;
}) {
  const isUser = message.role === "user";
  const [showSources, setShowSources] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: TIMING.medium,
        ease: EASING.interactive,
        delay: index * 0.03,
      }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Avatar with glow */}
      <motion.div
        whileHover={{ scale: 1.1 }}
        transition={SPRING.snappy}
        className={`relative w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${
          isUser
            ? "bg-gradient-to-br from-primary to-primary/80 text-primary-foreground"
            : "bg-gradient-to-br from-muted to-muted/80 border border-border/50"
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Sparkles className="w-4 h-4 text-primary" />
        )}
        {/* Subtle glow */}
        {!isUser && (
          <div className="absolute inset-0 rounded-xl bg-primary/20 blur-md -z-10" />
        )}
      </motion.div>

      <div className={`flex-1 max-w-[85%] ${isUser ? "text-right" : ""}`}>
        <motion.div
          whileHover={{ scale: 1.01 }}
          transition={{ duration: 0.2 }}
          className={`relative inline-block rounded-2xl px-4 py-3 shadow-sm ${
            isUser
              ? "bg-gradient-to-br from-primary to-primary/90 text-primary-foreground rounded-tr-md"
              : "glass rounded-tl-md border border-border/50"
          }`}
        >
          {/* Shimmer overlay for AI messages */}
          {!isUser && (
            <div className="absolute inset-0 rounded-2xl rounded-tl-md overflow-hidden pointer-events-none">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/5 to-transparent -translate-x-full animate-[shimmer_3s_infinite]" />
            </div>
          )}
          <p className="relative text-[15px] leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        </motion.div>

        {/* Sources section */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mt-3"
          >
            <motion.button
              onClick={() => setShowSources(!showSources)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium text-muted-foreground hover:text-foreground bg-muted/50 hover:bg-muted border border-border/50 transition-all duration-200"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>
                {message.sources.length} source
                {message.sources.length > 1 ? "s" : ""}
              </span>
              <motion.div
                animate={{ rotate: showSources ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-3.5 h-3.5" />
              </motion.div>
            </motion.button>

            <AnimatePresence>
              {showSources && (
                <motion.div
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                  variants={expandVariants}
                  className="mt-3 space-y-2 overflow-hidden"
                >
                  {message.sources.map((source, idx) => (
                    <SourceCitation key={idx} source={source} index={idx} />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Structured Data Table (for extraction mode) */}
        {!isUser && message.structuredData && message.structuredData.entries.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-4"
          >
            {message.structuredData.extraction_type === 'wage_table' && (
              <WageTable entries={message.structuredData.entries as WageEntry[]} />
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

// Premium typing indicator
function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: TIMING.fast }}
      className="flex gap-3"
    >
      <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-muted to-muted/80 border border-border/50 flex items-center justify-center shadow-lg">
        <Sparkles className="w-4 h-4 text-primary" />
        <div className="absolute inset-0 rounded-xl bg-primary/20 blur-md -z-10 animate-pulse" />
      </div>
      <div className="glass rounded-2xl rounded-tl-md px-5 py-3.5 border border-border/50 shadow-sm">
        <div className="flex gap-1.5 items-center">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-gradient-to-br from-primary to-accent"
              animate={{
                y: [0, -8, 0],
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: i * 0.15,
                ease: "easeInOut",
              }}
            />
          ))}
          <span className="ml-2 text-xs text-muted-foreground">
            Thinking...
          </span>
        </div>
      </div>
    </motion.div>
  );
}

export default function ChatPage() {
  const router = useRouter();
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { messages, isLoading, sendMessage, clearMessages, setMode, mode } =
    useChatStore();
  const { user, isAuthenticated, logout, checkAuth, isCheckingAuth } =
    useAuthStore();
  const hasHydrated = useHasHydrated();
  const { darkMode, toggleDarkMode } = useThemeStore();
  
  // Streaming upload with real-time progress
  const { 
    uploadWithStreaming, 
    isUploading: uploading, 
    progress: uploadProgress,
    reset: resetUpload,
    cancel: cancelUpload,
  } = useStreamingUpload({
    onComplete: (data) => {
      toast.success(
        `Indexed ${data.chunks} chunks from ${data.pages} pages in ${data.time_seconds?.toFixed(1)}s`
      );
      fetchDocs();
      // Auto-hide progress after 3 seconds
      setTimeout(() => resetUpload(), 3000);
    },
    onError: (error) => {
      toast.error(error || "Failed to upload file");
    },
  });

  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [documents, setDocuments] = useState<{ total_chunks: number }>({
    total_chunks: 0,
  });

  // Apply theme after hydration
  useEffect(() => {
    if (hasHydrated) {
      document.documentElement.classList.toggle("dark", darkMode);
    }
  }, [darkMode, hasHydrated]);

  // Check auth only once after hydration
  useEffect(() => {
    if (hasHydrated) {
      checkAuth();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasHydrated]);

  // Redirect if not authenticated (only after hydration and auth check complete)
  useEffect(() => {
    if (hasHydrated && !isCheckingAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isCheckingAuth, router, hasHydrated]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Fetch document stats - only when authenticated and hydrated
  const fetchDocs = useCallback(async () => {
    try {
      const res = await apiClient.get(API_ENDPOINTS.DOCUMENTS);
      setDocuments(res.data);
    } catch (e) {
      console.error("Failed to fetch docs:", e);
    }
  }, []);

  useEffect(() => {
    if (hasHydrated && isAuthenticated) {
      fetchDocs();
    }
  }, [hasHydrated, isAuthenticated, fetchDocs]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Only PDF files are supported");
      return;
    }

    // Use streaming upload for real-time progress
    await uploadWithStreaming(file);
    
    // Clear the input
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const [clearing, setClearing] = useState(false);

  const handleClearDocuments = async () => {
    if (!confirm("Are you sure you want to delete all documents? This cannot be undone.")) {
      return;
    }
    
    setClearing(true);
    try {
      await apiClient.delete(API_ENDPOINTS.CLEAR_DOCUMENTS);
      toast.success("All documents cleared");
      setDocuments({ total_chunks: 0 });
      clearMessages(); // Also clear chat since context is gone
    } catch (err) {
      console.error("Clear error:", err);
      toast.error("Failed to clear documents");
    } finally {
      setClearing(false);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    if (documents.total_chunks === 0) {
      toast.error("Please upload a document first");
      return;
    }

    const query = input.trim();
    setInput("");
    await sendMessage(query);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const modeOptions = [
    {
      value: "qa",
      label: "Q&A",
      icon: Sparkles,
      description: "Get answers with citations",
    },
    {
      value: "extraction",
      label: "Extract",
      icon: Zap,
      description: "Pull structured data",
    },
    {
      value: "sources_only",
      label: "Sources",
      icon: FileText,
      description: "Find relevant passages",
    },
  ] as const;

  return (
    <div className="h-screen flex bg-mesh overflow-hidden">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            {/* Overlay */}
            <motion.div
              initial="hidden"
              animate="visible"
              exit="hidden"
              variants={overlayVariants}
              onClick={() => setSidebarOpen(false)}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
            />

            {/* Sidebar panel */}
            <motion.aside
              initial="hidden"
              animate="visible"
              exit="exit"
              variants={sidebarVariants}
              className="fixed lg:relative z-50 h-full w-80 glass border-r border-border/50 flex flex-col shadow-2xl"
            >
              {/* Header */}
              <div className="p-5 border-b border-border/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h1 className="font-bold text-foreground">Constructure</h1>
                    <p className="text-xs text-muted-foreground">
                      RAG Assistant
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-2 rounded-lg hover:bg-muted/80 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Actions */}
              <div className="p-4 space-y-3">
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Button
                    onClick={clearMessages}
                    variant="outline"
                    className="w-full justify-start gap-3 h-11 border-border/50 hover:bg-muted/80 hover:border-primary/30 transition-all duration-200"
                  >
                    <Plus className="w-4 h-4" />
                    <span>New Chat</span>
                  </Button>
                </motion.div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleUpload}
                  className="hidden"
                />
                
                {/* Upload button with cancel option */}
                <div className="relative">
                  <motion.div
                    whileHover={!uploading ? { scale: 1.02 } : undefined}
                    whileTap={!uploading ? { scale: 0.98 } : undefined}
                  >
                    <Button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="w-full justify-start gap-3 h-11 bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg shadow-primary/25 transition-all duration-200"
                    >
                      {uploading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Upload className="w-4 h-4" />
                      )}
                      <span className="flex-1 text-left">
                        {uploading ? "Processing..." : "Upload PDF"}
                      </span>
                      {uploading && (
                        <span className="text-xs opacity-75">
                          {uploadProgress.progress}%
                        </span>
                      )}
                    </Button>
                  </motion.div>
                  
                  {/* Cancel button */}
                  {uploading && (
                    <motion.button
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        cancelUpload();
                        toast.info("Upload cancelled");
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-white/20 transition-colors"
                      title="Cancel upload"
                    >
                      <XCircle className="w-4 h-4" />
                    </motion.button>
                  )}
                </div>

                {/* Upload Progress with detailed steps */}
                <UploadProgress 
                  data={uploadProgress} 
                  isVisible={uploading || uploadProgress.step === 'complete' || uploadProgress.step === 'error'} 
                />

                {/* Document stats */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-xl bg-gradient-to-br from-muted/80 to-muted/40 border border-border/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                      <File className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-foreground">
                        {documents.total_chunks}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        chunks indexed
                      </p>
                    </div>
                    {documents.total_chunks > 0 && (
                      <motion.button
                        onClick={handleClearDocuments}
                        disabled={clearing}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className="p-2 rounded-lg hover:bg-destructive/10 text-destructive/70 hover:text-destructive transition-colors"
                        title="Clear all documents"
                      >
                        {clearing ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              </div>

              {/* Mode selector */}
              <div className="px-4 pb-4">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Mode
                </p>
                <div className="space-y-1.5">
                  {modeOptions.map((m) => (
                    <motion.button
                      key={m.value}
                      onClick={() => setMode(m.value)}
                      whileHover={{ scale: 1.02, x: 4 }}
                      whileTap={{ scale: 0.98 }}
                      className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-all duration-200 flex items-center gap-3 ${
                        mode === m.value
                          ? "bg-gradient-to-r from-primary to-primary/90 text-primary-foreground shadow-lg shadow-primary/25"
                          : "hover:bg-muted/80 border border-transparent hover:border-border/50"
                      }`}
                    >
                      <m.icon className="w-4 h-4" />
                      <div className="flex-1">
                        <p className="font-medium">{m.label}</p>
                        <p
                          className={`text-xs ${
                            mode === m.value
                              ? "text-primary-foreground/70"
                              : "text-muted-foreground"
                          }`}
                        >
                          {m.description}
                        </p>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className="mt-auto p-4 border-t border-border/50 space-y-3">
                <div className="flex items-center justify-between">
                  <motion.button
                    whileHover={{ scale: 1.1, rotate: 15 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={toggleDarkMode}
                    className="p-2.5 rounded-xl hover:bg-muted/80 transition-colors"
                  >
                    {darkMode ? (
                      <Sun className="w-5 h-5 text-amber-500" />
                    ) : (
                      <Moon className="w-5 h-5 text-indigo-500" />
                    )}
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={handleLogout}
                    className="p-2.5 rounded-xl hover:bg-destructive/10 text-destructive transition-colors"
                  >
                    <LogOut className="w-5 h-5" />
                  </motion.button>
                </div>

                {/* User info */}
                <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/50">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center text-primary font-bold border border-primary/20">
                    {user?.email?.charAt(0).toUpperCase() || "U"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {user?.email?.split("@")[0]}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {user?.email}
                    </p>
                  </div>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: TIMING.medium }}
          className="h-16 glass border-b border-border/50 flex items-center px-4 gap-4 shrink-0"
        >
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setSidebarOpen(true)}
            className="p-2.5 rounded-xl hover:bg-muted/80 transition-colors"
          >
            <Menu className="w-5 h-5" />
          </motion.button>

          <div className="flex-1 flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-medium text-muted-foreground">
                {mode === "qa"
                  ? "Q&A Mode"
                  : mode === "extraction"
                  ? "Extraction Mode"
                  : "Sources Mode"}
              </span>
            </motion.div>
          </div>

          <span className="text-xs px-3 py-1.5 rounded-full bg-gradient-to-r from-primary/10 to-accent/10 text-primary font-medium border border-primary/20">
            {documents.total_chunks} chunks
          </span>
        </motion.header>

        {/* Messages area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: TIMING.slow, ease: EASING.entrance }}
              className="h-full flex flex-col items-center justify-center text-center px-4"
            >
              {/* Hero icon */}
              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="relative mb-6"
              >
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-2xl shadow-primary/30">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                {/* Glow rings */}
                <div className="absolute inset-0 rounded-2xl bg-primary/30 blur-xl -z-10 animate-pulse" />
                <div className="absolute -inset-4 rounded-3xl bg-primary/10 blur-2xl -z-20" />
              </motion.div>

              <h2 className="text-2xl font-bold mb-2 text-gradient">
                Start a conversation
              </h2>
              <p className="text-muted-foreground text-sm max-w-md leading-relaxed">
                {documents.total_chunks === 0
                  ? "Upload a PDF document first, then ask questions and get answers backed by your documents."
                  : "Your documents are ready. Ask anything and get intelligent answers with source citations."}
              </p>

              {/* Quick tips */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl"
              >
                {[
                  { icon: "💡", text: "Ask specific questions" },
                  { icon: "📄", text: "Reference page numbers" },
                  { icon: "🔍", text: "Get source citations" },
                ].map((tip, i) => (
                  <motion.div
                    key={i}
                    whileHover={{ scale: 1.05, y: -2 }}
                    className="flex items-center gap-2 px-4 py-3 rounded-xl bg-muted/50 border border-border/50 text-sm"
                  >
                    <span className="text-lg">{tip.icon}</span>
                    <span className="text-muted-foreground">{tip.text}</span>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          )}

          <AnimatePresence mode="popLayout">
            {messages.map((msg, index) => {
              // Skip rendering empty streaming messages - TypingIndicator handles this
              if (msg.isStreaming && !msg.content) return null;
              return <ChatMessage key={msg.id} message={msg} index={index} />;
            })}
            {isLoading && <TypingIndicator />}
          </AnimatePresence>
        </div>

        {/* Input area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: TIMING.medium, delay: 0.1 }}
          className="p-4 glass border-t border-border/50 shrink-0"
        >
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="relative flex items-end gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    documents.total_chunks === 0
                      ? "Upload a document to start..."
                      : "Ask a question about your documents..."
                  }
                  disabled={isLoading || documents.total_chunks === 0}
                  className="w-full rounded-2xl px-5 py-4 pr-14 bg-muted/50 border border-border/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground/60 text-[15px] outline-none transition-all duration-200 disabled:opacity-50"
                />
                {/* Character count */}
                {input.length > 0 && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute right-14 bottom-4 text-xs text-muted-foreground"
                  >
                    {input.length}
                  </motion.span>
                )}
              </div>

              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  type="submit"
                  size="icon"
                  disabled={
                    !input.trim() || isLoading || documents.total_chunks === 0
                  }
                  className="w-12 h-12 rounded-xl bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg shadow-primary/25 disabled:shadow-none disabled:opacity-50 transition-all duration-200"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </Button>
              </motion.div>
            </div>

            {/* Keyboard hint */}
            <p className="text-center text-xs text-muted-foreground mt-3">
              Press{" "}
              <kbd className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">
                Enter
              </kbd>{" "}
              to send
            </p>
          </form>
        </motion.div>
      </main>
    </div>
  );
}
