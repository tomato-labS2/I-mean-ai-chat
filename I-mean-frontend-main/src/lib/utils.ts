import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Tailwind 클래스 병합 유틸 함수
 * clsx로 조건부 클래스를 구성하고 twMerge로 중복된 Tailwind 클래스를 정리
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(...inputs)) // ✅ 수정: ...inputs 로 전개해야 함
}

/**
 * 날짜를 한국어 형식으로 포맷 (예: 2025년 5월 27일)
 */
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(date))
}

/**
 * 간단한 고유 ID 생성기 (예: "g8f7q2lx8uv")
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15)
}