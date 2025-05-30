# AI 커플 상담 채팅 앱 - 시스템 통합 가이드

## 현재 상황
- **Spring Backend**: 로그인/회원가입 완료, 프론트엔드와 연결됨. JWT 토큰 발급 (페이로드에 `member_id` 및 커플 관련 정보 포함).
- **FastAPI Backend**: 채팅 기능 구현 (순수 WebSocket 사용).
- **Node.js/TypeScript 프론트엔드**: 로그인 시 Spring으로부터 받은 토큰을 localStorage에 저장 (예: `imean_access_token`).
- **목표**: 모든 시스템을 연결하여 실시간 채팅이 가능하도록 통합.

## 통합 아키텍처 설계

### 1. 토큰 검증 방식 결정
**방식: JWT 토큰 공유 검증**
- Spring에서 생성한 JWT 토큰을 FastAPI 서버에서 검증.
- 동일한 JWT 비밀키를 Spring과 FastAPI 서버에서 공유.
- 환경변수 (`JWT_SECRET_KEY`)로 비밀키 관리.

### 2. 사용자 정보 동기화 방안

**Option A: 데이터베이스 공유 (현재 프로젝트 구조에 가까움)**
- Spring과 FastAPI가 동일한 사용자/커플 정보 관련 테이블에 접근할 수 있도록 구성 (스키마 동기화 필요).
- FastAPI는 토큰 검증 후 `member_id`를 통해 필요한 사용자 정보를 DB에서 조회.

**Option B: API 호출 방식 (필요시 고려)**
- FastAPI 서버가 인증/인가 또는 추가 사용자 정보 필요시 Spring API를 호출.
- 이 경우, FastAPI는 Spring API 클라이언트 역할 수행.

## 구현 단계별 가이드

### Phase 1: FastAPI 서버 준비
```python
# FastAPI 서버에서 필요한 주요 기능 (현재 프로젝트 구조 반영)
# - JWT 토큰 검증 로직 (Spring과 호환)
# - WebSocket 연결 핸들러에서 토큰 검증 및 사용자 식별 (member_id 사용)
# - 채팅방(Room) 및 세션(Session) 관리 로직 (DB와 연동)
# - 메시지 수신, 처리, 브로드캐스팅 로직

# 제거되었거나 필요 없는 기능 (기존 Python 소켓서버 기준)
# - 임시 사용자 테이블 관련 코드 (Spring DB 또는 공유 DB 사용)
# - FastAPI 자체의 별도 토큰 생성 로직 (Spring 토큰 사용)
# - 임시 인증 시스템 (Spring 토큰 검증으로 대체)
```

### Phase 2: 토큰 검증 시스템 구축 (FastAPI)
```python
# FastAPI 웹소켓 핸들러 또는 의존성 주입 함수 내 토큰 검증 예시
import jwt
from fastapi import WebSocket, Query, status, HTTPException
import os # 환경 변수 사용을 위해

# SECRET_KEY는 .env 파일에서 로드
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256" # Spring과 동일한 알고리즘 사용

async def verify_spring_token(token: str = Query(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        member_id: str = payload.get("sub") # Spring 토큰의 사용자 식별자 키 (예: "sub", "member_id") 확인 필요
        if member_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: member_id missing")
        
        # 추가적으로 필요한 정보 (예: couple_id)가 토큰에 있다면 여기서 추출
        # couple_id = payload.get("couple_id") 
        # if couple_id is None:
        #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: couple_id missing")

        return {"member_id": member_id} # , "couple_id": couple_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# FastAPI 웹소켓 엔드포인트 예시 (현재 프로젝트 main.py 참고)
# @app.websocket("/api/sessions/ws/{room_id}")
# async def websocket_endpoint(
#     websocket: WebSocket,
#     room_id: int,
#     token_payload: dict = Depends(verify_spring_token) # 토큰 검증 의존성 주입
# ):
#     member_id = token_payload["member_id"]
#     # couple_id = token_payload["couple_id"] # 토큰에서 couple_id를 가져오거나, room_id와 member_id로 DB에서 조회
#     
#     await manager.connect(websocket, room_id, member_id) # ConnectionManager의 connect 호출
#     try:
#         # ... (메시지 수신 및 처리 로직) ...
#     except WebSocketDisconnect:
#         manager.disconnect(room_id, member_id)
```
*참고: 위 `verify_spring_token` 함수는 예시이며, 실제 Spring 토큰의 페이로드 구조에 맞게 `payload.get()`의 키 값을 조정해야 합니다. `member_id`를 `sub`으로 사용하는 경우가 많습니다.*

### Phase 3: 프론트엔드 WebSocket 연결 (TypeScript)
```typescript
// 프론트엔드에서 WebSocket 연결 시 토큰 전달
const accessToken = localStorage.getItem('imean_access_token'); // Spring 로그인 후 저장된 토큰 키
const roomId = /* 채팅방 ID - API 호출 또는 다른 경로로 획득 */;

// FastAPI 웹소켓 엔드포인트 URL (실제 프로젝트의 경로 확인 후 적용)
// 예시: ws://localhost:8000/api/sessions/ws/{room_id}?token=${accessToken}
// 여기서 REACT_APP_SOCKET_URL은 FastAPI 서버의 기본 주소 (예: http://localhost:8000)
const fastapiServerBaseUrl = process.env.REACT_APP_SOCKET_URL || 'ws://localhost:8000'; // 환경변수 사용
const socketUrl = `${fastapiServerBaseUrl.replace('http', 'ws')}/api/sessions/ws/${roomId}?token=${accessToken}`;

const socket = new WebSocket(socketUrl);

socket.onopen = () => {
    console.log('WebSocket connection established with FastAPI server.');
    // 연결 성공 후 초기 메시지 전송 또는 UI 업데이트
    // 예: socket.send(JSON.stringify({ type: "join_room", data: { roomId } }));
};

socket.onmessage = (event) => {
    try {
        const message = JSON.parse(event.data as string);
        console.log('Message from FastAPI server:', message);
        // 서버로부터 메시지 수신 처리 (타입에 따른 분기 등)
        // 예: if (message.type === "message") { ... }
        // 예: if (message.type === "session") { ... } // 세션 정보 업데이트
    } catch (error) {
        console.error('Error parsing message from server:', error, event.data);
    }
};

socket.onerror = (error) => {
    console.error('WebSocket error:', error);
    // 오류 처리 로직 (예: 사용자에게 알림, 로그인 페이지로 리다이렉트 등)
};

socket.onclose = (event) => {
    console.log('WebSocket connection closed:', event.code, event.reason);
    // 연결 종료 처리 로직
};

// 메시지 전송 함수 예시
function sendMessageToServer(content: string, currentSessionId: string) {
    if (socket.readyState === WebSocket.OPEN) {
        const messagePayload = {
            // type: "message", // 필요에 따라 메시지 타입 정의
            content: content,
            session_id: currentSessionId // 현재 세션 ID 포함 (FastAPI 메시지 구조 참고)
        };
        socket.send(JSON.stringify(messagePayload));
    } else {
        console.error('WebSocket is not open. ReadyState:', socket.readyState);
    }
}
```

### Phase 4: 채팅방 참여 및 세션 시작 프로토콜 (FastAPI)
FastAPI 서버는 웹소켓 연결 시 URL 경로의 `room_id`와 쿼리 파라미터의 `token`을 사용합니다.
1.  **연결 수립**: 프론트엔드는 `imean_access_token`과 대상 `room_id`를 포함하여 FastAPI 웹소켓 엔드포인트로 연결을 시도합니다. (예: `ws://localhost:8000/api/sessions/ws/{room_id}?token=xxx`)
2.  **토큰 검증**: FastAPI는 전달된 토큰을 검증하여 `member_id`를 획득하고 사용자를 인증합니다.
3.  **ConnectionManager 등록**: 인증된 사용자는 FastAPI의 `ConnectionManager`에 해당 `room_id`와 `member_id`로 등록됩니다. (`manager.connect(websocket, room_id, member_id)`)
4.  **세션 시작/정보 전송**:
    *   현재 프로젝트(`app/main.py`의 `websocket_endpoint`)에서는 두 명의 사용자가 접속하면 새 세션을 시작하거나 기존 세션 정보를 클라이언트에게 브로드캐스트합니다.
    *   클라이언트는 `{"type": "session", "content": "...", "session_id": "...", ...}` 형태의 메시지를 받아 현재 세션 ID 및 상태를 인지합니다.
    *   초기 시스템 안내 메시지 등도 이 단계에서 서버가 전송할 수 있습니다.
5.  **메시지 송수신**:
    *   **클라이언트 -> 서버**: 프론트엔드는 사용자가 입력한 메시지를 JSON 형식으로 직렬화하여 전송합니다. 이 때, 현재 활성화된 `session_id`를 포함해야 할 수 있습니다.
        ```json
        {
            "content": "안녕하세요!",
            "session_id": "현재_세션_ID" // FastAPI가 요구하는 구조에 따름
        }
        ```
    *   **서버 -> 클라이언트**: FastAPI는 수신한 메시지를 해당 `room_id`의 다른 사용자에게 브로드캐스트합니다. 메시지에는 발신자 정보(`member_id` 또는 서버가 지정한 식별자), 내용, 타임스탬프, `session_id` 등이 포함됩니다.
        ```json
        {
            "type": "message",
            "user_id": "보낸사람_member_id", // 또는 다른 식별자
            "content": "안녕하세요!",
            "timestamp": "2023-10-27T10:00:00Z",
            "session_id": "해당_메시지의_세션_ID"
        }
        ```
        (실제 프로젝트의 `ChatLog` 모델 및 `broadcast_to_room` 호출 시 전달되는 메시지 구조를 정확히 따라야 합니다.)

## 환경 설정

### Spring `application.yml` (또는 `.properties`)
(유지 - JWT 비밀키 및 유효기간 설정은 Spring에서 관리)
```yaml
jwt:
  secret: ${JWT_SECRET_KEY:your-secret-key-here} # FastAPI의 .env와 동일해야 함
  # ... 기타 Spring 설정 ...
```

### FastAPI `.env`
```env
JWT_SECRET_KEY=your-secret-key-here # Spring과 동일. 이미 작성된 상태.
DATABASE_URL=mysql+aiomysql://user:pass@host:port/dbname # FastAPI용 DB 접속 정보
# SPRING_API_BASE_URL=http://localhost:8080 # Option B 선택 시 필요
```

### Node.js 프론트엔드 `.env`
```env
REACT_APP_SPRING_API_URL=http://localhost:8080 # Spring API 서버 주소
REACT_APP_SOCKET_URL=http://localhost:8000   # FastAPI 서버 주소 (웹소켓 연결 시 ws:// 스킴 사용)
```

## 데이터 플로우

### 1. 로그인 플로우 (Spring 주도)
```
사용자 → 프론트엔드 → Spring API (/login) → JWT 토큰 생성 (`imean_access_token` 등) → 프론트엔드 localStorage 저장
```

### 2. 채팅 연결 플로우 (FastAPI 주도)
```
프론트엔드 (localStorage의 `imean_access_token` 사용) → FastAPI WebSocket 연결 요청 (예: /api/sessions/ws/{room_id}?token=...) → FastAPI 서버 → 토큰 검증 (공유 SECRET_KEY 사용, `member_id` 추출) → 사용자 정보 (필요시 DB 조회) → ConnectionManager 등록, 채팅방 입장 및 세션 시작 알림
```

### 3. 메시지 전송 플로우 (FastAPI 주도)
```
프론트엔드 (메시지 입력) → WebSocket 메시지 전송 (JSON, `content`, `session_id` 등 포함) → FastAPI 서버 → 해당 채팅방 사용자들에게 메시지 브로드캐스트 → (필요시) 메시지 DB 저장 (`ChatLog`)
```

## 테스트 시나리오

### 1. 인증 테스트
- [ ] 유효한 Spring 토큰으로 FastAPI WebSocket 연결 성공 (`member_id` 정상 식별)
- [ ] 만료된 Spring 토큰으로 FastAPI WebSocket 연결 실패 (적절한 에러 코드 및 메시지 반환)
- [ ] 잘못된/위변조된 토큰으로 FastAPI WebSocket 연결 실패

### 2. 채팅 기능 테스트
- [ ] 커플 간 실시간 메시지 송수신 (양방향)
- [ ] FastAPI 세션(`Session` 모델)별 메시지 그룹핑 및 DB 저장 확인
- [ ] `room_id` 및 토큰을 통해 채팅방 자동 참여 및 세션 시작 확인

### 3. 세션 관리 테스트 (FastAPI 기준)
- [ ] FastAPI `Session` 모델에 따른 시간별/주제별 세션 진행 로직 확인
- [ ] 세션 변경 시 프론트엔드에 알림 및 UI 업데이트 확인 (예: 새로운 `session_id` 및 주제 안내)
- [ ] 이전 세션 메시지 로드 기능 (구현되어 있다면 테스트)

## 주요 고려사항

1.  **보안**:
    *   `JWT_SECRET_KEY`의 안전한 관리 (환경변수 사용, 노출 금지).
    *   FastAPI의 CORS 설정: 프론트엔드 도메인만 허용하도록 구체적으로 설정 권장 (`allow_origins=["*"]`는 개발 초기 단계 이후에는 변경).
    *   WebSocket 통신 시 데이터 검증 (입력값 유효성 등).
2.  **에러 처리**:
    *   토큰 만료/무효, 네트워크 오류, WebSocket 연결 끊김 등 다양한 예외 상황에 대한 프론트엔드 및 백엔드의 견고한 처리.
    *   사용자에게 적절한 피드백 제공.
3.  **성능**:
    *   동시 접속자 수 증가에 따른 FastAPI 서버 성능 (비동기 처리, DB 커넥션 풀 등).
    *   메시지 브로드캐스팅 효율성.
4.  **확장성**:
    *   추후 AI 상담 기능 추가 시 메시지 흐름, AI 역할 정의 등 고려.
    *   API 엔드포인트 및 WebSocket 메시지 구조의 유연성.
5.  **사용자 식별자 일관성**: Spring의 `member_id` (또는 토큰 내 사용자 식별 키)를 FastAPI 전반에서 일관되게 사용하여 혼선 방지.

## 다음 단계

1.  FastAPI 서버에서 Spring JWT 토큰 검증 로직 최종 확인 및 적용 (`SECRET_KEY`, 알고리즘, 페이로드 키 일치).
2.  FastAPI의 `ConnectionManager` 및 웹소켓 핸들러가 `member_id`를 사용하도록 수정 (기존 `user_id` 사용 부분 변경).
3.  FastAPI의 데이터베이스 모델 및 로직에서 `User` 대신 `Member` 개념으로 명칭 또는 필드 조정 고려 (필수는 아니나, 일관성 확보).
4.  프론트엔드 WebSocket 연결 코드 수정 (순수 `WebSocket` 사용, FastAPI 엔드포인트 및 토큰 전달 방식 적용).
5.  프론트엔드에서 메시지 송수신 로직을 FastAPI의 JSON 구조에 맞게 수정.
6.  통합 테스트 집중 수행 (인증, 채팅 기본 기능, 세션 관리).
7.  CORS 및 기타 보안 설정 점검.