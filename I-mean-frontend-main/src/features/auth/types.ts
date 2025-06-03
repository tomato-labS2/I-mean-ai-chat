export interface User {
    memberId: number
    memberCode: string
    memberRole: string
    coupleStatus: "SINGLE" | "COUPLED"
    coupleId: number | null
    isInCouple?: boolean
    isAdmin?: boolean
    isSuperAdmin?: boolean
    memberEmail?: string
    memberNickName?: string
}
  
export interface LoginFormData {
    email: string
    password: string
}
  
export interface RegisterFormData {
    email: string
    password: string
    confirmPassword: string
    nickname: string
    phone: string
}
  
export interface MemberInfo {
    memberId: number
    memberCode: string
    memberEmail: string
    memberNickName: string
    memberRole: string
    coupleStatus: "SINGLE" | "COUPLED"
    coupleId: number | null
}
  
export interface AuthApiResponse {
    success: boolean
    message: string
    data: {
        accessToken: string
        refreshToken: string
        tokenType: string
        expiresIn: number
        memberInfo: MemberInfo
    }
}
  
export interface CoupleCodeResponse {
    code: string
}
  
export {}
  