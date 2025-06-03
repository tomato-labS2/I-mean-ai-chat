"use client"

import { useState, useEffect } from "react"
import { Menu } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { ChatRoomModal } from "@/features/chat/components/ChatRoomModal"
import { ChatInterface } from "@/features/chat/components/ChatInterface"
import { BottomNavigation } from "@/features/chat/components/BottomNavigation"
import { useChat } from "@/features/chat/hooks/useChat"
import { tokenStorage } from "@/features/auth/utils/tokenStorage"
import { useToast } from "@/components/common/Toast"

export default function MainPage() {
  const [activeTab, setActiveTab] = useState("home")
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [currentChatRoom, setCurrentChatRoom] = useState<string | null>(null)
  const [hasError, setHasError] = useState(false)
  const [initialRoomName, setInitialRoomName] = useState("")

  const { chatRooms, createChatRoom, getMessagesForRoom, addMessage, addHistoryMessages, clearMessagesForRoom } = useChat()
  const { showToast } = useToast()

  useEffect(() => {
    console.log("메인 페이지 마운트됨")
    console.log("현재 URL:", window.location.href)
    console.log("현재 경로:", window.location.pathname)
    
    return () => {
      console.log("메인 페이지 언마운트됨")
    }
  }, [])

  if (hasError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-xl font-bold text-red-600 mb-4">페이지 로딩 중 오류가 발생했습니다</h1>
          <button 
            onClick={() => setHasError(false)}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  const handleTabChange = async (tab: string) => {
    setActiveTab(tab)
    if (tab === "couple-chat") {
      const coupleId = tokenStorage.getCoupleId()
      if (!coupleId) {
        showToast("오류: 커플 정보가 없습니다. 먼저 커플을 등록해주세요.")
        setActiveTab("home")
        return
      }

      try {
        console.log(`[MainPage] 커플 채팅 탭 클릭. coupleId: ${coupleId}로 채팅방 조회/생성 시도`);
        const roomData = await createChatRoom({ name: "커플 채팅", coupleId })
        console.log("[MainPage] 조회/생성 결과:", roomData);

        if (roomData.is_existing) {
          // showToast(`기존 채팅방 "${roomData.name}"에 참여합니다.`)
          await new Promise(resolve => setTimeout(resolve, 1000))
          setCurrentChatRoom(roomData.id)
          setIsModalOpen(false)
        } else {
          showToast(`새로운 커플 채팅방 이름을 설정해주세요.`)
          setInitialRoomName(roomData.name || "")
          setIsModalOpen(true)
        }
      } catch (error) {
        console.error("커플 채팅방 조회/생성 중 오류 (handleTabChange):", error)
        setActiveTab("home")
      }
    } else if (tab === "ai-counseling") {
      console.log("AI 상담 기능")
      showToast("정보: AI 상담 기능은 준비 중입니다.")
    }
  }

  const handleConfirmAndCreateRoom = async (roomNameFromModal: string) => {
    if (!roomNameFromModal.trim()) {
      showToast("경고: 채팅방 이름을 입력해주세요.")
      return
    }
    const coupleId = tokenStorage.getCoupleId()
    if (!coupleId) {
      showToast("오류: 커플 ID를 찾을 수 없습니다. 다시 시도해주세요.")
      setActiveTab("home")
      setIsModalOpen(false)
      return
    }

    try {
      console.log(`[MainPage] 모달에서 이름 입력 후 채팅방 생성/확정 시도: ${roomNameFromModal}, coupleId: ${coupleId}`);
      const newRoomData = await createChatRoom({ name: roomNameFromModal.trim(), coupleId })
      console.log("[MainPage] 모달 확인 후 생성/확정 결과:", newRoomData);
      
      if (newRoomData.is_existing && newRoomData.name !== roomNameFromModal.trim()) {
        showToast(`"${newRoomData.name}" 채팅방에 참여합니다. (요청 이름: ${roomNameFromModal.trim()})`)
      } else if (newRoomData.is_existing) {
        showToast(`기존 채팅방 "${newRoomData.name}"에 참여합니다.`)
      } else {
        showToast(`"${newRoomData.name}" 채팅방이 생성되었습니다!`)
      }
      await new Promise(resolve => setTimeout(resolve, 1000))
      setCurrentChatRoom(newRoomData.id)
      setIsModalOpen(false)

    } catch (error) {
      console.error("채팅방 생성/확정 중 오류 (handleConfirmAndCreateRoom):", error)
      showToast("오류: 채팅방을 만들거나 참여하는 중 문제가 발생했습니다.")
    }
  }

  const handleBackToMain = () => {
    setCurrentChatRoom(null)
    setActiveTab("home")
  }

  const handleSendMessage = (content: string) => {
    // 메시지 전송은 ChatInterface에서 WebSocket을 통해 처리
    console.log("메시지 전송 요청:", content)
  }

  const currentRoom = chatRooms.find((room) => room.id === currentChatRoom)
  const currentMessages = currentChatRoom ? getMessagesForRoom(currentChatRoom) : []

  if (currentChatRoom && currentRoom) {
    return (
      <ChatInterface
        roomName={currentRoom.name}
        roomId={currentChatRoom}
        messages={currentMessages}
        onMessageReceived={addMessage}
        onHistoryReceived={addHistoryMessages}
        onBack={handleBackToMain}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-green-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <button className="p-2">
            <Menu className="w-6 h-6 text-gray-600" />
          </button>
          <div className="text-center">
            <h1 className="text-xl font-bold text-green-600">I:mean</h1>
            <p className="text-xs text-gray-500">couple counseling</p>
          </div>
          <div className="w-10"></div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4 pb-20">
        <div className="text-center">
          <div className="w-32 h-32 bg-green-200 rounded-full mx-auto mb-8 flex items-center justify-center">
            <span className="text-4xl">💑</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">AI 상담사와 함께하는</h2>
          <h2 className="text-2xl font-bold text-gray-800 mb-8">커플 채팅</h2>
          <p className="text-gray-600 mb-8">
            하단의 채팅 아이콘을 눌러
            <br />
            새로운 채팅방을 시작해보세요
          </p>
          
          <Link href="/auth/couple-register" className="block">
            <Button className="w-full max-w-xs h-12 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200">
              커플 등록
            </Button>
          </Link>
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNavigation activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Chat Room Creation Modal */}
      <ChatRoomModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onConfirm={handleConfirmAndCreateRoom} 
        initialValue={initialRoomName} 
      />
    </div>
  )
}
