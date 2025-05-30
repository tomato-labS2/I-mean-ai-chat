import { tokenStorage } from "@/features/auth/utils/tokenStorage"
import type { ChatRoom, CreateChatRoomData } from "../types"

const API_BASE = "http://localhost:8000/api"
// const API_BASE = "http://59.13.225.242:8000/api"

// API 응답을 위한 인터페이스 정의
export interface CreateChatRoomResponse extends ChatRoom {
  is_existing: boolean;
}

export const chatApi = {
  // 채팅방 생성 또는 조회
  createChatRoom: async (data: CreateChatRoomData): Promise<CreateChatRoomResponse> => {
    const token = tokenStorage.getToken()
    const memberId = tokenStorage.getMemberId()
    
    console.log("채팅방 생성/조회 요청 데이터:", {
      token: token ? "존재함" : "없음",
      memberId,
      roomName: data.name, // 사용자가 입력하거나 기본값으로 설정된 이름
      coupleId: data.coupleId
    })
    
    if (!token) {
      throw new Error("로그인이 필요합니다.")
    }
    
    if (!memberId) {
      throw new Error("사용자 정보가 없습니다.")
    }

    const requestBody = {
      user_id: memberId,
      room_name: data.name,
      couple_id: data.coupleId
    }

    console.log("API 요청 (POST /api/rooms):", {
      url: `${API_BASE}/rooms`,
      method: "POST",
      body: requestBody
    })

    const res = await fetch(`${API_BASE}/rooms`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(requestBody),
    })

    console.log("API 응답 상태:", res.status, res.statusText)

    if (!res.ok) {
      let errorMessage = "채팅방 생성/조회에 실패했습니다."
      try {
        const errorData = await res.json()
        console.log("에러 응답 데이터:", errorData)
        errorMessage = errorData.message || errorData.detail || `서버 오류 (${res.status}): ${res.statusText}`
      } catch (e) {
        console.log("에러 응답 파싱 실패:", e)
        errorMessage = `서버 오류 (${res.status}): ${res.statusText}`
      }
      throw new Error(errorMessage)
    }

    const result = await res.json()
    console.log("성공 응답 데이터 (createChatRoom):", result)
    
    let roomId: string
    let roomName: string // 서버 응답 기준 이름
    let createdAt: Date
    let is_existing: boolean = false // 기본값

    // 서버 응답 구조에 따라 is_existing 필드 추출 (루트 또는 data 객체 내부)
    if (typeof result.is_existing === 'boolean') {
      is_existing = result.is_existing;
    } else if (result.data && typeof result.data.is_existing === 'boolean') {
      is_existing = result.data.is_existing;
    }
    console.log("파싱된 is_existing 값:", is_existing);

    // room_id, room_name, created_at 추출 (기존 로직과 유사하게, 서버 응답 우선)
    if (result.data) {
      roomId = result.data.room_id?.toString() || 
               result.data.id?.toString() || 
               result.data.roomId?.toString() ||
               Date.now().toString()
      
      roomName = result.data.room_name || 
                 result.data.name || 
                 result.data.roomName || 
                 data.name // 요청 시 보낸 이름은 최후순위
      
      createdAt = result.data.created_at ? new Date(result.data.created_at) :
                  result.data.createdAt ? new Date(result.data.createdAt) :
                  new Date()
    } else {
      roomId = result.room_id?.toString() || 
               result.id?.toString() || 
               result.roomId?.toString() ||
               Date.now().toString()
      
      roomName = result.room_name || 
                 result.name || 
                 result.roomName || 
                 data.name // 요청 시 보낸 이름은 최후순위
      
      createdAt = result.created_at ? new Date(result.created_at) :
                  result.createdAt ? new Date(result.createdAt) :
                  new Date()
    }

    console.log("파싱된 최종 채팅방 데이터:", { roomId, roomName, createdAt, is_existing })

    return {
      id: roomId,
      name: roomName, // 서버가 최종적으로 결정한 이름
      createdAt: createdAt,
      is_existing: is_existing,
    }
  },
} 