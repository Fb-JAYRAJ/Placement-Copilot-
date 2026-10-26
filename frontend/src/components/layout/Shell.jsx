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
    <div className="flex flex-col h-full bg-[#131313] border-r border-[#3d4a3d]">
      {/* Brand Header */}
      <div className="p-6 border-b border-[#1f1f1f]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-[4px] bg-[#4be277]/10 border border-[#4be277]/40 flex items-center justify-center text-[#4be277]">
            <Icon name="terminal" className="text-xl" />
          </div>
          <div>
            <div className="text-base font-bold text-[#e2e2e2] tracking-tight">Placement Copilot</div>
            <div className="label-mono text-[10px] text-[#4be277] font-semibold">TECHNICAL MASTERY</div>
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
                  ? 'text-[#4be277] bg-[#4be277]/5 border-l-2 border-[#4be277] pl-[12px]'
                  : 'text-[#bccbb9] hover:text-[#e2e2e2] hover:bg-[#1b1b1b]'
              }`
            }
          >
            <Icon name={item.icon} className="text-lg" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Info & Bottom Actions */}
      <div className="p-4 border-t border-[#1f1f1f] space-y-3">
        {user && (
          <div className="px-2 py-1.5 flex items-center gap-2.5 bg-[#1b1b1b] rounded-[4px] border border-[#2a2a2a]">
            <div className="w-7 h-7 rounded-full bg-[#2a2a2a] text-[#4be277] flex items-center justify-center text-xs font-bold">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium text-[#e2e2e2] truncate">{user.name}</div>
              <div className="text-[10px] text-[#869585] truncate">{user.target_role || 'Candidate'}</div>
            </div>
          </div>
        )}

        <button
          onClick={handleStartPractice}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors shadow-sm"
        >
          <Icon name="bolt" className="text-base" />
          <span>Start Practice</span>
        </button>

        <div className="pt-2 border-t border-[#1f1f1f] flex items-center justify-between text-xs text-[#869585]">
          <button
            onClick={() => navigate('/profile')}
            className="flex items-center gap-1 hover:text-[#e2e2e2] transition-colors py-1"
          >
            <Icon name="settings" className="text-sm" />
            <span>Settings</span>
          </button>
          <button
            onClick={() => setShowHelpModal(true)}
            className="flex items-center gap-1 hover:text-[#e2e2e2] transition-colors py-1"
          >
            <Icon name="help_outline" className="text-sm" />
            <span>Help</span>
          </button>
          <button
            id="logout-button"
            data-testid="logout-button"
            onClick={handleLogout}
            className="flex items-center gap-1 text-[#ffb4ab] hover:text-[#ffb4ab]/80 transition-colors py-1"
          >
            <Icon name="logout" className="text-sm" />
            <span>Exit</span>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#131313] text-[#e2e2e2] flex flex-col lg:flex-row">
      {/* Mobile Top Bar */}
      <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-[#131313] border-b border-[#3d4a3d] sticky top-0 z-30">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-[4px] bg-[#4be277]/10 border border-[#4be277]/40 flex items-center justify-center text-[#4be277]">
            <Icon name="terminal" className="text-lg" />
          </div>
          <span className="font-bold text-sm text-[#e2e2e2]">Placement Copilot</span>
        </div>
        <button
          onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
          aria-label="Toggle Navigation Drawer"
          className="p-1.5 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-[#e2e2e2]"
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
      <main className="flex-1 lg:ml-[280px] min-h-screen bg-[#131313] overflow-x-hidden">
        <div className="max-w-[1440px] mx-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Help Modal */}
      {showHelpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
          <div className="bg-[#1f1f1f] border border-[#3d4a3d] rounded-[8px] max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#2a2a2a] pb-3">
              <div className="flex items-center gap-2">
                <Icon name="help" className="text-[#4be277]" />
                <h3 className="font-bold text-lg text-[#e2e2e2]">Placement Copilot Guide</h3>
              </div>
              <button
                onClick={() => setShowHelpModal(false)}
                className="text-[#869585] hover:text-[#e2e2e2]"
              >
                <Icon name="close" className="text-xl" />
              </button>
            </div>
            <div className="space-y-3 text-sm text-[#bccbb9]">
              <p>
                <strong className="text-[#e2e2e2]">Placement Readiness Score:</strong> A deterministic 0–100 composite score synthesized from ATS alignment (25%), DSA mastery (35%), adaptive mock interview performance (30%), and study consistency (10%).
              </p>
              <p>
                <strong className="text-[#e2e2e2]">Deterministic ATS:</strong> Extracts skills via 1–4-grams and fuzzy taxonomy matching. Scores are based on keyword coverage, TF-IDF cosine, and semantic embeddings.
              </p>
              <p>
                <strong className="text-[#e2e2e2]">DSA Mastery & SM-2:</strong> Uses mathematical exponential decay (τ = 45 days) and spaced repetition review schedules to optimize retention.
              </p>
              <p>
                <strong className="text-[#e2e2e2]">Adaptive Interview:</strong> Powered by Item Response Theory (IRT) where questions adapt dynamically to your live capability θ.
              </p>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowHelpModal(false)}
                className="px-4 py-2 rounded-[4px] bg-[#4be277] text-[#003915] font-semibold text-xs uppercase tracking-wider"
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
