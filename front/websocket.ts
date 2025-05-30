import type { ChatMessage } from "@/features/chat/types"; // ChatMessage 타입 임포트

const WEBSOCKET_URL = 'ws://localhost:8000/api/sessions/ws';
// 다른 가능한 WebSocket URL들:
// const WEBSOCKET_URL = 'ws://localhost:8000/ws/sessions';
// const WEBSOCKET_URL = 'ws://localhost:8000/ws';

let socket: WebSocket | null = null;
let currentSessionId: number | undefined = undefined; // 현재 세션 ID 저장

// 시스템 프롬프트 발생 시 UI에 알리고 사용자 응답을 받을 콜백 타입
export type SystemPromptCallback = (message: string, sessionId: number | undefined) => void;

// WebSocketMessage 인터페이스를 export하여 외부에서 타입 참조 가능하도록 수정
export interface WebSocketMessage {
  type: "message" | "ai_message" | "system" | "session" | "response" | "error" | "chat_history";
  content?: string;
  user_id?: string | number;
  timestamp?: string | Date; 
  session_id?: number;
  messages?: ChatMessage[]; 
  error?: string;
}

// WebSocket 연결 테스트 함수 추가
export const testWebSocketConnection = async (roomId: string | number): Promise<boolean> => {
  const token = localStorage.getItem('imean_access_token');
  if (!token) {
    console.error('JWT token not found for connection test');
    return false;
  }

  const testUrls = [
    `ws://localhost:8000/api/sessions/ws/${roomId}?token=${token}`,
    `ws://localhost:8000/ws/sessions/${roomId}?token=${token}`,
    `ws://localhost:8000/ws/${roomId}?token=${token}`,
    `ws://localhost:8000/api/ws/${roomId}?token=${token}`
  ];

  for (const testUrl of testUrls) {
    try {
      console.log('WebSocket URL 테스트:', testUrl);
      const testSocket = new WebSocket(testUrl);
      
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          testSocket.close();
          resolve(false);
        }, 2000);

        testSocket.onopen = () => {
          console.log('✅ WebSocket 연결 성공:', testUrl);
          clearTimeout(timeout);
          testSocket.close();
          resolve(true);
        };

        testSocket.onerror = () => {
          console.log('❌ WebSocket 연결 실패:', testUrl);
          clearTimeout(timeout);
          resolve(false);
        };
      });
    } catch (error) {
      console.log('❌ WebSocket URL 에러:', testUrl, error);
    }
  }
  
  return false;
};

// onSystemPrompt 콜백을 인자로 추가
export const connectWebSocket = (
  roomId: string | number,
  onSystemPrompt: SystemPromptCallback,
  onMessageReceived: (message: WebSocketMessage) => void,
  onSessionUpdate: (message: WebSocketMessage) => void,
  onConnectionSuccess?: () => void,
  onConnectionError?: (event?: Event | CloseEvent) => void,
  onConnectionClose?: (event?: CloseEvent) => void
): Promise<void> => {
  return new Promise((resolve, reject) => {
    const token = localStorage.getItem('imean_access_token');
    if (!token) {
      console.error('JWT token not found in localStorage.');
      reject(new Error('JWT token not found'));
      return;
    }

    const url = `${WEBSOCKET_URL}/${roomId}?token=${token}`;
    console.log('WebSocket 연결 시도:', {
      url: url,
      roomId: roomId,
      hasToken: !!token,
      tokenLength: token.length
    });

    // 이미 연결되어 있거나 연결 중인 경우, 먼저 기존 연결을 명확히 닫음
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      console.log('기존 WebSocket 연결 종료, readyState:', socket.readyState);
      socket.onclose = null; // 기존 onclose 핸들러 제거
      socket.onerror = null; // 기존 onerror 핸들러 제거
      socket.onopen = null; // 기존 onopen 핸들러 제거
      socket.onmessage = null; // 기존 onmessage 핸들러 제거
      socket.close();
      socket = null; // 소켓 참조 제거
      currentSessionId = undefined;
    }
    
    socket = new WebSocket(url);
    console.log('WebSocket 객체 생성 완료, readyState:', socket.readyState);

    socket.onopen = () => {
      console.log('WebSocket connection established successfully!');
      currentSessionId = undefined; // 연결 시 세션 ID 초기화
      if (onConnectionSuccess) onConnectionSuccess();
      resolve();
    };

    socket.onmessage = (event) => {
      try {
        const rawMessage = JSON.parse(event.data as string);
        console.log("Raw WebSocket message received (websocket.ts):", rawMessage);

        const messageType = rawMessage.type as WebSocketMessage['type'];
        const validMessageTypes: WebSocketMessage['type'][] = ["message", "ai_message", "system", "session", "response", "error", "chat_history"];

        if (!validMessageTypes.includes(messageType)) {
            console.error("Invalid or missing message type from server:", rawMessage.type, rawMessage);
            onMessageReceived?.({
              type: "error",
              content: `서버로부터 알 수 없는 메시지 타입('${rawMessage.type}')을 수신했습니다.`,
              timestamp: new Date().toISOString(),
            });
            return;
        }

        const message: WebSocketMessage = {
          type: messageType, 
          content: rawMessage.content,
          user_id: rawMessage.user_id || rawMessage.member_code || rawMessage.memberId,
          timestamp: rawMessage.timestamp || new Date().toISOString(),
          session_id: rawMessage.session_id,
          messages: messageType === 'chat_history' ? (rawMessage.messages || []) : undefined,
          error: rawMessage.error,
        };
        
        switch (message.type) {
          case "system":
            if (message.content?.includes("계속하시겠습니까?")) {
              onSystemPrompt(message.content, message.session_id);
            } else {
              onMessageReceived(message); 
            }
            break;
          case "session":
            onSessionUpdate(message);
            break;
          case "chat_history":
          case "message":
          case "ai_message":
          case "error":
          case "response":
            onMessageReceived(message);
            break;
          default: 
            const _exhaustiveCheck: never = message.type;
            console.warn("Unhandled WebSocket message type (pre-validated, should not reach here):", _exhaustiveCheck, message);
            onMessageReceived?.({ ...message, type: "error", content: `Unhandled type: ${_exhaustiveCheck}`});
        }

      } catch (error) {
        console.error("Error processing WebSocket message:", error, event.data);
        onMessageReceived?.({
          type: "error",
          content: "메시지 처리 중 오류가 발생했습니다.",
          timestamp: new Date().toISOString(),
        });
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error details:', {
        error: error,
        readyState: socket?.readyState,
        url: url,
        timestamp: new Date().toISOString()
      });
      if (onConnectionError) onConnectionError(error as Event);
      handleReconnect();
    };

    socket.onclose = (event) => {
      console.log('WebSocket connection closed:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
        timestamp: new Date().toISOString()
      });
      socket = null;
      currentSessionId = undefined;
      if (onConnectionClose) onConnectionClose(event);
      if (event.code !== 1000 && event.code !== 1005) { 
        handleReconnect();
      } else {
        // TODO: Implement reconnection logic if needed
      }
    };
  });
};

// sendMessage 함수는 type: 'response'일 경우 현재 sessionId를 포함하도록 수정
export const sendWebSocketMessage = (type: WebSocketMessage['type'], content: string, sessionId?: number) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    const messagePayload: Partial<WebSocketMessage> = { type, content };
    if (type === 'response' && currentSessionId !== undefined) {
      messagePayload.session_id = currentSessionId;
    }
    socket.send(JSON.stringify(messagePayload));
    console.log('Sent message:', messagePayload);
  } else {
    console.error('WebSocket is not connected or not open.');
  }
};

export const closeWebSocket = () => {
  if (socket) {
    socket.close();
  }
  currentSessionId = undefined;
};

const handleReconnect = () => {
  // Implementation of handleReconnect function
};

// Example usage comment (simplified to avoid linter issues)
/*
  To use this module:
  1. Import connectWebSocket, sendWebSocketMessage, closeWebSocket.
  2. Call connectWebSocket(roomId, handleSystemPrompt, handleMessageReceived, handleSessionUpdate) in your component (e.g., useEffect).
     - handleSystemPrompt: (message: string, sessionId: number | undefined) => void;
     - handleMessageReceived: (message: WebSocketMessage) => void;
     - handleSessionUpdate: (message: WebSocketMessage) => void;
  3. Use sendWebSocketMessage('type', payload) to send messages.
  4. Call closeWebSocket when the component unmounts or connection is no longer needed.

  Example for handling system prompts in a React component:

  const [prompt, setPrompt] = useState(null);

  const handleSysPrompt = (msg, sessionId) => {
    setPrompt({ msg, sessionId });
  };

  // In connectWebSocket call:
  // connectWebSocket(roomId, handleSysPrompt, ...);

  // In your JSX:
  // if (prompt) { ... UI to ask user ... sendWebSocketMessage('response', ...) ... setPrompt(null) ... }
*/ 