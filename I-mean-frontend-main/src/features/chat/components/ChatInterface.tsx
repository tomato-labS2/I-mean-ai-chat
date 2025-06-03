"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { ArrowLeft, Send } from "lucide-react"
import type { ChatMessage } from "../types"
import { connectWebSocket, sendWebSocketMessage, closeWebSocket, testWebSocketConnection, type WebSocketMessage } from "@/lib/websocket"
import { tokenStorage } from "@/features/auth/utils/tokenStorage"

interface ChatInterfaceProps {
  roomName: string
  roomId: string
  messages: ChatMessage[]
  onMessageReceived: (message: ChatMessage) => void
  onHistoryReceived: (messages: ChatMessage[], roomId: string) => void
  onBack: () => void
}

export const ChatInterface = ({ roomName, roomId, messages, onMessageReceived, onHistoryReceived, onBack }: ChatInterfaceProps) => {
  const [inputMessage, setInputMessage] = useState("")
  const [isAiMode, setIsAiMode] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [systemPrompt, setSystemPrompt] = useState<{ message: string; sessionId: number | undefined } | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsInitializedRef = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (wsInitializedRef.current || !roomId) return
    wsInitializedRef.current = true

    let isMounted = true

    const setupWebSocket = async () => {
      if (!isMounted) return
      console.log(`[ChatInterface ${roomId}] WebSocket 연결 테스트 시작...`)
      const canConnect = await testWebSocketConnection(roomId)
      if (!isMounted) return

      if (!canConnect) {
        console.error(`[ChatInterface ${roomId}] WebSocket 연결 테스트 실패`)
        setIsConnected(false)
        return
      }

      const handleSystemPrompt = (message: string, sessionId: number | undefined) => {
        if (!isMounted) return
        console.log(`[ChatInterface ${roomId}] 시스템 프롬프트:`, message, sessionId)
        setSystemPrompt({ message, sessionId })
      }

      const handleWebSocketMessage = (wsMessage: WebSocketMessage) => {
        if (!isMounted) return
        console.log(`[ChatInterface ${roomId}] WebSocket 메시지 수신:`, wsMessage)

        if (wsMessage.type === "pong") {
          console.log(`[ChatInterface ${roomId}] pong 메시지 수신 - 연결 유지용`)
          return // 아무 것도 하지 않음
        }

        if (wsMessage.type === "chat_history" && wsMessage.messages) {
          const historyChatMessages: ChatMessage[] = wsMessage.messages.map(m => ({
            ...m,
            timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
          }))
          onHistoryReceived(historyChatMessages, roomId)
        } else {
          const currentMemberId = tokenStorage.getMemberId()?.toString()
          let timestamp = wsMessage.timestamp ? new Date(wsMessage.timestamp) : new Date()
          if (isNaN(timestamp.getTime())) timestamp = new Date()

          let sender: "user" | "partner" | "ai" = "partner"
          if (wsMessage.type === "system" || wsMessage.type === "error") {
            sender = "ai"
          } else if (wsMessage.user_id && wsMessage.user_id.toString() === currentMemberId) {
            sender = "user"
          }
          
          const chatMessage: ChatMessage = {
            id: wsMessage.session_id ? `ws_${wsMessage.session_id}_${Date.now()}` : `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            content: wsMessage.content || wsMessage.error || "",
            sender: sender,
            timestamp: timestamp,
            roomId: roomId,
          }
          onMessageReceived(chatMessage)
        }
      }

      const handleSessionUpdate = (wsMessage: WebSocketMessage) => {
        if (!isMounted) return
        console.log(`[ChatInterface ${roomId}] 세션 업데이트:`, wsMessage)
        
        // 세션 메시지도 채팅 UI에 표시하도록 처리
        if (wsMessage.content) {
          const currentMemberId = tokenStorage.getMemberId()?.toString()
          let timestamp = wsMessage.timestamp ? new Date(wsMessage.timestamp) : new Date()
          if (isNaN(timestamp.getTime())) timestamp = new Date()

          let sender: "user" | "partner" | "ai" = "ai" // 세션 메시지는 기본적으로 AI/시스템 메시지로 처리
          if (wsMessage.user_id && wsMessage.user_id.toString() === currentMemberId) {
            sender = "user"
          } else if (wsMessage.user_id) {
            sender = "partner"
          }
          
          const chatMessage: ChatMessage = {
            id: wsMessage.session_id ? `session_${wsMessage.session_id}_${Date.now()}` : `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            content: wsMessage.content,
            sender: sender,
            timestamp: timestamp,
            roomId: roomId,
          }
          onMessageReceived(chatMessage)
        }
      }
      
      const handleConnectionSuccess = () => {
        if (!isMounted) return
        console.log(`[ChatInterface ${roomId}] WebSocket 연결 성공`)
        setIsConnected(true)
      }

      const handleConnectionError = () => {
        if (!isMounted) return
        console.error(`[ChatInterface ${roomId}] WebSocket 연결 오류`)
        setIsConnected(false)
      }

      const handleConnectionClose = (event?: CloseEvent) => {
        if (!isMounted) return
        console.log(`[ChatInterface ${roomId}] WebSocket 연결 닫힘. Code: ${event?.code}`)
        setIsConnected(false)
      }

      try {
        console.log(`[ChatInterface ${roomId}] connectWebSocket 호출`)
        await connectWebSocket(
          roomId,
          handleSystemPrompt,
          handleWebSocketMessage, 
          handleSessionUpdate,
          handleConnectionSuccess,
          handleConnectionError,
          handleConnectionClose
        )
      } catch (error) {
        if (!isMounted) return
        console.error(`[ChatInterface ${roomId}] WebSocket 연결 설정 실패:`, error)
        setIsConnected(false)
      }
    }

    setupWebSocket()

    return () => {
      console.log(`[ChatInterface ${roomId}] 컴포넌트 언마운트, WebSocket 정리`)
      isMounted = false
      wsInitializedRef.current = false
      closeWebSocket() 
      setIsConnected(false)
    }
  }, [roomId])

  const handleSend = () => {
    if (inputMessage.trim() && isConnected) {
      const messageType = isAiMode ? "ai_message" : "message"
      sendWebSocketMessage(messageType as WebSocketMessage['type'], inputMessage.trim())
      setInputMessage("")
    } else if (!isConnected) {
      console.warn("Cannot send message, WebSocket is not connected.")
    }
  }

  const handleSystemResponse = (response: string) => {
    if (systemPrompt && systemPrompt.sessionId) {
      sendWebSocketMessage("response", response, systemPrompt.sessionId)
      setSystemPrompt(null)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
  }

  const getSenderName = (sender: string) => {
    const memberNickname = localStorage.getItem("imean_member_nickname")
    switch (sender) {
      case "user":
        return "나"
      case "partner":
        return memberNickname
      case "ai":
        return "AI 상담사"
      default:
        return sender
    }
  }

  const toggleAiMode = () => {
    setIsAiMode(!isAiMode)
  }

  const AiAvatar = ({ size = 48 }: { size?: number }) => (
    <div
      className="rounded-full bg-gradient-to-br from-yellow-300 to-orange-300 flex items-center justify-center border-2 border-yellow-200"
      style={{ width: size, height: size }}
    >
      <span className="text-lg">😊</span>
    </div>
  )

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center">
        <button onClick={onBack} className="mr-3">
          <ArrowLeft className="w-6 h-6 text-gray-600" />
        </button>
        <h1 className="text-lg font-medium text-gray-800 flex-1">{roomName}</h1>
        
        {/* 연결 상태 표시 */}
        <div className={`w-3 h-3 rounded-full mr-3 ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
        
        <button
          onClick={toggleAiMode}
          className={`rounded-full transition-all ${isAiMode ? "ring-2 ring-pink-400" : ""}`}
        >
          <AiAvatar size={40} />
        </button>
      </div>

      {/* System Prompt Modal */}
      {systemPrompt && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4">
            <h3 className="text-lg font-semibold mb-4">시스템 메시지</h3>
            <p className="text-gray-700 mb-6">{systemPrompt.message}</p>
            <div className="flex gap-3">
              <button
                onClick={() => handleSystemResponse("네")}
                className="flex-1 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600"
              >
                네
              </button>
              <button
                onClick={() => handleSystemResponse("아니요")}
                className="flex-1 bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
              >
                아니요
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!isConnected && (
          <div className="text-center text-gray-500 py-4">
            WebSocket 연결 중...
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
            {message.sender !== "user" && (
              <div className="flex-shrink-0 mr-3">
                {message.sender === "ai" ? <AiAvatar /> : <div className="w-12 h-12 bg-green-200 rounded-full"></div>}
              </div>
            )}

            <div
              className={`flex flex-col ${message.sender === "user" ? "items-end" : "items-start"} max-w-xs lg:max-w-md`}
            >
              {message.sender !== "user" && (
                <span className="text-sm text-gray-600 mb-1 ml-1">{getSenderName(message.sender)}</span>
              )}

              <div className={`flex items-end ${message.sender === "user" ? "flex-row-reverse" : "flex-row"} gap-2`}>
                <div
                  className={`px-4 py-3 rounded-lg ${
                    message.sender === "user" ? "bg-green-200 text-gray-800" : "bg-gray-200 text-gray-800"
                  }`}
                >
                  <p className="text-sm leading-relaxed break-all">{message.content}</p>
                </div>

                <div className="text-xs text-gray-500 flex-shrink-0 pb-1">{formatTime(new Date(message.timestamp))}</div>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className={`border-t border-gray-200 p-4 transition-colors ${isAiMode ? "bg-pink-100" : "bg-white"}`}>
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isAiMode ? "AI 상담사에게 메시지 보내기" : "메시지 입력"}
            disabled={!isConnected}
            className={`flex-1 border rounded-full px-4 py-2 focus:outline-none transition-colors disabled:bg-gray-100 disabled:text-gray-400 ${
              isAiMode
                ? "border-pink-300 focus:border-pink-400 bg-pink-50 placeholder-pink-400"
                : "border-gray-300 focus:border-green-400 bg-white placeholder-gray-400"
            }`}
          />
          <button
            onClick={handleSend}
            disabled={!inputMessage.trim() || !isConnected}
            className={`rounded-full p-2 transition-colors ${
              isAiMode
                ? "bg-pink-200 hover:bg-pink-300 disabled:bg-pink-100 disabled:text-pink-400 text-pink-600"
                : "bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 text-gray-600"
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
