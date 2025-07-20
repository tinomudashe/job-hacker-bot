"use client";

import { useAuth } from "@clerk/nextjs";
import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

interface PageContextState {
  pageId: string | null;
  setPageId: (pageId: string | null) => void;
  isLoading: boolean;
  isLoaded: boolean;
  error: string | null;
  clearPage: () => void;
}

const PageContext = createContext<PageContextState | undefined>(undefined);

export const usePage = () => {
  const context = useContext(PageContext);
  if (!context) {
    throw new Error("usePage must be used within a PageProvider");
  }
  return context;
};

interface PageProviderProps {
  children: ReactNode;
}

export const PageProvider = ({ children }: PageProviderProps) => {
  const { getToken, isLoaded: isAuthLoaded } = useAuth();
  const [pageId, setPageId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoaded, setIsPageLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLastOpenedPage = useCallback(async () => {
    const token = await getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const response = await fetch("/api/pages/last-opened", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const lastPage = await response.json();
        if (lastPage && lastPage.id) {
          setPageId(lastPage.id);
        }
      }
    } catch (err) {
      setError("Failed to fetch last opened page.");
    } finally {
      setIsLoading(false);
      setIsPageLoaded(true);
    }
  }, [getToken]);

  useEffect(() => {
    if (isAuthLoaded) {
      fetchLastOpenedPage();
    }
  }, [isAuthLoaded, fetchLastOpenedPage]);

  const clearPage = () => {
    setPageId(null);
  };

  const value = {
    pageId,
    setPageId,
    isLoading,
    isLoaded,
    error,
    clearPage,
  };

  return <PageContext.Provider value={value}>{children}</PageContext.Provider>;
};
