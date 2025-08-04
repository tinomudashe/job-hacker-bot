import { useEffect, useState } from "react";

// Common webview user agent substrings
const WEBVIEW_PATTERNS = [
  "WebView",
  "(iPhone|iPod|iPad)(?!.*Safari)",
  "Android.*(wv)",
  "FBAN",
  "FBAV",
  "Instagram",
  "LinkedIn",
];

export function useIsWebview(): boolean {
  const [isWebview, setIsWebview] = useState(false);

  useEffect(() => {
    // This code only runs on the client
    const userAgent =
      navigator.userAgent || navigator.vendor || (window as any).opera;

    for (const pattern of WEBVIEW_PATTERNS) {
      if (new RegExp(pattern, "i").test(userAgent)) {
        setIsWebview(true);
        return;
      }
    }
  }, []);

  return isWebview;
}
