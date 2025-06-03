import type { ReactNode } from "react";

export default function AuthLayout({
  children,
}: {
  children: ReactNode
}) {
  return <div className="min-h-screen bg-gradient-to-b from-[#f5f3f0] to-[#ede9e4]">{children}</div>
}
