import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 便于 Docker 镜像体积更小
  output: "standalone",
};

export default nextConfig;
