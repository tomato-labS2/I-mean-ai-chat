import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,

  // 정적 export를 위한 옵션
  trailingSlash: true, //모든 경로에 슬래시 붙여서 S3에서 폴더처럼 인식
  output: "export",
  images: {
    loader: "akamai", // 정적 사이트에 적합한 이미지 처리 방식
    path: "/",        // 이미지 경로 기준
    unoptimized: true, // 이 설정을 추가
  },

  // (선택) basePath도 설정 가능
  // basePath: '/your-subpath',
};

export default nextConfig;