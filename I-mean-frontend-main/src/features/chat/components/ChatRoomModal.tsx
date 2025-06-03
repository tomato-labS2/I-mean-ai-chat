"use client"

import { useState, useCallback, useEffect, useRef } from "react"

interface ChatRoomModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (roomName: string) => void
  initialValue?: string
}

export const ChatRoomModal = ({ isOpen, onClose, onConfirm, initialValue = "" }: ChatRoomModalProps) => {
  const [roomName, setRoomName] = useState(initialValue)
  const maxLength = 50
  const inputRef = useRef<HTMLInputElement>(null); // 입력 필드 참조

  // 모달이 열릴 때 입력 필드에 포커스
  useEffect(() => {
    if (isOpen) {
      // 모달이 열릴 때 initialValue를 사용하여 roomName 상태를 설정
      // 이렇게 하면 모달이 다시 열릴 때마다 initialValue로 업데이트됨
      setRoomName(initialValue || "")
      if (inputRef.current) {
        inputRef.current.focus();
      }
    } else {
      // 모달이 닫힐 때 roomName을 초기화 (선택적)
      // setRoomName(initialValue || ""); 
    }
  }, [isOpen, initialValue]);

  const handleConfirm = useCallback(() => {
    if (roomName.trim()) {
      onConfirm(roomName.trim())
      // 확인 후 입력 필드 초기화는 모달이 닫히거나 다음에 열릴 때 initialValue에 의해 처리되도록
      // setRoomName(""); // 이 부분을 제거하거나, initialValue로 리셋하도록 변경
    } else {
      // 사용자에게 이름을 입력하라는 피드백을 줄 수 있음 (예: input 테두리 변경)
    }
  }, [roomName, onConfirm]); // roomName과 onConfirm에 의존

  const handleCancel = useCallback(() => {
    onClose()
    // 취소 시에도 입력 필드를 initialValue로 리셋하거나 비울 수 있음
    // setRoomName(initialValue || ""); 
  }, [onClose]); // onClose에 의존

  // Enter 키로 확인 기능
  const handleKeyPress = useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && roomName.trim()) {
      handleConfirm();
    }
  }, [handleConfirm, roomName]);

  // Hook 호출 이후에 위치시킴
  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      role="dialog" // ARIA role 추가
      aria-modal="true" // ARIA modal 속성 추가
      aria-labelledby="chatRoomModalTitle" // 제목을 가리키는 ID 추가 (아래 h2에 id 추가 필요)
    >
      <div className="bg-white rounded-lg w-full max-w-sm mx-4 shadow-xl"> {/* 그림자 효과 추가 */} 
        <div className="p-6">
          <h2 id="chatRoomModalTitle" className="text-center text-gray-800 mb-6 text-lg font-semibold"> {/* ID 추가 및 스타일 약간 변경 */} 
            채팅방 이름을 입력해주세요.
          </h2>

          <div className="mb-6">
            <input
              ref={inputRef} // ref 연결
              type="text"
              value={roomName}
              onChange={(e) => setRoomName(e.target.value)}
              onKeyPress={handleKeyPress} // Enter 키 핸들러 추가
              placeholder="채팅방 이름" // 플레이스홀더 예시 추가
              maxLength={maxLength}
              className="w-full border-b border-gray-300 pb-2 text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors duration-300" // 포커스 스타일 변경
            />
            <div className="text-right text-sm text-gray-500 mt-1"> {/* 글자 수 카운터 색상 변경 */} 
              {roomName.length}/{maxLength}
            </div>
          </div>

          <div className="flex border-t border-gray-200">
            <button 
              onClick={handleCancel} 
              className="flex-1 py-3 text-gray-700 hover:bg-gray-100 transition-colors duration-150 rounded-bl-lg" // 호버 효과 및 모서리 둥글게
            >
              취소
            </button>
            <div className="w-px bg-gray-200"></div> {/* 구분선 */} 
            <button
              onClick={handleConfirm}
              disabled={!roomName.trim()}
              className="flex-1 py-3 text-blue-600 hover:bg-blue-50 transition-colors duration-150 rounded-br-lg disabled:text-gray-400 disabled:hover:bg-transparent font-semibold" // 확인 버튼 스타일 및 호버 효과 변경
            >
              확인
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
