"use client"

import { SignInButton } from "@clerk/nextjs"
import { Button } from "./ui/button"
import { Bot, Briefcase, FileText, MessageSquare, Sparkles, ArrowRight, Users, TrendingUp, Shield, Zap, Star, CheckCircle } from "lucide-react"

export function LoginPrompt() {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen p-3 sm:p-4 pt-16 sm:pt-20 overflow-hidden bg-background">
      {/* Background Effects - More consistent with theme */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-50/20 via-purple-50/10 to-pink-50/20 dark:from-blue-950/20 dark:via-purple-950/10 dark:to-pink-950/20" />
      <div className="fixed inset-0 bg-grid-pattern opacity-[0.02] dark:opacity-[0.05]" />
      
      {/* Floating Elements - More subtle and theme-consistent */}
      <div className="fixed top-20 left-4 sm:left-10 w-12 h-12 sm:w-20 sm:h-20 bg-gradient-to-r from-blue-500/10 to-purple-600/10 rounded-full opacity-50 animate-pulse" />
      <div className="fixed bottom-32 right-6 sm:right-16 w-10 h-10 sm:w-16 sm:h-16 bg-gradient-to-r from-purple-500/10 to-pink-600/10 rounded-full opacity-50 animate-pulse delay-1000" />
      <div className="fixed top-1/3 right-8 sm:right-20 w-8 h-8 sm:w-12 sm:h-12 bg-gradient-to-r from-green-500/10 to-blue-600/10 rounded-full opacity-50 animate-pulse delay-500" />
      
      {/* Main Content */}
      <div className="relative z-10 w-full max-w-sm sm:max-w-lg md:max-w-2xl lg:max-w-3xl xl:max-w-4xl mx-auto">
        {/* Logo/Header Section */}
        <div className="text-center mb-6 sm:mb-8 md:mb-12 lg:mb-16">
          <div className="flex justify-center mb-4 sm:mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-blue-500 via-purple-600 to-indigo-700 rounded-2xl sm:rounded-3xl shadow-2xl shadow-blue-500/20 animate-pulse ring-2 ring-background">
              <Bot className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
            </div>
          </div>
          
          {/* Social Proof Badge */}
          <div className="flex justify-center mb-4 sm:mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 bg-background/80 backdrop-blur-sm border border-green-500/20 rounded-full shadow-lg">
              <Users className="w-3 h-3 sm:w-4 sm:h-4 text-green-600" />
              <span className="text-xs sm:text-sm font-medium text-green-700 dark:text-green-400">Join 500+ successful job seekers</span>
            </div>
          </div>
          
          <h1 className="text-2xl sm:text-4xl md:text-5xl lg:text-6xl font-black bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-800 dark:from-blue-400 dark:via-purple-400 dark:to-indigo-300 bg-clip-text text-transparent mb-3 sm:mb-4 leading-tight px-2">
            Land Your Dream Job
            <br />
            <span className="text-xl sm:text-3xl md:text-4xl lg:text-5xl">with AI Power</span>
          </h1>
          
          <p className="text-sm sm:text-xl text-muted-foreground leading-relaxed mb-4 sm:mb-6 max-w-lg sm:max-w-2xl mx-auto px-2">
            Get personalized resumes, compelling cover letters, and ace interviews with our advanced AI assistant
          </p>
          
          {/* Trust Indicators */}
          <div className="flex items-center justify-center flex-wrap gap-3 sm:gap-6 text-xs sm:text-sm text-muted-foreground px-2">
            <div className="flex items-center gap-1">
              <Shield className="w-3 h-3 sm:w-4 sm:h-4 text-green-500" />
              <span>100% Secure</span>
            </div>
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3 sm:w-4 sm:h-4 text-yellow-500" />
              <span>Instant Results</span>
            </div>
            <div className="flex items-center gap-1">
              <Star className="w-3 h-3 sm:w-4 sm:h-4 text-orange-500" />
              <span>AI-Powered</span>
            </div>
          </div>
        </div>

        {/* Key Benefits - Improved mobile layout */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-12 px-2">
          <div className="text-center p-4 sm:p-0">
            <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg ring-2 ring-background">
              <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <h3 className="text-lg sm:text-2xl font-bold text-foreground mb-1 sm:mb-2">3x Higher</h3>
            <p className="text-xs sm:text-sm text-muted-foreground">Interview Success Rate</p>
          </div>
          <div className="text-center p-4 sm:p-0">
            <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg ring-2 ring-background">
              <Zap className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <h3 className="text-lg sm:text-2xl font-bold text-foreground mb-1 sm:mb-2">60% Faster</h3>
            <p className="text-xs sm:text-sm text-muted-foreground">Application Process</p>
          </div>
          <div className="text-center p-4 sm:p-0">
            <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 bg-gradient-to-br from-green-500 to-green-600 rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg ring-2 ring-background">
              <Users className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <h3 className="text-lg sm:text-2xl font-bold text-foreground mb-1 sm:mb-2">500+</h3>
            <p className="text-xs sm:text-sm text-muted-foreground">Jobs Landed</p>
          </div>
        </div>

        {/* Features Grid - Improved mobile layout */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-6 sm:mb-8 px-2">
          <div className="group p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-background/80 backdrop-blur-sm border border-blue-200/30 dark:border-blue-800/20 hover:scale-105 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-xl">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg sm:rounded-xl flex items-center justify-center mb-2 sm:mb-3 group-hover:scale-110 transition-transform ring-2 ring-background">
              <Briefcase className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <p className="font-semibold text-foreground mb-1 text-sm sm:text-base">Smart Job Matching</p>
            <p className="text-xs text-muted-foreground">AI finds perfect opportunities</p>
          </div>
          <div className="group p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-background/80 backdrop-blur-sm border border-purple-200/30 dark:border-purple-800/20 hover:scale-105 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-xl">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg sm:rounded-xl flex items-center justify-center mb-2 sm:mb-3 group-hover:scale-110 transition-transform ring-2 ring-background">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <p className="font-semibold text-foreground mb-1 text-sm sm:text-base">ATS-Optimized Resumes</p>
            <p className="text-xs text-muted-foreground">Beat applicant tracking systems</p>
          </div>
          <div className="group p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-background/80 backdrop-blur-sm border border-green-200/30 dark:border-green-800/20 hover:scale-105 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-xl">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg sm:rounded-xl flex items-center justify-center mb-2 sm:mb-3 group-hover:scale-110 transition-transform ring-2 ring-background">
              <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <p className="font-semibold text-foreground mb-1 text-sm sm:text-base">Custom Cover Letters</p>
            <p className="text-xs text-muted-foreground">Tailored for each application</p>
          </div>
          <div className="group p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-background/80 backdrop-blur-sm border border-yellow-200/30 dark:border-yellow-800/20 hover:scale-105 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-xl">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg sm:rounded-xl flex items-center justify-center mb-2 sm:mb-3 group-hover:scale-110 transition-transform ring-2 ring-background">
              <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <p className="font-semibold text-foreground mb-1 text-sm sm:text-base">Interview Coaching</p>
            <p className="text-xs text-muted-foreground">Practice with AI feedback</p>
          </div>
        </div>

        {/* Testimonial - Mobile optimized */}
        <div className="p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-background/80 backdrop-blur-sm border border-border/50 mb-6 sm:mb-8 shadow-lg mx-2">
          <div className="flex items-center gap-3 sm:gap-4 mb-2 sm:mb-3">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center ring-2 ring-background">
              <span className="text-white font-bold text-sm sm:text-base">S</span>
            </div>
            <div>
              <p className="font-semibold text-foreground text-sm sm:text-base">Sarah Chen</p>
              <p className="text-xs sm:text-sm text-muted-foreground">Software Engineer at Google</p>
            </div>
          </div>
          <p className="text-xs sm:text-sm text-muted-foreground italic leading-relaxed">
            "JobHackerBot helped me land my dream job at Google! The AI-generated resume got me 5x more interviews."
          </p>
          <div className="flex gap-1 mt-2">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="w-3 h-3 sm:w-4 sm:h-4 fill-yellow-400 text-yellow-400" />
            ))}
          </div>
        </div>

        {/* Main Card - Mobile optimized */}
        <div className="p-6 sm:p-8 rounded-xl sm:rounded-2xl md:rounded-3xl bg-background/90 backdrop-blur-xl border border-border/50 shadow-2xl shadow-black/5 dark:shadow-white/5 mx-2">
          <div className="text-center">
            <h2 className="text-xl sm:text-2xl font-bold text-foreground mb-2">
              Start Your Success Story Today
            </h2>
            <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6 leading-relaxed">
              Join hundreds who've transformed their careers with AI-powered job applications
            </p>
            
            {/* What you get - Mobile grid layout */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 mb-4 sm:mb-6 text-left">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-green-500 flex-shrink-0" />
                <span className="text-xs sm:text-sm text-muted-foreground">Unlimited resumes & cover letters</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-green-500 flex-shrink-0" />
                <span className="text-xs sm:text-sm text-muted-foreground">AI interview preparation</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-green-500 flex-shrink-0" />
                <span className="text-xs sm:text-sm text-muted-foreground">Job matching algorithm</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-green-500 flex-shrink-0" />
                <span className="text-xs sm:text-sm text-muted-foreground">24/7 AI career coach</span>
              </div>
            </div>
            
        <SignInButton mode="modal">
              <Button 
                size="lg"
                className="w-full h-12 sm:h-14 bg-gradient-to-r from-blue-500 via-purple-600 to-indigo-700 hover:from-blue-600 hover:via-purple-700 hover:to-indigo-800 text-white shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-[1.02] group font-semibold text-base sm:text-lg rounded-xl touch-manipulation"
              >
                <span className="flex items-center justify-center gap-2 sm:gap-3">
                  <Bot className="w-4 h-4 sm:w-5 sm:h-5" />
                  Start Building Your Future
                  <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 group-hover:translate-x-1 transition-transform" />
                </span>
              </Button>
        </SignInButton>
            
            <div className="flex items-center justify-center flex-wrap gap-2 sm:gap-4 mt-3 sm:mt-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Shield className="w-3 h-3 text-green-500" />
                <span>Free forever</span>
              </div>
              <span>•</span>
              <span>No credit card required</span>
              <span>•</span>
              <span>Setup in 30 seconds</span>
            </div>
          </div>
        </div>
        
        {/* Bottom spacing for mobile */}
        <div className="h-6 sm:h-0" />
      </div>
    </div>
  )
} 