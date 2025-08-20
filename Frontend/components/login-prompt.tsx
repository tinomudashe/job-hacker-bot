"use client";

import { SignInButton } from "@clerk/nextjs";
import {
  ArrowDown,
  ArrowRight,
  Award,
  Brain,
  CheckCircle,
  Clock,
  FileText,
  MessageSquare,
  Shield,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";
import Image from "next/image";
import * as React from "react";
import { Button } from "./ui/button";
import { Logo } from "./ui/logo";
import { ThemedImage } from "./ui/themed-image";

export function LoginPrompt() {

  return (
    <>
      <div className="relative min-h-screen bg-white dark:bg-black overflow-hidden">
        {/* Sophisticated Background Grid with Animation */}
        <div className="fixed inset-0 top-0 left-0 right-0 bottom-0 bg-[linear-gradient(to_right,#f1f5f9_1px,transparent_1px),linear-gradient(to_bottom,#f1f5f9_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_110%)] dark:bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] animate-grid-float" />

        {/* Hero Section */}
        <section className="relative px-6 pt-12 pb-16 sm:pt-16 sm:pb-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            {/* Logo Section with Animation */}
            <div className="flex justify-center mb-10 animate-float">
              <Logo size="lg" />
            </div>

            {/* Main Headline with Animation */}
            <div className="text-center animate-fade-in-up">
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900 dark:text-white mb-6">
                The AI-Powered
                <br />
                <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent animate-text-shimmer">
                  Career Platform
                </span>
              </h1>

              <p className="mx-auto max-w-3xl text-lg sm:text-xl text-gray-600 dark:text-gray-400 leading-relaxed mb-12 animate-fade-in-up animation-delay-200">
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  Beat the bots. Get the job.
                </strong>{" "}
                JobHackerBot uses{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  enterprise-grade AI
                </strong>{" "}
                to level the playing field. Generate{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  ATS-optimized resumes
                </strong>
                , craft{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  compelling cover letters
                </strong>
                , and train with{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  smart interview coaching
                </strong>
                . Everything you need to{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  win
                </strong>{" "}
                in today's{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  bot-filtered hiring
                </strong>
                .
              </p>

              {/* CTA Section with Animation */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-fade-in-up animation-delay-400">
                <SignInButton mode="modal">
                  <Button
                    size="lg"
                    className="h-14 px-8 text-lg font-semibold bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105 transform"
                  >
                    Start Building Your Future
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </SignInButton>

                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => {
                    const element = document.getElementById('features-section');
                    element?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="h-14 px-8 text-lg font-semibold bg-white dark:bg-gray-900 border-2 border-gray-900 dark:border-white text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl transition-all duration-300 group shadow-md hover:shadow-lg overflow-hidden"
                >
                  <span className="relative flex items-center justify-center">
                    <span>Explore Features</span>
                    <ArrowDown className="ml-2 h-5 w-5 transition-transform duration-300 group-hover:translate-y-0.5" />
                  </span>
                </Button>
              </div>

              {/* Trust Indicators with Stagger Animation */}
              <div className="flex items-center justify-center gap-8 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-2 animate-fade-in-up animation-delay-600 hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-300 cursor-default">
                  <Shield className="w-4 h-4 text-emerald-500" />
                  <span>SOC 2 Compliant</span>
                </div>
                <div className="flex items-center gap-2 animate-fade-in-up animation-delay-700 hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-300 cursor-default">
                  <Users className="w-4 h-4 text-blue-500" />
                  <span>1K+ Professionals</span>
                </div>
                <div className="flex items-center gap-2 animate-fade-in-up animation-delay-800 hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-300 cursor-default">
                  <Award className="w-4 h-4 text-amber-500" />
                  <span>99.9% Uptime SLA</span>
                </div>
              </div>
            </div>
          </div>
        </section>


        {/* Key Metrics with Animation */}
        <section className="relative px-6 py-16 bg-gray-50/50 dark:bg-gray-900/30">
          <div className="mx-auto max-w-7xl">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
              <div className="text-center animate-fade-in-up">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/30 mb-4 hover:scale-110 transition-transform duration-300">
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

              <div className="text-center animate-fade-in-up animation-delay-200">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 mb-4 hover:scale-110 transition-transform duration-300">
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

              <div className="text-center animate-fade-in-up animation-delay-400">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 dark:bg-purple-900/30 mb-4 hover:scale-110 transition-transform duration-300">
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
        <section id="features-section" className="relative px-6 py-24">
          <div className="mx-auto max-w-7xl">
            <div className="text-center mb-16">
              <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white mb-6">
                Everything you need to land your dream job
              </h2>
              <p className="mx-auto max-w-3xl text-xl text-gray-600 dark:text-gray-400">
                Our enterprise-grade platform combines cutting-edge AI with
                proven methodologies to give you an unfair advantage in today's
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
                      tracking systems and get noticed by hiring managers. Our
                      AI analyzes job descriptions and tailors your experience
                      to match exactly what employers want.
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
                <div className="aspect-[16/9] bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-950/30 dark:to-indigo-950/30 rounded-2xl p-4 sm:p-6 border border-gray-200/50 dark:border-gray-800/50 flex items-center justify-center">
                  <ThemedImage
                    lightSrc="/mockups/resume-light.png"
                    darkSrc="/mockups/resume-dark.png"
                    alt="AI-Powered Resume Generation Mockup"
                    width={1280}
                    height={720}
                  />
                </div>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mt-24">
              {/* Product Mockup */}
              <div className="relative order-2 lg:order-1">
                <div className="aspect-[16/9] bg-gradient-to-br from-purple-50 to-pink-100 dark:from-purple-950/30 dark:to-pink-950/30 rounded-2xl p-4 sm:p-6 border border-gray-200/50 dark:border-gray-800/50 flex items-center justify-center">
                  <ThemedImage
                    lightSrc="/mockups/cover-letter-light.png"
                    darkSrc="/mockups/cover-letter-dark.png"
                    alt="Compelling Cover Letters Mockup"
                    width={1280}
                    height={720}
                  />
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
                      culture and job requirements to craft compelling
                      narratives that showcase your unique value proposition.
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
                      Practice with AI-powered interview simulations that adapt
                      to your industry and role. Get real-time feedback on your
                      responses, body language, and communication style to
                      ensure you're fully prepared for any interview scenario.
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
                <div className="aspect-[16/9] bg-gradient-to-br from-emerald-50 to-teal-100 dark:from-emerald-950/30 dark:to-teal-950/30 rounded-2xl p-4 sm:p-6 border border-gray-200/50 dark:border-gray-800/50 flex items-center justify-center">
                  <ThemedImage
                    lightSrc="/mockups/interview-light.png"
                    darkSrc="/mockups/interview-dark.png"
                    alt="Expert Interview Coaching Mockup"
                    width={1280}
                    height={720}
                  />
                </div>
              </div>
            </div>

            {/* Feature 4 - CV Review */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mt-24">
              {/* Product Mockup */}
              <div className="relative order-2 lg:order-1">
                <div className="aspect-[16/9] bg-gradient-to-br from-rose-50 to-red-100 dark:from-rose-950/30 dark:to-red-950/30 rounded-2xl p-4 sm:p-6 border border-gray-200/50 dark:border-gray-800/50 flex items-center justify-center">
                  <ThemedImage
                    lightSrc="/mockups/cv-review-light.png"
                    darkSrc="/mockups/cv-review-dark.png"
                    alt="ATS CV Review Mockup"
                    width={1280}
                    height={720}
                  />
                </div>
              </div>

              <div className="space-y-8 order-1 lg:order-2">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center">
                    <Shield className="w-6 h-6 text-rose-600 dark:text-rose-400" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                      ATS CV Review & Scoring
                    </h3>
                    <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                      Get instant feedback on your CV's ATS compatibility with our 
                      advanced scoring system. Identify gaps, optimize keywords, and 
                      ensure your CV passes through applicant tracking systems before 
                      you apply.
                    </p>
                    <ul className="space-y-2">
                      {[
                        "Instant ATS compatibility score (0-100)",
                        "Keyword gap analysis and suggestions",
                        "Formatting issues detection and fixes",
                        "Industry-specific optimization tips",
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

            {/* Feature 5 - Professional Email */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mt-24">
              <div className="space-y-8">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                      Professional Email Outreach
                    </h3>
                    <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                      Craft compelling outreach emails that get responses. Our AI 
                      creates personalized messages that stand out in crowded inboxes,
                      whether you're following up on applications, networking with 
                      professionals, or reaching out to recruiters.
                    </p>
                    <ul className="space-y-2">
                      {[
                        "Personalized subject lines that get opened",
                        "Professional tone matching for each company",
                        "Follow-up sequences that drive responses",
                        "Templates for networking and cold outreach",
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
                <div className="aspect-[16/9] bg-gradient-to-br from-indigo-50 to-blue-100 dark:from-indigo-950/30 dark:to-blue-950/30 rounded-2xl p-4 sm:p-6 border border-gray-200/50 dark:border-gray-800/50 flex items-center justify-center">
                  <ThemedImage
                    lightSrc="/mockups/email-light.png"
                    darkSrc="/mockups/email-dark.png"
                    alt="Professional Email Outreach Mockup"
                    width={1280}
                    height={720}
                  />
                </div>
              </div>
            </div>

            {/* Feature 6 - Smart Job Search */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mt-24">
              {/* Product Mockup */}
              <div className="relative order-2 lg:order-1">
                <div className="aspect-[16/9] bg-gradient-to-br from-amber-50 to-orange-100 dark:from-amber-950/30 dark:to-orange-950/30 rounded-2xl p-4 sm:p-6 border border-gray-200/50 dark:border-gray-800/50 flex items-center justify-center">
                  <ThemedImage
                    lightSrc="/mockups/jobs-light.png"
                    darkSrc="/mockups/jobs-dark.png"
                    alt="Smart Job Discovery Mockup"
                    width={1280}
                    height={720}
                  />
                </div>
              </div>

              <div className="space-y-8 order-1 lg:order-2">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <Target className="w-6 h-6 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                      Smart Job Discovery
                    </h3>
                    <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                      Find perfect-fit opportunities with AI-powered job matching.
                      Our intelligent search analyzes your skills and preferences to 
                      surface roles you're most likely to succeed in, saving hours 
                      of manual searching.
                    </p>
                    <ul className="space-y-2">
                      {[
                        "AI-matched jobs based on your profile",
                        "Real-time alerts for new opportunities",
                        "Salary insights and company culture data",
                        "One-click application with tailored materials",
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
          </div>
        </section>

        {/* Testimonial */}
        <section className="relative px-6 py-24 bg-gray-50/50 dark:bg-gray-900/30">
          <div className="mx-auto max-w-4xl text-center">
            <div className="flex justify-center mb-4">
              <Image
                src="/oliwia.JPG"
                alt="Oliwia Kościółek"
                width={64}
                height={64}
                className="rounded-full"
              />
            </div>
            <blockquote className="text-xl sm:text-2xl font-medium text-gray-900 dark:text-white leading-relaxed">
              <p>
                “I genuinely believe in this product and how it works.
                JobHackerBot helped me present myself more clearly and
                confidently in applications. It’s not just about automation – it
                actually understands how to highlight your strengths.”
              </p>
            </blockquote>
            <figcaption className="mt-8">
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                Oliwia Kościółek
              </div>
              <div className="text-gray-600 dark:text-gray-400">
                Graduate in English Linguistics
              </div>
            </figcaption>
          </div>
        </section>

        {/* Final CTA */}
        <section className="relative px-6 pt-16 pb-24 border-t border-gray-200/50 dark:border-gray-800/50">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-white">
              Ready to accelerate your career?
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-lg text-gray-600 dark:text-gray-400">
              Join thousands of professionals who've transformed their careers
              with AI-powered job applications.
            </p>
            <div className="mt-10 flex justify-center">
              <SignInButton mode="modal">
                <Button
                  size="lg"
                  className="h-14 px-8 text-lg font-semibold bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105 transform"
                >
                  Get Started
                </Button>
              </SignInButton>
            </div>
            <div className="mt-8 flex justify-center items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span>1-day free trial</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span>Just $2.99/week after</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span>Setup in 60 seconds</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="relative z-10 bg-white dark:bg-black border-t border-gray-200/50 dark:border-gray-800/50">
        <div className="mx-auto max-w-7xl py-8 px-6 text-sm text-gray-500 dark:text-gray-400">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-6 text-center sm:text-left">
            <p>&copy; 2025 JobHackerBot. All rights reserved.</p>
            <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
              <a
                href="mailto:bot@jobhackerbot.com"
                className="hover:text-gray-900 dark:hover:text-white"
              >
                Support: bot@jobhackerbot.com
              </a>
              <a
                href="/JobHackerBot_Terms_Conditions.pdf"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 dark:hover:text-white"
              >
                Privacy
              </a>
              <a
                href="/JobHackerBot_Terms_Conditions.pdf"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 dark:hover:text-white"
              >
                Terms & Conditions
              </a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
