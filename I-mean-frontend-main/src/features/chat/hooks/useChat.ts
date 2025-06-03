"use client"

import { useState, useCallback } from "react"
import type { ChatRoom, ChatMessage, CreateChatRoomData } from "../types"
import { chatApi, type CreateChatRoomResponse } from "../api/chatApi"
import { useToast } from "@/components/common/Toast"
import { sendWebSocketMessage } from "@/lib/websocket"

export const useChat = () => {
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { showToast } = useToast()

  const createChatRoom = useCallback(async (data: CreateChatRoomData): Promise<CreateChatRoomResponse> => {
    setIsLoading(true)
    try {
      console.log("채팅방 생성/조회 시도 (useChat):", data.name, data.coupleId)
      const newRoomData = await chatApi.createChatRoom(data)
      console.log("채팅방 생성/조회 성공 (useChat):", newRoomData)
      
      const roomToAdd: ChatRoom = {
        id: newRoomData.id,
        name: newRoomData.name,
        createdAt: newRoomData.createdAt,
      };

      setChatRooms((prev) => {
        const existingRoomIndex = prev.findIndex(room => room.id === roomToAdd.id);
        if (existingRoomIndex > -1) {
          const updatedRooms = [...prev];
          updatedRooms[existingRoomIndex] = roomToAdd;
          return updatedRooms;
        } else {
          return [...prev, roomToAdd];
        }
      })
      
      // 토스트 메시지는 MainPage.tsx에서 is_existing 값에 따라 직접 처리하므로 여기서는 제거하거나 일반화
      // if (newRoomData.is_existing) {
      //   showToast(`기존 채팅방 "${newRoomData.name}"에 참여합니다.`)
      // } else {
      //   showToast(`"${newRoomData.name}" 채팅방이 생성되었습니다!`)
      // }
      return newRoomData
    } catch (error) {
      console.error("채팅방 생성/조회 실패 (useChat):", error)
      const errorMessage = error instanceof Error ? error.message : "채팅방 생성/조회에 실패했습니다."
      showToast(errorMessage)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [showToast])

  const addMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => {
      if (prev.find(m => m.id === message.id)) return prev;
      return [...prev, message].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    });
  }, []);

  const addHistoryMessages = useCallback((historyMessages: ChatMessage[], roomId: string) => {
    setMessages((prev) => {
      const combinedMessages = [...prev];
      historyMessages.forEach(histMsg => {
        if (!combinedMessages.find(m => m.id === histMsg.id)) {
          // 히스토리 메시지는 일반적으로 가장 오래된 것이므로, unshift보다는 시간순 정렬을 보장하는 것이 더 중요
          combinedMessages.push(histMsg); 
        }
      });
      // 모든 메시지를 시간순으로 정렬
      return combinedMessages.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    });
  }, []);

  const clearMessagesForRoom = useCallback((roomId: string) => {
    console.log(`[useChat] clearMessagesForRoom for ${roomId} - 현재는 실제 동작 안 함, 필요시 주석 해제`);
    // setMessages((prev) => prev.filter(msg => msg.roomId !== roomId));
  }, []);

  const getMessagesForRoom = useCallback(
    (roomId: string) => {
      return messages.filter((message) => message.roomId === roomId)
                     .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    },
    [messages],
  )

  const sendMessage = useCallback((roomId: string, content: string) => {
    // WebSocket 연결이 되어 있다고 가정하고 메시지 전송
    if (!content.trim()) return;
    try {
      sendWebSocketMessage("message", content);
    } catch (e) {
      showToast("메시지 전송 중 오류가 발생했습니다.");
      console.error("sendMessage error:", e);
    }
  }, [showToast]);

  return {
    chatRooms,
    messages,
    isLoading,
    createChatRoom,
    addMessage,
    addHistoryMessages,
    clearMessagesForRoom,
    getMessagesForRoom,
    sendMessage,
  }
}