"use client";

import { useTheme } from "next-themes";
import Image from "next/image";
import { useEffect, useState } from "react";

interface ThemedImageProps {
  lightSrc: string;
  darkSrc: string;
  alt: string;
  width: number;
  height: number;
}

export function ThemedImage({
  lightSrc,
  darkSrc,
  alt,
  width,
  height,
}: ThemedImageProps) {
  const { theme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    // Render a placeholder or nothing to avoid hydration mismatch
    return (
      <div
        style={{ width, height }}
        className="bg-gray-200 dark:bg-gray-800 rounded-xl"
      />
    );
  }

  const src = resolvedTheme === "dark" ? darkSrc : lightSrc;

  return (
    <Image
      src={src}
      alt={alt}
      width={width}
      height={height}
      className="w-full h-auto rounded-xl shadow-2xl"
    />
  );
}
