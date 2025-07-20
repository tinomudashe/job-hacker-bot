"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/lib/toast";
import { useAuth } from "@clerk/nextjs";
import {
  Award,
  BarChart3,
  Brain,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  FileText,
  Mic,
  RotateCcw,
  Sparkles,
  Target,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import * as React from "react";

interface Flashcard {
  question: string;
  answer: string;
}

interface FlashcardAnswer {
  questionIndex: number;
  userAnswer: string;
  feedback?: {
    feedback: string;
    is_correct: boolean;
    tone_score: number;
    correctness_score: number;
    confidence_score: number;
    overall_score: number;
    improvement_tips: string;
  };
  answerMethod: "text" | "voice";
}

interface FlashcardDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jobTitle?: string;
  companyName?: string;
  interviewContent?: string;
  preGeneratedFlashcards?: Array<{ question: string; answer: string }>;
}

export function FlashcardDialog({
  open,
  onOpenChange,
  jobTitle = "",
  companyName = "",
  interviewContent = "",
  preGeneratedFlashcards = undefined,
}: FlashcardDialogProps) {
  const { getToken } = useAuth();

  // Core state
  const [flashcards, setFlashcards] = React.useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [mode, setMode] = React.useState<"setup" | "practice" | "review">(
    preGeneratedFlashcards && preGeneratedFlashcards.length > 0
      ? "practice"
      : "setup"
  );

  // Setup state
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [customJobTitle, setCustomJobTitle] = React.useState(jobTitle);
  const [customCompany, setCustomCompany] = React.useState(companyName);
  const [flashcardCount, setFlashcardCount] = React.useState(10);

  // Practice state
  const [showAnswer, setShowAnswer] = React.useState(false);
  const [userAnswer, setUserAnswer] = React.useState("");
  const [answers, setAnswers] = React.useState<FlashcardAnswer[]>([]);
  const [isEvaluating, setIsEvaluating] = React.useState(false);
  const [currentAnswerMethod, setCurrentAnswerMethod] = React.useState<
    "text" | "voice"
  >("text");

  // Voice recording state
  const [isRecording, setIsRecording] = React.useState(false);
  const [isTranscribing, setIsTranscribing] = React.useState(false);
  const [mediaRecorder, setMediaRecorder] =
    React.useState<MediaRecorder | null>(null);
  const [audioBlob, setAudioBlob] = React.useState<Blob | null>(null);
  const [recordingDuration, setRecordingDuration] = React.useState(0);
  const [audioPlaying, setAudioPlaying] = React.useState(false);
  const [audioLoading, setAudioLoading] = React.useState(false);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);
  const feedbackRef = React.useRef<HTMLDivElement | null>(null);

  // Feedback section collapse state
  const [feedbackSections, setFeedbackSections] = React.useState({
    scores: true,
    feedback: false,
    tips: false,
    sample: false,
  });

  const currentFlashcard = flashcards[currentIndex];
  const currentAnswer = answers.find((a) => a.questionIndex === currentIndex);
  const isAnswered = !!currentAnswer;

  // Initialize with pre-generated flashcards if available
  React.useEffect(() => {
    if (preGeneratedFlashcards && preGeneratedFlashcards.length > 0) {
      console.log(
        "🧠 Using pre-generated flashcards:",
        preGeneratedFlashcards.length
      );
      setFlashcards(preGeneratedFlashcards);
      setCurrentIndex(0);
      setAnswers([]);
      setMode("practice");
    }
  }, [preGeneratedFlashcards]);

  // Recording timer
  React.useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } else {
      setRecordingDuration(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const handleTranscription = async (blob: Blob) => {
    setIsTranscribing(true);
    setUserAnswer("");
    try {
      const token = await getToken();
      if (!token) {
        toast.error("Please sign in to transcribe your answer.");
        return;
      }

      const formData = new FormData();
      formData.append("file", blob, "audio.webm");
      formData.append(
        "api_key",
        process.env.NEXT_PUBLIC_GOOGLE_TTS_API_KEY || ""
      );

      const response = await fetch("/api/stt", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to transcribe audio.");
      }

      const result = await response.json();
      setUserAnswer(result.transcript);
      setCurrentAnswerMethod("text");
      toast.success("Your answer has been transcribed for review.");
    } catch (error) {
      console.error("Transcription error:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to transcribe audio."
      );
    } finally {
      setIsTranscribing(false);
    }
  };

  const playTextAsSpeech = async (text: string) => {
    if (audioLoading || audioPlaying) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        setAudioPlaying(false);
      }
      return;
    }

    setAudioLoading(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          text,
          api_key: process.env.NEXT_PUBLIC_GOOGLE_TTS_API_KEY,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch audio");
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
        setAudioPlaying(true);
      }
    } catch (error) {
      console.error("Error playing text as speech:", error);
      toast.error("Failed to play audio. Please try again.");
    } finally {
      setAudioLoading(false);
    }
  };

  React.useEffect(() => {
    audioRef.current = new Audio();
    audioRef.current.onended = () => setAudioPlaying(false);

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }
    };
  }, []);

  const generateFlashcards = async () => {
    // If we have pre-generated flashcards, use them directly
    if (preGeneratedFlashcards && preGeneratedFlashcards.length > 0) {
      setFlashcards(preGeneratedFlashcards);
      setCurrentIndex(0);
      setMode("practice");
      setAnswers([]);
      toast.success(
        `Using ${preGeneratedFlashcards.length} personalized interview questions!`,
        { description: "Answer each question to get AI feedback" }
      );
      return;
    }

    if (!customJobTitle.trim()) {
      toast.error("Please enter a job title to generate flashcards");
      return;
    }

    setIsGenerating(true);

    try {
      const token = await getToken();
      if (!token) {
        toast.error("Please sign in to generate flashcards");
        return;
      }

      let sourceContent = interviewContent;
      if (!sourceContent && customJobTitle) {
        sourceContent = `Interview preparation for ${customJobTitle}${
          customCompany ? ` at ${customCompany}` : ""
        }`;
      }

      const response = await fetch("/api/flashcards/generate", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source_type: "job_description",
          content: sourceContent,
          count: flashcardCount,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate flashcards");
      }

      const data = await response.json();
      setFlashcards(data.flashcards);
      setCurrentIndex(0);
      setMode("practice");
      setAnswers([]);

      toast.success(
        `Generated ${data.flashcards.length} interview flashcards!`,
        { description: "Answer each question to get AI feedback" }
      );
    } catch (error) {
      console.error("Error generating flashcards:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to generate flashcards"
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        handleTranscription(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setCurrentAnswerMethod("voice");
      setUserAnswer("");
    } catch (error) {
      toast.error("Could not access microphone");
      console.error("Recording error:", error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  };

  const submitAnswer = async () => {
    if (!userAnswer.trim()) {
      toast.error("Please provide an answer");
      return;
    }

    setIsEvaluating(true);

    try {
      const token = await getToken();
      if (!token) {
        toast.error("Please sign in to get feedback");
        return;
      }

      const formData = new FormData();
      formData.append("question", currentFlashcard.question);
      formData.append("text_answer", userAnswer);

      const response = await fetch("/api/flashcards/feedback", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to get feedback");
      }

      const feedback = await response.json();

      const newAnswer: FlashcardAnswer = {
        questionIndex: currentIndex,
        userAnswer: userAnswer,
        feedback,
        answerMethod: "text",
      };

      setAnswers((prev) => [
        ...prev.filter((a) => a.questionIndex !== currentIndex),
        newAnswer,
      ]);
      setShowAnswer(true);

      // Expand only the scores section when new feedback appears
      setFeedbackSections({
        scores: true,
        feedback: false,
        tips: false,
        sample: false,
      });

      // --- UI FIX: Scroll to feedback on mobile after submission ---
      setTimeout(() => {
        if (window.innerWidth < 1024 && feedbackRef.current) {
          feedbackRef.current.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }, 100);

      toast.success("Answer evaluated!", {
        description: `Overall score: ${feedback.overall_score}/10`,
      });
    } catch (error) {
      console.error("Error getting feedback:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to get feedback"
      );
    } finally {
      setIsEvaluating(false);
    }
  };

  const nextCard = () => {
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setShowAnswer(false);
      setUserAnswer("");
      setAudioBlob(null);
      setCurrentAnswerMethod("text");
      // Reset feedback sections for new card
      setFeedbackSections({
        scores: true,
        feedback: false,
        tips: false,
        sample: false,
      });
    } else {
      // All cards completed, go to review
      setMode("review");
    }
  };

  const prevCard = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setShowAnswer(false);
      setUserAnswer("");
      setAudioBlob(null);
      setCurrentAnswerMethod("text");
      // Reset feedback sections for new card
      setFeedbackSections({
        scores: true,
        feedback: false,
        tips: false,
        sample: false,
      });
    }
  };

  const resetPractice = () => {
    setCurrentIndex(0);
    setShowAnswer(false);
    setUserAnswer("");
    setAnswers([]);
    setAudioBlob(null);
    setCurrentAnswerMethod("text");
    setMode("practice");
    // Reset feedback sections
    setFeedbackSections({
      scores: true,
      feedback: false,
      tips: false,
      sample: false,
    });
    toast.success("Practice session reset");
  };

  const getOverallStats = () => {
    if (answers.length === 0) return null;

    const totalScore = answers.reduce(
      (sum, a) => sum + (a.feedback?.overall_score || 0),
      0
    );
    const avgScore = totalScore / answers.length;
    const avgTone =
      answers.reduce((sum, a) => sum + (a.feedback?.tone_score || 0), 0) /
      answers.length;
    const avgCorrectness =
      answers.reduce(
        (sum, a) => sum + (a.feedback?.correctness_score || 0),
        0
      ) / answers.length;
    const avgConfidence =
      answers.reduce((sum, a) => sum + (a.feedback?.confidence_score || 0), 0) /
      answers.length;

    return {
      totalAnswered: answers.length,
      avgScore: Math.round(avgScore * 10) / 10,
      avgTone: Math.round(avgTone * 10) / 10,
      avgCorrectness: Math.round(avgCorrectness * 10) / 10,
      avgConfidence: Math.round(avgConfidence * 10) / 10,
    };
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const toggleFeedbackSection = (section: keyof typeof feedbackSections) => {
    setFeedbackSections((prev) => {
      // If clicking the same section that's already open, close it
      if (prev[section]) {
        return {
          scores: false,
          feedback: false,
          tips: false,
          sample: false,
        };
      }

      // Otherwise, close all sections and open only the clicked one
      return {
        scores: section === "scores",
        feedback: section === "feedback",
        tips: section === "tips",
        sample: section === "sample",
      };
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        hideCloseButton // UI FIX: Use the new prop to hide the default close button.
        className="max-w-[95vw] sm:max-w-6xl max-h-[92vh] sm:max-h-[95vh] w-[95vw] h-[92vh] sm:w-[95vw] sm:h-[95vh] flex flex-col !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 !border !border-gray-200 dark:!border-white/8 shadow-2xl rounded-2xl sm:rounded-3xl overflow-hidden p-0"
      >
        {/* --- UI UPDATE: Made Header Responsive --- */}
        <div className="flex-shrink-0 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 !border-b !border-gray-200 dark:!border-white/8 p-3 sm:p-5 relative z-10">
          <div className="flex items-center justify-between gap-3 sm:gap-4">
            {/* Left: Document Type */}
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl !bg-blue-100 !border !border-blue-200 shadow-lg flex items-center justify-center backdrop-blur-sm dark:!bg-blue-500/20 dark:!border-blue-500/40 flex-shrink-0">
                <Brain className="h-5 w-5 sm:h-6 sm:w-6 !text-blue-600 dark:!text-blue-400" />
              </div>
              <div className="min-w-0">
                <DialogTitle className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-gray-100 leading-tight sm:leading-normal">
                  Interview Flashcards
                </DialogTitle>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mt-0.5 sm:-mt-0.5 leading-tight sm:leading-normal">
                  Practice with AI-powered feedback
                </p>
              </div>
            </div>

            {/* Right: Status and Actions */}
            <div className="flex flex-col items-end gap-2">
              <div className="flex items-center gap-2 sm:gap-3">
                {mode === "practice" && (
                  <Badge
                    variant="outline"
                    // --- UI FIX: Hide the badge on mobile, show on larger screens ---
                    className="hidden sm:flex text-xs sm:text-sm bg-white/80 border-gray-300/60 backdrop-blur-sm text-gray-700 dark:bg-gray-800/80 dark:border-gray-600/60 dark:text-gray-300 font-medium"
                  >
                    {currentIndex + 1} of {flashcards.length}
                  </Badge>
                )}
                {mode === "review" && (
                  <Badge
                    variant="outline"
                    className="text-xs sm:text-sm bg-muted text-foreground border border-border font-medium"
                  >
                    Review Results
                  </Badge>
                )}
                {preGeneratedFlashcards &&
                  preGeneratedFlashcards.length > 0 && (
                    <Badge
                      variant="outline"
                      className="hidden sm:flex bg-muted text-foreground border border-border font-medium"
                    >
                      <Sparkles className="h-3 w-3 mr-1" />
                      AI Generated
                    </Badge>
                  )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onOpenChange(false)}
                  className="h-9 w-9 sm:h-10 sm:w-10 rounded-lg sm:rounded-xl transition-all duration-300 hover:scale-105 !bg-gray-100 !border !border-gray-200 hover:!bg-gray-200 dark:!bg-background/60 dark:!border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:!bg-background/80 ml-2 flex-shrink-0"
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Close</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
        {/* --- END UI UPDATE --- */}

        {mode === "setup" && (
          /* Setup/Generation View */
          <div className="flex-1 overflow-auto p-3 sm:p-6">
            {/* --- UI UPDATE: Made Setup View Responsive --- */}
            <div className="max-w-4xl mx-auto space-y-6 sm:space-y-8">
              {preGeneratedFlashcards && preGeneratedFlashcards.length > 0 ? (
                /* Questions Already Available */
                <div className="text-center py-8 sm:py-12 px-4 sm:px-6">
                  <div className="relative w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6 sm:mb-8">
                    <div className="w-full h-full bg-primary rounded-2xl sm:rounded-3xl flex items-center justify-center shadow-2xl transform hover:scale-105 transition-transform duration-300">
                      <Brain className="h-10 w-10 sm:h-12 sm:w-12 text-primary-foreground drop-shadow-lg" />
                    </div>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-bold mb-3 sm:mb-4 text-gray-900 dark:text-gray-100">
                    Questions Ready!
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed text-base sm:text-lg">
                    Your personalized interview questions are ready.
                  </p>
                  <div className="mt-6 sm:mt-8 p-4 sm:p-6 !bg-white dark:!bg-background/60 backdrop-blur-md rounded-xl !border !border-gray-200 dark:!border-white/8 shadow-lg">
                    <div className="flex items-center justify-center gap-3 mb-3 sm:mb-4">
                      <div className="w-7 h-7 sm:w-8 sm:h-8 bg-primary rounded-lg sm:rounded-xl flex items-center justify-center shadow-md">
                        <Check className="h-4 w-4 sm:h-4 sm:w-4 text-primary-foreground" />
                      </div>
                      <p className="text-gray-900 dark:text-gray-100 font-bold text-base sm:text-lg">
                        {preGeneratedFlashcards.length} Personalized Questions
                      </p>
                    </div>
                    <p className="text-gray-700 dark:text-gray-300 text-sm sm:text-base leading-relaxed">
                      Questions include CV-specific scenarios and role-specific
                      challenges.
                    </p>
                  </div>
                  <Button
                    onClick={() => setMode("practice")}
                    size="lg"
                    className="mt-6 sm:mt-8 bg-primary hover:bg-primary/90 text-primary-foreground px-8 sm:px-10 py-3 sm:py-4 rounded-xl font-bold text-base sm:text-lg transition-all duration-300 hover:scale-105 hover:shadow-lg transform active:scale-95"
                  >
                    <Brain className="h-5 w-5 sm:h-6 sm:w-6 mr-3" />
                    Start Practice
                  </Button>
                </div>
              ) : (
                /* Standard Setup View */
                <div className="text-center py-8 sm:py-12 px-4 sm:px-6">
                  <div className="relative w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6 sm:mb-8">
                    <div className="w-full h-full bg-primary rounded-2xl sm:rounded-3xl flex items-center justify-center shadow-2xl transform hover:scale-105 transition-transform duration-300">
                      <Brain className="h-10 w-10 sm:h-12 sm:w-12 text-primary-foreground drop-shadow-lg" />
                    </div>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-bold mb-3 sm:mb-4 text-gray-900 dark:text-gray-100">
                    Flashcard Practice
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed text-base sm:text-lg">
                    Generate questions and practice with AI-powered feedback.
                  </p>
                </div>
              )}

              {(!preGeneratedFlashcards ||
                preGeneratedFlashcards.length === 0) && (
                <>
                  <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-xl p-4 sm:p-8 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <div className="space-y-6 sm:space-y-8">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
                        <div className="space-y-2 sm:space-y-3">
                          <Label
                            htmlFor="job-title"
                            className="text-sm font-semibold text-gray-900 dark:text-gray-100"
                          >
                            Job Title *
                          </Label>
                          <Input
                            id="job-title"
                            value={customJobTitle}
                            onChange={(e) => setCustomJobTitle(e.target.value)}
                            placeholder="e.g., Senior Software Engineer"
                            className="bg-white/80 border-gray-300/60 backdrop-blur-sm hover:bg-white/95 hover:border-gray-400/70 focus:bg-white dark:bg-transparent dark:border-gray-600/60 dark:hover:border-gray-500/70"
                          />
                        </div>
                        <div className="space-y-2 sm:space-y-3">
                          <Label
                            htmlFor="company-name"
                            className="text-sm font-semibold text-gray-900 dark:text-gray-100"
                          >
                            Company Name
                          </Label>
                          <Input
                            id="company-name"
                            value={customCompany}
                            onChange={(e) => setCustomCompany(e.target.value)}
                            placeholder="e.g., TechCorp Inc."
                            className="bg-white/80 border-gray-300/60 backdrop-blur-sm hover:bg-white/95 hover:border-gray-400/70 focus:bg-white dark:bg-transparent dark:border-gray-600/60 dark:hover:border-gray-500/70"
                          />
                        </div>
                      </div>
                      <div className="space-y-2 sm:space-y-3">
                        <Label
                          htmlFor="flashcard-count"
                          className="text-sm font-semibold text-gray-900 dark:text-gray-100"
                        >
                          Number of Questions
                        </Label>
                        <div className="flex flex-wrap gap-2">
                          {[5, 10, 15, 20].map((count) => (
                            <Button
                              key={count}
                              variant={
                                flashcardCount === count ? "default" : "outline"
                              }
                              size="sm"
                              onClick={() => setFlashcardCount(count)}
                              className={
                                flashcardCount === count
                                  ? "bg-primary hover:bg-primary/90 text-primary-foreground"
                                  : "bg-white/80 border-gray-300/60 text-gray-700 hover:bg-white/95 hover:border-gray-400/70 dark:bg-transparent dark:border-gray-600/60 dark:text-gray-300 dark:hover:bg-gray-700/50"
                              }
                            >
                              {count}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-center pt-2">
                    <Button
                      onClick={generateFlashcards}
                      disabled={isGenerating || !customJobTitle.trim()}
                      size="lg"
                      className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 sm:px-8 py-3 rounded-xl font-semibold transition-all duration-300 hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 w-full sm:w-auto"
                    >
                      {isGenerating ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white mr-3" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Brain className="h-5 w-5 mr-3" />
                          Generate Questions
                        </>
                      )}
                    </Button>
                  </div>
                </>
              )}
            </div>
            {/* --- END UI UPDATE --- */}
          </div>
        )}

        {mode === "practice" && currentFlashcard && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* 
              --- UI FIX: This container now manages two distinct layouts.
              - Default (mobile): A single scrollable column (overflow-y-auto).
              - Large screens (desktop): A flex-row with internal scrolling managed by its children.
            --- 
            */}
            <div className="flex-1 flex flex-col lg:flex-row overflow-y-auto lg:overflow-hidden">
              {/* Question Section - on desktop, this column scrolls independently */}
              <div className="flex-1 lg:overflow-y-auto p-3 sm:p-4 lg:p-6">
                <div className="max-w-3xl mx-auto space-y-4 sm:space-y-6">
                  {/* Progress Bar */}
                  <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-xl p-3 sm:p-4 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Progress
                      </span>
                      <span className="hidden sm:block text-sm text-gray-600 dark:text-gray-400">
                        {currentIndex + 1} / {flashcards.length}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${
                            ((currentIndex + 1) / flashcards.length) * 100
                          }%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Question Card */}
                  <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <div className="flex items-start gap-3 sm:gap-4 mb-4 sm:mb-6">
                      <div className="w-8 h-8 sm:w-10 sm:h-10 bg-primary rounded-xl flex items-center justify-center shadow-md flex-shrink-0">
                        <ClipboardList className="h-4 w-4 sm:h-5 sm:w-5 text-primary-foreground" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1 sm:mb-2">
                          Interview Question
                        </h3>
                        <p className="text-sm sm:text-base text-gray-700 dark:text-gray-300 leading-relaxed">
                          {currentFlashcard.question}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          playTextAsSpeech(currentFlashcard.question)
                        }
                        disabled={audioLoading}
                        className="p-2 rounded-full transition-colors duration-200 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                        aria-label="Read question aloud"
                      >
                        {audioLoading ? (
                          <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        ) : audioPlaying ? (
                          <VolumeX className="h-5 w-5" />
                        ) : (
                          <Volume2 className="h-5 w-5" />
                        )}
                      </button>
                    </div>

                    {/* Answer Input Options */}
                    <div className="space-y-4">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant={
                            currentAnswerMethod === "text"
                              ? "default"
                              : "outline"
                          }
                          size="sm"
                          onClick={() => setCurrentAnswerMethod("text")}
                          className={
                            currentAnswerMethod === "text"
                              ? "bg-primary text-primary-foreground"
                              : "bg-white/80 border-gray-300/60 text-gray-700 hover:bg-white/95 dark:bg-transparent dark:border-gray-600/60 dark:text-gray-300"
                          }
                        >
                          <FileText className="h-4 w-4 mr-2" />
                          Text Answer
                        </Button>
                        <Button
                          variant={
                            currentAnswerMethod === "voice"
                              ? "default"
                              : "outline"
                          }
                          size="sm"
                          onClick={() => setCurrentAnswerMethod("voice")}
                          className={
                            currentAnswerMethod === "voice"
                              ? "bg-primary text-primary-foreground"
                              : "bg-white/80 border-gray-300/60 text-gray-700 hover:bg-white/95 dark:bg-transparent dark:border-gray-600/60 dark:text-gray-300"
                          }
                        >
                          <Mic className="h-4 w-4 mr-2" />
                          Voice Answer
                        </Button>
                      </div>

                      {/* Text Input */}
                      {currentAnswerMethod === "text" && (
                        <Textarea
                          value={userAnswer}
                          onChange={(e) => setUserAnswer(e.target.value)}
                          placeholder="Type your answer here..."
                          rows={4}
                          className="text-sm sm:text-base bg-white/80 border-gray-300/60 backdrop-blur-sm hover:bg-white/95 hover:border-gray-400/70 focus:bg-white dark:bg-transparent dark:border-gray-600/60 dark:hover:border-gray-500/70"
                        />
                      )}

                      {/* Voice Recording */}
                      {currentAnswerMethod === "voice" && (
                        <div className="space-y-4">
                          <div className="flex items-center justify-center gap-4 p-4 sm:p-6 bg-white/80 dark:bg-transparent rounded-xl border border-gray-300/60 dark:border-gray-600/60">
                            {isTranscribing ? (
                              <div className="text-center space-y-4">
                                <div className="flex items-center justify-center gap-2 text-primary">
                                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
                                  <span className="font-semibold">
                                    Transcribing...
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <div className="flex flex-col items-center justify-center gap-4">
                                <button
                                  type="button"
                                  onClick={
                                    isRecording ? stopRecording : startRecording
                                  }
                                  className="relative flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-full transition-all duration-300 ease-in-out bg-red-500 hover:bg-red-600 focus:outline-none focus:ring-4 focus:ring-red-300 dark:focus:ring-red-800 shadow-lg"
                                >
                                  <div
                                    className={`absolute inset-0 bg-red-400 rounded-full transition-transform duration-500 ease-in-out ${
                                      isRecording
                                        ? "scale-150 opacity-0"
                                        : "scale-100 opacity-50"
                                    }`}
                                    style={{
                                      animation: isRecording
                                        ? "pulse 2s infinite"
                                        : "none",
                                    }}
                                  ></div>
                                  <Mic
                                    className={`h-7 w-7 sm:h-8 sm:w-8 text-white transition-transform duration-300 ease-in-out ${
                                      isRecording ? "scale-75" : "scale-100"
                                    }`}
                                  />
                                </button>
                                {isRecording && (
                                  <div className="flex items-center justify-center gap-2 text-red-600 dark:text-red-400">
                                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                                    <span className="font-mono text-base sm:text-lg">
                                      {formatTime(recordingDuration)}
                                    </span>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Submit Button */}
                      <Button
                        onClick={submitAnswer}
                        disabled={
                          isEvaluating || !userAnswer.trim() || isAnswered
                        }
                        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground py-2.5 sm:py-3 rounded-xl font-semibold transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                      >
                        {isEvaluating ? (
                          <>
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white mr-2" />
                            Getting AI Feedback...
                          </>
                        ) : isAnswered ? (
                          <>
                            <Check className="h-5 w-5 mr-2" />
                            Answer Submitted
                          </>
                        ) : (
                          <>
                            <Target className="h-5 w-5 mr-2" />
                            Submit for AI Review
                          </>
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Navigation for Desktop */}
                  <div className="hidden lg:flex justify-between items-center pt-2 sm:pt-4">
                    <Button
                      onClick={prevCard}
                      disabled={currentIndex === 0}
                      variant="outline"
                      size="sm"
                      className="text-xs sm:text-sm bg-white/80 border-gray-300/60 text-gray-700 hover:bg-white/95 hover:border-gray-400/70 dark:bg-transparent dark:border-gray-600/60 dark:text-gray-300 dark:hover:bg-gray-700/50 disabled:opacity-50"
                    >
                      <ChevronLeft className="h-4 w-4 mr-1 sm:mr-2" />
                      Previous
                    </Button>
                    <Button
                      onClick={resetPractice}
                      variant="outline"
                      size="sm"
                      className="text-xs sm:text-sm bg-white/80 border-gray-300/60 text-gray-700 hover:bg-white/95 hover:border-gray-400/70 dark:bg-transparent dark:border-gray-600/60 dark:text-gray-300 dark:hover:bg-gray-700/50"
                    >
                      <RotateCcw className="h-4 w-4 mr-1 sm:mr-2" />
                      Reset
                    </Button>
                    <Button
                      onClick={nextCard}
                      disabled={!isAnswered}
                      size="sm"
                      className="text-xs sm:text-sm bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {currentIndex === flashcards.length - 1 ? (
                        <>
                          View Results
                          <Award className="h-4 w-4 ml-1 sm:ml-2" />
                        </>
                      ) : (
                        <>
                          Next
                          <ChevronRight className="h-4 w-4 ml-1 sm:ml-2" />
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>

              {/* Feedback Section - on desktop, this column is fixed width and scrolls internally */}
              {currentAnswer && showAnswer && (
                <div
                  ref={feedbackRef}
                  className="w-full lg:w-96 lg:flex-shrink-0 p-3 sm:p-4 lg:p-6 flex flex-col lg:border-l lg:dark:border-white/10 lg:overflow-y-auto"
                >
                  <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-xl shadow-lg !border !border-gray-200 dark:!border-white/8 flex flex-col h-full">
                    {/* Card Header */}
                    <div className="flex-shrink-0 p-4 lg:p-6 border-b border-gray-200 dark:border-white/10">
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <BarChart3 className="h-5 w-5 text-foreground" />
                        AI Feedback
                      </h3>
                    </div>
                    {/* Scrollable Content */}
                    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4 sm:space-y-6">
                      {/* Performance Scores, etc. */}
                      {(() => {
                        const scoreColors: { [key: string]: string } = {
                          "Overall Score": "from-blue-500 to-blue-600",
                          "Tone Quality": "from-green-500 to-green-600",
                          Correctness: "from-purple-500 to-purple-600",
                          Confidence: "from-orange-500 to-orange-600",
                        };

                        return [
                          {
                            label: "Overall Score",
                            score: currentAnswer.feedback?.overall_score || 0,
                          },
                          {
                            label: "Tone Quality",
                            score: currentAnswer.feedback?.tone_score || 0,
                          },
                          {
                            label: "Correctness",
                            score:
                              currentAnswer.feedback?.correctness_score || 0,
                          },
                          {
                            label: "Confidence",
                            score:
                              currentAnswer.feedback?.confidence_score || 0,
                          },
                        ].map((item) => (
                          <div
                            key={item.label}
                            className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-lg p-3 sm:p-4 shadow !border !border-gray-200 dark:!border-white/8"
                          >
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                {item.label}
                              </span>
                              <span className="text-base sm:text-lg font-bold text-gray-900 dark:text-gray-100">
                                {item.score}/10
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className={`bg-gradient-to-r ${
                                  scoreColors[item.label]
                                } h-2 rounded-full transition-all duration-500`}
                                style={{
                                  width: `${(item.score / 10) * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                        ));
                      })()}

                      {/* Detailed Feedback */}
                      {currentAnswer.feedback?.feedback && (
                        <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-lg shadow !border !border-gray-200 dark:!border-white/8">
                          <button
                            onClick={() => toggleFeedbackSection("feedback")}
                            className="w-full flex items-center justify-between p-3 sm:p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/80 transition-colors duration-200 rounded-lg"
                          >
                            <h4 className="font-medium text-sm sm:text-base text-gray-900 dark:text-gray-100 flex items-center gap-2">
                              <FileText className="h-4 w-4 text-green-500" />
                              Detailed Feedback
                            </h4>
                            <ChevronDown
                              className={`h-4 w-4 text-gray-500 transition-transform duration-200 ${
                                feedbackSections.feedback
                                  ? "transform rotate-180"
                                  : ""
                              }`}
                            />
                          </button>
                          {feedbackSections.feedback && (
                            <div className="px-3 sm:px-4 pb-3 sm:pb-4 animate-in slide-in-from-top duration-200">
                              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                {currentAnswer.feedback.feedback}
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Improvement Tips */}
                      {currentAnswer.feedback?.improvement_tips && (
                        <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-lg shadow !border !border-gray-200 dark:!border-white/8">
                          <button
                            onClick={() => toggleFeedbackSection("tips")}
                            className="w-full flex items-center justify-between p-3 sm:p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/80 transition-colors duration-200 rounded-lg"
                          >
                            <h4 className="font-medium text-sm sm:text-base text-gray-900 dark:text-gray-100 flex items-center gap-2">
                              <Sparkles className="h-4 w-4 text-yellow-500" />
                              Improvement Tips
                            </h4>
                            <ChevronDown
                              className={`h-4 w-4 text-gray-500 transition-transform duration-200 ${
                                feedbackSections.tips
                                  ? "transform rotate-180"
                                  : ""
                              }`}
                            />
                          </button>
                          {feedbackSections.tips && (
                            <div className="px-3 sm:px-4 pb-3 sm:pb-4 animate-in slide-in-from-top duration-200">
                              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                {currentAnswer.feedback.improvement_tips}
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Sample Answer */}
                      {showAnswer && currentFlashcard.answer && (
                        <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-lg shadow !border !border-gray-200 dark:!border-white/8">
                          <button
                            onClick={() => toggleFeedbackSection("sample")}
                            className="w-full flex items-center justify-between p-3 sm:p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/80 transition-colors duration-200 rounded-lg"
                          >
                            <h4 className="font-medium text-sm sm:text-base text-gray-900 dark:text-gray-100 flex items-center gap-2">
                              <Volume2 className="h-4 w-4 text-teal-500" />
                              Sample Answer
                            </h4>
                            <ChevronDown
                              className={`h-4 w-4 text-gray-500 transition-transform duration-200 ${
                                feedbackSections.sample
                                  ? "transform rotate-180"
                                  : ""
                              }`}
                            />
                          </button>
                          {feedbackSections.sample && (
                            <div className="px-3 sm:px-4 pb-3 sm:pb-4 animate-in slide-in-from-top duration-200">
                              <div className="flex items-start gap-2">
                                <p className="flex-1 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                  {currentFlashcard.answer}
                                </p>
                                <button
                                  type="button"
                                  onClick={() =>
                                    playTextAsSpeech(currentFlashcard.answer)
                                  }
                                  disabled={audioLoading}
                                  className="p-2 rounded-full transition-colors duration-200 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                                  aria-label="Read sample answer aloud"
                                >
                                  {audioLoading ? (
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                  ) : audioPlaying ? (
                                    <VolumeX className="h-4 w-4" />
                                  ) : (
                                    <Volume2 className="h-4 w-4" />
                                  )}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Sticky Footer for Mobile Navigation */}
            <div className="lg:hidden flex-shrink-0 border-t border-gray-200 dark:border-white/10 p-3 bg-white/95 dark:bg-background/95 backdrop-blur-sm sticky bottom-0">
              <div className="flex items-center justify-between w-full gap-2">
                <Button
                  onClick={prevCard}
                  disabled={currentIndex === 0}
                  variant="outline"
                  size="sm"
                  className="text-xs flex-1"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Prev
                </Button>

                <Badge
                  variant="outline"
                  className="text-xs font-medium px-3 py-1.5"
                >
                  {currentIndex + 1} / {flashcards.length}
                </Badge>

                <Button
                  onClick={nextCard}
                  disabled={!isAnswered}
                  size="sm"
                  className="text-xs flex-1 bg-primary text-primary-foreground"
                >
                  {currentIndex === flashcards.length - 1 ? "Results" : "Next"}
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {mode === "review" && (
          /* Review View */
          <div className="flex-1 overflow-auto p-3 sm:p-6">
            {/* --- UI UPDATE: Made Review View Responsive --- */}
            <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">
              {/* Overall Performance */}
              {(() => {
                const stats = getOverallStats();
                return stats ? (
                  <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-3">
                      <Award className="h-5 sm:h-6 w-5 sm:w-6 text-foreground" />
                      Performance Summary
                    </h2>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
                      {[
                        {
                          label: "Answered",
                          value: `${stats.totalAnswered}/${flashcards.length}`,
                        },
                        {
                          label: "Avg Score",
                          value: `${stats.avgScore}/10`,
                        },
                        {
                          label: "Tone Quality",
                          value: `${stats.avgTone}/10`,
                        },
                        {
                          label: "Confidence",
                          value: `${stats.avgConfidence}/10`,
                        },
                      ].map((stat) => (
                        <div
                          key={stat.label}
                          className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-lg p-3 sm:p-4 text-center shadow !border !border-gray-200 dark:!border-white/8"
                        >
                          <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                            {stat.value}
                          </div>
                          <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                            {stat.label}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null;
              })()}

              {/* Individual Question Results */}
              <div className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-xl p-4 sm:p-6 shadow-lg !border !border-gray-200 dark:!border-white/8">
                <h3 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2">
                  <ClipboardList className="h-5 w-5 text-teal-600" />
                  Question Breakdown
                </h3>
                <div className="space-y-3 sm:space-y-4">
                  {flashcards.map((card, index) => {
                    const answer = answers.find(
                      (a) => a.questionIndex === index
                    );
                    return (
                      <div
                        key={index}
                        className="!bg-white dark:!bg-background/60 backdrop-blur-md rounded-lg p-3 sm:p-4 shadow !border !border-gray-200 dark:!border-white/8"
                      >
                        <div className="flex items-start justify-between gap-3 sm:gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                Q{index + 1}:
                              </span>
                              <Badge
                                variant="outline"
                                className={
                                  answer?.answerMethod === "voice"
                                    ? "bg-muted text-foreground"
                                    : "bg-muted text-foreground"
                                }
                              >
                                {answer?.answerMethod === "voice" ? (
                                  <Mic className="h-3 w-3 mr-1" />
                                ) : (
                                  <FileText className="h-3 w-3 mr-1" />
                                )}
                                {answer?.answerMethod === "voice"
                                  ? "Voice"
                                  : "Text"}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-2 truncate">
                              {card.question}
                            </p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            {answer?.feedback ? (
                              <div className="space-y-1">
                                <div className="text-base sm:text-lg font-bold text-gray-900 dark:text-gray-100">
                                  {answer.feedback.overall_score}/10
                                </div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                  Score
                                </div>
                              </div>
                            ) : (
                              <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                                Not answered
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center gap-3 sm:gap-4 pt-2">
                <Button
                  onClick={resetPractice}
                  variant="outline"
                  size="lg"
                  className="text-sm sm:text-base bg-white/80 border-gray-300/60 text-gray-700 hover:bg-white/95 hover:border-gray-400/70 dark:bg-transparent dark:border-gray-600/60 dark:text-gray-300 dark:hover:bg-gray-700/50 px-4 sm:px-6 py-2 sm:py-3 rounded-xl font-semibold"
                >
                  <RotateCcw className="h-4 sm:h-5 w-4 sm:h-5 mr-2" />
                  Practice Again
                </Button>
                <Button
                  onClick={() => onOpenChange(false)}
                  size="lg"
                  className="text-sm sm:text-base bg-primary hover:bg-primary/90 text-primary-foreground px-4 sm:px-6 py-2 sm:py-3 rounded-xl font-semibold transition-all duration-300 hover:scale-105"
                >
                  <Check className="h-4 sm:h-5 w-4 sm:h-5 mr-2" />
                  Close
                </Button>
              </div>
            </div>
            {/* --- END UI UPDATE --- */}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
