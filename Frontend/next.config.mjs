/** @type {import('next').NextConfig} */
const nextConfig = {
  // Safari compatibility optimizations
  experimental: {
    optimizeServerReact: false, // Better Safari compatibility
    serverComponentsHmrCache: false, // Prevents Safari caching issues
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
        ],
      },
      {
        source: "/:path*(?:js|css|html)",
        headers: [
          {
            key: "Cache-Control",
            value: "no-store, max-age=0",
          },
        ],
      },
      {
        source: "/:path*(?:jpg|jpeg|gif|png|svg|ico|webp|mp4)",
        headers: [
          {
            key: "Cache-control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
