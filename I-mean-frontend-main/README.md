
## 🧠 I-MEAN-Frontend

커플 갈등 해소를 돕는 **AI 상담 챗 애플리케이션**의 프론트엔드입니다.
Next.js 기반의 TypeScript 프로젝트로, 도메인 기반 폴더 구조로 구성되어 유지보수성과 협업 효율을 높였습니다.

---

## 🚀 기술 스택

| 종류     | 사용 기술                      |
| ------ | -------------------------- |
| 프레임워크  | Next.js (App Router)       |
| 언어     | TypeScript                 |
| 스타일    | CSS (글로벌 스타일 적용)           |
| 상태관리   | (필요 시 추가)                  |
| API 통신 | Fetch API (환경변수 기반 URL 사용) |
| 기타     | dotenv, Git                |

---

## 📁 폴더 구조 및 역할

```bash
src/
├── app/                  # Next.js app 라우팅 구조 (layout, page)
├── components/           # 공통 UI 컴포넌트 (예: Button, Modal 등)
├── features/             # 도메인 단위 폴더 (auth, chat 등)
│   ├── auth/             # 인증 도메인
│   │   ├── components/   # auth 관련 UI 컴포넌트
│   │   ├── hooks/        # auth 관련 커스텀 훅
│   │   ├── pages/        # auth 관련 라우팅 페이지
│   │   └── types.ts      # auth 관련 타입 정의
│   └── chat/             # 채팅 도메인 구조 (auth와 동일)
├── lib/
│   └── api.ts            # 공통 API 요청 함수 정의 (ex: fetchSomething)
├── styles/               # 전역 스타일
├── types/                # 전체에서 쓰이는 전역 타입 정의
```

---

## 🧩 주요 파일 설명

| 파일               | 설명                                     |
| ---------------- | -------------------------------------- |
| `.env.local`     | 환경변수 설정 (API URL 등) - Git에는 올라가지 않음    |
| `next.config.ts` | Next.js 전역 설정 파일 (strict mode 등)       |
| `tsconfig.json`  | TypeScript 설정 및 alias(`@features/*` 등) |
| `lib/api.ts`     | 서버 API 요청 함수들 모아둔 파일                   |

---

## ✅ `.ts`, `.tsx`, `api.ts` 차이

| 파일       | 설명                            |
| -------- | ----------------------------- |
| `.tsx`   | 리액트 컴포넌트 파일. JSX 문법 포함. UI 반환 |
| `.ts`    | 타입, 로직, 유틸 함수 파일. JSX 없음      |
| `api.ts` | 공통 API 통신 로직을 분리해서 관리하는 용도    |

---

## 🌐 환경 변수 예시 (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8080/api
```

* `NEXT_PUBLIC_` 접두사를 붙여야 **브라우저에서도 읽을 수 있음**
* `.env.local` 파일은 `.gitignore`에 포함되어 있음
