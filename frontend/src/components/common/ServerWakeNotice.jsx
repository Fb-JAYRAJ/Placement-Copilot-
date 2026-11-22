import React, { useEffect, useState } from 'react';
import api from '@/lib/api/client';

const SLOW_AFTER_MS = 2500;
const RETRY_EVERY_MS = 3000;
const GIVE_UP_AFTER_MS = 120000;

/**
 * Pings the API health endpoint when the app loads. Free hosting puts the backend to sleep when idle,
 * so the first request can take up to about a minute. If the API has not answered after a couple of
 * seconds, show a short notice and keep retrying until it wakes up.
 */
export const ServerWakeNotice = () => {
  const [status, setStatus] = useState('idle'); // 'idle' | 'waking' | 'down'

  useEffect(() => {
    let cancelled = false;
    const startedAt = Date.now();
    const slowTimer = setTimeout(() => {
      if (!cancelled) setStatus('waking');
    }, SLOW_AFTER_MS);

    const check = async () => {
      while (!cancelled && Date.now() - startedAt < GIVE_UP_AFTER_MS) {
        try {
          const res = await fetch(`${api.baseUrl}/health`, { cache: 'no-store' });
          if (res.ok) {
            clearTimeout(slowTimer);
            if (!cancelled) setStatus('idle');
            return;
          }
        } catch {
          // Network error: the server may still be starting, so try again shortly.
        }
        await new Promise((resolve) => setTimeout(resolve, RETRY_EVERY_MS));
      }
      clearTimeout(slowTimer);
      if (!cancelled) setStatus('down');
    };

    check();

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
  }, []);

  if (status === 'idle') return null;

  const isDown = status === 'down';
  return (
    <div
      role={isDown ? 'alert' : 'status'}
      aria-live={isDown ? 'assertive' : 'polite'}
      className="fixed top-0 inset-x-0 z-[60] flex items-center justify-center gap-3 px-4 py-2 bg-surface-container-high border-b border-outline-variant text-xs text-on-surface"
    >
      {!isDown && (
        <div className="w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      )}
      <span>
        {isDown
          ? 'The server is not responding right now. Please try again in a minute.'
          : 'Waking up the server. Free hosting sleeps when idle, so this can take up to a minute.'}
      </span>
    </div>
  );
};

export default ServerWakeNotice;
