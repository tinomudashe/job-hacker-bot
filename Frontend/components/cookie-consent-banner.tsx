"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CookieConsent from "react-cookie-consent";

export function CookieConsentBanner() {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return null;
  }

  return (
    <CookieConsent
      location="bottom"
      buttonText="Accept"
      declineButtonText="Decline"
      cookieName="jobHackerBotCookieConsent"
      style={{
        background: "linear-gradient(to right, #1e3a8a, #3b82f6)",
        color: "#ffffff",
        padding: "1rem",
        boxShadow: "0 -4px 6px rgba(0, 0, 0, 0.1)",
        zIndex: 1000,
      }}
      buttonStyle={{
        background: "#ffffff",
        color: "#1e3a8a",
        fontSize: "14px",
        fontWeight: "bold",
        borderRadius: "0.375rem",
        padding: "0.5rem 1rem",
      }}
      declineButtonStyle={{
        background: "transparent",
        color: "#ffffff",
        fontSize: "14px",
        fontWeight: "normal",
        borderRadius: "0.375rem",
        padding: "0.5rem 1rem",
        border: "1px solid #ffffff",
      }}
      expires={150}
      enableDeclineButton
    >
      <div className="text-sm">
        <span>
          We use cookies to enhance your experience. By clicking "Accept", you
          agree to our use of cookies. Read our{" "}
        </span>
        <Link
          href="/JobHackerBot_Terms_Conditions.pdf"
          target="_blank"
          rel="noopener noreferrer"
          className="font-bold underline hover:text-blue-200"
        >
          Terms and Conditions
        </Link>
        <span> for more information.</span>
      </div>
    </CookieConsent>
  );
}
