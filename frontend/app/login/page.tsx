"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  FileText,
  Bot,
  Sparkles,
  Zap,
  Shield,
  Moon,
  Sun,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuthStore, useHasHydrated } from "@/lib/hooks/useAuth";
import { useThemeStore } from "@/lib/hooks/useTheme";
import { toast } from "sonner";
import { TIMING, EASING } from "@/lib/animations";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuthStore();
  const hasHydrated = useHasHydrated();
  const { darkMode, toggleDarkMode } = useThemeStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false); // Local form loading state

  // Apply persisted theme (only after hydration)
  useEffect(() => {
    if (hasHydrated) {
      document.documentElement.classList.toggle("dark", darkMode);
    }
  }, [darkMode, hasHydrated]);

  // Redirect if already authenticated (only after hydration)
  // Note: We don't call checkAuth() here - the login page doesn't need to verify auth
  // The persisted isAuthenticated state is enough to redirect logged-in users
  useEffect(() => {
    if (hasHydrated && isAuthenticated) {
      router.replace("/chat");
    }
  }, [hasHydrated, isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsSubmitting(true);
    const success = await login(email, password);

    if (success) {
      toast.success("Welcome back!");
      router.push("/chat");
    } else {
      toast.error("Invalid credentials");
      setIsSubmitting(false);
    }
  };

  const features = [
    {
      icon: FileText,
      title: "PDF Processing",
      desc: "Upload and index documents instantly",
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: Bot,
      title: "Smart Q&A",
      desc: "Ask questions in natural language",
      color: "from-violet-500 to-purple-500",
    },
    {
      icon: Sparkles,
      title: "Source Citations",
      desc: "Every answer backed by sources",
      color: "from-amber-500 to-orange-500",
    },
  ];

  return (
    <div className="h-screen flex bg-mesh overflow-hidden">
      {/* Dark mode toggle - fixed position */}
      <motion.button
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2, duration: TIMING.medium }}
        onClick={toggleDarkMode}
        className="fixed top-6 right-6 p-3 rounded-xl glass hover:scale-105 transition-transform z-50 group border border-border/50"
        aria-label="Toggle dark mode"
      >
        <AnimatePresence mode="wait">
          {darkMode ? (
            <motion.div
              key="sun"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: TIMING.fast }}
            >
              <Sun className="w-5 h-5 text-amber-400 group-hover:text-amber-300" />
            </motion.div>
          ) : (
            <motion.div
              key="moon"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: TIMING.fast }}
            >
              <Moon className="w-5 h-5 text-primary group-hover:text-primary/80" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Left side - Hero section */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden flex-col justify-center px-12 xl:px-20 py-12">
        {/* Animated gradient orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            animate={{
              x: [0, 30, 0],
              y: [0, -20, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-20 left-20 w-72 h-72 rounded-full bg-gradient-to-br from-primary/30 to-accent/20 blur-3xl"
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
            className="absolute bottom-32 right-10 w-80 h-80 rounded-full bg-gradient-to-br from-accent/25 to-primary/15 blur-3xl"
          />
        </div>

        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: TIMING.slow, ease: EASING.entrance }}
          className="relative z-10"
        >
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: TIMING.fast }}
            className="flex items-center gap-4 mb-10"
          >
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-xl shadow-primary/30">
              <Sparkles className="w-7 h-7 text-white" />
              <div className="absolute inset-0 rounded-2xl bg-primary/30 blur-xl -z-10" />
            </div>
            <div>
              <span className="text-2xl font-bold">Constructure</span>
              <p className="text-sm text-muted-foreground">RAG Assistant</p>
            </div>
          </motion.div>

          {/* Hero text */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: TIMING.medium, delay: 0.3 }}
            className="text-5xl font-bold mb-6 leading-tight"
          >
            Document Intelligence
            <br />
            <span className="text-gradient">Made Simple</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: TIMING.medium, delay: 0.4 }}
            className="text-lg text-muted-foreground mb-12 max-w-lg leading-relaxed"
          >
            Upload your construction documents and get instant answers using
            AI-powered semantic search with source citations.
          </motion.p>

          {/* Features */}
          <div className="space-y-3">
            {features.map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: TIMING.fast, delay: 0.2 + i * 0.05 }}
                className="group flex items-start gap-4 p-4 rounded-2xl glass border border-border/50 hover:border-primary/30 transition-colors duration-200"
              >
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center shrink-0 shadow-lg`}
                >
                  <item.icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">{item.title}</p>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Right side - Login form */}
      <div className="flex-1 flex items-center justify-center p-6 py-16 relative">
        {/* Mobile background orb */}
        <div className="lg:hidden absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 right-10 w-64 h-64 rounded-full bg-gradient-to-br from-primary/20 to-accent/10 blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: TIMING.slow, ease: EASING.entrance }}
          className="relative w-full max-w-md"
        >
          {/* Mobile logo */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: TIMING.fast }}
            className="lg:hidden text-center mb-10"
          >
            <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center mx-auto mb-4 shadow-xl shadow-primary/30">
              <Sparkles className="w-8 h-8 text-white" />
              <div className="absolute inset-0 rounded-2xl bg-primary/30 blur-xl -z-10" />
            </div>
            <h1 className="text-2xl font-bold">Constructure RAG</h1>
            <p className="text-muted-foreground mt-1">Document Intelligence</p>
          </motion.div>

          {/* Form card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-3xl p-8 border border-border/50 shadow-2xl"
          >
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-2">Welcome back</h2>
              <p className="text-muted-foreground">
                Sign in to access your documents
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="text-sm font-medium mb-2 block text-foreground/80">
                  Email
                </label>
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-12 rounded-xl bg-muted/50 border-border/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                  autoComplete="email"
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block text-foreground/80">
                  Password
                </label>
                <div className="relative">
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-12 rounded-xl pr-12 bg-muted/50 border-border/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                    autoComplete="current-password"
                  />
                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </motion.button>
                </div>
              </div>

              <motion.div
                whileHover={{ scale: isSubmitting ? 1 : 1.02 }}
                whileTap={{ scale: isSubmitting ? 1 : 0.98 }}
              >
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-12 rounded-xl bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg shadow-primary/25 text-base font-semibold transition-all duration-300"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin mr-2" />
                      Signing in...
                    </>
                  ) : (
                    <>
                      Sign in
                      <ArrowRight className="w-5 h-5 ml-2" />
                    </>
                  )}
                </Button>
              </motion.div>
            </form>

            {/* Demo credentials */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-8 pt-6 border-t border-border/50"
            >
              <div className="flex items-center gap-2 justify-center text-sm text-muted-foreground mb-4">
                <Shield className="w-4 h-4" />
                <span>Demo credentials available</span>
              </div>
              <motion.button
                type="button"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  setEmail("testingcheckuser1234@gmail.com");
                  setPassword("constructure2024");
                  toast.info("Demo credentials filled!");
                }}
                className="w-full py-3 rounded-xl border border-border/50 text-sm font-medium hover:bg-muted/50 hover:border-primary/30 transition-all duration-200 flex items-center justify-center gap-2"
              >
                <Zap className="w-4 h-4 text-primary" />
                Fill demo account
              </motion.button>
            </motion.div>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-xs text-center text-muted-foreground mt-8"
          >
            Technical assignment for Constructure AI
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}
