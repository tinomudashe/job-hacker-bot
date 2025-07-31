import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// EDIT: Add a new helper function to get the API URL from environment variables.
// This centralizes the backend URL and makes it easy to switch between environments.
export const getApiUrl = (path: string): string => {
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://jobckerbot-backend-556781469272.europe-west1.run.app";
  return `${apiUrl}${path}`;
};

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function formatCurrency(
  amount: number,
  currency: string = "USD"
): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(amount);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function validateFileType(file: File, acceptedTypes: string): boolean {
  if (!acceptedTypes) return true;
  const types = acceptedTypes.split(",").map((type) => type.trim());
  return types.some((type) => {
    if (type.startsWith(".")) {
      return file.name.toLowerCase().endsWith(type.toLowerCase());
    }
    if (type.includes("*")) {
      const [main] = type.split("*");
      return file.type.startsWith(main);
    }
    return file.type === type;
  });
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String(error);
}
