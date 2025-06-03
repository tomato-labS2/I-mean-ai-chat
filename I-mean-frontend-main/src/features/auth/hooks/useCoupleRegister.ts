"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { authApi } from "@/features/auth/api/authApi"
import { useToast } from "@/components/common/Toast"

export function useCoupleRegister() {
  const [isLoading, setIsLoading] = useState(false)
  const [coupleCode, setCoupleCode] = useState<string | null>(null)
  const router = useRouter()
  const { showToast } = useToast()

  const generateCode = async () => {
    setIsLoading(true)
    try {
      // 실제 API가 있다면 호출
      // const result = await authApi.generateCoupleCode();
      // setCoupleCode(result.code);
      // 임시 mock
      setCoupleCode(Math.random().toString(36).substring(2, 8).toUpperCase())
    } finally {
      setIsLoading(false)
    }
  }

  const joinCouple = async (partnerCode: string) => {
    setIsLoading(true)
    try {
      console.log("커플 연결 시도 중...", partnerCode)
      await authApi.joinCouple(partnerCode)
      console.log("커플 연결 성공")
      showToast("커플 연결이 완료되었습니다! 메인 페이지로 이동합니다.")
      
      // 메인 페이지로 리다이렉트
      setTimeout(() => {
        console.log("메인 페이지로 리다이렉트...")
        router.push("/main")
        
        // 추가 안전장치
        setTimeout(() => {
          if (window.location.pathname !== "/main") {
            console.log("router.push 실패, window.location 사용...")
            window.location.href = "/main"
          }
        }, 1000)
      }, 500)
      
    } catch (error) {
      console.error("Couple join failed:", error)
      const errorMessage = error instanceof Error ? error.message : "커플 연결에 실패했습니다."
      showToast(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    generateCode,
    joinCouple,
    isLoading,
    coupleCode,
  }
}
