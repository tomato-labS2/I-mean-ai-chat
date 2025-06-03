"use client"

import React, { createContext, useContext, useState, useCallback } from "react";

interface Toast {
  id: number;
  message: string;
}

interface ToastContextType {
  showToast: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const showToast = useCallback((message: string) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 2500);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed top-6 left-1/2 z-50 flex flex-col items-center" style={{ transform: 'translateX(-50%)' }}>
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="mb-2 px-6 py-3 bg-[#222] text-white rounded-xl shadow-lg text-sm animate-fade-in"
            style={{ minWidth: 200, textAlign: 'center' }}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}; 