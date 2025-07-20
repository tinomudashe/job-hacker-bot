/** @type {import('next').NextConfig} */
import path from "path";

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

  // Webpack optimizations for Safari
  webpack: (config, { dev, isServer }) => {
    // Add alias to resolve @/ paths
    config.resolve.alias["@"] = path.resolve("./");

    // Safari-specific optimizations
    if (!dev && !isServer) {
      // Optimize for Safari's JavaScript engine
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          ...config.optimization.splitChunks,
          cacheGroups: {
            ...config.optimization.splitChunks?.cacheGroups,
            // Create separate chunk for polyfills (Safari needs more)
            polyfills: {
              name: "polyfills",
              test: /[\\/]node_modules[\\/](core-js|regenerator-runtime)/,
              priority: 10,
              chunks: "all",
            },
          },
        },
      };
    }

    return config;
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
