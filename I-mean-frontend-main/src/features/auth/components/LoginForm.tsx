"use client"

import type React from "react"
import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { useLogin } from "@/features/auth/hooks/useLogin"
import { Eye, EyeOff, Lock } from "lucide-react"

export function LoginForm() {
  const { login, isLoading } = useLogin()
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await login(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-6 slide-up">
      <div className="space-y-4">
        <div className="relative">
          <Input
            type="email"
            placeholder="이메일"
            value={formData.email}
            onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
            className="w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 text-[#5a5a5a] placeholder:text-[#999] shadow-sm"
            required
          />
        </div>

        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            placeholder="비밀번호"
            value={formData.password}
            onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
            className="w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 pr-12 text-[#5a5a5a] placeholder:text-[#999] shadow-sm"
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-[#999] hover:text-[#5a9b5a] transition-colors"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      <Button
        type="submit"
        disabled={isLoading}
        className="w-full h-14 bg-[#f4e6a1] hover:bg-[#f0e085] disabled:bg-[#f4e6a1]/50 text-[#5a5a5a] font-semibold rounded-2xl border-0 shadow-lg transition-all duration-200 text-lg"
      >
        {isLoading ? (
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 border-2 border-[#5a5a5a]/30 border-t-[#5a5a5a] rounded-full animate-spin"></div>
            로그인 중...
          </div>
        ) : (
          <>
            <Lock className="w-5 h-5 mr-2" />
            로그인
          </>
        )}
      </Button>

      <div className="text-center space-y-3">
        <Link href="/forgot-password" className="block text-[#5a9b5a] text-sm font-medium underline underline-offset-2">
          로그인 정보를 잊으셨나요?
        </Link>

        <div className="text-sm text-[#999]">
          계정이 없으신가요?{" "}
          <Link href="/auth/register" className="text-[#5a9b5a] font-semibold underline underline-offset-2">
            회원가입
          </Link>
        </div>
      </div>
    </form>
  )
}
