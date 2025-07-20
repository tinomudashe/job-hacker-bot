"use client";

import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { SignInButton } from "@clerk/nextjs";
import {
  ArrowRight,
  Award,
  Brain,
  CheckCircle,
  Clock,
  FileText,
  MessageSquare,
  PlayCircle,
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

const taglines = [
  "JobHackerBot: Level the playing field — automate your way in.",
  "JobHackerBot: Your AI wingman for cracking the hiring code.",
  "JobHackerBot: Let your own bot do the hard part.",
  "JobHackerBot: Smarter job applications, powered by AI.",
  "JobHackerBot: Turn the tables on applicant tracking systems.",
];

export function LoginPrompt() {
  const [currentTaglineIndex, setCurrentTaglineIndex] = React.useState(0);
  const [isFading, setIsFading] = React.useState(false);

  React.useEffect(() => {
    const intervalId = setInterval(() => {
      setIsFading(true);
      // Wait for the fade-out transition to complete before changing the text
      setTimeout(() => {
        setCurrentTaglineIndex(
          (prevIndex) => (prevIndex + 1) % taglines.length
        );
        setIsFading(false);
      }, 500); // This duration must match the CSS transition duration
    }, 4000); // Change text every 4 seconds

    return () => clearInterval(intervalId); // Cleanup on component unmount
  }, []);

  return (
    <>
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
                  <span
                    className={`transition-opacity duration-500 ${
                      isFading ? "opacity-0" : "opacity-100"
                    }`}
                  >
                    {taglines[currentTaglineIndex]}
                  </span>
                </span>
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

              <p className="mx-auto max-w-3xl text-lg sm:text-xl text-gray-600 dark:text-gray-400 leading-relaxed mb-12">
                We believe you deserve the job, not the algorithm. JobHackerBot
                uses{" "}
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
                —all designed to help{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  real humans win
                </strong>{" "}
                in an{" "}
                <strong className="font-semibold text-gray-800 dark:text-gray-200">
                  AI-filtered world
                </strong>
                .
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

                <Dialog>
                  <DialogTrigger asChild>
                    <Button
                      variant="outline"
                      size="lg"
                      className="h-14 px-8 text-lg font-semibold border-2 border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 rounded-xl transition-all duration-200"
                    >
                      <PlayCircle className="mr-2 h-5 w-5" />
                      Watch Demo
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="w-[95vw] max-w-4xl p-0 bg-transparent border-none shadow-none">
                    {/* Browser Mockup Frame */}
                    <div className="bg-gray-800/50 dark:bg-black/50 backdrop-blur-sm rounded-lg overflow-hidden border border-white/10 shadow-2xl">
                      {/* Browser Header */}
                      <div className="h-10 flex items-center px-4 bg-gray-200/80 dark:bg-gray-900/80">
                        <div className="flex space-x-2">
                          <div className="w-3 h-3 rounded-full bg-red-500"></div>
                          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                          <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        </div>
                      </div>
                      {/* Video Content */}
                      <div className="aspect-video">
                        <video
                          className="w-full h-full"
                          src="/jobhackerbot-demo.mp4"
                          controls
                          autoPlay
                          muted
                          playsInline
                        />
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>

              {/* Trust Indicators */}
              <div className="flex items-center justify-center gap-8 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-emerald-500" />
                  <span>SOC 2 Compliant</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-blue-500" />
                  <span>1K+ Professionals</span>
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
              TRUSTED BY PROFESSIONALS WHO ASPIRE TO WORK AT
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-8 items-center opacity-70">
              {[
                { name: "Google", logo: "/google-g-logo-only.svg" },
                { name: "Meta", logo: "/meta-3.svg" },
                { name: "Visa", logo: "/visa-10.svg" },
                { name: "Coca-Cola", logo: "/coca-cola-2021.svg" },
                { name: "Netflix", logo: "/netflix-logo-icon.svg" },
              ].map((company, i) => (
                <div key={i} className="flex justify-center">
                  <Image
                    src={company.logo}
                    alt={company.name}
                    width={120}
                    height={40}
                    className="object-contain"
                  />
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
                  className="h-14 px-8 text-lg font-semibold bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 dark:text-gray-900 text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
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
