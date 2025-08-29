"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@clerk/nextjs";
import { format } from "date-fns";
import {
  AlertCircle,
  Chrome,
  Clock,
  Copy,
  Eye,
  EyeOff,
  Key,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

interface Token {
  id: string;
  name: string;
  created_at: string;
  last_used: string | null;
  expires_at: string | null;
  is_active: boolean;
}

interface NewToken {
  id: string;
  name: string;
  token: string;
  created_at: string;
  expires_at: string | null;
}

export function ExtensionTokensManager() {
  const { getToken } = useAuth();
  const [tokens, setTokens] = React.useState<Token[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isCreating, setIsCreating] = React.useState(false);
  const [showCreateDialog, setShowCreateDialog] = React.useState(false);
  const [showTokenDialog, setShowTokenDialog] = React.useState(false);
  const [newToken, setNewToken] = React.useState<NewToken | null>(null);
  const [tokenName, setTokenName] = React.useState("");
  const [tokenExpiry, setTokenExpiry] = React.useState("never");
  const [showToken, setShowToken] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch tokens on mount
  React.useEffect(() => {
    fetchTokens();
  }, []);

  const fetchTokens = async () => {
    setIsLoading(true);
    try {
      const authToken = await getToken();
      const response = await fetch(`${API_URL}/api/extension-tokens/`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTokens(data);
      } else {
        toast.error("Failed to load tokens");
      }
    } catch (error) {
      console.error("Error fetching tokens:", error);
      toast.error("Failed to load extension tokens");
    } finally {
      setIsLoading(false);
    }
  };

  const createToken = async () => {
    if (!tokenName.trim()) {
      toast.error("Please enter a token name");
      return;
    }

    setIsCreating(true);
    try {
      const authToken = await getToken();
      const expiresInDays = tokenExpiry === "never" ? null : parseInt(tokenExpiry);

      const response = await fetch(`${API_URL}/api/extension-tokens/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: tokenName,
          expires_in_days: expiresInDays,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setNewToken(data);
        setShowCreateDialog(false);
        setShowTokenDialog(true);
        setTokenName("");
        setTokenExpiry("never");
        await fetchTokens();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to create token");
      }
    } catch (error) {
      console.error("Error creating token:", error);
      toast.error("Failed to create token");
    } finally {
      setIsCreating(false);
    }
  };

  const revokeToken = async (tokenId: string) => {
    if (!confirm("Are you sure you want to revoke this token? This action cannot be undone.")) {
      return;
    }

    try {
      const authToken = await getToken();
      const response = await fetch(`${API_URL}/api/extension-tokens/${tokenId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        toast.success("Token revoked successfully");
        await fetchTokens();
      } else {
        toast.error("Failed to revoke token");
      }
    } catch (error) {
      console.error("Error revoking token:", error);
      toast.error("Failed to revoke token");
    }
  };

  const copyToken = async () => {
    if (newToken?.token) {
      await navigator.clipboard.writeText(newToken.token);
      setCopied(true);
      toast.success("Token copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Chrome className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            Chrome Extension Access
          </CardTitle>
          <CardDescription>
            Generate personal access tokens to use with the Job Hacker Bot Chrome Extension
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Access tokens allow you to use the Chrome Extension without signing in. Keep your tokens secure and never share them publicly.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Tokens List */}
      <Card className="!bg-white !border !border-gray-200 dark:!bg-background/60 dark:backdrop-blur-xl dark:backdrop-saturate-150 dark:!border-white/8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Active Tokens</CardTitle>
            <Button
              onClick={() => setShowCreateDialog(true)}
              size="sm"
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Generate New Token
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : tokens.length === 0 ? (
            <div className="text-center py-8">
              <Key className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">No tokens generated yet</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                Create a token to start using the Chrome Extension
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {tokens.map((token) => (
                <div
                  key={token.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-white/8 bg-gray-50 dark:bg-background/40"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{token.name}</span>
                      {!token.is_active && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400">
                          Revoked
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span>Created {format(new Date(token.created_at), "MMM d, yyyy")}</span>
                      {token.last_used && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Last used {format(new Date(token.last_used), "MMM d, yyyy")}
                        </span>
                      )}
                      {token.expires_at && (
                        <span>Expires {format(new Date(token.expires_at), "MMM d, yyyy")}</span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => revokeToken(token.id)}
                    disabled={!token.is_active}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Token Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate New Access Token</DialogTitle>
            <DialogDescription>
              Create a personal access token for the Chrome Extension
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="token-name">Token Name</Label>
              <Input
                id="token-name"
                placeholder="e.g., Chrome Extension - Personal Laptop"
                value={tokenName}
                onChange={(e) => setTokenName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="token-expiry">Expiration</Label>
              <Select value={tokenExpiry} onValueChange={setTokenExpiry}>
                <SelectTrigger id="token-expiry">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="never">Never expires</SelectItem>
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="90">90 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={createToken} disabled={isCreating}>
              {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Generate Token
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Show New Token Dialog */}
      <Dialog open={showTokenDialog} onOpenChange={setShowTokenDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Your New Access Token</DialogTitle>
            <DialogDescription>
              Save this token now. You won't be able to see it again!
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Copy this token and paste it in your Chrome Extension settings. This is the only time you'll see this token.
              </AlertDescription>
            </Alert>
            <div className="space-y-2">
              <Label>Access Token</Label>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Input
                    type={showToken ? "text" : "password"}
                    value={newToken?.token || ""}
                    readOnly
                    className="pr-10 font-mono text-sm"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1 h-7 w-7 p-0"
                    onClick={() => setShowToken(!showToken)}
                  >
                    {showToken ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <Button onClick={copyToken} variant="outline">
                  {copied ? "Copied!" : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              <p className="font-medium mb-2">How to use this token:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Open the Job Hacker Bot Chrome Extension</li>
                <li>Click on the extension icon in your browser</li>
                <li>Enter this token when prompted</li>
                <li>The extension will remember your token</li>
              </ol>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowTokenDialog(false)}>
              I've Saved My Token
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}