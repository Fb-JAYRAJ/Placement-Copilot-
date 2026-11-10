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

const AuthField = ({
  label,
  type = 'text',
  placeholder,
  registration,
  error,
  autoComplete,
  showToggle = false,
  isPasswordVisible = false,
  onTogglePassword,
}) => (
  <div>
    <label className="block label-mono text-[11px] text-on-surface-variant mb-1.5">{label}</label>
    <div className={showToggle ? 'relative' : undefined}>
      <input
        type={showToggle ? (isPasswordVisible ? 'text' : 'password') : type}
        autoComplete={autoComplete}
        placeholder={placeholder}
        {...registration}
        className={`w-full px-3 py-2 ${showToggle ? 'pr-10' : ''} rounded-[2px] bg-surface-container-low border border-outline-variant text-sm text-on-surface placeholder-outline focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-primary transition-all`}
      />
      {showToggle && (
        <button
          type="button"
          onClick={onTogglePassword}
          className="absolute right-3 top-2.5 text-outline hover:text-on-surface transition-colors"
        >
          <Icon name={isPasswordVisible ? 'visibility_off' : 'visibility'} className="text-lg" />
        </button>
      )}
    </div>
    {error && <p className="text-[11px] text-error mt-1">{error.message}</p>}
  </div>
);

const SubmitButton = ({ isSubmitting, loadingText, text, className = '' }) => (
  <button
    type="submit"
    disabled={isSubmitting}
    className={`w-full py-2.5 px-4 rounded-[4px] bg-primary text-on-primary text-xs font-bold uppercase tracking-wider hover:bg-primary-container transition-colors flex items-center justify-center gap-2 disabled:opacity-50 ${className}`}
  >
    {isSubmitting ? (
      <>
        <div className="w-4 h-4 border-2 border-on-primary border-t-transparent rounded-full animate-spin" />
        <span>{loadingText}</span>
      </>
    ) : (
      <span>{text}</span>
    )}
  </button>
);

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
      grad_year: '',
      target_role: '',
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
    <div className="h-screen w-screen overflow-hidden flex flex-col md:flex-row bg-surface text-on-surface">
      {/* Left Branding Panel (Fixed, Never Shifts) */}
      <div className="hidden md:flex flex-1 flex-col justify-between p-10 lg:p-14 bg-surface-container-lowest border-r border-surface-container relative overflow-hidden">
        {/* Soft Green Glow Backdrop */}
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 -right-32 w-80 h-80 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

        {/* Top Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-[4px] bg-primary/10 border border-primary/50 flex items-center justify-center text-primary shadow-[0_0_15px_rgba(75,226,119,0.2)]">
            <Icon name="terminal" className="text-2xl" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-on-surface">Placement Copilot</span>
            <div className="label-mono text-[10px] text-primary">PORTFOLIO-GRADE PREPARATION</div>
          </div>
        </div>

        {/* Headline & Value Bullets */}
        <div className="relative z-10 space-y-8 my-auto">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[12px] bg-surface-container border border-outline-variant text-xs text-primary font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              <span>Version 2026.1 Active</span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-black text-on-surface tracking-tight leading-tight">
              Master Your Technical Journey
            </h1>
            <p className="text-sm text-on-surface-variant max-w-md leading-relaxed">
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
                <div className="w-5 h-5 rounded-[2px] bg-primary/15 border border-primary/40 flex items-center justify-center text-primary shrink-0 mt-0.5">
                  <Icon name="check" className="text-sm" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-on-surface">{bullet.title}</div>
                  <div className="text-xs text-outline">{bullet.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer info & Demo Quick-Login */}
        <div className="relative z-10 pt-6 border-t border-surface-container flex items-center justify-between">
          <div className="text-xs text-outline">
            Built with React 19, FastAPI & Neon Serverless
          </div>
          {isDemoEnabled && (
            <button
              id="demo-login-btn-desktop"
              data-testid="demo-login-button"
              onClick={handleDemoLogin}
              disabled={isSubmitting}
              type="button"
              className="text-xs text-primary hover:underline font-mono disabled:opacity-50"
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
              <div className="w-8 h-8 rounded-[4px] bg-primary/10 border border-primary/50 flex items-center justify-center text-primary">
                <Icon name="terminal" className="text-xl" />
              </div>
              <span className="text-base font-bold text-on-surface">Placement Copilot</span>
            </div>
            {isDemoEnabled && (
              <button
                id="demo-login-btn-mobile"
                data-testid="demo-login-button-mobile"
                onClick={handleDemoLogin}
                disabled={isSubmitting}
                type="button"
                className="text-xs text-primary hover:underline font-mono disabled:opacity-50"
              >
                Demo Account →
              </button>
            )}
          </div>

          {/* Pill Toggle for Sign In / Create Account */}
          <div className="p-1 rounded-[12px] bg-surface-container border border-outline-variant flex items-center">
            <button
              type="button"
              onClick={() => handleToggleMode(false)}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-[12px] transition-all ${
                !isSignup
                  ? 'bg-primary text-on-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => handleToggleMode(true)}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-[12px] transition-all ${
                isSignup
                  ? 'bg-primary text-on-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Title Header */}
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-on-surface">
              {isSignup ? 'Start Your Preparation' : 'Welcome Back'}
            </h2>
            <p className="text-xs text-outline mt-1">
              {isSignup
                ? 'Create your candidate profile to track problems and mock interviews.'
                : 'Sign in to access your readiness analytics and scheduled reviews.'}
            </p>
          </div>

          {/* Server Error Alert */}
          {serverError && (
            <div
              role="alert"
              className="p-3 rounded-[4px] bg-error-container/20 border border-error/40 text-xs text-error flex items-start gap-2"
            >
              <Icon name="error" className="text-base shrink-0 mt-0.5" />
              <div className="flex-1">{serverError}</div>
            </div>
          )}

          {/* Form */}
          {!isSignup ? (
            <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4">
              <AuthField
                label="EMAIL ADDRESS"
                type="email"
                autoComplete="email"
                placeholder="name@university.edu"
                registration={loginForm.register('email')}
                error={loginForm.formState.errors.email}
              />
              <AuthField
                label="PASSWORD"
                autoComplete="current-password"
                placeholder="Enter password"
                registration={loginForm.register('password')}
                error={loginForm.formState.errors.password}
                showToggle
                isPasswordVisible={showPassword}
                onTogglePassword={() => setShowPassword(!showPassword)}
              />
              <SubmitButton isSubmitting={isSubmitting} loadingText="Signing In..." text="Sign In" />
            </form>
          ) : (
            <form onSubmit={signupForm.handleSubmit(onSignupSubmit)} className="space-y-4">
              <AuthField
                label="FULL NAME"
                placeholder="Full Name"
                registration={signupForm.register('name')}
                error={signupForm.formState.errors.name}
              />
              <AuthField
                label="EMAIL ADDRESS"
                type="email"
                placeholder="name@university.edu"
                registration={signupForm.register('email')}
                error={signupForm.formState.errors.email}
              />
              <AuthField
                label="PASSWORD (MIN 10 CHARS)"
                placeholder="Min. 10 characters"
                registration={signupForm.register('password')}
                error={signupForm.formState.errors.password}
                showToggle
                isPasswordVisible={showPassword}
                onTogglePassword={() => setShowPassword(!showPassword)}
              />
              <div className="grid grid-cols-2 gap-3">
                <AuthField
                  label="GRAD YEAR"
                  type="number"
                  placeholder="2026"
                  registration={signupForm.register('grad_year')}
                  error={signupForm.formState.errors.grad_year}
                />
                <AuthField
                  label="TARGET ROLE"
                  placeholder="Software Engineer"
                  registration={signupForm.register('target_role')}
                  error={signupForm.formState.errors.target_role}
                />
              </div>
              <SubmitButton
                isSubmitting={isSubmitting}
                loadingText="Creating Account..."
                text="Create Account"
                className="mt-2"
              />
            </form>
          )}

          {/* Social Buttons (Disabled with Tooltip) */}
          <div className="space-y-3 pt-2">
            <div className="relative flex items-center justify-center">
              <div className="border-t border-surface-container w-full" />
              <span className="bg-surface px-3 label-mono text-[10px] text-outline absolute">
                OR CONTINUE WITH
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="relative group">
                <button
                  type="button"
                  disabled
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-[4px] bg-surface-container-low border border-surface-container-high text-xs text-outline opacity-60 cursor-not-allowed"
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
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block bg-surface-container-high text-on-surface text-[10px] px-2 py-0.5 rounded-[2px] whitespace-nowrap shadow-md pointer-events-none">
                  Coming soon
                </div>
              </div>

              <div className="relative group">
                <button
                  type="button"
                  disabled
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-[4px] bg-surface-container-low border border-surface-container-high text-xs text-outline opacity-60 cursor-not-allowed"
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
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block bg-surface-container-high text-on-surface text-[10px] px-2 py-0.5 rounded-[2px] whitespace-nowrap shadow-md pointer-events-none">
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
