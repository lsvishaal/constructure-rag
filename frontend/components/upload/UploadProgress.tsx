"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
  Sparkles,
  Scissors,
  Database,
  Cpu,
} from "lucide-react";
import { TIMING, EASING, SPRING } from "@/lib/animations";

export type UploadStep = 
  | "idle"
  | "saving"
  | "parsing"
  | "chunking"
  | "embedding"
  | "indexing"
  | "complete"
  | "error";

export interface UploadProgressData {
  step: UploadStep;
  progress: number;
  detail: string;
  filename?: string;
  pages?: number;
  text_pages?: number;
  chunks?: number;
  time_seconds?: number;
  pages_per_second?: number;
  error?: string;
}

interface Props {
  data: UploadProgressData;
  isVisible: boolean;
}

const STEPS = [
  { key: "saving", label: "Saving", icon: FileText, description: "Uploading file to server" },
  { key: "parsing", label: "Parsing", icon: FileText, description: "Extracting text from PDF" },
  { key: "chunking", label: "Chunking", icon: Scissors, description: "Splitting into semantic chunks" },
  { key: "embedding", label: "Embedding", icon: Cpu, description: "Generating vector embeddings" },
  { key: "indexing", label: "Indexing", icon: Database, description: "Storing in vector database" },
] as const;

function getStepStatus(stepKey: string, currentStep: UploadStep): "pending" | "active" | "complete" | "error" {
  if (currentStep === "error") return "error";
  if (currentStep === "complete") return "complete";
  
  const stepOrder = ["saving", "parsing", "chunking", "embedding", "indexing"];
  const currentIndex = stepOrder.indexOf(currentStep);
  const stepIndex = stepOrder.indexOf(stepKey);
  
  if (currentIndex === -1) return "pending"; // idle state
  if (stepIndex < currentIndex) return "complete";
  if (stepIndex === currentIndex) return "active";
  return "pending";
}

function StepIcon({ status, icon: Icon }: { status: "pending" | "active" | "complete" | "error"; icon: React.ComponentType<{ className?: string }> }) {
  if (status === "complete") {
    return (
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={SPRING.bouncy}
      >
        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
      </motion.div>
    );
  }
  
  if (status === "active") {
    return (
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      >
        <Loader2 className="w-5 h-5 text-primary" />
      </motion.div>
    );
  }
  
  if (status === "error") {
    return <AlertCircle className="w-5 h-5 text-destructive" />;
  }
  
  return <Circle className="w-5 h-5 text-muted-foreground/40" />;
}

export function UploadProgress({ data, isVisible }: Props) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, height: 0, marginTop: 0 }}
          animate={{ opacity: 1, height: "auto", marginTop: 12 }}
          exit={{ opacity: 0, height: 0, marginTop: 0 }}
          transition={{ duration: TIMING.medium, ease: EASING.entrance }}
          className="overflow-hidden"
        >
          <div className="p-4 rounded-xl bg-gradient-to-br from-muted/80 to-muted/40 border border-border/50">
            {/* Header with filename */}
            {data.filename && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 mb-4 pb-3 border-b border-border/50"
              >
                <FileText className="w-4 h-4 text-primary" />
                <span className="font-medium text-sm truncate">{data.filename}</span>
              </motion.div>
            )}
            
            {/* Progress bar */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                <span>{data.detail}</span>
                <span className="font-mono">{data.progress}%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-primary to-primary/80 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${data.progress}%` }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                />
              </div>
            </div>
            
            {/* Steps */}
            <div className="space-y-2">
              {STEPS.map((step, idx) => {
                const status = getStepStatus(step.key, data.step);
                const Icon = step.icon;
                
                return (
                  <motion.div
                    key={step.key}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                      status === "active" 
                        ? "bg-primary/10 border border-primary/20" 
                        : status === "complete"
                        ? "bg-emerald-500/10"
                        : ""
                    }`}
                  >
                    <StepIcon status={status} icon={Icon} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className={`text-sm font-medium ${
                          status === "active" ? "text-primary" : 
                          status === "complete" ? "text-emerald-600 dark:text-emerald-400" : 
                          "text-muted-foreground"
                        }`}>
                          {step.label}
                        </span>
                        {status === "active" && data.step === step.key && (
                          <span className="text-xs text-muted-foreground">
                            {data.step === "parsing" && data.pages_per_second && `${data.pages_per_second.toFixed(0)} pg/s`}
                            {data.step === "embedding" && data.chunks && `${data.chunks} chunks`}
                          </span>
                        )}
                      </div>
                      <p className={`text-xs ${
                        status === "pending" ? "text-muted-foreground/50" : "text-muted-foreground"
                      }`}>
                        {step.description}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
            
            {/* Completion stats */}
            <AnimatePresence>
              {data.step === "complete" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: TIMING.medium }}
                  className="mt-4 pt-4 border-t border-border/50"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-emerald-500" />
                    <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                      Processing Complete!
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    {data.pages !== undefined && (
                      <div className="p-2 rounded-lg bg-background/50">
                        <p className="text-lg font-bold text-foreground">{data.pages}</p>
                        <p className="text-xs text-muted-foreground">pages</p>
                      </div>
                    )}
                    {data.chunks !== undefined && (
                      <div className="p-2 rounded-lg bg-background/50">
                        <p className="text-lg font-bold text-foreground">{data.chunks}</p>
                        <p className="text-xs text-muted-foreground">chunks</p>
                      </div>
                    )}
                    {data.time_seconds !== undefined && (
                      <div className="p-2 rounded-lg bg-background/50">
                        <p className="text-lg font-bold text-foreground">{data.time_seconds.toFixed(1)}s</p>
                        <p className="text-xs text-muted-foreground">total time</p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Error state */}
            <AnimatePresence>
              {data.step === "error" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20"
                >
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-destructive" />
                    <span className="text-sm font-medium text-destructive">Upload Failed</span>
                  </div>
                  {data.error && (
                    <p className="mt-1 text-xs text-destructive/80">{data.error}</p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default UploadProgress;
