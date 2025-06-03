import React, { useEffect, useState, useCallback } from 'react';
import {
  connectWebSocket,
  sendWebSocketMessage,
  closeWebSocket,
  WebSocketMessage,
  SystemPromptCallback
} from '../lib/websocket'; // 경로가 실제 프로젝트 구조에 맞는지 확인해주세요.

interface ChatRoomProps {
  roomId: string | number;
  currentUserId: string; // 현재 로그인한 사용자의 ID
}

interface SystemPromptInfo {
  message: string;
  sessionId: number | undefined;
}

const ChatRoom: React.FC<ChatRoomProps> = ({ roomId, currentUserId }) => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState<SystemPromptInfo | null>(null);

  const handleSystemPrompt: SystemPromptCallback = useCallback((message, sessionId) => {
    console.log('System prompt received in component:', message, sessionId);
    setSystemPrompt({ message, sessionId });
  }, []);

  const handleMessageReceived = useCallback((message: WebSocketMessage) => {
    setMessages((prevMessages) => [...prevMessages, message]);
    if (message.type === 'system' && systemPrompt && !message.content?.includes('계속하시겠습니까?')) {
        setSystemPrompt(null);
    }
  }, [systemPrompt]);

  const handleSessionUpdate = useCallback((message: WebSocketMessage) => {
    console.log('Session updated in component:', message);
    setMessages((prevMessages) => [...prevMessages, message]);
  }, []);

  useEffect(() => {
    if (!roomId) return;

    console.log(`Attempting to connect to WebSocket for room: ${roomId}`);
    connectWebSocket(
      roomId,
      handleSystemPrompt,
      handleMessageReceived,
      handleSessionUpdate
    )
      .then(() => {
        console.log('Successfully connected to WebSocket.');
        setIsConnected(true);
      })
      .catch((error) => {
        console.error('Failed to connect to WebSocket:', error);
        setIsConnected(false);
      });

    return () => {
      console.log('Closing WebSocket connection.');
      closeWebSocket();
      setIsConnected(false);
    };
  }, [roomId, handleSystemPrompt, handleMessageReceived, handleSessionUpdate]);

  const handleSendMessage = () => {
    if (inputValue.trim() && isConnected) {
      // 클라이언트에서 보내는 메시지에는 user_id를 포함하지 않음 (서버가 토큰으로 식별)
      sendWebSocketMessage('message', inputValue.trim());
      setInputValue('');
    } else if (!isConnected) {
      console.error('Cannot send message, WebSocket is not connected.');
      alert('서버에 연결되지 않았습니다. 잠시 후 다시 시도해주세요.');
    }
  };

  const handlePromptResponse = (response: boolean) => {
    if (systemPrompt) {
      sendWebSocketMessage('response', response ? '네' : '아니요');
      setSystemPrompt(null); 
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: 'auto' }}>
      <h2>채팅방 (Room ID: {roomId})</h2>
      <div style={{ 
        border: '1px solid #ccc', 
        padding: '10px', 
        height: '300px', 
        overflowY: 'auto', 
        marginBottom: '10px' 
      }}>
        {messages.map((msg, index) => {
          const isMyMessage = msg.user_id === currentUserId;
          return (
            <div 
              key={index} 
              style={{
                marginBottom: '5px', 
                padding: '8px 12px', // 패딩 조정
                borderRadius: '8px', // 좀 더 둥글게
                backgroundColor: msg.type === 'system' || msg.type === 'session' 
                                 ? '#e9ecef' // 시스템 메시지 배경색 변경
                                 : isMyMessage 
                                   ? '#dcf8c6' // 내 메시지 배경색 변경 (연한 녹색)
                                   : '#ffffff', // 상대방 메시지 배경색 (흰색)
                border: msg.type !== 'system' && msg.type !== 'session' && !isMyMessage 
                        ? '1px solid #e0e0e0' // 상대방 메시지 테두리
                        : 'none',
                marginLeft: isMyMessage && msg.type !== 'system' && msg.type !== 'session' ? 'auto' : '0', // 내 메시지 오른쪽 정렬
                marginRight: !isMyMessage && msg.type !== 'system' && msg.type !== 'session' ? 'auto' : '0', // 상대 메시지 왼쪽 정렬
                maxWidth: '75%', // 메시지 최대 너비
                float: isMyMessage ? 'right' : 'left', // float으로 정렬 (개선된 정렬 방식)
                clear: 'both', // float 해제
                boxShadow: '0 1px 1px rgba(0,0,0,0.05)' // 약간의 그림자 효과
              }}
            >
              <strong>
                {msg.type === 'system' || msg.type === 'session' 
                  ? msg.type.toUpperCase() 
                  : (isMyMessage ? '나' : `상대방`)}{/* 현재는 상대방 ID를 표시하지 않음 */}
                {/* {msg.user_id ? (isMyMessage ? '나' : `User ${msg.user_id}`) : msg.type.toUpperCase()}: */}
              </strong>
              <span style={{ display: 'block', marginTop: '3px' }}> {/* 메시지 내용 줄바꿈 및 간격 */} 
                {typeof msg.content === 'object' ? JSON.stringify(msg.content) : msg.content}
              </span>
              {msg.timestamp && 
                <small style={{ 
                  display:'block', // 시간도 별도 줄로
                  marginTop: '5px', 
                  color: '#888', 
                  textAlign: isMyMessage ? 'right' : 'left' // 시간 정렬
                }}>
                  ({new Date(msg.timestamp).toLocaleTimeString()})
                </small>}
            </div>
          );
        })}
      </div>

      {systemPrompt && (
        <div style={{ 
          border: '1px solid #007bff', 
          padding: '15px', 
          marginBottom: '10px', 
          backgroundColor: '#f8f9fa',
          borderRadius: '5px'
        }}>
          <p style={{ margin: '0 0 10px 0' }}><strong>시스템 알림:</strong> {systemPrompt.message}</p>
          <button 
            onClick={() => handlePromptResponse(true)} 
            style={{ marginRight: '10px', padding: '8px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            네
          </button>
          <button 
            onClick={() => handlePromptResponse(false)}
            style={{ padding: '8px 15px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            아니요
          </button>        
        </div>
      )}

      <div style={{ display: 'flex', clear: 'both', paddingTop: '10px' /* 메시지 영역과 겹치지 않도록 */ }}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          style={{ flexGrow: 1, padding: '10px', marginRight: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
          placeholder={isConnected ? "메시지를 입력하세요..." : "연결 중..."}
          disabled={!isConnected || !!systemPrompt}
        />
        <button 
          onClick={handleSendMessage}
          style={{ padding: '10px 15px', borderRadius: '5px', border: 'none', backgroundColor: '#007bff', color: 'white' }}
          disabled={!isConnected || !!systemPrompt}
        >
          보내기
        </button>
      </div>
      <p style={{ marginTop: '10px', textAlign: 'center' }}>Connection Status: {isConnected ? 
        <span style={{color: 'green', fontWeight:'bold'}}>● Connected</span> : 
        <span style={{color: 'red', fontWeight:'bold'}}>● Disconnected</span>}
      </p>
    </div>
  );
};

export default ChatRoom; 