import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/authStore';
import Icon from '@/components/common/Icon';

/**
 * Shell layout with responsive navigation drawer and candidate header.
 */
export const Shell = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: 'dashboard' },
    { name: 'Resume ATS', path: '/resume', icon: 'description' },
    { name: 'DSA Tracker', path: '/dsa', icon: 'terminal' },
    { name: 'Mock Interview', path: '/interview', icon: 'psychology' },
    { name: 'Profile', path: '/profile', icon: 'account_circle' },
  ];

  const handleStartPractice = () => {
    navigate('/dsa');
    setMobileDrawerOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-surface border-r border-outline-variant">
      {/* Brand Header */}
      <div className="p-6 border-b border-surface-container">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-[4px] bg-primary/10 border border-primary/40 flex items-center justify-center text-primary">
            <Icon name="terminal" className="text-xl" />
          </div>
          <div>
            <div className="text-base font-bold text-on-surface tracking-tight">Placement Copilot</div>
            <div className="label-mono text-[10px] text-primary font-semibold">TECHNICAL MASTERY</div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            onClick={() => setMobileDrawerOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-[2px] text-sm font-medium transition-all ${
                isActive
                  ? 'text-primary bg-primary/5 border-l-2 border-primary pl-[12px]'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low'
              }`
            }
          >
            <Icon name={item.icon} className="text-lg" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Info & Bottom Actions */}
      <div className="p-4 border-t border-surface-container space-y-3">
        {user && (
          <div className="px-2 py-1.5 flex items-center gap-2.5 bg-surface-container-low rounded-[4px] border border-surface-container-high">
            <div className="w-7 h-7 rounded-full bg-surface-container-high text-primary flex items-center justify-center text-xs font-bold">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium text-on-surface truncate">{user.name}</div>
              <div className="text-[10px] text-outline truncate">{user.target_role || 'Candidate'}</div>
            </div>
          </div>
        )}

        <button
          onClick={handleStartPractice}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-[4px] bg-primary text-on-primary text-xs font-bold uppercase tracking-wider hover:bg-primary-container transition-colors shadow-sm"
        >
          <Icon name="bolt" className="text-base" />
          <span>Start Practice</span>
        </button>

        <div className="pt-2 border-t border-surface-container flex items-center justify-between text-xs text-outline">
          <button
            onClick={() => navigate('/profile')}
            className="flex items-center gap-1 hover:text-on-surface transition-colors py-1"
          >
            <Icon name="settings" className="text-sm" />
            <span>Settings</span>
          </button>
          <button
            onClick={() => setShowHelpModal(true)}
            className="flex items-center gap-1 hover:text-on-surface transition-colors py-1"
          >
            <Icon name="help_outline" className="text-sm" />
            <span>Help</span>
          </button>
          <button
            id="logout-button"
            data-testid="logout-button"
            onClick={handleLogout}
            className="flex items-center gap-1 text-error hover:text-error/80 transition-colors py-1"
          >
            <Icon name="logout" className="text-sm" />
            <span>Exit</span>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-surface text-on-surface flex flex-col lg:flex-row">
      {/* Mobile Top Bar */}
      <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-surface border-b border-outline-variant sticky top-0 z-30">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-[4px] bg-primary/10 border border-primary/40 flex items-center justify-center text-primary">
            <Icon name="terminal" className="text-lg" />
          </div>
          <span className="font-bold text-sm text-on-surface">Placement Copilot</span>
        </div>
        <button
          onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
          aria-label="Toggle Navigation Drawer"
          className="p-1.5 rounded-[4px] bg-surface-container border border-outline-variant text-on-surface"
        >
          <Icon name={mobileDrawerOpen ? 'close' : 'menu'} className="text-xl" />
        </button>
      </header>

      {/* Mobile Backdrop & Drawer */}
      {mobileDrawerOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileDrawerOpen(false)}
          />
          <div className="relative w-[280px] max-w-[80vw] h-full z-50 animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Desktop Fixed Left Sidebar */}
      <aside className="hidden lg:block fixed top-0 bottom-0 left-0 w-[280px] z-20">
        {sidebarContent}
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 lg:ml-[280px] min-h-screen bg-surface overflow-x-hidden">
        <div className="max-w-[1440px] mx-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Help Modal */}
      {showHelpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
          <div className="bg-surface-container border border-outline-variant rounded-[8px] max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-surface-container-high pb-3">
              <div className="flex items-center gap-2">
                <Icon name="help" className="text-primary" />
                <h3 className="font-bold text-lg text-on-surface">Placement Copilot Guide</h3>
              </div>
              <button
                onClick={() => setShowHelpModal(false)}
                className="text-outline hover:text-on-surface"
              >
                <Icon name="close" className="text-xl" />
              </button>
            </div>
            <div className="space-y-3 text-sm text-on-surface-variant">
              <p>
                <strong className="text-on-surface">Placement Readiness Score:</strong> A deterministic 0–100 composite score synthesized from ATS alignment (25%), DSA mastery (35%), adaptive mock interview performance (30%), and study consistency (10%).
              </p>
              <p>
                <strong className="text-on-surface">Deterministic ATS:</strong> Extracts skills via 1–4-grams and fuzzy taxonomy matching. Scores are based on keyword coverage, TF-IDF cosine, and semantic embeddings.
              </p>
              <p>
                <strong className="text-on-surface">DSA Mastery & SM-2:</strong> Uses mathematical exponential decay (τ = 45 days) and spaced repetition review schedules to optimize retention.
              </p>
              <p>
                <strong className="text-on-surface">Adaptive Interview:</strong> Powered by Item Response Theory (IRT) where questions adapt dynamically to your live capability θ.
              </p>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowHelpModal(false)}
                className="px-4 py-2 rounded-[4px] bg-primary text-on-primary font-semibold text-xs uppercase tracking-wider"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Shell;
