"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { authApi } from "@/features/auth/api/authApi"
import type { LoginFormData } from "@/features/auth/types"
import { useToast } from "@/components/common/Toast"
import { tokenStorage } from "@/features/auth/utils/tokenStorage"

export function useLogin() {
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { showToast } = useToast()

  const login = async (formData: LoginFormData) => {
    setIsLoading(true)
    try {
      console.log("로그인 시도 중...", formData.email)
      const loginResult = await authApi.login(formData)
      console.log("로그인 API 성공:", loginResult)
      
      const token = tokenStorage.getToken()
      console.log("저장된 토큰 확인:", token ? "토큰 존재" : "토큰 없음")
      
      if (!token) {
        console.error("토큰 저장 실패")
        showToast("로그인 토큰 저장에 실패했습니다. 다시 시도해주세요.")
        return
      }
      
      console.log("메인 페이지로 리다이렉션 시작...")
      console.log("현재 경로:", window.location.pathname)
      showToast("로그인 성공! 메인 페이지로 이동합니다.")
      
      // 라우터를 사용한 리다이렉션 시도
      setTimeout(() => {
        console.log("router.replace 실행...")
        console.log("router.replace 실행 전 경로:", window.location.pathname)
        router.replace("/main")
        
        // 추가 안전장치: 1초 후에도 이동하지 않으면 window.location 사용
        setTimeout(() => {
          console.log("router.replace 실행 후 경로:", window.location.pathname)
          if (window.location.pathname !== "/main") {
            console.log("router.replace 실패, window.location 사용...")
            window.location.href = "/main"
            
            // 추가 확인
            setTimeout(() => {
              console.log("window.location 실행 후 경로:", window.location.pathname)
            }, 500)
          } else {
            console.log("router.replace 성공!")
          }
        }, 1000)
      }, 500)
      
    } catch (error) {
      console.error("로그인 실패:", error)
      const errorMessage = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다."
      showToast(`로그인에 실패했습니다: ${errorMessage}`)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    login,
    isLoading,
  }
}
