"use client";

import { 
  Sparkles, 
  Briefcase, 
  FileText, 
  TrendingUp,
  Zap,
  Target,
  Rocket,
  Mail,
  Clock
} from "lucide-react";
import { motion } from "framer-motion";

interface EmptyScreenProps {
  onSendMessage: (message: string) => void;
}

export function EmptyScreen({ onSendMessage }: EmptyScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-4 sm:px-6 py-8 sm:py-12 pb-44 relative">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/3 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* Hero Section with modern typography */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10 sm:mb-12 text-center max-w-3xl relative z-10"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-6 rounded-full bg-primary/10 border border-primary/20 backdrop-blur-sm">
          <Sparkles className="w-4 h-4 text-primary animate-pulse" />
          <span className="text-xs font-medium text-primary">AI-Powered Career Assistant</span>
        </div>
        
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
          <span className="bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
            How can I help you
          </span>
          <br />
          <span className="bg-gradient-to-r from-primary via-primary/80 to-primary bg-clip-text text-transparent">
            with your career today?
          </span>
        </h1>
        
        <p className="text-lg sm:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto">
          Continue where we left off or start something new. I'm here to help with resumes, cover letters, job search, and career guidance.
        </p>
      </motion.div>

      {/* Popular Actions - 2025 Style Pills */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="mt-6 sm:mt-8 relative z-10"
      >
        <p className="text-xs uppercase tracking-wider text-muted-foreground/60 mb-3 text-center">
          Quick Actions
        </p>
        <div className="flex flex-wrap gap-2 justify-center max-w-3xl">
          {[
            { icon: FileText, text: "Update my resume", gradient: "from-emerald-400 to-teal-600" },
            { icon: Briefcase, text: "Generate cover letter", gradient: "from-violet-400 to-purple-600" },
            { icon: Rocket, text: "Find remote jobs", gradient: "from-amber-400 to-orange-600" },
            { icon: Mail, text: "Write job application email", gradient: "from-blue-400 to-indigo-600" },
            { icon: Clock, text: "Follow-up on application", gradient: "from-pink-400 to-rose-600" },
            { icon: Target, text: "Review my resume", gradient: "from-blue-400 to-cyan-600" },
            { icon: TrendingUp, text: "Career advice", gradient: "from-purple-400 to-pink-600" },
            { icon: Zap, text: "Interview prep", gradient: "from-yellow-400 to-red-600" },
          ].map((action, i) => (
            <motion.button
              key={i}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="group flex items-center gap-2 px-4 py-2 rounded-full border border-border/50 bg-background/50 backdrop-blur-sm hover:bg-background/80 hover:border-primary/30 transition-all duration-300 relative z-10"
              onClick={() => onSendMessage(action.text)}
            >
              <div className={`p-1 rounded-full bg-gradient-to-br ${action.gradient}`}>
                <action.icon className="w-3 h-3 text-white" />
              </div>
              <span className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                {action.text}
              </span>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Footer hint with modern styling */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="mt-8 mb-4 text-center relative z-10"
      >
        <div className="inline-flex items-center gap-2 text-sm text-muted-foreground/60">
          <div className="w-1 h-1 rounded-full bg-muted-foreground/40 animate-pulse" />
          <span>Type a message to continue our conversation</span>
          <div className="w-1 h-1 rounded-full bg-muted-foreground/40 animate-pulse" style={{ animationDelay: '0.5s' }} />
        </div>
      </motion.div>
    </div>
  );
}