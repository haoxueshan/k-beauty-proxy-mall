const apiProxyTarget = (
  process.env.API_PROXY_TARGET ||
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "")
).replace(/\/+$/, "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**"
      }
    ]
  },
  async rewrites() {
    if (!apiProxyTarget) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`
      },
      {
        source: "/health",
        destination: `${apiProxyTarget}/health`
      }
    ];
  }
};

module.exports = nextConfig;
