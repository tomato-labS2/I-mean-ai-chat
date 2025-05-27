# 커플 상담 채팅방 시스템 개발 요구사항

## 사용자 로그인
- 사용자 로그인은 spring 서버에서 이미 구현이 되어있는 상태.
- spring 서버에서는 jwt 를 발급해 사용자 인증 처리가 완료됨.
- 현재 python 서버에서는 클라이언트가 websocket 연결을 시작할 때 jwt를 검증하고 해당 사용자 정보를 기반으로 채팅방을 생성하거나 관리해야 함.

## 로그인 이후 로직

## 1. 채팅방 생성 및 입장
- 커플 중 한 사람이 '채팅방 생성' 버튼을 클릭하여 채팅방 이름을 입력하면 채팅방이 생성되고 자동 입장
- `room_id`(auto increment), `room_name`, `couple_id`가 `rooms` 테이블에 저장
- 커플로 연결된 상대방에게는 자동으로 동일한 채팅방이 생성되어 입장만 가능 (추가 생성 불가)

## 2. 단독 입장 시 동작
- 한 명만 입장한 경우: system 안내 메시지 표시하지 않음
- 상대방과의 일반 채팅만 가능
- 대화 내용과 `session` 정보는 DB에 저장하지 않음
- 단순 메시지 전송 기능만 제공

## 3. 양쪽 모두 입장 시 세션 시작
- 두 사람 모두 입장 시 새로운 `session` 시작
- 세션 DB 생성 (`대화 주제` 컬럼 값: `topic_1_situation`)
-  system 안내 멘트 출력: "안녕하세요~ 커플 상담을 도와드릴 AI 상담사입니다~~..."

## 4. 세션 관리
- 15분 타이머 시작 (서버에서 시간 관리)
- 모든 대화 내용을 `logs` DB에 저장
- 15분 경과 시 현재 세션 종료
- `session` 테이블의 `세션종료시각` 컬럼 업데이트

## 5. 세션 종료 후 옵션 선택
세션 종료 후 사용자에게 두 가지 옵션 제시: 대화 이어가기 or 다음 단계로 넘어가기

### 5-1. '이어가고 싶음' 선택 시
- 새로운 `session` 생성
- 세션 DB 생성 (`대화 주제`: `topic_2_situation`)

### 5-2. '넘어가고 싶음' 선택 시
- 새로운 `session` 생성
- 세션 DB 생성 (`대화 주제`: `topic_1_emotion`)

## 6. 데이터베이스 구조 요구사항

### rooms 테이블
- `room_id` (auto increment, primary key)
- `room_name` (varchar)
- `couple_id` (foreign key)

### sessions 테이블
- `session_id` (auto increment, primary key)
- `room_id` (foreign key)
- `user_a_id` (foreign key)
- `user_b_id` (foreign key)
- `대화주제` (varchar) - topic_1_situation, topic_2_situation, topic_1_emotion, topic_2_emotion 등
- `세션시작시각` (localtime)
- `세션종료시각` (localtime, nullable) 

### logs 테이블
- `log_id` (auto increment, primary key)
- `room_id` (foreign key)
- `role` (ENUM) - user, assistant, system
- `speaker` (ENUM) - A, B, AI
- `content` (text)
- `timestamp` (datetime)
- `emotion_flagged` (boolean) - 감정표현 표함 여부(중재 판단용)
- `detected_emotions` (text) - 감지된 감정 키워드 목록 (예: [“분노”, “서운함”])

## 7. 시스템 플로우
1. 채팅방 생성 → 2. 상대방 자동 채팅방 생성 → 3. 단독/양쪽 입장 분기 → 4. 세션 시작 및 타이머 → 5. 세션 종료 → 6. 옵션 선택 → 7. 새 세션 생성

## 8. 주요 기능 요구사항
- 실시간 채팅 기능
- 서버 기반 타이머 관리
- 세션 상태 관리
- 시스템 메시지 자동 발송
- 사용자 옵션 선택 UI
- 데이터 영속성 보장