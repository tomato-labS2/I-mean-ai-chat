"use client"

import { RegisterForm } from "@/features/auth/components/RegisterForm"
import { Header } from "@/components/layout/Header"

export default function RegisterPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header title="회원가입" showBack />
      <div className="flex-1 px-6 py-8 overflow-y-auto">
        <div className="mb-8 text-center fade-in">
          <img src="/images/logo.png" alt="I:mean" width={220} height={220} className="mx-auto mb-2" style={{ maxHeight: '220px' }} />
          {/* <p className="text-[#5a9b5a] text-sm tracking-wider">CHAT WITH AI</p> */}
        </div>
        <RegisterForm />
      </div>
    </div>
  )
}
