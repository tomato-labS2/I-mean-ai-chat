"use client"

import type React from "react"
import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { useCoupleRegister } from "@/features/auth/hooks/useCoupleRegister"
import { Heart, Copy } from "lucide-react"
import { tokenStorage } from "@/features/auth/utils/tokenStorage"

const kakaoKey = process.env.NEXT_PUBLIC_KAKAO_JAVASCRIPT_KEY as string;

interface KakaoLink {
  createDefaultButton: (opts: Record<string, unknown>) => void;
}
interface KakaoSDK {
  isInitialized: () => boolean;
  init: (key: string) => void;
  Link: KakaoLink;
}

export function CoupleCodeForm() {
  const { joinCouple, isLoading, coupleCode } = useCoupleRegister()
  const [partnerCode, setPartnerCode] = useState("")
  const [mode, setMode] = useState<"generate" | "join">("generate")
  const [memberCode, setMemberCode] = useState<string | null>(null)

  const handleJoinCouple = async (e: React.FormEvent) => {
    e.preventDefault()
    await joinCouple(partnerCode)
  }

  const copyToClipboard = async () => {
    if (coupleCode) {
      await navigator.clipboard.writeText(coupleCode)
      // Toast 알림 추가 가능
    }
  }

  useEffect(() => {
    setMemberCode(tokenStorage.getMemberCode())

    const win = window as unknown as { Kakao?: KakaoSDK }
    const createKakaoButton = () => {
      const kakao = win.Kakao;
      if (
        !kakao ||
        typeof kakao !== "object" ||
        typeof kakao.isInitialized !== "function" ||
        typeof kakao.init !== "function" ||
        typeof kakao.Link !== "object" ||
        typeof kakao.Link.createDefaultButton !== "function"
      ) {
        console.log('Kakao SDK not loaded or invalid')
        return
      }
      if (!kakao.isInitialized()) {
        console.log('Kakao SDK loaded but not initialized')
      } else {
        console.log('Kakao SDK loaded and initialized')
      }
      if (!document.getElementById('btnKakao')) {
        console.log('btnKakao button not found in DOM')
      } else {
        console.log('btnKakao button found, creating Kakao share button')
      }
      try {
        kakao.Link.createDefaultButton({
          container: "#btnKakao",
          objectType: "feed",
          content: {
            title: "커플 초대 코드 공유",
            description: `아래 코드를 입력하면 커플로 연결돼요 💕\n코드: ${memberCode}`,
            imageUrl: "https://yourdomain.com/share-image.png",
            link: {
              mobileWebUrl: `http://localhost:3000/invite?code=${memberCode}`,
              webUrl: `http://localhost:3000/invite?code=${memberCode}`,
            }
          },
          buttons: [
            {
              title: "코드로 접속하기",
              link: {
                mobileWebUrl: `http://localhost:3000/invite?code=${memberCode}`,
                webUrl: `http://localhost:3000/invite?code=${memberCode}`,
              },
            }
          ]
        })
        console.log('Kakao share button created')
      } catch (e) {
        console.error('Kakao button creation error:', e)
      }
    }

    // Kakao SDK 동적 로드
    if (typeof window !== "undefined" && !win.Kakao) {
      console.log('Kakao SDK not found, loading script...')
      const script = document.createElement("script")
      script.src = "https://developers.kakao.com/sdk/js/kakao.js"
      script.async = true
      script.onload = () => {
        console.log('Kakao SDK script loaded')
        console.log('KAKAO KEY:', kakaoKey)
        if (win.Kakao && typeof win.Kakao.isInitialized === 'function') {
          if (!win.Kakao.isInitialized()) {
            win.Kakao.init(kakaoKey)
            console.log('Kakao SDK initialized')
          }
          createKakaoButton()
        } else {
          console.log('Kakao SDK not loaded after script')
        }
      }
      document.body.appendChild(script)
    } else if (win.Kakao && !win.Kakao.isInitialized()) {
      console.log('KAKAO KEY:', kakaoKey);
      win.Kakao.init(kakaoKey)
      console.log('Kakao SDK initialized (already loaded)')
      createKakaoButton()
    } else if (win.Kakao && win.Kakao.isInitialized()) {
      console.log('Kakao SDK already loaded and initialized')
      createKakaoButton()
    }
  }, [memberCode])

  return (
    <div className="w-full max-w-sm space-y-6 slide-up">
      {/* Mode Toggle */}
      <div className="flex bg-white/80 backdrop-blur-sm rounded-2xl p-1">
        <button
          type="button"
          onClick={() => setMode("generate")}
          className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all ${
            mode === "generate" ? "bg-[#f4e6a1] text-[#5a5a5a] shadow-sm" : "text-[#999] hover:text-[#5a5a5a]"
          }`}
        >
          코드 생성
        </button>
        <button
          type="button"
          onClick={() => setMode("join")}
          className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all ${
            mode === "join" ? "bg-[#f4e6a1] text-[#5a5a5a] shadow-sm" : "text-[#999] hover:text-[#5a5a5a]"
          }`}
        >
          코드 입력
        </button>
      </div>

      {mode === "generate" ? (
        <div className="space-y-4">
          <div className="text-center space-y-2">
            <Heart className="w-12 h-12 text-[#5a9b5a] mx-auto" />
            <h3 className="text-lg font-semibold text-[#5a5a5a]">내 커플 코드</h3>
            <p className="text-sm text-[#999]">파트너에게 공유할 본인 코드를 확인하고 공유하세요</p>
          </div>

          {memberCode ? (
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 text-center space-y-4">
              <div className="text-2xl font-bold text-[#5a9b5a] tracking-wider">{memberCode}</div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  onClick={copyToClipboard}
                  className="flex-1 h-12 bg-white hover:bg-gray-50 text-[#5a5a5a] border border-[#e0e0e0] rounded-xl"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  복사
                </Button>
                <Button
                  type="button"
                  id="btnKakao"
                  className="flex-1 h-12 bg-[#fee500] hover:bg-[#ffe066] text-[#3c1e1e] rounded-xl font-bold"
                >
                  카카오로 공유
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center text-[#999]">로그인 후 이용 가능합니다.</div>
          )}
        </div>
      ) : (
        <form onSubmit={handleJoinCouple} className="space-y-4">
          <div className="text-center space-y-2">
            <Heart className="w-12 h-12 text-[#5a9b5a] mx-auto" />
            <h3 className="text-lg font-semibold text-[#5a5a5a]">커플 코드 입력</h3>
            <p className="text-sm text-[#999]">파트너가 공유한 코드를 입력하세요</p>
          </div>

          <Input
            type="text"
            placeholder="커플 코드 입력"
            value={partnerCode}
            onChange={(e) => setPartnerCode(e.target.value.toUpperCase())}
            className="w-full h-14 bg-white/80 backdrop-blur-sm border-0 rounded-2xl px-4 text-center text-lg font-bold tracking-wider text-[#5a5a5a] placeholder:text-[#999] shadow-sm"
            maxLength={6}
            required
          />

          <Button
            type="submit"
            disabled={isLoading || partnerCode.length !== 6}
            className="w-full h-14 bg-[#f4e6a1] hover:bg-[#f0e085] disabled:bg-[#f4e6a1]/50 text-[#5a5a5a] font-semibold rounded-2xl"
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 border-2 border-[#5a5a5a]/30 border-t-[#5a5a5a] rounded-full animate-spin"></div>
                연결 중...
              </div>
            ) : (
              <>
                <Heart className="w-5 h-5 mr-2" />
                커플 연결하기
              </>
            )}
          </Button>
        </form>
      )}

      <div className="text-center">
        <div className="text-sm text-[#999]">
          개인으로 가입하시나요?{" "}
          <Link href="/register" className="text-[#5a9b5a] font-semibold underline underline-offset-2">
            일반 회원가입
          </Link>
        </div>
      </div>
    </div>
  )
}
