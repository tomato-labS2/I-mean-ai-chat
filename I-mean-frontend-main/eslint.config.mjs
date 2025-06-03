import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // 새 객체를 추가하여 특정 룰을 오버라이드합니다.
    rules: {
      "@next/next/no-img-element": "off", // <img> 태그 사용 시 ESLint 경고를 비활성화
    },
  },
];

export default eslintConfig;
