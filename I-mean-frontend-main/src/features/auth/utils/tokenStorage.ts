const TOKEN_KEY = "imean_access_token"
const REFRESH_TOKEN_KEY = "imean_refresh_token"
const MEMBER_CODE_KEY = "imean_member_code"
const COUPLE_STATUS_KEY = "imean_couple_status"
const MEMBER_ID_KEY = "imean_member_id"
const COUPLE_ID_KEY = "imean_couple_id"
const MEMBER_ROLE_KEY = "imean_member_role"
const MEMBER_NICKNAME_KEY = "imean_member_nickname"

export const tokenStorage = {
  setToken(token: string) {
    console.log("setToken 호출됨, token:", token)
    if (typeof window !== "undefined") {
      localStorage.setItem(TOKEN_KEY, token)
    }
  },

  getToken() {
    if (typeof window !== "undefined") {
      return localStorage.getItem(TOKEN_KEY)
    }
    return null
  },

  setRefreshToken(token: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem(REFRESH_TOKEN_KEY, token)
    }
  },

  getRefreshToken() {
    if (typeof window !== "undefined") {
      return localStorage.getItem(REFRESH_TOKEN_KEY)
    }
    return null
  },

  setMemberCode(code: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem(MEMBER_CODE_KEY, code)
    }
  },

  getMemberCode() {
    if (typeof window !== "undefined") {
      return localStorage.getItem(MEMBER_CODE_KEY)
    }
    return null
  },

  setCoupleStatus(status: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem(COUPLE_STATUS_KEY, status)
    }
  },

  getCoupleStatus() {
    if (typeof window !== "undefined") {
      return localStorage.getItem(COUPLE_STATUS_KEY)
    }
    return null
  },

  setMemberId(id: number | undefined | null) {
    if (typeof window !== "undefined" && typeof id === "number" && !isNaN(id)) {
      localStorage.setItem(MEMBER_ID_KEY, id.toString())
    }
  },

  getMemberId() {
    if (typeof window !== "undefined") {
      const id = localStorage.getItem(MEMBER_ID_KEY)
      return id ? Number(id) : null
    }
    return null
  },

  setCoupleId(id: number | null | undefined) {
    if (typeof window !== "undefined") {
      if (id === null || id === undefined) {
        localStorage.removeItem(COUPLE_ID_KEY)
      } else if (typeof id === "number" && !isNaN(id)) {
        localStorage.setItem(COUPLE_ID_KEY, id.toString())
      }
    }
  },

  getCoupleId() {
    if (typeof window !== "undefined") {
      const id = localStorage.getItem(COUPLE_ID_KEY)
      return id ? Number(id) : null
    }
    return null
  },

  setMemberRole(role: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem(MEMBER_ROLE_KEY, role)
    }
  },

  getMemberRole() {
    if (typeof window !== "undefined") {
      return localStorage.getItem(MEMBER_ROLE_KEY)
    }
    return null
  },

  setMemberNickname(nickname: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem(MEMBER_NICKNAME_KEY, nickname)
    }
  },
  
  getMemberNickname() {
    if (typeof window !== "undefined") {
      return localStorage.getItem(MEMBER_NICKNAME_KEY)
    }
    return null
  },

  clear() {
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(MEMBER_CODE_KEY)
      localStorage.removeItem(COUPLE_STATUS_KEY)
      localStorage.removeItem(MEMBER_ID_KEY)
      localStorage.removeItem(COUPLE_ID_KEY)
      localStorage.removeItem(MEMBER_ROLE_KEY)
      localStorage.removeItem(MEMBER_NICKNAME_KEY)
    }
  },
}
