import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Key, 
  CheckCircle2, 
  AlertCircle,
  Eye,
  EyeOff,
  Save,
  Trash2,
  ExternalLink,
  X
} from 'lucide-react';

interface SettingsProps {
  onClose: () => void;
  onTokenSaved: () => void | Promise<void>;
}

const Settings: React.FC<SettingsProps> = ({ onClose, onTokenSaved }) => {
  const [token, setToken] = useState('');
  const [savedToken, setSavedToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [tokenInfo, setTokenInfo] = useState<{ name: string } | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [userProfile, setUserProfile] = useState<{
    firstName?: string;
    lastName?: string;
    email?: string;
    profileImage?: string;
  } | null>(null);

  useEffect(() => {
    // Load saved settings
    chrome.storage.local.get(['extensionToken', 'userProfile', 'sessionToken'], (result) => {
      if (result.extensionToken) {
        setSavedToken(result.extensionToken);
        setToken(result.extensionToken);
        // Validate existing token
        validateToken(result.extensionToken);
      }
      if (result.userProfile) {
        setUserProfile(result.userProfile);
      }
    });
  }, []);

  const validateToken = async (tokenToValidate: string) => {
    if (!tokenToValidate || !tokenToValidate.startsWith('jhb_')) {
      setTokenValid(false);
      setTokenInfo(null);
      return;
    }

    setIsValidating(true);
    try {
      const response = await fetch(`https://jobhackerbot.com/api/extension-tokens/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokenToValidate}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTokenValid(true);
        setTokenInfo({ name: data.token_name });
      } else {
        setTokenValid(false);
        setTokenInfo(null);
      }
    } catch (error) {
      console.error('Error validating token:', error);
      setTokenValid(false);
      setTokenInfo(null);
    } finally {
      setIsValidating(false);
    }
  };

  const handleSaveToken = async () => {
    if (!token.trim()) {
      // Clear token and user profile
      chrome.storage.local.remove(['extensionToken', 'userProfile'], () => {
        setToken('');
        setSavedToken('');
        setTokenValid(null);
        setTokenInfo(null);
        setIsEditing(false);
        onTokenSaved();
      });
      return;
    }

    // Validate before saving
    await validateToken(token);
    
    if (tokenValid) {
      // Save token using Promise wrapper for async/await
      await new Promise<void>((resolve) => {
        chrome.storage.local.set({ 
          extensionToken: token
        }, () => {
          setSavedToken(token);
          setIsEditing(false);
          resolve();
        });
      });
      
      // Call onTokenSaved after storage is complete
      await onTokenSaved();
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setToken(savedToken);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setToken(savedToken);
    if (savedToken) {
      validateToken(savedToken);
    }
  };

  const clearToken = async () => {
    if (confirm('Are you sure you want to remove the saved token?')) {
      await new Promise<void>((resolve) => {
        chrome.storage.local.remove(['extensionToken', 'userProfile'], () => {
          setToken('');
          setSavedToken('');
          setTokenValid(null);
          setTokenInfo(null);
          setIsEditing(false);
          resolve();
        });
      });
      
      // Call onTokenSaved after storage is complete
      await onTokenSaved();
    }
  };

  const openTokenManager = () => {
    window.open(`https://jobhackerbot.com/settings#extension-tokens`, '_blank');
  };

  return (
    <div className="min-h-screen h-screen flex flex-col relative overflow-hidden bg-gradient-to-br from-gray-50/50 via-white to-purple-50/30">
      {/* Background Gradient Orbs */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute -top-20 -left-20 w-40 h-40 bg-purple-400/15 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-20 -right-20 w-40 h-40 bg-blue-400/15 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-gradient-to-br from-purple-300/10 to-blue-300/10 rounded-full blur-3xl"></div>
      </div>
      
      {/* Header */}
      <div className="sticky top-0 z-20 header-glass px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-white flex items-center justify-center shadow-lg shadow-gray-900/25">
              <SettingsIcon className="w-4 h-4 text-gray-700" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900">Settings</h1>
              <p className="text-[9px] text-gray-500">Configure Extension</p>
            </div>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="w-8 h-8 rounded-lg bg-white/60 backdrop-blur-xl border border-gray-200/30 hover:bg-white/80 hover:scale-105 transition-all duration-300 shadow-md shadow-gray-900/10 hover:shadow-lg hover:shadow-gray-900/15 flex items-center justify-center"
            aria-label="Close settings"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Content - Scrollable with padding for sticky bottom */}
      <div className="flex-1 overflow-y-auto px-4 py-3 pb-20 space-y-4 relative z-10">
        {/* Token Section */}
        <div className="bg-white/80 backdrop-blur-xl backdrop-saturate-150 rounded-xl p-4 border border-white/60 shadow-lg shadow-gray-900/10 transition-all duration-300 hover:shadow-xl hover:shadow-gray-900/15 hover:bg-white/85">
          <div className="flex items-center gap-2 mb-3">
            <Key className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-semibold text-gray-900">Access Token</h2>
          </div>

          <p className="text-xs text-gray-600 mb-3">
            Use a personal access token to authenticate without signing in
          </p>

          <div className="space-y-4">
            {/* Show saved token status if not editing */}
            {savedToken && !isEditing ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Saved Token
                </label>
                <div className="bg-green-50/80 backdrop-blur-sm border border-green-200/50 rounded-xl p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-md shadow-gray-900/20">
                        <CheckCircle2 className="w-4 h-4 text-green-600" />
                      </div>
                      <span className="text-sm font-semibold text-green-700">Token Active</span>
                    </div>
                    <button
                      onClick={handleEdit}
                      className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 bg-blue-50/50 backdrop-blur-sm border border-blue-200/50 rounded-lg hover:bg-blue-100/50 transition-all duration-200"
                      type="button"
                    >
                      Edit
                    </button>
                  </div>
                  {tokenInfo && (
                    <p className="text-xs text-gray-600">Name: {tokenInfo.name}</p>
                  )}
                  <div className="relative mt-2">
                    <input
                      type={showToken ? 'text' : 'password'}
                      value={savedToken}
                      readOnly
                      className="input pr-10 font-mono text-sm bg-white"
                    />
                    <button
                      onClick={() => setShowToken(!showToken)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                    >
                      {showToken ? (
                        <EyeOff className="w-4 h-4 text-gray-500" />
                      ) : (
                        <Eye className="w-4 h-4 text-gray-500" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {savedToken && isEditing ? 'Edit Token' : 'Token'}
                </label>
                <div className="relative">
                  <input
                    type={showToken ? 'text' : 'password'}
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="jhb_your_token_here"
                    className="input pr-10 font-mono text-sm"
                  />
                  <button
                    onClick={() => setShowToken(!showToken)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                  >
                    {showToken ? (
                      <EyeOff className="w-4 h-4 text-gray-500" />
                    ) : (
                      <Eye className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Token Status */}
            {isValidating ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                <span>Validating token...</span>
              </div>
            ) : tokenValid === true ? (
              <div className="flex items-center justify-between p-3 bg-green-50/80 backdrop-blur-sm border border-green-200/50 rounded-xl shadow-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium text-green-700">
                    Token valid{tokenInfo?.name && `: ${tokenInfo.name}`}
                  </span>
                </div>
                <button
                  onClick={clearToken}
                  className="p-1.5 rounded-lg hover:bg-red-50/50 transition-all duration-200"
                  type="button"
                  aria-label="Remove token"
                >
                  <Trash2 className="w-4 h-4 text-red-600 hover:text-red-700" />
                </button>
              </div>
            ) : tokenValid === false ? (
              <div className="flex items-center gap-2 p-3 bg-red-50/80 backdrop-blur-sm border border-red-200/50 rounded-xl shadow-sm">
                <AlertCircle className="w-4 h-4 text-red-600" />
                <span className="text-sm font-medium text-red-700">
                  Invalid or expired token
                </span>
              </div>
            ) : null}

            {/* Action Buttons */}
            {savedToken && !isEditing ? (
              <div className="flex gap-3">
                <button
                  onClick={clearToken}
                  className="btn-secondary flex-1"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Remove Token</span>
                </button>
                <button
                  onClick={openTokenManager}
                  className="btn-secondary"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>Manage Tokens</span>
                </button>
              </div>
            ) : (
              <div className="flex gap-3">
                {isEditing && (
                  <button
                    onClick={handleCancel}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                )}
                <button
                  onClick={handleSaveToken}
                  className="btn-primary flex-1"
                  disabled={!token.trim() || (isValidating && token.trim() !== '')}
                >
                  <Save className="w-4 h-4" />
                  <span>{isEditing ? 'Update Token' : 'Save Token'}</span>
                </button>
                <button
                  onClick={openTokenManager}
                  className="btn-secondary"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>Get Token</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50/80 backdrop-blur-xl backdrop-saturate-150 rounded-2xl p-5 border border-blue-200/50 shadow-xl shadow-gray-900/15">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-md shadow-gray-900/20 flex-shrink-0">
              <span className="text-xs font-bold text-blue-600">?</span>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-blue-700 mb-2">
                How to get an access token
              </h3>
              <ol className="text-xs text-gray-700 space-y-1.5 list-decimal list-inside">
                <li>Open Job Hacker Bot in your browser</li>
                <li>Go to Settings → Chrome Extension Access</li>
                <li>Click "Generate New Token"</li>
                <li>Copy the token and paste it here</li>
              </ol>
            </div>
          </div>
        </div>

      </div>
      
      {/* Sign In Alternative - Sticky Bottom */}
      <div className="sticky bottom-0 z-20 mt-auto p-3 bg-gradient-to-t from-white via-white/95 to-transparent">
        <div className="bg-white/90 backdrop-blur-2xl backdrop-saturate-150 rounded-xl shadow-xl shadow-gray-900/15 border border-gray-200/20 p-4">
          {userProfile ? (
            <div className="flex items-center justify-center">
              <div className="flex items-center gap-3">
                {userProfile.profileImage ? (
                  <img 
                    src={userProfile.profileImage}
                    alt={`${userProfile.firstName || 'User'}`}
                    className="w-10 h-10 rounded-full border-2 border-white shadow-md shadow-gray-900/20 object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const initialsDiv = document.createElement('div');
                      initialsDiv.className = 'w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-sm shadow-md shadow-gray-900/20';
                      initialsDiv.textContent = `${userProfile.firstName?.[0] || ''}${userProfile.lastName?.[0] || ''}`.toUpperCase();
                      target.parentElement?.appendChild(initialsDiv);
                    }}
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-sm shadow-md shadow-gray-900/20">
                    {`${userProfile.firstName?.[0] || ''}${userProfile.lastName?.[0] || ''}`.toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {userProfile.firstName} {userProfile.lastName}
                  </p>
                  <p className="text-xs text-green-600 font-medium flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Signed in to Job Hacker Bot
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-3 font-medium">
                Sign in for seamless authentication
              </p>
              <a
                href={`https://jobhackerbot.com/sign-in?from=extension`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl font-semibold text-sm hover:shadow-lg hover:shadow-gray-900/25 hover:scale-[1.02] transition-all duration-300 shadow-md shadow-gray-900/20 w-full justify-center"
                onClick={() => {
                  // Check for auth after a delay
                  setTimeout(async () => {
                    const result = await chrome.storage.local.get(['userProfile', 'sessionToken']);
                    if (result.userProfile) {
                      setUserProfile(result.userProfile);
                    }
                  }, 5000);
                }}
              >
                Sign in to Job Hacker Bot
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;