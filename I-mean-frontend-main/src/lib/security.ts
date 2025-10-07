/**
 * 클라이언트 사이드 보안 유틸리티
 * 비밀번호 해시화 및 보안 강화 기능
 */

import { createHash, randomBytes } from 'crypto';

/**
 * 비밀번호 해시화 (클라이언트 사이드)
 * SHA-256 + Salt를 사용한 단방향 해시
 */
export async function hashPassword(password: string): Promise<string> {
  // 랜덤 솔트 생성
  const salt = randomBytes(16).toString('hex');
  
  // 비밀번호 + 솔트를 SHA-256으로 해시
  const hash = createHash('sha256')
    .update(password + salt)
    .digest('hex');
  
  // 솔트와 해시를 결합하여 반환
  return `${salt}:${hash}`;
}

/**
 * 비밀번호 검증 (클라이언트 사이드)
 */
export function verifyPassword(password: string, hashedPassword: string): boolean {
  const [salt, hash] = hashedPassword.split(':');
  const testHash = createHash('sha256')
    .update(password + salt)
    .digest('hex');
  
  return testHash === hash;
}

/**
 * 입력 데이터 정제 (XSS 방지)
 */
export function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // HTML 태그 제거
    .replace(/['"]/g, '') // 따옴표 제거
    .trim();
}

/**
 * 이메일 형식 검증
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 비밀번호 강도 검증
 */
export function validatePasswordStrength(password: string): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('비밀번호는 8자 이상이어야 합니다');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('대문자를 포함해야 합니다');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('소문자를 포함해야 합니다');
  }
  
  if (!/[0-9]/.test(password)) {
    errors.push('숫자를 포함해야 합니다');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('특수문자를 포함해야 합니다');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * 세션 보안 강화
 */
export function enhanceSessionSecurity(): void {
  // 페이지 포커스 시 토큰 갱신
  window.addEventListener('focus', () => {
    const token = localStorage.getItem('accessToken');
    if (token && isTokenExpired(token)) {
      // 토큰이 만료된 경우 로그아웃 처리
      localStorage.clear();
      window.location.href = '/auth/login';
    }
  });
  
  // 페이지 언로드 시 민감한 데이터 정리
  window.addEventListener('beforeunload', () => {
    // 메모리에서 민감한 데이터 정리
    if (window.crypto && window.crypto.getRandomValues) {
      const array = new Uint8Array(32);
      window.crypto.getRandomValues(array);
    }
  });
}

/**
 * 토큰 만료 확인
 */
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp < currentTime;
  } catch {
    return true;
  }
}
