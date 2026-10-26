import { create } from 'zustand';

/**
 * Toast notification store.
 * Supports 'success', 'error', 'warning', and 'info' toast types.
 */
export const useToastStore = create((set) => ({
  toasts: [],
  /**
   * Dispatches a new notification to the active toast queue.
   * @param {Object} toast - Toast payload
   * @param {'success'|'error'|'warning'|'info'} toast.type - Toast category
   * @param {string} toast.message - Body text
   * @param {string} [toast.title] - Optional title header
   * @param {number} [toast.duration] - Milliseconds before auto-dismiss (defaults to 4000ms)
   */
  showToast: (toast) => {
    const id = Math.random().toString(36).substring(2, 9);
    const duration = toast.duration ?? 4000;
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }));
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
      }, duration);
    }
  },
  removeToast: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export const toast = {
  success: (message, title) => useToastStore.getState().showToast({ type: 'success', message, title }),
  error: (message, title) => useToastStore.getState().showToast({ type: 'error', message, title }),
  warning: (message, title) => useToastStore.getState().showToast({ type: 'warning', message, title }),
  info: (message, title) => useToastStore.getState().showToast({ type: 'info', message, title }),
};

export default toast;
