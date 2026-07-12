import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone output -> slim Docker image (docker-compose `frontend`
  // service copies only .next/standalone, not full node_modules).
  output: "standalone",
};

export default nextConfig;
