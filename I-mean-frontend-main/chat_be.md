1. HTTP API 기본 URL: http://localhost:5501
WebSocket 접속 URL: ws://localhost:5501/api/sessions/ws/{room_id}?token={JWT_토큰}
{room_id}: 접속하려는 채팅방의 ID입니다.
{JWT_토큰}: Spring 서버에서 로그인 후 발급받은 JWT 토큰입니다. : local storage 에서 "imean_access_token" 으로 저장됨.

2. 인증 (Authentication):
HTTP API 요청 시:
클라이언트는 Spring 서버에서 발급받은 JWT를 HTTP 요청 헤더의 Authorization 필드에 Bearer <JWT_토큰> 형식으로 포함해야 합니다.
예시: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
WebSocket 연결 시:
위의 WebSocket 접속 URL에 명시된 것처럼, 쿼리 파라미터 token 값으로 JWT 토큰을 전달해야 합니다.

3. 주요 API 엔드포인트 및 요청/응답:
채팅방 생성/참여:
엔드포인트: POST /api/rooms
요청 헤더: Authorization: Bearer <JWT_토큰>
요청 본문 (JSON):
        {
          "room_name": "둘만의 대화방", // 원하는 방 이름
          "couple_id": 123            // 커플 ID (숫자)
        }
성공 응답 (JSON, HTTP 200):
        {
          "room_id": 1, // 생성되거나 참여한 방의 ID
          "room_name": "둘만의 대화방",
          "couple_id": 123,
          "created_at": "2023-10-27T10:30:00.123Z", // ISO 8601 형식 타임스탬프
          "is_existing": false // false면 새로 생성됨, true면 기존 방에 참여
        }
실패 응답:
HTTP 401 Unauthorized: 토큰이 없거나 유효하지 않은 경우.
HTTP 400 Bad Request: 요청 본문이 잘못된 경우 (예: room_name 누락).
HTTP 500 Internal Server Error: 서버 내부 오류.

4. WebSocket 메시지 프로토콜:
클라이언트와 서버는 WebSocket을 통해 JSON 형식의 메시지를 주고받습니다. 모든 메시지는 type 필드를 가져 메시지의 종류를 구분합니다.
클라이언트 -> 서버 메시지:
        {
          "type": "message",
          "content": "안녕하세요! 오늘 날씨 좋네요."
        }
세션 연장/종료 응답 (서버가 연장 여부를 물었을 때):
        {
          "type": "response",
          "content": "네" // 또는 "아니요"
        }
서버 -> 클라이언트 메시지:
다른 사용자의 채팅 메시지 수신:
        {
          "type": "message",
          "user_id": "상대방_사용자_ID", // 메시지를 보낸 사용자의 ID (JWT의 'sub' 값)
          "content": "네, 정말 좋아요!",
          "timestamp": "2023-10-27T10:31:00.456Z", // 메시지 수신 시간 (서버 기준)
          "session_id": 5 // 현재 진행중인 세션의 ID (세션 진행 중에만 포함)
        }
시스템 메시지 수신 (안내, 경고, 세션 시작/종료 알림 등):
        {
          "type": "system",
          "content": "상황에 대한 대화 시간이 종료되었습니다. 계속하시겠습니까?",
          "timestamp": "2023-10-27T10:50:00.789Z"
        }
세션 정보 업데이트 (새로운 세션 시작, 주제 변경 등):
        {
          "type": "session",
          "content": "이제 감정에 대한 대화를 시작하겠습니다.", // 안내 메시지
          "session_id": 6,                             // 새로운 세션 ID
          "topic": "topic_2_emotion",                  // 새로운 세션 주제
          "timestamp": "2023-10-27T10:51:00.123Z"
        }
topic 종류:
topic_1_situation: 상황 관련 대화
topic_2_emotion: 감정 관련 대화
프론트엔드 개발 시 주요 흐름:
사용자는 Spring 서버를 통해 로그인하고 JWT 토큰을 발급받습니다.
발급받은 JWT 토큰을 안전하게 저장합니다 (예: 브라우저의 localStorage, sessionStorage 또는 메모리).
채팅방에 입장하거나 생성하려면 /api/rooms 엔드포인트로 JWT와 함께 POST 요청을 보냅니다. 응답으로 room_id를 받습니다.
받은 room_id와 JWT 토큰을 사용하여 WebSocket URL에 연결합니다.
WebSocket 연결이 성공하면, 정의된 메시지 프로토콜에 따라 메시지를 주고받습니다.
서버로부터 오는 메시지의 type을 확인하여 UI를 적절히 업데이트합니다. (새 메시지 표시, 시스템 알림 표시 등)
사용자가 메시지를 입력하면 지정된 JSON 형식으로 서버에 전송합니다.
서버가 세션 연장 여부를 물어보면("type": "system" 메시지), 사용자의 선택("네"/"아니요")을 받아 "type": "response" 메시지로 응답합니다.