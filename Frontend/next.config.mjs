/** @type {import('next').NextConfig} */
const nextConfig = {
  // Safari compatibility optimizations
  experimental: {
    optimizeServerReact: false, // Better Safari compatibility
  },

  // Compiler optimizations for Safari
  compiler: {
    styledComponents: false, // Disable if not using styled-components
    removeConsole:
      process.env.NODE_ENV === "production"
        ? { exclude: ["error", "warn"] }
        : false,
  },

  // Headers for Safari compatibility
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
          // Safari-specific headers
          {
            key: "X-WebKit-CSP",
            value:
              "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:",
          },
        ],
      },
    ];
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
