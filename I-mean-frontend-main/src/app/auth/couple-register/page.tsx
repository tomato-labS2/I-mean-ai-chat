"use client"

import { CoupleCodeForm } from "@/features/auth/components/CoupleCodeForm"
import { Header } from "@/components/layout/Header"
import { useAuth } from "@/features/auth/hooks/useAuth"
import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function CoupleRegisterPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/auth/login")
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) return null
  if (!isAuthenticated) return null

  return (
    <div className="flex flex-col min-h-screen">
      <Header title="커플 등록" showBack />
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-8">
        <div className="mb-12 text-center fade-in">
          <h2 className="text-4xl font-bold text-[#5a9b5a] mb-2">커플 등록</h2>
          <p className="text-[#999] text-sm">파트너와 함께 AI 채팅을 시작하세요</p>
        </div>
        <CoupleCodeForm />
      </div>
    </div>
  )
}
