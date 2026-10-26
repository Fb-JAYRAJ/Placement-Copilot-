import React from 'react';
import { useToastStore } from './toastStore';
import Icon from './Icon';

export const ToastContainer = () => {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
};

const ToastCard = ({ toast, onClose }) => {
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return { name: 'check_circle', color: 'text-[#4be277]' };
      case 'error':
        return { name: 'error', color: 'text-[#ffb4ab]' };
      case 'warning':
        return { name: 'warning', color: 'text-[#facc15]' };
      default:
        return { name: 'info', color: 'text-[#bccbb9]' };
    }
  };

  const icon = getIcon();

  return (
    <div
      role="alert"
      className="pointer-events-auto flex items-start gap-3 p-3.5 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] shadow-2xl transition-all animate-in fade-in slide-in-from-bottom-2"
    >
      <Icon name={icon.name} className={`${icon.color} text-xl flex-shrink-0 mt-0.5`} />
      <div className="flex-1 min-w-0">
        {toast.title && <div className="text-xs font-semibold uppercase tracking-wider text-[#e2e2e2] mb-0.5">{toast.title}</div>}
        <div className="text-sm text-[#bccbb9] leading-snug break-words">{toast.message}</div>
      </div>
      <button
        onClick={onClose}
        aria-label="Close notification"
        className="text-[#869585] hover:text-[#e2e2e2] transition-colors p-0.5"
      >
        <Icon name="close" className="text-base" />
      </button>
    </div>
  );
};

export default ToastContainer;
