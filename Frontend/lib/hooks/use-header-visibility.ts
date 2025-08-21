"use client";

import { useEffect, useState, useCallback } from "react";

const STORAGE_KEY = "header-visibility";

export function useHeaderVisibility(defaultVisible = true) {
  const [isHeaderVisible, setIsHeaderVisible] = useState(defaultVisible);

  // Load saved preference on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved !== null) {
      setIsHeaderVisible(saved === "true");
    }
  }, []);

  // Toggle header visibility
  const toggleHeader = useCallback(() => {
    setIsHeaderVisible((prev) => {
      const newValue = !prev;
      localStorage.setItem(STORAGE_KEY, String(newValue));
      return newValue;
    });
  }, []);

  // Set header visibility directly
  const setHeaderVisibility = useCallback((visible: boolean) => {
    setIsHeaderVisible(visible);
    localStorage.setItem(STORAGE_KEY, String(visible));
  }, []);

  // Keyboard shortcut (Ctrl+H or Cmd+H)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "h") {
        e.preventDefault();
        toggleHeader();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [toggleHeader]);

  return {
    isHeaderVisible,
    toggleHeader,
    setHeaderVisibility
  };
}