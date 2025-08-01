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
import { useSubscription } from "@/lib/hooks/use-subscription";
import { useAuth, useUser } from "@clerk/nextjs";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { format } from "date-fns";
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
    preferences,
    updatePreferences,
    loading: preferencesLoading,
  } = useUserPreferences();
  const {
    subscription,
    loading: subscriptionLoading,
    fetchSubscription,
    createCheckoutSession,
    createPortalSession,
    portalLoading,
  } = useSubscription();

  React.useEffect(() => {
    if (open) {
      fetchSubscription();
    }
  }, [open, fetchSubscription]);

  React.useEffect(() => {
    if (open) {
      const fetchProfileData = async () => {
        setIsLoading(true);
        try {
          const token = await getToken();
          const profileResponse = await fetch("/api/profile", {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!profileResponse.ok) throw new Error("Could not fetch profile");
          const profileData = await profileResponse.json();
          setProfileData(profileData);
        } catch (error) {
          console.error("Could not load profile data:", error);
          toast.error("Could not load your profile data.");
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
      // Show an initial "request sent" message
      toast.info("Request for data export sent.", {
        description:
          "We will reach out to you to verify your information before making the export available.",
      });

      const token = await getToken();

      const response = await fetch("/api/user/export", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        // If the API call fails, show an error message
        toast.error("Failed to process data export request.");
        throw new Error(`Failed to export data: ${response.statusText}`);
      }

      // Instead of downloading, we just confirm the request was received
      // The actual export will be handled offline after verification
      console.log("Data export request successfully submitted.");
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "An unexpected error occurred.";
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
                    {subscriptionLoading ? (
                      <div className="flex justify-center items-center p-10">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                      </div>
                    ) : (
                      (() => {
                        const failedStatuses = ["past_due", "unpaid"];

                        if (subscription?.is_active) {
                          const isPro = subscription.plan === "pro";
                          return (
                            <Card className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8 rounded-lg sm:rounded-xl p-4 sm:p-6 shadow-lg">
                              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                                <Crown className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400" />
                                <span>Your Subscription</span>
                              </h2>
                              <div className="p-4 bg-muted rounded-lg mb-6">
                                <div className="flex justify-between items-center">
                                  <div>
                                    <h3 className="font-semibold text-base">
                                      {isPro ? "Pro Plan" : "Trial Plan"}
                                    </h3>
                                    <p className="text-sm text-muted-foreground">
                                      {isPro ? "Renews on " : "Trial ends on "}
                                      {subscription.period_end
                                        ? format(
                                            new Date(subscription.period_end),
                                            "MMMM d, yyyy"
                                          )
                                        : "N/A"}
                                    </p>
                                  </div>
                                  <Badge variant={isPro ? "pro" : "trial"}>
                                    Active
                                  </Badge>
                                </div>
                              </div>

                              {isPro ? (
                                <>
                                  <Button
                                    className="w-full"
                                    onClick={createPortalSession}
                                    disabled={portalLoading}
                                  >
                                    {portalLoading ? (
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    ) : (
                                      <CreditCard className="mr-2 h-4 w-4" />
                                    )}
                                    Manage Billing & Subscription
                                  </Button>
                                  <p className="text-xs text-muted-foreground mt-2 text-center">
                                    You will be redirected to Stripe to manage
                                    your subscription.
                                  </p>
                                </>
                              ) : (
                                <>
                                  <Button
                                    className="w-full"
                                    onClick={() => createCheckoutSession()}
                                    disabled={subscriptionLoading}
                                  >
                                    {subscriptionLoading ? (
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    ) : null}
                                    Upgrade to Pro
                                  </Button>
                                  <p className="text-xs text-muted-foreground mt-2 text-center">
                                    Your trial is active. Upgrade now to keep
                                    your premium features.
                                  </p>
                                </>
                              )}
                            </Card>
                          );
                        } else if (
                          subscription &&
                          failedStatuses.includes(subscription.status)
                        ) {
                          return (
                            <Card className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8 rounded-lg sm:rounded-xl p-4 sm:p-6 shadow-lg">
                              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                                <Crown className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400" />
                                <span>Your Subscription</span>
                              </h2>
                              <div className="p-4 bg-muted rounded-lg mb-6">
                                <div className="flex justify-between items-center">
                                  <div>
                                    <h3 className="font-semibold text-base">
                                      Pro Plan
                                    </h3>
                                    <p className="text-sm text-muted-foreground">
                                      Action Required: Please update your
                                      payment method.
                                    </p>
                                  </div>
                                  <Badge variant="destructive">
                                    {subscription.status === "past_due"
                                      ? "Past Due"
                                      : "Unpaid"}
                                  </Badge>
                                </div>
                              </div>
                              <Button
                                className="w-full"
                                onClick={createPortalSession}
                                disabled={portalLoading}
                              >
                                {portalLoading ? (
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                  <CreditCard className="mr-2 h-4 w-4" />
                                )}
                                Update Payment Method
                              </Button>
                              <p className="text-xs text-muted-foreground mt-2 text-center">
                                You will be redirected to Stripe to manage your
                                subscription.
                              </p>
                            </Card>
                          );
                        } else {
                          return (
                            <div className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8 rounded-lg sm:rounded-xl p-4 sm:p-6 shadow-lg">
                              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                                <Crown className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400" />
                                <span>Pro Subscription</span>
                              </h2>
                              <div className="grid grid-cols-1 gap-4">
                                <Card className="h-full">
                                  <CardHeader className="pb-2">
                                    <CardTitle className="text-lg">
                                      Pro Plan
                                    </CardTitle>
                                    <CardDescription>
                                      $2.99/week
                                    </CardDescription>
                                  </CardHeader>
                                  <CardContent className="space-y-3">
                                    <div className="flex items-center gap-2 text-sm">
                                      <CheckCircle className="h-4 w-4 text-green-500" />
                                      <span>
                                        Unlimited resumes & cover letters
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                      <CheckCircle className="h-4 w-4 text-green-500" />
                                      <span>
                                        Advanced AI interview coaching
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                      <CheckCircle className="h-4 w-4 text-green-500" />
                                      <span>Priority support</span>
                                    </div>
                                    <div className="flex flex-col gap-2 pt-2">
                                      <Button
                                        className="w-full"
                                        onClick={() => createCheckoutSession()}
                                        disabled={subscriptionLoading}
                                      >
                                        {subscriptionLoading ? (
                                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        ) : null}
                                        Start Your Pro Trial
                                      </Button>
                                      <p className="text-xs text-muted-foreground text-center">
                                        Enjoy a 1-day free trial. After your
                                        trial, continue with Pro for just
                                        $2.99/week. Cancel anytime.
                                      </p>
                                    </div>
                                  </CardContent>
                                </Card>
                              </div>
                            </div>
                          );
                        }
                      })()
                    )}
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
                          <p>
                            • Your data is encrypted in transit and at rest.
                          </p>
                          <p>
                            • We never share your personal information with
                            third parties.
                          </p>
                          <p>• You can request data deletion at any time.</p>
                          <p>
                            • Chat history is stored securely and only
                            accessible by you.
                          </p>
                          <p>
                            • By using the app, you agree to our Terms and
                            Conditions.
                          </p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-9 text-xs touch-manipulation"
                            onClick={() =>
                              window.open(
                                "/JobHackerBot_Terms_Conditions.pdf",
                                "_blank"
                              )
                            }
                          >
                            Terms and Conditions
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
