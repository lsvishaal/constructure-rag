"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Loader2 } from "lucide-react";
import { useAuthStore, useHasHydrated } from "@/lib/hooks/useAuth";
import { useThemeStore } from "@/lib/hooks/useTheme";

export default function HomePage() {
  const router = useRouter();
  const { checkAuth, isAuthenticated, isCheckingAuth } = useAuthStore();
  const hasHydrated = useHasHydrated();
  const { darkMode } = useThemeStore();

  // Apply theme only after hydration
  useEffect(() => {
    if (hasHydrated) {
      document.documentElement.classList.toggle("dark", darkMode);
    }
  }, [darkMode, hasHydrated]);

  // Check auth only after hydration
  useEffect(() => {
    if (hasHydrated) {
      checkAuth();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasHydrated]);

  // Redirect only after hydration and auth check complete
  useEffect(() => {
    if (hasHydrated && !isCheckingAuth) {
      router.push(isAuthenticated ? "/chat" : "/login");
    }
  }, [hasHydrated, isAuthenticated, isCheckingAuth, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-mesh">
      {/* Background orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            x: [0, 30, 0],
            y: [0, -20, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-gradient-to-br from-primary/20 to-accent/10 blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, -20, 0],
            y: [0, 30, 0],
            scale: [1, 0.9, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1,
          }}
          className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-gradient-to-br from-accent/15 to-primary/10 blur-3xl"
        />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 flex flex-col items-center gap-6"
      >
        {/* Logo */}
        <motion.div
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="relative"
        >
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-2xl shadow-primary/30">
            <Sparkles className="w-10 h-10 text-white" />
          </div>
          <div className="absolute inset-0 rounded-2xl bg-primary/30 blur-xl -z-10 animate-pulse" />
        </motion.div>

        {/* Loading text */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col items-center gap-3"
        >
          <h1 className="text-2xl font-bold text-gradient">Constructure RAG</h1>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Loading...</span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
