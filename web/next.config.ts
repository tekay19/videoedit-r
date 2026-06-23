import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bu klasörü workspace kökü olarak sabitle (birden fazla klasör/lockfile
  // olduğunda Turbopack'in yanlış kök çıkarımını engeller).
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
