"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CookieConsent from "react-cookie-consent";

export function CookieConsentWrapper() {
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
      expires={150}
      enableDeclineButton
      flipButtons
      // Use classes to ensure proper layering and styling within Tailwind CSS
      containerClasses="!bg-gray-800/80 dark:!bg-black/80 backdrop-blur-md !border-t !border-white/10"
      contentClasses="!flex !items-center !justify-center"
      buttonClasses="!bg-blue-600 !hover:bg-blue-700 !text-white !font-semibold !rounded-lg !px-4 !py-2 !text-sm"
      declineButtonClasses="!bg-transparent !border !border-white/20 !hover:bg-white/10 !text-white !font-semibold !rounded-lg !px-4 !py-2 !text-sm"
    >
      <span className="text-sm text-gray-200 dark:text-gray-300">
        We use cookies to enhance your experience and for analytics.{" "}
        <Link
          href="/JobHackerBot_Terms_Conditions.pdf"
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-blue-400 hover:underline"
        >
          Learn more.
        </Link>
      </span>
    </CookieConsent>
  );
}
