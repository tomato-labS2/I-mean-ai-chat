"use client"

import type React from "react"
import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { useRegister } from "@/features/auth/hooks/useRegister"
import { Eye, EyeOff, UserPlus } from "lucide-react"
import type { RegisterFormData } from "@/features/auth/types"

export function RegisterForm() {
  const { register, isLoading } = useRegister()
  const [formData, setFormData] = useState<RegisterFormData>({
    email: "",
    password: "",
    confirmPassword: "",
    nickname: "",
    phone: "",
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [errors, setErrors] = useState<Partial<RegisterFormData>>({})

  const handleChange = (field: keyof RegisterFormData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }))
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<RegisterFormData> = {}

    if (!formData.email.includes("@")) {
      newErrors.email = "올바른 이메일 형식이 아닙니다"
    }

    if (formData.password.length < 6) {
      newErrors.password = "비밀번호는 6자 이상이어야 합니다"
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "비밀번호가 일치하지 않습니다"
    }

    if (formData.nickname.length < 2) {
      newErrors.nickname = "닉네임은 2자 이상이어야 합니다"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return
    await register(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm mx-auto space-y-4 slide-up">
      <div className="space-y-4">
        <div>
          <Input
            type="email"
            placeholder="이메일"
            value={formData.email}
            onChange={handleChange("email")}
            className={`w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 text-[#5a5a5a] placeholder:text-[#999] shadow-sm ${errors.email ? "ring-2 ring-red-400" : ""}`}
            required
          />
          {errors.email && <p className="text-red-500 text-xs mt-1 px-2">{errors.email}</p>}
        </div>

        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            placeholder="비밀번호"
            value={formData.password}
            onChange={handleChange("password")}
            className={`w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 pr-12 text-[#5a5a5a] placeholder:text-[#999] shadow-sm ${errors.password ? "ring-2 ring-red-400" : ""}`}
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-[#999] hover:text-[#5a9b5a] transition-colors"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
          {errors.password && <p className="text-red-500 text-xs mt-1 px-2">{errors.password}</p>}
        </div>

        <div className="relative">
          <Input
            type={showConfirmPassword ? "text" : "password"}
            placeholder="비밀번호 확인"
            value={formData.confirmPassword}
            onChange={handleChange("confirmPassword")}
            className={`w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 pr-12 text-[#5a5a5a] placeholder:text-[#999] shadow-sm ${errors.confirmPassword ? "ring-2 ring-red-400" : ""}`}
            required
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-[#999] hover:text-[#5a9b5a] transition-colors"
          >
            {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
          {errors.confirmPassword && <p className="text-red-500 text-xs mt-1 px-2">{errors.confirmPassword}</p>}
        </div>

        <div>
          <Input
            type="text"
            placeholder="닉네임"
            value={formData.nickname}
            onChange={handleChange("nickname")}
            className={`w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 text-[#5a5a5a] placeholder:text-[#999] shadow-sm ${errors.nickname ? "ring-2 ring-red-400" : ""}`}
            required
          />
          {errors.nickname && <p className="text-red-500 text-xs mt-1 px-2">{errors.nickname}</p>}
        </div>

        <div>
          <Input
            type="tel"
            placeholder="휴대폰 번호 (선택사항)"
            value={formData.phone}
            onChange={handleChange("phone")}
            className="w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 text-[#5a5a5a] placeholder:text-[#999] shadow-sm"
          />
        </div>
      </div>

      <div className="pt-4">
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full h-14 bg-[#f4e6a1] hover:bg-[#f0e085] disabled:bg-[#f4e6a1]/50 text-[#5a5a5a] font-semibold rounded-2xl border-0 shadow-lg transition-all duration-200 text-lg"
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 border-2 border-[#5a5a5a]/30 border-t-[#5a5a5a] rounded-full animate-spin"></div>
              가입 중...
            </div>
          ) : (
            <>
              <UserPlus className="w-5 h-5 mr-2" />
              회원가입
            </>
          )}
        </Button>
      </div>

      <div className="text-center pt-4">
        <div className="text-sm text-[#999]">
          이미 계정이 있으신가요?{" "}
          <Link href="/auth/login" className="text-[#5a9b5a] font-semibold underline underline-offset-2">
            로그인
          </Link>
        </div>
      </div>
    </form>
  )
}
