# Next.js 프론트엔드 Dockerfile
FROM node:18-alpine

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 모든 의존성 설치 (개발 의존성 포함)
RUN npm install

# 소스 코드 복사
COPY . .

# Next.js 애플리케이션 빌드 (ESLint 및 TypeScript 체크 비활성화)
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build -- --no-lint

# 포트 노출
EXPOSE 3000

# 환경 변수 설정
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 애플리케이션 실행 (정적 파일 서빙)
RUN npm install -g serve
CMD ["serve", "-s", "out", "-l", "3000"]
