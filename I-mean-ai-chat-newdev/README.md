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
│   ├── utils/               # 유틸리티 함수
│   │   ├── logger.py        # 로깅 시스템
│   │   ├── exceptions.py    # 커스텀 예외 클래스
│   │   └── error_handler.py # 에러 핸들러
│   └── routers/             # API 라우터
├── logs/                    # 로그 파일 저장 디렉토리
├── env.sample               # 환경변수 샘플 파일 (복사해서 사용)
├── requirements.txt         # 설치된 패키지 목록
└── .gitignore               # 깃 무시 설정
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

### 2. 환경변수 설정

```bash
cp env.sample .env.dev
```

`.env.dev` 내용 예시:

```env
# Database Configuration
DB_URL=mysql+pymysql://root:1234@localhost:9915/i_mean

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here_make_it_long_and_random

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
SESSION_DURATION_MINUTES=1

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs

# Environment
ENV=dev
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

## 📋 로깅 시스템

### 로그 레벨
- **DEBUG**: 상세한 디버깅 정보
- **INFO**: 일반적인 정보 메시지
- **WARNING**: 경고 메시지
- **ERROR**: 오류 메시지
- **CRITICAL**: 심각한 오류 메시지

### 로그 파일
- `logs/app.log`: 일반 로그 (INFO 레벨 이상)
- `logs/error.log`: 오류 로그 (ERROR 레벨 이상)
- `logs/debug.log`: 디버그 로그 (DEBUG 레벨)

### 로그 포맷
```
2024-01-01 12:00:00 - imean_chat.main - INFO - Application startup completed successfully
```

---

## 🛡️ 에러 핸들링

### 커스텀 예외 클래스
- `ImeanBaseException`: 기본 예외 클래스
- `AuthenticationError`: 인증 관련 예외
- `ValidationError`: 데이터 검증 예외
- `DatabaseError`: 데이터베이스 관련 예외
- `OpenAIServiceError`: OpenAI 서비스 관련 예외
- `WebSocketError`: WebSocket 관련 예외

### 에러 응답 형식
```json
{
  "message": "오류 메시지",
  "error_code": "ERROR_CODE",
  "details": {
    "additional_info": "추가 정보"
  }
}
```

### 전역 에러 핸들러
- 요청 검증 오류 (422)
- HTTP 예외 (400, 401, 403, 404, 500 등)
- 데이터베이스 오류
- WebSocket 오류
- OpenAI 서비스 오류

---

## 📌 진행 상태 요약

* [x] FastAPI 기본 세팅 완료
* [x] `.env` 환경 분리 적용
* [x] konlpy 테스트 준비
* [x] GPT 연동용 service 구조 마련
* [x] 로깅 시스템 구축
* [x] 에러 핸들링 강화
* [ ] 감정 필터링/중재 로직 구현 예정
* [ ] 커플 대화 흐름 API 설계 예정

---

## 🔧 개발 가이드

### 로깅 사용법
```python
from app.utils.logger import get_logger

logger = get_logger("your_module_name")

logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("오류 메시지", exc_info=True)
```

### 예외 처리
```python
from app.utils.exceptions import ValidationError, DatabaseError

try:
    # 코드 실행
    pass
except ValidationError as e:
    logger.error(f"검증 오류: {e.message}")
except DatabaseError as e:
    logger.error(f"데이터베이스 오류: {e.message}")
```

---

## 🙋‍♀️ 팀 공지용 공유 포인트

* `env.sample`로만 Git 커밋
* `.env.dev`는 각자 로컬에서 생성
* `pip freeze > requirements.txt`로 의존성 업데이트
* 로그 파일은 `logs/` 디렉토리에 저장
* 민감한 정보는 로그에 기록하지 않음

---

함께하는 AI 커플 챗 프로젝트 — 더 나은 대화를 위한 작은 시작! 💬💚
