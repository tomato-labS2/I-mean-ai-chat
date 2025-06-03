"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Sparkles, MessageCircle } from "lucide-react"

export default function HomePage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f5f3f0] to-[#ede9e4] flex flex-col">
      {/* Status bar spacer */}
      <div className="h-safe-top bg-[#c8d5c8]"></div>

      {/* Header */}
      <div className="h-16 bg-[#c8d5c8] flex items-center justify-center">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-6 h-6 text-[#5a9b5a]" />
          <span className="text-[#5a9b5a] font-medium">AI Chat</span>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-8 fade-in">
        {/* Logo section */}
        <div className="mb-12 text-center">
          <div className="relative mb-4">
            <img src="/images/logo.png" alt="I:mean" width={220} height={220} className="mx-auto mb-2" style={{ maxHeight: '220px' }} />
            <Sparkles className="absolute -top-2 -right-2 w-8 h-8 text-[#f4e6a1] animate-pulse" />
          </div>
          <p className="text-[#999] text-xs mt-2">AI와 함께하는 스마트한 대화</p>
        </div>

        {/* Action buttons */}
        <div className="w-full max-w-sm space-y-4">
          <Link href="/auth/register" className="block">
            <Button className="w-full h-14 bg-[#f4e6a1] hover:bg-[#f0e085] text-[#5a5a5a] font-semibold rounded-2xl border-0 shadow-lg hover:shadow-xl transition-all duration-200 text-lg">
              회원 가입
            </Button>
          </Link>

          <div className="text-center py-2">
            <span className="text-[#999] text-sm">이미 계정이 있으신가요? </span>
            <Link href="/auth/login" className="text-[#5a9b5a] text-sm font-semibold underline underline-offset-2">
              로그인
            </Link>
          </div>
        </div>

        {/* Features preview */}
        <div className="mt-12 grid grid-cols-2 gap-4 w-full max-w-sm">
          <div className="bg-white/50 backdrop-blur-sm rounded-xl p-4 text-center">
            <MessageCircle className="w-8 h-8 text-[#5a9b5a] mx-auto mb-2" />
            <p className="text-xs text-[#666]">실시간 채팅</p>
          </div>
          <div className="bg-white/50 backdrop-blur-sm rounded-xl p-4 text-center">
            <Sparkles className="w-8 h-8 text-[#5a9b5a] mx-auto mb-2" />
            <p className="text-xs text-[#666]">AI 어시스턴트</p>
          </div>
        </div>
      </div>

      {/* Bottom safe area */}
      <div className="h-safe-bottom bg-[#c8d5c8]"></div>
    </div>
  )
}
