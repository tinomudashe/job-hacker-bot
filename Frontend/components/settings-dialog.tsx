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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth, useUser } from "@clerk/nextjs";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  CreditCard,
  Crown,
  Database,
  Download,
  FileText,
  Loader2,
  Lock,
  Shield,
  Trash2,
  Upload,
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

interface PersonalInfoFormData {
  firstName: string;
  lastName: string;
  jobTitle: string;
  company: string;
  location: string;
  linkedin: string;
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

      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }

      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
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

        const response = await fetch("/api/user/preferences", {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(newPreferences),
        });

        if (!response.ok) {
          throw new Error(
            `Failed to update preferences: ${response.statusText}`
          );
        }

        setPreferences((prev) => ({ ...prev, ...newPreferences }));
        toast.success("Preferences updated successfully");
      } catch (err) {
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
      };

      // Validate form
      const errors = validatePersonalInfo(personalInfo);
      if (errors.length > 0) {
        setFormErrors(errors);
        return;
      }

      const token = await getToken();

      const response = await fetch("/api/user/profile", {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(personalInfo),
      });

      if (!response.ok) {
        throw new Error(`Failed to update profile: ${response.statusText}`);
      }

      toast.success("Profile updated successfully");
    } catch (error) {
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
        className="max-w-4xl max-h-[90vh] overflow-hidden"
        role="dialog"
        aria-labelledby="settings-title"
      >
        <DialogHeader>
          <DialogTitle
            id="settings-title"
            className="text-2xl font-bold flex items-center gap-2"
          >
            <Shield className="h-6 w-6" aria-hidden="true" />
            Settings
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4" role="tablist">
            <TabsTrigger
              value="personal"
              className="flex items-center gap-2"
              role="tab"
              aria-controls="personal-tab"
            >
              <User className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Personal</span>
            </TabsTrigger>
            <TabsTrigger
              value="documents"
              className="flex items-center gap-2"
              role="tab"
              aria-controls="documents-tab"
            >
              <FileText className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Documents</span>
            </TabsTrigger>
            <TabsTrigger
              value="subscription"
              className="flex items-center gap-2"
              role="tab"
              aria-controls="subscription-tab"
            >
              <CreditCard className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Subscription</span>
            </TabsTrigger>
            <TabsTrigger
              value="privacy"
              className="flex items-center gap-2"
              role="tab"
              aria-controls="privacy-tab"
            >
              <Database className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Privacy</span>
            </TabsTrigger>
          </TabsList>

          <div className="mt-6 max-h-[60vh] overflow-y-auto scrollbar-thin">
            {/* Personal Info Tab */}
            <TabsContent
              value="personal"
              className="space-y-6"
              id="personal-tab"
              role="tabpanel"
            >
              <Card>
                <CardHeader>
                  <CardTitle>Personal Information</CardTitle>
                  <CardDescription>
                    Update your profile and account details
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {formErrors.length > 0 && (
                    <Alert variant="destructive" className="mb-4">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <ul className="list-disc list-inside">
                          {formErrors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}

                  <form onSubmit={handleUpdateProfile} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">First Name *</Label>
                        <Input
                          id="firstName"
                          name="firstName"
                          defaultValue={user?.firstName || ""}
                          required
                          aria-describedby="firstName-error"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Last Name *</Label>
                        <Input
                          id="lastName"
                          name="lastName"
                          defaultValue={user?.lastName || ""}
                          required
                          aria-describedby="lastName-error"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        defaultValue={
                          user?.primaryEmailAddress?.emailAddress || ""
                        }
                        disabled
                        aria-describedby="email-help"
                      />
                      <p
                        id="email-help"
                        className="text-xs text-muted-foreground"
                      >
                        Email cannot be changed here. Please use your account
                        settings.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="jobTitle">Current Job Title</Label>
                      <Input
                        id="jobTitle"
                        name="jobTitle"
                        placeholder="e.g., Software Engineer"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="company">Current Company</Label>
                      <Input
                        id="company"
                        name="company"
                        placeholder="e.g., TechCorp Inc."
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="location">Location</Label>
                      <Input
                        id="location"
                        name="location"
                        placeholder="e.g., San Francisco, CA"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="linkedin">LinkedIn Profile</Label>
                      <Input
                        id="linkedin"
                        name="linkedin"
                        type="url"
                        placeholder="https://linkedin.com/in/yourprofile"
                        aria-describedby="linkedin-help"
                      />
                      <p
                        id="linkedin-help"
                        className="text-xs text-muted-foreground"
                      >
                        Must be a valid LinkedIn profile URL
                      </p>
                    </div>

                    <Separator />

                    <div className="space-y-4">
                      <h4 className="font-semibold">Preferences</h4>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="emailNotifications">
                            Email Notifications
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Receive updates about your job applications
                          </p>
                        </div>
                        <Switch
                          id="emailNotifications"
                          checked={preferences.emailNotifications}
                          onCheckedChange={(checked) =>
                            updatePreferences({ emailNotifications: checked })
                          }
                          disabled={preferencesLoading}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="marketingEmails">
                            Marketing Emails
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Receive tips and product updates
                          </p>
                        </div>
                        <Switch
                          id="marketingEmails"
                          checked={preferences.marketingEmails}
                          onCheckedChange={(checked) =>
                            updatePreferences({ marketingEmails: checked })
                          }
                          disabled={preferencesLoading}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="dataCollection">
                            Analytics & Improvement
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Help us improve the product with usage data
                          </p>
                        </div>
                        <Switch
                          id="dataCollection"
                          checked={preferences.dataCollection}
                          onCheckedChange={(checked) =>
                            updatePreferences({ dataCollection: checked })
                          }
                          disabled={preferencesLoading}
                        />
                      </div>
                    </div>

                    <Button type="submit" disabled={isLoading}>
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
                </CardContent>
              </Card>
            </TabsContent>

            {/* Documents Tab */}
            <TabsContent
              value="documents"
              className="space-y-6"
              id="documents-tab"
              role="tabpanel"
            >
              <Card>
                <CardHeader>
                  <CardTitle>Document Management</CardTitle>
                  <CardDescription>
                    Upload, manage, and organize your career documents
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 text-center">
                    <Upload
                      className="h-8 w-8 mx-auto mb-2 text-muted-foreground"
                      aria-hidden="true"
                    />
                    <h3 className="font-semibold mb-1">Upload Documents</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Drag and drop files here, or click to browse
                    </p>
                    <Button variant="outline">
                      <Upload className="h-4 w-4 mr-2" aria-hidden="true" />
                      Choose Files
                    </Button>
                  </div>

                  {documentsError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{documentsError}</AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold">Your Documents</h4>
                      {documentsLoading && (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      )}
                    </div>

                    {documents.length === 0 && !documentsLoading ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No documents uploaded yet
                      </p>
                    ) : (
                      documents.map((doc) => (
                        <div
                          key={doc.id}
                          className="flex items-center justify-between p-3 border rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <FileText
                              className="h-5 w-5 text-blue-500"
                              aria-hidden="true"
                            />
                            <div>
                              <p className="font-medium">{doc.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {doc.type} • {doc.size} • {doc.uploadDate}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label={`Download ${doc.name}`}
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteDocument(doc.id)}
                              aria-label={`Delete ${doc.name}`}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Subscription Tab */}
            <TabsContent
              value="subscription"
              className="space-y-6"
              id="subscription-tab"
              role="tabpanel"
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Crown
                      className="h-5 w-5 text-amber-500"
                      aria-hidden="true"
                    />
                    Current Plan
                  </CardTitle>
                  <CardDescription>
                    Manage your subscription and billing information
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30 rounded-lg">
                    <div>
                      <h3 className="font-semibold">Free Plan</h3>
                      <p className="text-sm text-muted-foreground">
                        Basic features with usage limits
                      </p>
                    </div>
                    <Badge variant="outline">Current</Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Pro Plan</CardTitle>
                        <CardDescription>$19/month</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            aria-hidden="true"
                          />
                          Unlimited resumes & cover letters
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            aria-hidden="true"
                          />
                          Advanced AI interview coaching
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            aria-hidden="true"
                          />
                          Priority support
                        </div>
                        <Button className="w-full mt-4">Upgrade to Pro</Button>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Enterprise</CardTitle>
                        <CardDescription>Custom pricing</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            aria-hidden="true"
                          />
                          Everything in Pro
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            aria-hidden="true"
                          />
                          Team management
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle
                            className="h-4 w-4 text-green-500"
                            aria-hidden="true"
                          />
                          Custom integrations
                        </div>
                        <Button variant="outline" className="w-full mt-4">
                          Contact Sales
                        </Button>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="pt-4 border-t">
                    <h4 className="font-semibold mb-2">Usage This Month</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">12</div>
                        <div className="text-sm text-muted-foreground">
                          Resumes Generated
                        </div>
                        <div className="text-xs text-muted-foreground">
                          of 15 free
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">8</div>
                        <div className="text-sm text-muted-foreground">
                          Cover Letters
                        </div>
                        <div className="text-xs text-muted-foreground">
                          of 10 free
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">25</div>
                        <div className="text-sm text-muted-foreground">
                          AI Interactions
                        </div>
                        <div className="text-xs text-muted-foreground">
                          of 100 free
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Privacy & Data Tab */}
            <TabsContent
              value="privacy"
              className="space-y-6"
              id="privacy-tab"
              role="tabpanel"
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lock className="h-5 w-5" aria-hidden="true" />
                    Privacy & Data Management
                  </CardTitle>
                  <CardDescription>
                    Control your data and privacy settings
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Data Export */}
                  <div className="space-y-3">
                    <h4 className="font-semibold">Export Your Data</h4>
                    <p className="text-sm text-muted-foreground">
                      Download a copy of all your data including chat history,
                      documents, and profile information.
                    </p>
                    <Button
                      variant="outline"
                      className="w-full sm:w-auto"
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

                  <Separator />

                  {/* Clear Chat History */}
                  <div className="space-y-3">
                    <h4 className="font-semibold flex items-center gap-2">
                      <AlertTriangle
                        className="h-5 w-5 text-orange-500"
                        aria-hidden="true"
                      />
                      Clear Chat History
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete all your chat conversations and message
                      history. This action cannot be undone.
                    </p>
                    <Button
                      variant="destructive"
                      onClick={handleClearChatHistory}
                      disabled={isLoading}
                      className="w-full sm:w-auto"
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4 mr-2" />
                      )}
                      Clear Chat History
                    </Button>
                  </div>

                  <Separator />

                  {/* Delete Documents */}
                  <div className="space-y-3">
                    <h4 className="font-semibold flex items-center gap-2">
                      <AlertTriangle
                        className="h-5 w-5 text-orange-500"
                        aria-hidden="true"
                      />
                      Delete All Documents
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      Remove all uploaded documents including resumes, cover
                      letters, and portfolios.
                    </p>
                    <Button
                      variant="destructive"
                      className="w-full sm:w-auto"
                      onClick={handleDeleteAllDocuments}
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4 mr-2" />
                      )}
                      Delete All Documents
                    </Button>
                  </div>

                  <Separator />

                  {/* Account Deletion */}
                  <div className="space-y-3">
                    <h4 className="font-semibold flex items-center gap-2 text-red-600">
                      <AlertTriangle className="h-5 w-5" aria-hidden="true" />
                      Danger Zone
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete your account and all associated data.
                      This action is irreversible.
                    </p>
                    <Button
                      variant="destructive"
                      className="w-full sm:w-auto bg-red-600 hover:bg-red-700"
                      disabled={isLoading}
                    >
                      <X className="h-4 w-4 mr-2" aria-hidden="true" />
                      Delete Account
                    </Button>
                  </div>

                  <Separator />

                  {/* Privacy Information */}
                  <div className="space-y-3">
                    <h4 className="font-semibold">Privacy Information</h4>
                    <div className="text-sm text-muted-foreground space-y-2">
                      <p>• Your data is encrypted in transit and at rest</p>
                      <p>
                        • We never share your personal information with third
                        parties
                      </p>
                      <p>• You can request data deletion at any time</p>
                      <p>
                        • Chat history is stored securely and only accessible by
                        you
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        Privacy Policy
                      </Button>
                      <Button variant="outline" size="sm">
                        Terms of Service
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
