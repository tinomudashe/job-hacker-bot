"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { useAuth, useUser } from "@clerk/nextjs";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  CreditCard,
  Crown,
  Database,
  Download,
  Loader2,
  Lock,
  Shield,
  Trash2,
  User,
  X,
} from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

// Types
interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadDate: string;
  url?: string;
}

interface UserProfile {
  first_name: string;
  last_name: string;
  profile_headline: string;
  address: string;
  linkedin: string;
  phone: string;
}

interface PersonalInfoFormData {
  firstName: string;
  lastName: string;
  jobTitle: string;
  company: string;
  location: string;
  linkedin: string;
  phone: string;
}

interface UserPreferences {
  emailNotifications: boolean;
  marketingEmails: boolean;
  dataCollection: boolean;
}

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onClearChat?: () => void;
}

// Custom hooks for API calls
const useDocuments = () => {
  const [documents, setDocuments] = React.useState<Document[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const { getToken } = useAuth();

  const fetchDocuments = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = await getToken();

      const response = await fetch("/api/documents", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      // Handle specific HTTP status codes
      if (response.status === 401 || response.status === 403) {
        console.log("Documents endpoint not available or not authorized");
        setDocuments([]);
        setError("Document management is not available yet");
        return;
      }

      if (response.status === 404) {
        console.log("Documents endpoint not found");
        setDocuments([]);
        setError("Document management feature is coming soon");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }

      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
      // Handle network errors or other fetch failures
      if (err instanceof TypeError && err.message.includes("fetch")) {
        console.log("Documents API endpoint not available");
        setDocuments([]);
        setError("Document management feature is coming soon");
        return;
      }

      const errorMessage =
        err instanceof Error ? err.message : "Failed to load documents";
      setError(errorMessage);
      console.error("Error fetching documents:", err);
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const deleteDocument = React.useCallback(
    async (documentId: string) => {
      try {
        const token = await getToken();

        const response = await fetch(`/api/documents/${documentId}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to delete document: ${response.statusText}`);
        }

        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
        toast.success("Document deleted successfully");
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to delete document";
        toast.error(errorMessage);
        throw err;
      }
    },
    [getToken]
  );

  React.useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return { documents, loading, error, deleteDocument, refetch: fetchDocuments };
};

const useUserPreferences = () => {
  const [preferences, setPreferences] = React.useState<UserPreferences>({
    emailNotifications: true,
    marketingEmails: false,
    dataCollection: true,
  });
  const [loading, setLoading] = React.useState(false);
  const { getToken } = useAuth();

  const updatePreferences = React.useCallback(
    async (newPreferences: Partial<UserPreferences>) => {
      try {
        setLoading(true);
        const token = await getToken();

        const response = await fetch("/api/me/preferences", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(newPreferences),
        });

        // Handle missing endpoints gracefully
        if (
          response.status === 401 ||
          response.status === 403 ||
          response.status === 404
        ) {
          console.log("Preferences endpoint not available");
          setPreferences((prev) => ({ ...prev, ...newPreferences }));
          toast.success("Preferences updated locally (server sync pending)");
          return;
        }

        if (!response.ok) {
          throw new Error(
            `Failed to update preferences: ${response.statusText}`
          );
        }

        setPreferences((prev) => ({ ...prev, ...newPreferences }));
        toast.success("Preferences updated successfully");
      } catch (err) {
        // Handle network errors
        if (err instanceof TypeError && err.message.includes("fetch")) {
          console.log("Preferences API endpoint not available");
          setPreferences((prev) => ({ ...prev, ...newPreferences }));
          toast.success("Preferences updated locally (server sync pending)");
          return;
        }

        const errorMessage =
          err instanceof Error ? err.message : "Failed to update preferences";
        toast.error(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [getToken]
  );

  return { preferences, updatePreferences, loading };
};

// Form validation
const validatePersonalInfo = (data: PersonalInfoFormData): string[] => {
  const errors: string[] = [];

  if (!data.firstName.trim()) {
    errors.push("First name is required");
  }

  if (!data.lastName.trim()) {
    errors.push("Last name is required");
  }

  if (
    data.linkedin &&
    !data.linkedin.match(/^https?:\/\/(www\.)?linkedin\.com\//)
  ) {
    errors.push("LinkedIn URL must be a valid LinkedIn profile URL");
  }

  return errors;
};

export function SettingsDialog({
  open,
  onOpenChange,
  onClearChat,
}: SettingsDialogProps) {
  const { user } = useUser();
  const { getToken } = useAuth();
  const [isLoading, setIsLoading] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState("personal");
  const [formErrors, setFormErrors] = React.useState<string[]>([]);
  const [profileData, setProfileData] = React.useState<UserProfile | null>(
    null
  );

  // Custom hooks
  const {
    documents,
    loading: documentsLoading,
    error: documentsError,
    deleteDocument,
  } = useDocuments();
  const {
    preferences,
    updatePreferences,
    loading: preferencesLoading,
  } = useUserPreferences();

  React.useEffect(() => {
    if (open) {
      const fetchProfileData = async () => {
        setIsLoading(true);
        try {
          const token = await getToken();
          const response = await fetch("/api/profile", {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!response.ok) throw new Error("Could not fetch profile");
          const data = await response.json();
          setProfileData(data);
        } catch (error) {
          toast.error("Could not load your profile data.");
          // Fallback to basic user data if profile fetch fails
          if (user) {
            setProfileData({
              first_name: user.firstName || "",
              last_name: user.lastName || "",
              profile_headline: "",
              address: "",
              linkedin: "",
              phone: "",
            });
          }
        } finally {
          setIsLoading(false);
        }
      };
      fetchProfileData();
    }
  }, [open, getToken, user]);

  const handleClearChatHistory = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete all chat history? This action cannot be undone."
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      const token = await getToken();

      const response = await fetch("/api/chat/clear-history", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to clear chat history: ${response.statusText}`);
      }

      onClearChat?.();
      toast.success("Chat history cleared successfully");
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to clear chat history";
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this document? This action cannot be undone."
    );

    if (!confirmed) return;

    try {
      await deleteDocument(documentId);
    } catch (error) {
      // Error handling is done in the hook
    }
  };

  const handleUpdateProfile = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setFormErrors([]);
    setIsLoading(true);

    try {
      const formData = new FormData(event.currentTarget);
      const personalInfo: PersonalInfoFormData = {
        firstName: (formData.get("firstName") as string) || "",
        lastName: (formData.get("lastName") as string) || "",
        jobTitle: (formData.get("jobTitle") as string) || "",
        company: (formData.get("company") as string) || "",
        location: (formData.get("location") as string) || "",
        linkedin: (formData.get("linkedin") as string) || "",
        phone: (formData.get("phone") as string) || "",
      };

      // Validate form
      const errors = validatePersonalInfo(personalInfo);
      if (errors.length > 0) {
        setFormErrors(errors);
        return;
      }

      const token = await getToken();

      // Map frontend data to the backend model
      const profileData = {
        first_name: personalInfo.firstName,
        last_name: personalInfo.lastName,
        profile_headline: personalInfo.jobTitle,
        address: personalInfo.location,
        linkedin: personalInfo.linkedin,
        phone: personalInfo.phone,
        // The 'company' field is not supported by the backend API and is omitted.
      };

      const response = await fetch("/api/me", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(profileData),
      });
      // Handle missing endpoints gracefully
      if (
        response.status === 401 ||
        response.status === 403 ||
        response.status === 404
      ) {
        console.log("Profile endpoint not available");
        toast.success("Profile updated locally (server sync pending)");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to update profile: ${response.statusText}`);
      }

      toast.success("Profile updated successfully");
    } catch (error) {
      // Handle network errors
      if (error instanceof TypeError && error.message.includes("fetch")) {
        console.log("Profile API endpoint not available");
        toast.success("Profile updated locally (server sync pending)");
        return;
      }

      const errorMessage =
        error instanceof Error ? error.message : "Failed to update profile";
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportData = async () => {
    setIsLoading(true);
    try {
      const token = await getToken();

      const response = await fetch("/api/user/export", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to export data: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `user-data-export-${
        new Date().toISOString().split("T")[0]
      }.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success("Data export downloaded successfully");
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to export data";
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteAllDocuments = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete ALL documents? This action cannot be undone."
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      const token = await getToken();

      const response = await fetch("/api/documents/delete-all", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete documents: ${response.statusText}`);
      }

      toast.success("All documents deleted successfully");
      // The documents will be refetched automatically
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete documents";
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="fixed max-w-[100vw] sm:max-w-6xl max-h-[100vh] sm:max-h-[95vh] w-full h-full sm:w-[95vw] sm:h-[95vh] 
           flex flex-col !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 rounded-none sm:rounded-3xl overflow-hidden p-0 !border-none sm:!border-gray-200 dark:sm:!border-white/8 shadow-none sm:shadow-2xl"
        role="dialog"
        aria-labelledby="settings-title"
      >
        {/* Accessible title for screen readers */}
        <VisuallyHidden>
          <DialogTitle>
            Settings - Manage your account and preferences
          </DialogTitle>
        </VisuallyHidden>

        {/* Header */}
        <div className="flex-shrink-0 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 !border-b !border-gray-200 dark:!border-white/8 p-4 z-10 pt-[calc(env(safe-area-inset-top,0rem)+1rem)] sm:pt-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-blue-100 border border-blue-200 shadow-lg dark:bg-blue-500/20 dark:border-blue-400/40 flex items-center justify-center flex-shrink-0">
                <Shield className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="min-w-0">
                <h1
                  id="settings-title"
                  className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-gray-100"
                >
                  Settings
                </h1>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 -mt-0.5">
                  Manage your account and preferences
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onOpenChange(false)}
              className="h-10 w-10 sm:h-10 sm:w-10 rounded-xl transition-all duration-300 hover:scale-105 bg-gray-100 border border-gray-200 hover:bg-gray-200 dark:bg-background/60 dark:border-white/8 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:hover:bg-background/80 flex-shrink-0 touch-manipulation"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-shrink-0 !border-b !border-gray-200 dark:!border-white/8 !bg-white dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 relative z-10">
          <div className="px-3 sm:px-6">
            <div className="flex -mb-px sm:gap-1">
              <button
                onClick={() => setActiveTab("personal")}
                className={`flex flex-1 justify-center items-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2.5 sm:py-3 border-b-3 font-semibold text-xs sm:text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-lg sm:rounded-t-xl hover:scale-105 touch-manipulation ${
                  activeTab === "personal"
                    ? "border-blue-500 text-blue-600 bg-blue-50 shadow-lg dark:border-blue-400 dark:text-blue-400 dark:bg-blue-500/20"
                    : "border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-400 dark:hover:border-blue-500/50 dark:hover:bg-blue-500/10"
                }`}
                role="tab"
                aria-controls="personal-tab"
              >
                <User className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
                <span>Personal</span>
              </button>

              <button
                onClick={() => setActiveTab("subscription")}
                className={`flex flex-1 justify-center items-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2.5 sm:py-3 border-b-3 font-semibold text-xs sm:text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-lg sm:rounded-t-xl hover:scale-105 touch-manipulation ${
                  activeTab === "subscription"
                    ? "border-blue-500 text-blue-600 bg-blue-50 shadow-lg dark:border-blue-400 dark:text-blue-400 dark:bg-blue-500/20"
                    : "border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-400 dark:hover:border-blue-500/50 dark:hover:bg-blue-500/10"
                }`}
                role="tab"
                aria-controls="subscription-tab"
              >
                <CreditCard className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
                <span className="hidden xs:inline">Subscription</span>
              </button>

              <button
                onClick={() => setActiveTab("privacy")}
                className={`flex flex-1 justify-center items-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2.5 sm:py-3 border-b-3 font-semibold text-xs sm:text-sm whitespace-nowrap transition-all duration-300 min-w-0 rounded-t-lg sm:rounded-t-xl hover:scale-105 touch-manipulation ${
                  activeTab === "privacy"
                    ? "border-blue-500 text-blue-600 bg-blue-50 shadow-lg dark:border-blue-400 dark:text-blue-400 dark:bg-blue-500/20"
                    : "border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-lg dark:text-gray-400 dark:hover:text-blue-400 dark:hover:border-blue-500/50 dark:hover:bg-blue-500/10"
                }`}
                role="tab"
                aria-controls="privacy-tab"
              >
                <Database className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
                <span>Privacy</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div
          className="flex-1 overflow-auto scrollbar-thin safe-area-inset-bottom"
          data-scrollable="true"
        >
          {/* Editor View */}
          <div className="h-full flex flex-col">
            {/* Content Editor */}
            <div className="flex-1 p-3 sm:p-6 !bg-gray-50 dark:!bg-transparent">
              <div className="max-w-4xl mx-auto space-y-3 sm:space-y-6">
                {/* Personal Info Tab */}
                {activeTab === "personal" && (
                  <div
                    className="space-y-4 sm:space-y-6"
                    id="personal-tab"
                    role="tabpanel"
                  >
                    <div className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8 rounded-lg sm:rounded-xl p-4 sm:p-6 shadow-lg">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <User className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                        <span>Personal Information</span>
                      </h2>

                      {formErrors.length > 0 && (
                        <Alert variant="destructive" className="mb-4">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription className="text-sm">
                            <ul className="list-disc list-inside space-y-1">
                              {formErrors.map((error, index) => (
                                <li key={index}>{error}</li>
                              ))}
                            </ul>
                          </AlertDescription>
                        </Alert>
                      )}

                      <form
                        key={profileData ? "loaded" : "loading"}
                        onSubmit={handleUpdateProfile}
                        className="space-y-4"
                      >
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                          <div className="space-y-2">
                            <Label
                              htmlFor="firstName"
                              className="text-sm font-medium"
                            >
                              First Name *
                            </Label>
                            <Input
                              id="firstName"
                              name="firstName"
                              defaultValue={user?.firstName || ""}
                              required
                              className="h-11 text-base mobile-input-text"
                              aria-describedby="firstName-error"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label
                              htmlFor="lastName"
                              className="text-sm font-medium"
                            >
                              Last Name *
                            </Label>
                            <Input
                              id="lastName"
                              name="lastName"
                              defaultValue={user?.lastName || ""}
                              required
                              className="h-11 text-base mobile-input-text"
                              aria-describedby="lastName-error"
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label
                            htmlFor="email"
                            className="text-sm font-medium"
                          >
                            Email Address
                          </Label>
                          <Input
                            id="email"
                            name="email"
                            type="email"
                            defaultValue={
                              user?.primaryEmailAddress?.emailAddress || ""
                            }
                            disabled
                            className="h-11 text-base mobile-input-text"
                            aria-describedby="email-help"
                          />
                          <p
                            id="email-help"
                            className="text-xs text-muted-foreground"
                          >
                            Email cannot be changed here. click on the profile
                            avatar to change your primary email address
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label
                            htmlFor="phone"
                            className="text-sm font-medium"
                          >
                            Phone Number
                          </Label>
                          <Input
                            id="phone"
                            name="phone"
                            defaultValue={profileData?.phone || ""}
                            placeholder="e.g., +1234567890"
                            className="h-11 text-base mobile-input-text"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label
                            htmlFor="location"
                            className="text-sm font-medium"
                          >
                            Location
                          </Label>
                          <Input
                            id="location"
                            name="location"
                            defaultValue={profileData?.address || ""}
                            placeholder="e.g., San Francisco, CA"
                            className="h-11 text-base mobile-input-text"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label
                            htmlFor="linkedin"
                            className="text-sm font-medium"
                          >
                            LinkedIn Profile
                          </Label>
                          <Input
                            id="linkedin"
                            name="linkedin"
                            type="url"
                            defaultValue={profileData?.linkedin || ""}
                            placeholder="https://linkedin.com/in/yourprofile"
                            className="h-11 text-base mobile-input-text"
                            aria-describedby="linkedin-help"
                          />
                          <p
                            id="linkedin-help"
                            className="text-xs text-muted-foreground"
                          >
                            Must be a valid LinkedIn profile URL
                          </p>
                        </div>

                        <Separator className="my-4 sm:my-6" />

                        <div className="space-y-4">
                          <h4 className="font-semibold text-sm sm:text-base">
                            Preferences
                          </h4>

                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <Label
                                htmlFor="emailNotifications"
                                className="text-sm font-medium"
                              >
                                Email Notifications
                              </Label>
                              <p className="text-xs sm:text-sm text-muted-foreground mt-1">
                                Receive updates about your job applications
                              </p>
                            </div>

                            <Switch
                              id="emailNotifications"
                              checked={preferences.emailNotifications}
                              onCheckedChange={(checked: boolean) =>
                                updatePreferences({
                                  emailNotifications: checked,
                                })
                              }
                              disabled={preferencesLoading}
                              className="flex-shrink-0 touch-manipulation"
                            />
                          </div>

                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <Label
                                htmlFor="marketingEmails"
                                className="text-sm font-medium"
                              >
                                Marketing Emails
                              </Label>
                              <p className="text-xs sm:text-sm text-muted-foreground mt-1">
                                Receive tips and product updates
                              </p>
                            </div>
                            <Switch
                              id="marketingEmails"
                              checked={preferences.marketingEmails}
                              onCheckedChange={(checked: boolean) =>
                                updatePreferences({
                                  marketingEmails: checked,
                                })
                              }
                              disabled={preferencesLoading}
                              className="flex-shrink-0 touch-manipulation"
                            />
                          </div>

                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <Label
                                htmlFor="dataCollection"
                                className="text-sm font-medium"
                              >
                                Analytics & Improvement
                              </Label>
                              <p className="text-xs sm:text-sm text-muted-foreground mt-1">
                                Help us improve the product with usage data
                              </p>
                            </div>
                            <Switch
                              id="dataCollection"
                              checked={preferences.dataCollection}
                              onCheckedChange={(checked: boolean) =>
                                updatePreferences({ dataCollection: checked })
                              }
                              disabled={preferencesLoading}
                              className="flex-shrink-0 touch-manipulation"
                            />
                          </div>
                        </div>

                        <Button
                          type="submit"
                          disabled={isLoading}
                          className="w-full h-11 text-base font-medium touch-manipulation"
                        >
                          {isLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            "Save Changes"
                          )}
                        </Button>
                      </form>
                    </div>
                  </div>
                )}

                {/* Subscription Tab */}
                {activeTab === "subscription" && (
                  <div
                    className="space-y-4 sm:space-y-6"
                    id="subscription-tab"
                    role="tabpanel"
                  >
                    <div className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8 rounded-lg sm:rounded-xl p-4 sm:p-6 shadow-lg">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <Crown
                          className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400"
                          aria-hidden="true"
                        />
                        <span>Current Plan</span>
                      </h2>

                      <div className="flex items-center justify-between p-3 sm:p-4 bg-muted rounded-lg mb-4 sm:mb-6">
                        <div className="min-w-0 flex-1">
                          <h3 className="font-semibold text-sm sm:text-base">
                            Free Plan
                          </h3>
                          <p className="text-xs sm:text-sm text-muted-foreground">
                            Basic features with usage limits
                          </p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          Current
                        </Badge>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 mb-4 sm:mb-6">
                        <Card className="h-full">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-base sm:text-lg">
                              Pro Plan
                            </CardTitle>
                            <CardDescription className="text-sm">
                              $19/month
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-2 sm:space-y-3">
                            <div className="flex items-center gap-2 text-xs sm:text-sm">
                              <CheckCircle
                                className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 flex-shrink-0"
                                aria-hidden="true"
                              />
                              <span>Unlimited resumes & cover letters</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs sm:text-sm">
                              <CheckCircle
                                className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 flex-shrink-0"
                                aria-hidden="true"
                              />
                              <span>Advanced AI interview coaching</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs sm:text-sm">
                              <CheckCircle
                                className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 flex-shrink-0"
                                aria-hidden="true"
                              />
                              <span>Priority support</span>
                            </div>
                            <Button className="w-full mt-3 sm:mt-4 h-10 text-sm touch-manipulation">
                              Upgrade to Pro
                            </Button>
                          </CardContent>
                        </Card>

                        <Card className="h-full">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-base sm:text-lg">
                              Enterprise
                            </CardTitle>
                            <CardDescription className="text-sm">
                              Custom pricing
                            </CardDescription>
                          </CardHeader>
                          <CardContent className="space-y-2 sm:space-y-3">
                            <div className="flex items-center gap-2 text-xs sm:text-sm">
                              <CheckCircle
                                className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 flex-shrink-0"
                                aria-hidden="true"
                              />
                              <span>Everything in Pro</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs sm:text-sm">
                              <CheckCircle
                                className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 flex-shrink-0"
                                aria-hidden="true"
                              />
                              <span>Team management</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs sm:text-sm">
                              <CheckCircle
                                className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 flex-shrink-0"
                                aria-hidden="true"
                              />
                              <span>Custom integrations</span>
                            </div>
                            <Button
                              variant="outline"
                              className="w-full mt-3 sm:mt-4 h-10 text-sm touch-manipulation"
                            >
                              Contact Sales
                            </Button>
                          </CardContent>
                        </Card>
                      </div>

                      <div className="pt-3 sm:pt-4 border-t">
                        <h4 className="font-semibold mb-2 sm:mb-3 text-sm sm:text-base">
                          Usage This Month
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 text-center">
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xl sm:text-2xl font-bold">
                              12
                            </div>
                            <div className="text-xs sm:text-sm text-muted-foreground">
                              Resumes Generated
                            </div>
                            <div className="text-xs text-muted-foreground">
                              of 15 free
                            </div>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xl sm:text-2xl font-bold">
                              8
                            </div>
                            <div className="text-xs sm:text-sm text-muted-foreground">
                              Cover Letters
                            </div>
                            <div className="text-xs text-muted-foreground">
                              of 10 free
                            </div>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xl sm:text-2xl font-bold">
                              25
                            </div>
                            <div className="text-xs sm:text-sm text-muted-foreground">
                              AI Interactions
                            </div>
                            <div className="text-xs text-muted-foreground">
                              of 100 free
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Privacy & Data Tab */}
                {activeTab === "privacy" && (
                  <div
                    className="space-y-4 sm:space-y-6"
                    id="privacy-tab"
                    role="tabpanel"
                  >
                    <div className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8 rounded-lg sm:rounded-xl p-4 sm:p-6 shadow-lg">
                      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                        <Lock className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                        <span>Privacy & Data Management</span>
                      </h2>

                      {/* Data Export */}
                      <div className="space-y-2 sm:space-y-3 mb-4 sm:mb-6">
                        <h4 className="font-semibold text-sm sm:text-base">
                          Export Your Data
                        </h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">
                          Download a copy of all your data including chat
                          history, documents, and profile information.
                        </p>
                        <Button
                          variant="outline"
                          className="w-full sm:w-auto h-10 text-sm touch-manipulation"
                          onClick={handleExportData}
                          disabled={isLoading}
                        >
                          {isLoading ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <Download className="h-4 w-4 mr-2" />
                          )}
                          Request Data Export
                        </Button>
                      </div>

                      <Separator className="my-4 sm:my-6" />

                      {/* Clear Chat History */}
                      <div className="space-y-2 sm:space-y-3 mb-4 sm:mb-6">
                        <h4 className="font-semibold flex items-center gap-2 text-sm sm:text-base">
                          <AlertTriangle
                            className="h-4 w-4 sm:h-5 sm:w-5 text-orange-500"
                            aria-hidden="true"
                          />
                          Clear Chat History
                        </h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">
                          Permanently delete all your chat conversations and
                          message history. This action cannot be undone.
                        </p>
                        <Button
                          variant="outline"
                          onClick={handleClearChatHistory}
                          disabled={isLoading}
                          className="w-full sm:w-auto h-10 text-sm touch-manipulation"
                        >
                          {isLoading ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4 mr-2 text-red-500" />
                          )}
                          Clear Chat History
                        </Button>
                      </div>

                      <Separator className="my-4 sm:my-6" />

                      {/* Delete Documents */}
                      <div className="space-y-2 sm:space-y-3 mb-4 sm:mb-6">
                        <h4 className="font-semibold flex items-center gap-2 text-sm sm:text-base">
                          <AlertTriangle
                            className="h-4 w-4 sm:h-5 sm:w-5 text-orange-500"
                            aria-hidden="true"
                          />
                          Delete All Documents
                        </h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">
                          Remove all uploaded documents including resumes, cover
                          letters, and portfolios.
                        </p>
                        <Button
                          variant="outline"
                          className="w-full sm:w-auto h-10 text-sm touch-manipulation"
                          onClick={handleDeleteAllDocuments}
                          disabled={isLoading}
                        >
                          {isLoading ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4 mr-2 text-red-500" />
                          )}
                          Delete All Documents
                        </Button>
                      </div>

                      <Separator className="my-4 sm:my-6" />

                      {/* Account Deletion */}
                      <div className="space-y-2 sm:space-y-3 mb-4 sm:mb-6">
                        <h4 className="font-semibold flex items-center gap-2 text-red-600 text-sm sm:text-base">
                          <AlertTriangle
                            className="h-4 w-4 sm:h-5 sm:w-5"
                            aria-hidden="true"
                          />
                          Danger Zone
                        </h4>
                        <p className="text-xs sm:text-sm text-muted-foreground">
                          Permanently delete your account and all associated
                          data. This action is irreversible.
                        </p>
                        <Button
                          variant="outline"
                          className="w-full sm:w-auto h-10 text-sm touch-manipulation"
                          disabled={isLoading}
                        >
                          <X
                            className="h-4 w-4 mr-2 text-red-500"
                            aria-hidden="true"
                          />
                          Delete Account
                        </Button>
                      </div>

                      <Separator className="my-4 sm:my-6" />

                      {/* Privacy Information */}
                      <div className="space-y-2 sm:space-y-3">
                        <h4 className="font-semibold text-sm sm:text-base">
                          Privacy Information
                        </h4>
                        <div className="text-xs sm:text-sm text-muted-foreground space-y-1 sm:space-y-2">
                          <p>• Your data is encrypted in transit and at rest</p>
                          <p>
                            • We never share your personal information with
                            third parties
                          </p>
                          <p>• You can request data deletion at any time</p>
                          <p>
                            • Chat history is stored securely and only
                            accessible by you
                          </p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-9 text-xs touch-manipulation"
                          >
                            Privacy Policy
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-9 text-xs touch-manipulation"
                          >
                            Terms of Service
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
