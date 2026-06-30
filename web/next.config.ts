import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow images from S3
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.amazonaws.com",
      },
    ],
  },
};

export default nextConfig;
