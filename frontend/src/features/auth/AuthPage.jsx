import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from './authStore';
import Icon from '@/components/common/Icon';
import { toast } from '@/components/common/toastStore';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

const signupSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(10, 'Password must be at least 10 characters long'),
  college: z.string().optional(),
  grad_year: z.coerce.number().min(2020).max(2035).optional().or(z.literal('')),
  target_role: z.string().optional(),
});

/**
 * Split-pane authentication page (Sign In & Sign Up).
 */
export const AuthPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { login, register: registerUser } = useAuthStore();

  const isSignupInitial = location.pathname.includes('/signup');
  const [isSignup, setIsSignup] = useState(isSignupInitial);
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isDemoEnabled = import.meta.env.VITE_ENABLE_DEMO !== 'false';

  const loginForm = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const signupForm = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
      college: '',
      grad_year: 2026,
      target_role: 'Software Engineer',
    },
  });

  const handleToggleMode = (signupMode) => {
    setIsSignup(signupMode);
    setServerError(null);
    window.history.replaceState(null, '', signupMode ? '/signup' : '/login');
  };

  const onLoginSubmit = async (data) => {
    setIsSubmitting(true);
    setServerError(null);
    try {
      await login(data.email, data.password);
      toast.success('Welcome back to Placement Copilot!');
      navigate('/');
    } catch (err) {
      const errorMsg = err?.message || 'Login failed. Please check your credentials.';
      setServerError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const onSignupSubmit = async (data) => {
    setIsSubmitting(true);
    setServerError(null);
    try {
      await registerUser({
        name: data.name,
        email: data.email,
        password: data.password,
        college: data.college || undefined,
        grad_year: typeof data.grad_year === 'number' ? data.grad_year : undefined,
        target_role: data.target_role || undefined,
      });
      toast.success('Account created successfully!');
      navigate('/');
    } catch (err) {
      const errorMsg = err?.message || 'Registration failed. Please check inputs.';
      setServerError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsSubmitting(true);
    setServerError(null);
    loginForm.setValue('email', 'demo@placementcopilot.com');
    loginForm.setValue('password', 'DemoCandidate2026!');
    handleToggleMode(false);
    try {
      await login('demo@placementcopilot.com', 'DemoCandidate2026!');
      toast.success('Welcome back to Placement Copilot!');
      navigate('/');
    } catch (err) {
      if (
        err?.code === 'AUTHENTICATION_FAILED' ||
        err?.message?.toLowerCase().includes('invalid email or password')
      ) {
        setServerError('Demo account does not exist. Please check database seeds.');
      } else if (
        err?.name === 'TypeError' ||
        err?.code === 'NETWORK_ERROR' ||
        err?.message?.toLowerCase().includes('fetch') ||
        err?.message?.toLowerCase().includes('network') ||
        err?.message?.toLowerCase().includes('failed to fetch')
      ) {
        setServerError('Backend server is unreachable. Please verify the backend is running at http://localhost:8000.');
      } else {
        const errorMsg = err?.message || 'Login failed. Please check your credentials.';
        setServerError(errorMsg);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col md:flex-row bg-[#131313] text-[#e2e2e2]">
      {/* Left Branding Panel (Fixed, Never Shifts) */}
      <div className="hidden md:flex flex-1 flex-col justify-between p-10 lg:p-14 bg-[#0e0e0e] border-r border-[#1f1f1f] relative overflow-hidden">
        {/* Soft Green Glow Backdrop */}
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-[#4be277]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 -right-32 w-80 h-80 bg-[#4be277]/5 rounded-full blur-3xl pointer-events-none" />

        {/* Top Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-[4px] bg-[#4be277]/10 border border-[#4be277]/50 flex items-center justify-center text-[#4be277] shadow-[0_0_15px_rgba(75,226,119,0.2)]">
            <Icon name="terminal" className="text-2xl" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-[#e2e2e2]">Placement Copilot</span>
            <div className="label-mono text-[10px] text-[#4be277]">PORTFOLIO-GRADE PREPARATION</div>
          </div>
        </div>

        {/* Headline & Value Bullets */}
        <div className="relative z-10 space-y-8 my-auto">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[12px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs text-[#4be277] font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4be277] animate-pulse" />
              <span>Version 2026.1 Active</span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-black text-[#e2e2e2] tracking-tight leading-tight">
              Master Your Technical Journey
            </h1>
            <p className="text-sm text-[#bccbb9] max-w-md leading-relaxed">
              Every score is mathematically derived and explainable. No fake percentiles. Grounded AI explanations for high-stakes campus and off-campus placements.
            </p>
          </div>

          <div className="space-y-4">
            {[
              {
                title: 'Deterministic ATS Alignment',
                desc: 'Skill taxonomy extraction with TF-IDF and semantic chunk analysis.',
              },
              {
                title: 'Exponential DSA Decay & SM-2',
                desc: 'Spaced repetition schedule targeting weak areas and retention.',
              },
              {
                title: 'Adaptive Mock Interviews',
                desc: 'Item Response Theory (IRT) engine matching question difficulty to your live ability θ.',
              },
              {
                title: 'Explainable Readiness Levers',
                desc: 'Simulated high-impact actions to systematically boost your readiness.',
              },
            ].map((bullet, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-[2px] bg-[#4be277]/15 border border-[#4be277]/40 flex items-center justify-center text-[#4be277] shrink-0 mt-0.5">
                  <Icon name="check" className="text-sm" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#e2e2e2]">{bullet.title}</div>
                  <div className="text-xs text-[#869585]">{bullet.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer info & Demo Quick-Login */}
        <div className="relative z-10 pt-6 border-t border-[#1f1f1f] flex items-center justify-between">
          <div className="text-xs text-[#869585]">
            Built with React 19, FastAPI & Neon Serverless
          </div>
          {isDemoEnabled && (
            <button
              id="demo-login-btn-desktop"
              data-testid="demo-login-button"
              onClick={handleDemoLogin}
              disabled={isSubmitting}
              type="button"
              className="text-xs text-[#4be277] hover:underline font-mono disabled:opacity-50"
            >
              {isSubmitting ? 'Signing in...' : 'Demo Account →'}
            </button>
          )}
        </div>
      </div>

      {/* Right Form Panel (Scrollable Only Here) */}
      <div className="flex-1 h-screen overflow-y-auto p-6 sm:p-10 lg:p-14 flex flex-col justify-center items-center">
        <div className="w-full max-w-[420px] space-y-6 my-auto">
          {/* Mobile Logo & Demo Login */}
          <div className="md:hidden flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-[4px] bg-[#4be277]/10 border border-[#4be277]/50 flex items-center justify-center text-[#4be277]">
                <Icon name="terminal" className="text-xl" />
              </div>
              <span className="text-base font-bold text-[#e2e2e2]">Placement Copilot</span>
            </div>
            {isDemoEnabled && (
              <button
                id="demo-login-btn-mobile"
                data-testid="demo-login-button-mobile"
                onClick={handleDemoLogin}
                disabled={isSubmitting}
                type="button"
                className="text-xs text-[#4be277] hover:underline font-mono disabled:opacity-50"
              >
                Demo Account →
              </button>
            )}
          </div>

          {/* Pill Toggle for Sign In / Create Account */}
          <div className="p-1 rounded-[12px] bg-[#1f1f1f] border border-[#3d4a3d] flex items-center">
            <button
              type="button"
              onClick={() => handleToggleMode(false)}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-[12px] transition-all ${
                !isSignup
                  ? 'bg-[#4be277] text-[#003915] shadow-sm'
                  : 'text-[#bccbb9] hover:text-[#e2e2e2]'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => handleToggleMode(true)}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-[12px] transition-all ${
                isSignup
                  ? 'bg-[#4be277] text-[#003915] shadow-sm'
                  : 'text-[#bccbb9] hover:text-[#e2e2e2]'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Title Header */}
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-[#e2e2e2]">
              {isSignup ? 'Start Your Preparation' : 'Welcome Back'}
            </h2>
            <p className="text-xs text-[#869585] mt-1">
              {isSignup
                ? 'Create your candidate profile to track problems and mock interviews.'
                : 'Sign in to access your readiness analytics and scheduled reviews.'}
            </p>
          </div>

          {/* Server Error Alert */}
          {serverError && (
            <div
              role="alert"
              className="p-3 rounded-[4px] bg-[#93000a]/20 border border-[#ffb4ab]/40 text-xs text-[#ffb4ab] flex items-start gap-2"
            >
              <Icon name="error" className="text-base shrink-0 mt-0.5" />
              <div className="flex-1">{serverError}</div>
            </div>
          )}

          {/* Form */}
          {!isSignup ? (
            <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4">
              <div>
                <label className="block label-mono text-[11px] text-[#bccbb9] mb-1.5">
                  EMAIL ADDRESS
                </label>
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="name@university.edu"
                  {...loginForm.register('email')}
                  className="w-full px-3 py-2 rounded-[2px] bg-[#1b1b1b] border border-[#3d4a3d] text-sm text-[#e2e2e2] placeholder-[#869585] focus:outline-hidden focus:border-[#4be277] focus:ring-1 focus:ring-[#4be277] transition-all"
                />
                {loginForm.formState.errors.email && (
                  <p className="text-[11px] text-[#ffb4ab] mt-1">
                    {loginForm.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="label-mono text-[11px] text-[#bccbb9]">PASSWORD</label>
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="Enter password"
                    {...loginForm.register('password')}
                    className="w-full px-3 py-2 pr-10 rounded-[2px] bg-[#1b1b1b] border border-[#3d4a3d] text-sm text-[#e2e2e2] placeholder-[#869585] focus:outline-hidden focus:border-[#4be277] focus:ring-1 focus:ring-[#4be277] transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-[#869585] hover:text-[#e2e2e2] transition-colors"
                  >
                    <Icon name={showPassword ? 'visibility_off' : 'visibility'} className="text-lg" />
                  </button>
                </div>
                {loginForm.formState.errors.password && (
                  <p className="text-[11px] text-[#ffb4ab] mt-1">
                    {loginForm.formState.errors.password.message}
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#003915] border-t-transparent rounded-full animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <span>Sign In</span>
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={signupForm.handleSubmit(onSignupSubmit)} className="space-y-4">
              <div>
                <label className="block label-mono text-[11px] text-[#bccbb9] mb-1.5">FULL NAME</label>
                <input
                  type="text"
                  placeholder="Jayraj Sawant"
                  {...signupForm.register('name')}
                  className="w-full px-3 py-2 rounded-[2px] bg-[#1b1b1b] border border-[#3d4a3d] text-sm text-[#e2e2e2] placeholder-[#869585] focus:outline-hidden focus:border-[#4be277] focus:ring-1 focus:ring-[#4be277]"
                />
                {signupForm.formState.errors.name && (
                  <p className="text-[11px] text-[#ffb4ab] mt-1">
                    {signupForm.formState.errors.name.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block label-mono text-[11px] text-[#bccbb9] mb-1.5">EMAIL ADDRESS</label>
                <input
                  type="email"
                  placeholder="name@university.edu"
                  {...signupForm.register('email')}
                  className="w-full px-3 py-2 rounded-[2px] bg-[#1b1b1b] border border-[#3d4a3d] text-sm text-[#e2e2e2] placeholder-[#869585] focus:outline-hidden focus:border-[#4be277] focus:ring-1 focus:ring-[#4be277]"
                />
                {signupForm.formState.errors.email && (
                  <p className="text-[11px] text-[#ffb4ab] mt-1">
                    {signupForm.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block label-mono text-[11px] text-[#bccbb9] mb-1.5">
                  PASSWORD (MIN 10 CHARS)
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Min. 10 characters"
                    {...signupForm.register('password')}
                    className="w-full px-3 py-2 pr-10 rounded-[2px] bg-[#1b1b1b] border border-[#3d4a3d] text-sm text-[#e2e2e2] placeholder-[#869585] focus:outline-hidden focus:border-[#4be277] focus:ring-1 focus:ring-[#4be277]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-[#869585] hover:text-[#e2e2e2]"
                  >
                    <Icon name={showPassword ? 'visibility_off' : 'visibility'} className="text-lg" />
                  </button>
                </div>
                {signupForm.formState.errors.password && (
                  <p className="text-[11px] text-[#ffb4ab] mt-1">
                    {signupForm.formState.errors.password.message}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block label-mono text-[11px] text-[#bccbb9] mb-1.5">GRAD YEAR</label>
                  <input
                    type="number"
                    placeholder="2026"
                    {...signupForm.register('grad_year')}
                    className="w-full px-3 py-2 rounded-[2px] bg-[#1b1b1b] border border-[#3d4a3d] text-sm text-[#e2e2e2] placeholder-[#869585] focus:outline-hidden focus:border-[#4be277]"
                  />
                </div>
                <div>
                  <label className="block label-mono text-[11px] text-[#bccbb9] mb-1.5">TARGET ROLE</label>
                  <input
                    type="text"
                    placeholder="SDE / SWE"
                    {...signupForm.register('target_role')}
                    className="w-full px-3 py-2 rounded-[2px] bg-[#1b1b1b] border border-[#3d4a3d] text-sm text-[#e2e2e2] placeholder-[#869585] focus:outline-hidden focus:border-[#4be277]"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#003915] border-t-transparent rounded-full animate-spin" />
                    <span>Creating Account...</span>
                  </>
                ) : (
                  <span>Create Account</span>
                )}
              </button>
            </form>
          )}

          {/* Social Buttons (Disabled with Tooltip) */}
          <div className="space-y-3 pt-2">
            <div className="relative flex items-center justify-center">
              <div className="border-t border-[#1f1f1f] w-full" />
              <span className="bg-[#131313] px-3 label-mono text-[10px] text-[#869585] absolute">
                OR CONTINUE WITH
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="relative group">
                <button
                  type="button"
                  disabled
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-[4px] bg-[#1b1b1b] border border-[#2a2a2a] text-xs text-[#869585] opacity-60 cursor-not-allowed"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  <span>Google</span>
                </button>
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block bg-[#2a2a2a] text-[#e2e2e2] text-[10px] px-2 py-0.5 rounded-[2px] whitespace-nowrap shadow-md pointer-events-none">
                  Coming soon
                </div>
              </div>

              <div className="relative group">
                <button
                  type="button"
                  disabled
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-[4px] bg-[#1b1b1b] border border-[#2a2a2a] text-xs text-[#869585] opacity-60 cursor-not-allowed"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                    />
                  </svg>
                  <span>GitHub</span>
                </button>
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block bg-[#2a2a2a] text-[#e2e2e2] text-[10px] px-2 py-0.5 rounded-[2px] whitespace-nowrap shadow-md pointer-events-none">
                  Coming soon
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
