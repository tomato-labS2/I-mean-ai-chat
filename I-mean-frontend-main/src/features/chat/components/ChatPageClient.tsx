"use client"

import { useRouter } from "next/navigation"
import { ChatInterface } from "@/features/chat/components/ChatInterface"
import { useChat } from "@/features/chat/hooks/useChat"

interface ChatPageClientProps {
  roomId: string;
}

export default function ChatPageClient({ roomId }: ChatPageClientProps) {
  const router = useRouter()
  const { chatRooms, sendMessage, getMessagesForRoom } = useChat()

  const currentRoom = chatRooms.find((room) => room.id === roomId)
  const messages = getMessagesForRoom(roomId)

  if (!currentRoom) {
    // 이 부분은 page.tsx에서 처리하거나, 혹은 여기서 에러 바운더리 등으로 처리할 수 있습니다.
    // 여기서는 간단히 메시지를 표시하거나, 특정 페이지로 리디렉션할 수 있습니다.
    // 예를 들어, router.replace('/chat-not-found'); 또는 null을 반환하고 page.tsx에서 처리
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>채팅방 정보를 불러오는 중이거나 찾을 수 없습니다.</p>
      </div>
    );
  }

  const handleSendMessage = (content: string) => {
    sendMessage(roomId, content)
  }

  const handleBack = () => {
    // router.push("/"); // 이전에는 홈으로 갔으나, 채팅 목록이나 메인 페이지로 가는 것이 더 적절할 수 있습니다.
    router.push("/main"); // 예: 메인 페이지로 이동
  }

  return (
    <ChatInterface
      roomName={currentRoom.name}
      messages={messages}
      onSendMessage={handleSendMessage}
      onBack={handleBack}
    />
  )
} 