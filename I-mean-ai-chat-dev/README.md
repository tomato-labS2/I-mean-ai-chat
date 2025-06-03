# I-mean-AI-Chat

AI 기반 커플 상담형 챗 서비스 (채팅, AI)

> 커플 간 감정과 상황을 조율하고 대화를 유도하는 FastAPI 기반 GPT 상담 서버

---

## 📦 프로젝트 구조

```bash
I-mean-ai-chat/
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── api/                 # 라우터 모듈
│   ├── models/              # Pydantic 요청/응답 모델
│   ├── services/            # GPT, 감정 필터, konlpy 등 기능 로직
│   └── utils/               # 유틸리티 함수
├── .env.sample              # 환경변수 샘플 파일 (복사해서 사용)
├── requirements.txt         # 설치된 패키지 목록
├── .gitignore               # 깃 무시 설정
```

---

## 🛠 개발 환경 설정

### 1. 가상환경 생성 및 패키지 설치

```bash
python -m venv venv
venv\Scripts\activate    # 윈도우일 경우

pip install -r requirements.txt
```

또는 수동 설치:

```bash
pip install fastapi uvicorn[standard] python-dotenv openai konlpy
```

### 2. `.env` 파일 설정

```bash
cp .env.sample .env.dev
```

`.env.dev` 내용 예시:

```env
ENV=dev
DB_URL=mysql+pymysql://root:1234@localhost:3306/imean_dev
OPENAI_API_KEY=your_openai_key_here
LOG_LEVEL=debug
```

> 실제 운영에서는 `.env.prod`를 서버에 직접 구성하며, Git에 포함하지 않음.

---

## 🚀 실행 방법

```bash
uvicorn app.main:app --reload
```

접속 확인:

* 기본 라우터: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## ✅ 설치된 주요 패키지

| 패키지                | 설명                 |
| ------------------ | ------------------ |
| fastapi            | 웹 프레임워크            |
| uvicorn\[standard] | ASGI 서버 실행기        |
| python-dotenv      | .env 환경 변수 로드      |
| openai             | GPT API 연동         |
| konlpy             | 형태소 분석기 (Okt 등 사용) |

---

## 📌 진행 상태 요약

* [x] FastAPI 기본 세팅 완료
* [x] `.env` 환경 분리 적용
* [x] konlpy 테스트 준비
* [x] GPT 연동용 service 구조 마련
* [ ] 감정 필터링/중재 로직 구현 예정
* [ ] 커플 대화 흐름 API 설계 예정

---

## 🙋‍♀️ 팀 공지용 공유 포인트

* `.env.sample`로만 Git 커밋
* `.env.dev`는 각자 로컬에서 생성
* `pip freeze > requirements.txt`로 의존성 업데이트

---

함께하는 AI 커플 챗 프로젝트 — 더 나은 대화를 위한 작은 시작! 💬💚
