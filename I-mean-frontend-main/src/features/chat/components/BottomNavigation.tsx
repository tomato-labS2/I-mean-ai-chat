"use client"

import { Home, MessageCircle, User } from "lucide-react"

const EarIcon = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 512 512">
    <path
      d="M335.72 330.76C381.73 299.5 416 251.34 416 192a160 160 0 00-320 0v206.57c0 44.26 35.74 81.43 80 81.43h0c44.26 0 66.83-25.94 77.29-40 14.77-19.81 41.71-81.56 82.43-109.24z"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="32"
    />
    <path
      d="M160 304V184c0-48.4 43.2-88 96-88h0c52.8 0 96 39.6 96 88"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="32"
    />
    <path
      d="M160 239c25-18 79.82-15 79.82-15 26 0 41.17 29.42 26 50.6 0 0-36.86 42.4-41.86 61.4"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="32"
    />
  </svg>
)

interface BottomNavigationProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

export const BottomNavigation = ({ activeTab, onTabChange }: BottomNavigationProps) => {
  const tabs = [
    { id: "home", icon: Home, label: "홈" },
    { id: "couple-chat", icon: MessageCircle, label: "커플채팅" },
    { id: "ai-counseling", icon: EarIcon, label: "AI상담" },
    { id: "profile", icon: User, label: "프로필" },
  ]

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
      <div className="flex">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex-1 py-3 px-2 flex flex-col items-center justify-center ${
                activeTab === tab.id ? "text-green-600" : "text-gray-400"
              }`}
            >
              <Icon className="w-6 h-6 mb-1" />
              <span className="text-xs">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
