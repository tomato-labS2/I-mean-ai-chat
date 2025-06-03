"use client"

import React from "react"

import { useRouter } from "next/navigation"
import { ArrowLeft, LogOut } from "lucide-react"
import { Button } from "@/components/ui/Button"
import { useLogout, useAuth } from "@/features/auth/hooks/useAuth"

interface HeaderProps {
  title: string
  showBack?: boolean
  rightElement?: React.ReactNode
}

export function Header({ title, showBack = false, rightElement }: HeaderProps) {
  const router = useRouter()
  const { logout } = useLogout()
  const { isAuthenticated } = useAuth()

  return (
    <div className="h-16 bg-[#c8d5c8] flex items-center px-4">
      {showBack ? (
        <button onClick={() => router.back()} className="p-2 rounded-full hover:bg-white/20 transition-colors">
          <ArrowLeft className="w-6 h-6 text-[#5a9b5a]" />
        </button>
      ) : (
        <div className="w-10"></div>
      )}

      <h1 className="flex-1 text-center text-[#5a9b5a] font-semibold">{title}</h1>

      <div className="w-24 flex flex-row items-center justify-end gap-2">
        {rightElement !== undefined ? rightElement : (
          isAuthenticated ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={logout}
              title="로그아웃"
              className="!bg-[#f4e6a1] !text-[#5a9b5a] hover:!bg-[#ffe066] hover:!text-[#3c1e1e] shadow-md border border-[#e0e0e0] transition-all duration-200 flex flex-row items-center gap-2 px-6 py-2 rounded-xl min-w-[130px]"
            >
              <LogOut className="w-4 h-4" />
              <span className="align-middle text-center leading-tight">로그아웃</span>
            </Button>
          ) : null
        )}
      </div>
    </div>
  )
}
