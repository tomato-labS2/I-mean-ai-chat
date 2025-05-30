export interface ChatRoom {
  id: string
  name: string
  createdAt: Date
  lastMessage?: string
  lastMessageTime?: Date
}

export interface ChatMessage {
  id: string
  content: string
  sender: "user" | "partner" | "ai"
  timestamp: Date
  roomId: string
}

export interface CreateChatRoomData {
  name: string
  coupleId: number
}