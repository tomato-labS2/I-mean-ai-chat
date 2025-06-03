import type { LoginFormData, RegisterFormData, AuthApiResponse, User } from "@/features/auth/types"
import { tokenStorage } from "@/features/auth/utils/tokenStorage"

// const API_BASE = "http://localhost:8080/api"
const API_BASE = "http://localhost:8080/api"
// const API_BASE = "http://59.13.225.242:8000/api"

export const authApi = {
  login: async (data: LoginFormData): Promise<AuthApiResponse["data"]> => {
    const res = await fetch(`${API_BASE}/member/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        memberEmail: data.email,
        memberPass: data.password,
      }),
    })
    const result: AuthApiResponse = await res.json()
    console.log("로그인 API 전체 응답:", result)
    console.log("memberInfo 구조:", result.data?.memberInfo)
    
    if (!res.ok || !result.success) {
      throw new Error("로그인 실패: " + (result.message || JSON.stringify(result)))
    }
    
    // 토큰 및 회원 정보 저장
    tokenStorage.setToken(result.data.accessToken)
    tokenStorage.setRefreshToken(result.data.refreshToken)
    tokenStorage.setMemberCode(result.data.memberInfo.memberCode)
    tokenStorage.setCoupleStatus(result.data.memberInfo.coupleStatus)
    tokenStorage.setMemberId(result.data.memberInfo.memberId)
    tokenStorage.setCoupleId(result.data.memberInfo.coupleId)
    tokenStorage.setMemberRole(result.data.memberInfo.memberRole)
    
    // 닉네임 저장 - 여러 가능한 필드명 시도
    const memberInfo = result.data.memberInfo as any;
    const nickname = memberInfo.memberNickName || 
                    memberInfo.memberNickname || 
                    memberInfo.nickname ||
                    memberInfo.nickName
    console.log("닉네임 저장 시도:", {
      memberNickName: memberInfo.memberNickName,
      memberNickname: memberInfo.memberNickname,
      nickname: memberInfo.nickname,
      nickName: memberInfo.nickName,
      selected: nickname
    })
    
    if (nickname) {
      tokenStorage.setMemberNickname(nickname)
      console.log("닉네임 저장 완료:", nickname)
      console.log("저장 후 localStorage 확인:", tokenStorage.getMemberNickname())
    } else {
      console.warn("닉네임 필드를 찾을 수 없습니다:", result.data.memberInfo)
    }
    
    return result.data
  },

  register: async (data: RegisterFormData): Promise<AuthApiResponse["data"]> => {
    const res = await fetch(`${API_BASE}/member/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        memberEmail: data.email,
        memberPass: data.password,
        memberNickName: data.nickname,
        memberPhone: data.phone,
      }),
    })
    const result: AuthApiResponse = await res.json()
    console.log("회원가입 API 전체 응답:", result)
    console.log("memberInfo 구조:", result.data?.memberInfo)
    
    if (!res.ok || !result.success) {
      throw new Error("회원가입 실패: " + (result.message || JSON.stringify(result)))
    }
    
    tokenStorage.setToken(result.data.accessToken)
    tokenStorage.setRefreshToken(result.data.refreshToken)
    tokenStorage.setMemberCode(result.data.memberInfo.memberCode)
    tokenStorage.setCoupleStatus(result.data.memberInfo.coupleStatus)
    tokenStorage.setMemberId(result.data.memberInfo.memberId)
    tokenStorage.setCoupleId(result.data.memberInfo.coupleId)
    tokenStorage.setMemberRole(result.data.memberInfo.memberRole)
    
    // 닉네임 저장 - 여러 가능한 필드명 시도
    const memberInfo = result.data.memberInfo as any;
    const nickname = memberInfo.memberNickName || 
                    memberInfo.memberNickname || 
                    memberInfo.nickname ||
                    memberInfo.nickName
    console.log("닉네임 저장 시도:", {
      memberNickName: memberInfo.memberNickName,
      memberNickname: memberInfo.memberNickname,
      nickname: memberInfo.nickname,
      nickName: memberInfo.nickName,
      selected: nickname
    })
    
    if (nickname) {
      tokenStorage.setMemberNickname(nickname)
      console.log("닉네임 저장 완료:", nickname)
      console.log("저장 후 localStorage 확인:", tokenStorage.getMemberNickname())
    } else {
      console.warn("닉네임 필드를 찾을 수 없습니다:", result.data.memberInfo)
    }
    
    return result.data
  },

  getProfile: async (): Promise<User> => {
    const token = tokenStorage.getToken()
    
    // 토큰이 있고 멤버 정보가 로컬 스토리지에 있다면 해당 정보를 사용
    const memberCode = tokenStorage.getMemberCode()
    const coupleStatus = tokenStorage.getCoupleStatus()
    const memberId = tokenStorage.getMemberId()
    const coupleId = tokenStorage.getCoupleId()
    const memberRole = tokenStorage.getMemberRole()
    const memberNickname = tokenStorage.getMemberNickname()

    if (token && memberCode) {
      // 로컬 스토리지의 정보로 User 객체 생성
      return {
        memberId: Number(memberId) || 0,
        memberCode: memberCode,
        memberRole: memberRole || "USER",
        coupleStatus: (coupleStatus as "SINGLE" | "COUPLED") || "SINGLE",
        coupleId: coupleId ? Number(coupleId) : null,
        isInCouple: coupleStatus === "COUPLED",
        isAdmin: memberRole === "ADMIN",
        isSuperAdmin: memberRole === "SUPER_ADMIN"
      }
    }
    
    // 토큰은 있지만 멤버 정보가 없는 경우 API 호출 시도
    // 실제 프로필 API가 구현되면 여기를 수정
    const res = await fetch(`${API_BASE}/member/profile`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    })
    
    if (!res.ok) {
      // API 호출 실패 시 토큰 클리어
      tokenStorage.clear()
      throw new Error("인증 정보가 유효하지 않습니다.")
    }
    
    const result = await res.json()
    if (!result.success) {
      throw new Error(result.message || "사용자 정보 조회 실패")
    }
    return result.data as User
  },

  generateCoupleCode: async (): Promise<{ code: string }> => {
    // 실제 API 호출 시뮬레이션
    await new Promise((resolve) => setTimeout(resolve, 1000))
    // Mock couple code
    const code = Math.random().toString(36).substring(2, 8).toUpperCase()
    return { code }
  },

  joinCouple: async (targetMemberCode: string): Promise<AuthApiResponse["data"]> => {
    const token = tokenStorage.getToken()
    const res = await fetch(`${API_BASE}/couple/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ targetMemberCode }),
    })
    const result: AuthApiResponse = await res.json()
    if (!res.ok || !result.success) {
      throw new Error("커플 등록 실패: " + (result.message || JSON.stringify(result)))
    }
    if (result.data?.accessToken) tokenStorage.setToken(result.data.accessToken)
    if (result.data?.memberInfo?.coupleStatus) tokenStorage.setCoupleStatus(result.data.memberInfo.coupleStatus)
    return result.data
  },

  logout: async (): Promise<void> => {
    const token = tokenStorage.getToken();
    const res = await fetch("http://localhost:8080/api/auth/logout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    const result = await res.json();
    if (!res.ok || !result.success) {
      throw new Error(result.message || "로그아웃 실패");
    }
    tokenStorage.clear();
  },

  // 기타 API 메서드 필요시 추가
}
