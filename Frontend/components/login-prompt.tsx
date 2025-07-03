"use client";

import { SignInButton } from "@clerk/nextjs";
import {
  ArrowRight,
  Award,
  Brain,
  CheckCircle,
  Clock,
  FileText,
  Globe,
  Layers,
  Lock,
  MessageSquare,
  Mic,
  PlayCircle,
  RefreshCw,
  Rocket,
  Shield,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";
import { Button } from "./ui/button";
import { Logo } from "./ui/logo";

export function LoginPrompt() {
  return (
    <div className="relative min-h-screen bg-white dark:bg-black overflow-hidden">
      {/* Sophisticated Background Grid */}
      <div className="fixed inset-0 top-0 left-0 right-0 bottom-0 bg-[linear-gradient(to_right,#f1f5f9_1px,transparent_1px),linear-gradient(to_bottom,#f1f5f9_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_110%)] dark:bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)]" />

      {/* Hero Section */}
      <section className="relative px-6 pt-8 pb-16 sm:pt-12 sm:pb-24 lg:px-8">
        <div className="mx-auto max-w-7xl">
          {/* Funding Announcement Banner */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-3 rounded-full bg-gray-50 dark:bg-gray-900/50 px-4 py-2 border border-gray-200/50 dark:border-gray-800/50 backdrop-blur-sm">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Series A: $50M raised to revolutionize job applications
              </span>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </div>
          </div>

          {/* Logo Section */}
          <div className="flex justify-center mb-8">
            <Logo size="lg" />
          </div>

          {/* Main Headline */}
          <div className="text-center">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900 dark:text-white mb-6">
              The AI-Powered
              <br />
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Career Platform
              </span>
            </h1>

            <p className="mx-auto max-w-3xl text-xl sm:text-2xl text-gray-600 dark:text-gray-400 leading-relaxed mb-12">
              Transform your career with enterprise-grade AI that generates
              ATS-optimized resumes, crafts compelling cover letters, and
              provides expert interview coaching.
            </p>

            {/* CTA Section */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
              <SignInButton mode="modal">
                <Button
                  size="lg"
                  className="h-14 px-8 text-lg font-semibold bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  Start Building Your Future
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </SignInButton>

              <Button
                variant="outline"
                size="lg"
                className="h-14 px-8 text-lg font-semibold border-2 border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 rounded-xl transition-all duration-200"
              >
                <PlayCircle className="mr-2 h-5 w-5" />
                Watch Demo
              </Button>
            </div>

            {/* Trust Indicators */}
            <div className="flex items-center justify-center gap-8 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" />
                <span>SOC 2 Compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-500" />
                <span>50K+ Professionals</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-500" />
                <span>99.9% Uptime SLA</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof - Enterprise Logos */}
      <section className="relative px-6 py-16 border-t border-gray-200/50 dark:border-gray-800/50">
        <div className="mx-auto max-w-7xl">
          <p className="text-center text-sm font-medium text-gray-500 dark:text-gray-400 mb-8 uppercase tracking-wide">
            Trusted by professionals at
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-8 items-center opacity-60">
            {[
              { name: "Google", logo: "🌐" },
              { name: "Microsoft", logo: "💻" },
              { name: "Meta", logo: "📘" },
              { name: "Apple", logo: "🍎" },
              { name: "Amazon", logo: "📦" },
              { name: "Netflix", logo: "🎬" },
            ].map((company, i) => (
              <div key={i} className="flex items-center justify-center">
                <div className="text-2xl">{company.logo}</div>
                <span className="ml-2 text-lg font-semibold text-gray-700 dark:text-gray-300">
                  {company.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Metrics */}
      <section className="relative px-6 py-16 bg-gray-50/50 dark:bg-gray-900/30">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/30 mb-4">
                <TrendingUp className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                4.7x
              </div>
              <div className="text-lg font-medium text-gray-600 dark:text-gray-400">
                Higher Interview Rate
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                vs traditional applications
              </div>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 mb-4">
                <Clock className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                73%
              </div>
              <div className="text-lg font-medium text-gray-600 dark:text-gray-400">
                Faster Application Process
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                average time reduction
              </div>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 dark:bg-purple-900/30 mb-4">
                <Target className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                92%
              </div>
              <div className="text-lg font-medium text-gray-600 dark:text-gray-400">
                ATS Pass Rate
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                applicant tracking systems
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Product Features */}
      <section className="relative px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white mb-6">
              Everything you need to land your dream job
            </h2>
            <p className="mx-auto max-w-3xl text-xl text-gray-600 dark:text-gray-400">
              Our enterprise-grade platform combines cutting-edge AI with proven
              methodologies to give you an unfair advantage in today's
              competitive job market.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Feature 1 */}
            <div className="space-y-8">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <Brain className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                    AI-Powered Resume Generation
                  </h3>
                  <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                    Generate ATS-optimized resumes that pass through applicant
                    tracking systems and get noticed by hiring managers. Our AI
                    analyzes job descriptions and tailors your experience to
                    match exactly what employers want.
                  </p>
                  <ul className="space-y-2">
                    {[
                      "ATS optimization with 92% pass rate",
                      "Industry-specific keyword integration",
                      "Professional formatting and design",
                      "Real-time job matching analysis",
                    ].map((feature, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                        <span className="text-gray-600 dark:text-gray-400">
                          {feature}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Product Mockup */}
            <div className="relative">
              <div className="aspect-[4/3] bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-950/30 dark:to-indigo-950/30 rounded-2xl p-8 border border-gray-200/50 dark:border-gray-800/50">
                <div className="w-full h-full bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6 overflow-hidden">
                  <div className="space-y-3">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
                    <div className="h-6 bg-blue-200 dark:bg-blue-800 rounded w-2/3"></div>
                    <div className="space-y-2">
                      <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-full"></div>
                      <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-4/5"></div>
                      <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-3/4"></div>
                    </div>
                    <div className="pt-4">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="h-8 bg-emerald-100 dark:bg-emerald-900/30 rounded"></div>
                        <div className="h-8 bg-blue-100 dark:bg-blue-900/30 rounded"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mt-24">
            {/* Product Mockup */}
            <div className="relative order-2 lg:order-1">
              <div className="aspect-[4/3] bg-gradient-to-br from-purple-50 to-pink-100 dark:from-purple-950/30 dark:to-pink-950/30 rounded-2xl p-8 border border-gray-200/50 dark:border-gray-800/50">
                <div className="w-full h-full bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-purple-500 rounded-full"></div>
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
                    </div>
                    <div className="space-y-3">
                      <div className="h-5 bg-purple-200 dark:bg-purple-800 rounded w-3/4"></div>
                      <div className="space-y-2">
                        <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-full"></div>
                        <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-5/6"></div>
                        <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-4/5"></div>
                        <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-full"></div>
                      </div>
                    </div>
                    <div className="pt-2 flex gap-2">
                      <div className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 rounded-full text-xs">
                        AI-Generated
                      </div>
                      <div className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 rounded-full text-xs">
                        Optimized
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-8 order-1 lg:order-2">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                    Compelling Cover Letters
                  </h3>
                  <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                    Create personalized cover letters that tell your story and
                    connect with hiring managers. Our AI analyzes company
                    culture and job requirements to craft compelling narratives
                    that showcase your unique value proposition.
                  </p>
                  <ul className="space-y-2">
                    {[
                      "Company-specific personalization",
                      "Industry tone and language matching",
                      "Compelling storytelling framework",
                      "Achievement highlighting and quantification",
                    ].map((feature, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                        <span className="text-gray-600 dark:text-gray-400">
                          {feature}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 3 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mt-24">
            <div className="space-y-8">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                    Expert Interview Coaching
                  </h3>
                  <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                    Practice with AI-powered interview simulations that adapt to
                    your industry and role. Get real-time feedback on your
                    responses, body language, and communication style to ensure
                    you're fully prepared for any interview scenario.
                  </p>
                  <ul className="space-y-2">
                    {[
                      "Role-specific practice questions",
                      "Real-time AI feedback and scoring",
                      "Voice and video analysis",
                      "Behavioral interview preparation",
                    ].map((feature, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                        <span className="text-gray-600 dark:text-gray-400">
                          {feature}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Product Mockup */}
            <div className="relative">
              <div className="aspect-[4/3] bg-gradient-to-br from-emerald-50 to-teal-100 dark:from-emerald-950/30 dark:to-teal-950/30 rounded-2xl p-8 border border-gray-200/50 dark:border-gray-800/50">
                <div className="w-full h-full bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                      <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                      <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                    </div>
                    <div className="space-y-3">
                      <div className="h-5 bg-emerald-200 dark:bg-emerald-800 rounded w-4/5"></div>
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2">
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                      </div>
                      <div className="flex gap-2">
                        <div className="flex-1 h-8 bg-emerald-100 dark:bg-emerald-900/30 rounded flex items-center justify-center">
                          <Mic className="w-4 h-4 text-emerald-600" />
                        </div>
                        <div className="w-16 h-8 bg-blue-100 dark:bg-blue-900/30 rounded flex items-center justify-center text-xs">
                          9.2/10
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enterprise Features */}
      <section className="relative px-6 py-24 bg-gray-50/50 dark:bg-gray-900/30">
        <div className="mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white mb-6">
              Enterprise-grade security and reliability
            </h2>
            <p className="mx-auto max-w-3xl text-xl text-gray-600 dark:text-gray-400">
              Built for scale with the security and compliance features that
              enterprises demand.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: <Lock className="w-6 h-6" />,
                title: "SOC 2 Type II",
                description:
                  "Comprehensive security audit and compliance certification",
              },
              {
                icon: <Globe className="w-6 h-6" />,
                title: "Global Infrastructure",
                description: "99.9% uptime SLA with multi-region deployment",
              },
              {
                icon: <RefreshCw className="w-6 h-6" />,
                title: "Real-time Sync",
                description: "Instant updates across all your job applications",
              },
              {
                icon: <Layers className="w-6 h-6" />,
                title: "Enterprise Integrations",
                description:
                  "Seamless integration with existing HR and ATS systems",
              },
            ].map((feature, i) => (
              <div key={i} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white dark:bg-gray-800 shadow-lg mb-4 border border-gray-200/50 dark:border-gray-700/50">
                  <div className="text-gray-600 dark:text-gray-400">
                    {feature.icon}
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonial */}
      <section className="relative px-6 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <div className="relative">
            <svg
              className="absolute -top-8 -left-8 w-16 h-16 text-gray-200 dark:text-gray-800"
              fill="currentColor"
              viewBox="0 0 32 32"
            >
              <path d="M9.352 4.8a7.2 7.2 0 0 1 7.2 7.2v7.2a7.2 7.2 0 0 1-7.2 7.2 7.2 7.2 0 0 1-7.2-7.2V12a7.2 7.2 0 0 1 7.2-7.2Zm13.6 0a7.2 7.2 0 0 1 7.2 7.2v7.2a7.2 7.2 0 0 1-7.2 7.2 7.2 7.2 0 0 1-7.2-7.2V12a7.2 7.2 0 0 1 7.2-7.2Z" />
            </svg>

            <blockquote className="text-2xl sm:text-3xl font-medium text-gray-900 dark:text-white leading-relaxed mb-8">
              "JobHackerBot completely transformed my job search. I went from
              getting zero responses to landing interviews at Google, Meta, and
              Microsoft. The AI-generated resumes are incredible."
            </blockquote>

            <div className="flex items-center justify-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">SK</span>
              </div>
              <div className="text-left">
                <div className="font-semibold text-gray-900 dark:text-white">
                  Sarah Kim
                </div>
                <div className="text-gray-600 dark:text-gray-400">
                  Senior Software Engineer, Google
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative px-6 py-24 bg-gray-900 dark:bg-black">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
            Ready to accelerate your career?
          </h2>
          <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto">
            Join thousands of professionals who've transformed their careers
            with AI-powered job applications.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8">
            <SignInButton mode="modal">
              <Button
                size="lg"
                className="h-14 px-8 text-lg font-semibold bg-white hover:bg-gray-100 text-gray-900 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Start Your Success Story
                <Rocket className="ml-2 h-5 w-5" />
              </Button>
            </SignInButton>
          </div>

          <div className="flex items-center justify-center gap-8 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Free to start</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Setup in 60 seconds</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
