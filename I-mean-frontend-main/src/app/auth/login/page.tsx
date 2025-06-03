"use client"

import { LoginForm } from "@/features/auth/components/LoginForm"
import { Header } from "@/components/layout/Header"

export default function LoginPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header title="로그인" showBack />
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-8">
        <div className="mb-12 text-center fade-in">
          <img src="/images/logo.png" alt="I:mean" width={220} height={220} className="mx-auto mb-2" style={{ maxHeight: '220px' }} />
          {/* <p className="text-[#5a9b5a] text-sm tracking-wider">CHAT WITH AI</p> */}
        </div>
        <LoginForm />
      </div>
    </div>
  )
}
