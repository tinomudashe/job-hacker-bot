"use client";

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
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RichTextEditor } from "@/components/ui/rich-text-editor";
import { useAuth } from "@clerk/nextjs";
import { Edit, Eye, Loader2, PlusCircle, Send, Trash2 } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

// --- Types ---
interface Template {
  id: string;
  name: string;
  subject: string;
  content: string;
}

// --- Main Component ---
export default function MarketingAdminPage() {
  const { getToken } = useAuth();
  const [templates, setTemplates] = React.useState<Template[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Form state
  const [formContent, setFormContent] = React.useState("");
  const [formSubject, setFormSubject] = React.useState("");
  const [formName, setFormName] = React.useState("");
  const [editingTemplateId, setEditingTemplateId] = React.useState<
    string | null
  >(null);

  // Fetching Hook
  const fetchTemplates = React.useCallback(async () => {
    setLoading(true);
    const token = await getToken();
    try {
      const response = await fetch("/api/marketing/templates", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch templates");
      const data = await response.json();
      setTemplates(data);
    } catch (error) {
      toast.error("Could not load templates.");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  React.useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleFormSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    const data = { name: formName, subject: formSubject, content: formContent };

    // In a real app, you'd have a PUT endpoint for updates
    // For now, we are creating a new one even on edit.
    const url = "/api/marketing/templates";
    const method = "POST";

    try {
      const token = await getToken();
      const response = await fetch(url, {
        method: method,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) throw new Error("Failed to save template.");
      toast.success(
        `Template ${editingTemplateId ? "updated" : "saved"} successfully!`
      );

      resetForm();
      fetchTemplates();
    } catch (error) {
      toast.error("Error saving template.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this template? This action cannot be undone."
      )
    ) {
      return;
    }

    setIsSubmitting(true);
    try {
      const token = await getToken();
      const response = await fetch(`/api/marketing/templates/${templateId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        // Handle cases where the server provides a specific error message
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to delete template." }));
        throw new Error(errorData.detail);
      }

      toast.success("Template deleted successfully.");
      fetchTemplates(); // Refresh the list
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "An unknown error occurred."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSendCampaign = async (templateId: string) => {
    if (
      !confirm(
        "Are you sure you want to send this campaign to all subscribed users?"
      )
    )
      return;
    setIsSubmitting(true);
    try {
      const token = await getToken();
      const response = await fetch("/api/marketing/send-email", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ template_id: templateId }),
      });
      if (!response.ok) throw new Error("Failed to send campaign.");
      toast.success("Campaign sending initiated!");
    } catch (error) {
      toast.error("Error sending campaign.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (template: Template) => {
    setEditingTemplateId(template.id);
    setFormName(template.name);
    setFormSubject(template.subject);
    setFormContent(template.content);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const resetForm = () => {
    setEditingTemplateId(null);
    setFormName("");
    setFormSubject("");
    setFormContent("");
  };

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">
          Marketing Campaigns
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-5">
        {/* Editor Form - Takes more space now */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PlusCircle className="h-5 w-5" />
              {editingTemplateId ? "Edit Template" : "Create New Template"}
            </CardTitle>
            <CardDescription>
              Design an email template. Use <code>{`{{first_name}}`}</code> for
              personalization.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <Label htmlFor="name">Template Name</Label>
                <Input
                  id="name"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  required
                  placeholder="e.g., Weekly Newsletter"
                />
              </div>
              <div>
                <Label htmlFor="subject">Email Subject</Label>
                <Input
                  id="subject"
                  value={formSubject}
                  onChange={(e) => setFormSubject(e.target.value)}
                  required
                  placeholder="The subject line for the email"
                />
              </div>
              <div>
                <Label>Email Body</Label>
                <RichTextEditor
                  content={formContent}
                  onChange={setFormContent}
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : editingTemplateId ? (
                    <Edit className="mr-2 h-4 w-4" />
                  ) : (
                    <PlusCircle className="mr-2 h-4 w-4" />
                  )}
                  {editingTemplateId ? "Update Template" : "Save Template"}
                </Button>
                {editingTemplateId && (
                  <Button type="button" variant="ghost" onClick={resetForm}>
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Templates List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Existing Templates</CardTitle>
            <CardDescription>
              Manage, preview, and send your campaigns.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <div className="divide-y divide-border">
                {templates.length > 0 ? (
                  templates.map((template) => (
                    <div
                      key={template.id}
                      className="flex items-center justify-between py-3"
                    >
                      <span className="font-medium text-sm">
                        {template.name}
                      </span>
                      <div className="flex items-center gap-1">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl w-full">
                            <DialogHeader>
                              <DialogTitle>
                                Preview: {template.subject}
                              </DialogTitle>
                            </DialogHeader>
                            <div
                              className="mt-4 prose dark:prose-invert max-w-none"
                              dangerouslySetInnerHTML={{
                                __html: template.content,
                              }}
                            />
                          </DialogContent>
                        </Dialog>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(template)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleDeleteTemplate(template.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="default"
                          size="icon"
                          onClick={() => handleSendCampaign(template.id)}
                          disabled={isSubmitting}
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No templates created yet.
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
