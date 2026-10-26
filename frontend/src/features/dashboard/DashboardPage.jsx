import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { getDashboardSummary } from '@/lib/api';
import { useAuthStore } from '@/features/auth/authStore';
import Icon from '@/components/common/Icon';
import { ResponsiveContainer, LineChart, Line } from 'recharts';

/**
 * Candidate intelligence overview dashboard.
 * Displays composite Placement Readiness Score, component breakdown,
 * simulated score levers, 7-day sparklines, and onboarding checklist.
 */
export const DashboardPage = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('30d');
  const [showCalculationPopover, setShowCalculationPopover] = useState(false);

  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['dashboard-summary', timeRange],
    queryFn: () => getDashboardSummary(timeRange),
  });

  const firstName = (user?.name || summary?.user_name || 'Candidate').split(' ')[0];

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-[#1f1f1f] rounded-[4px] w-64" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-80 bg-[#1f1f1f] rounded-[8px] lg:col-span-2" />
          <div className="h-80 bg-[#1f1f1f] rounded-[8px]" />
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-8 rounded-[8px] bg-[#1f1f1f] border border-[#ffb4ab]/30 text-center space-y-4">
        <Icon name="error" className="text-3xl text-[#ffb4ab]" />
        <h3 className="text-lg font-bold text-[#e2e2e2]">Failed to load dashboard metrics</h3>
        <p className="text-sm text-[#869585]">Could not reach the analytical readiness engine.</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider"
        >
          Retry
        </button>
      </div>
    );
  }

  const {
    composite,
    confidence,
    has_enough_data,
    delta_7d,
    components = {},
    weights = {},
    levers = [],
    ats_sparkline = [],
    dsa_sparkline = [],
    mock_sparkline = [],
    ats_average,
    dsa_topics_covered,
    current_streak,
    mock_average,
    daily_focus_task,
    recent_activity = [],
    onboarding_checklist = {},
  } = summary;

  const compositeVal = composite !== null && composite !== undefined ? Math.round(composite) : null;
  const isEnoughData = has_enough_data && compositeVal !== null && confidence > 0;

  // Semicircle gauge calculation: radius 90, circumference of half-circle = PI * 90 ≈ 282.74
  const radius = 90;
  const circumference = Math.PI * radius;
  const scorePercent = isEnoughData ? Math.min(100, Math.max(0, compositeVal)) : 0;
  const strokeDashoffset = circumference - (scorePercent / 100) * circumference;

  // Onboarding completion check
  const isOnboardingIncomplete =
    !onboarding_checklist.has_uploaded_resume ||
    !onboarding_checklist.has_logged_3_problems ||
    !onboarding_checklist.has_taken_mock;
  const completedStepsCount =
    (onboarding_checklist.has_uploaded_resume ? 1 : 0) +
    (onboarding_checklist.has_logged_3_problems ? 1 : 0) +
    (onboarding_checklist.has_taken_mock ? 1 : 0);

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1f1f1f] pb-5">
        <div>
          <div className="label-mono text-xs text-[#4be277] mb-1">CANDIDATE INTELLIGENCE OVERVIEW</div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#e2e2e2] tracking-tight">
            Welcome back, {firstName}
          </h1>
          <p className="text-xs text-[#869585] mt-0.5">
            Targeting {user?.target_role || 'Software Engineering'} · Class of {user?.grad_year || 2026}
          </p>
        </div>

        {/* 7d / 30d / 90d Segmented Control */}
        <div className="inline-flex p-1 rounded-[12px] bg-[#1b1b1b] border border-[#2a2a2a] self-start sm:self-auto">
          {['7d', '30d', '90d'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 text-xs font-semibold rounded-[12px] transition-all ${
                timeRange === range
                  ? 'bg-[#4be277] text-[#003915] shadow-sm'
                  : 'text-[#869585] hover:text-[#e2e2e2]'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Onboarding Checklist for Users Completing Initial Setup */}
      {isOnboardingIncomplete && (
        <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#4be277]/40 relative overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-[4px] bg-[#4be277]/20 flex items-center justify-center text-[#4be277]">
                <Icon name="rocket_launch" className="text-lg" />
              </div>
              <h2 className="text-base font-bold text-[#e2e2e2]">
                Placement Readiness Onboarding ({completedStepsCount}/3 Completed)
              </h2>
            </div>
            <span className="label-mono text-xs text-[#4be277]">GET STARTED</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/resume"
              className={`p-4 rounded-[4px] border transition-all ${
                onboarding_checklist.has_uploaded_resume
                  ? 'bg-[#1f1f1f] border-[#4be277]/30 text-[#bccbb9]'
                  : 'bg-[#1f1f1f] border-[#3d4a3d] hover:border-[#4be277]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#e2e2e2]">1. ATS Resume</span>
                <Icon
                  name={onboarding_checklist.has_uploaded_resume ? 'check_circle' : 'pending'}
                  className={onboarding_checklist.has_uploaded_resume ? 'text-[#4be277]' : 'text-[#869585]'}
                />
              </div>
              <p className="text-xs text-[#869585]">Upload your PDF or DOCX resume to benchmark alignment.</p>
            </Link>

            <Link
              to="/dsa"
              className={`p-4 rounded-[4px] border transition-all ${
                onboarding_checklist.has_logged_3_problems
                  ? 'bg-[#1f1f1f] border-[#4be277]/30 text-[#bccbb9]'
                  : 'bg-[#1f1f1f] border-[#3d4a3d] hover:border-[#4be277]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#e2e2e2]">2. Log 3 DSA Problems</span>
                <Icon
                  name={onboarding_checklist.has_logged_3_problems ? 'check_circle' : 'pending'}
                  className={onboarding_checklist.has_logged_3_problems ? 'text-[#4be277]' : 'text-[#869585]'}
                />
              </div>
              <p className="text-xs text-[#869585]">Log at least 3 solved or attempted coding problems.</p>
            </Link>

            <Link
              to="/interview"
              className={`p-4 rounded-[4px] border transition-all ${
                onboarding_checklist.has_taken_mock
                  ? 'bg-[#1f1f1f] border-[#4be277]/30 text-[#bccbb9]'
                  : 'bg-[#1f1f1f] border-[#3d4a3d] hover:border-[#4be277]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#e2e2e2]">3. Mock Interview</span>
                <Icon
                  name={onboarding_checklist.has_taken_mock ? 'check_circle' : 'pending'}
                  className={onboarding_checklist.has_taken_mock ? 'text-[#4be277]' : 'text-[#869585]'}
                />
              </div>
              <p className="text-xs text-[#869585]">Complete an adaptive IRT mock session to calibrate live θ.</p>
            </Link>
          </div>
        </div>
      )}

      {/* Main Grid: Readiness Gauge & Daily Focus Task */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Readiness Gauge Card (2 cols) */}
        <div className="lg:col-span-2 p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] relative">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="label-mono text-xs text-[#869585]">PORTFOLIO METRIC</div>
              <h2 className="text-lg font-bold text-[#e2e2e2]">Placement Readiness Score</h2>
            </div>
            <button
              onClick={() => setShowCalculationPopover(!showCalculationPopover)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs text-[#bccbb9] hover:text-[#e2e2e2] transition-colors"
            >
              <Icon name="info" className="text-sm text-[#4be277]" />
              <span>How is this calculated?</span>
            </button>
          </div>

          {/* Semicircle Gauge Visualization */}
          <div className="py-6 flex flex-col items-center justify-center">
            <div className="relative w-64 h-36 flex items-center justify-center">
              <svg className="w-64 h-36 overflow-visible" viewBox="0 0 220 120">
                {/* Background Arc */}
                <path
                  d="M 20 110 A 90 90 0 0 1 200 110"
                  fill="none"
                  stroke="#2a2a2a"
                  strokeWidth="14"
                  strokeLinecap="round"
                />
                {/* Active Arc */}
                {isEnoughData && (
                  <path
                    d="M 20 110 A 90 90 0 0 1 200 110"
                    fill="none"
                    stroke="#4be277"
                    strokeWidth="14"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    className="transition-all duration-1000 ease-out"
                  />
                )}
              </svg>

              {/* Gauge Center Readout */}
              <div className="absolute bottom-1 text-center flex flex-col items-center">
                {isEnoughData ? (
                  <>
                    <div className="flex items-baseline justify-center gap-1">
                      <span className="text-4xl sm:text-5xl font-black text-[#e2e2e2] tracking-tighter">
                        {compositeVal}
                      </span>
                      <span className="text-sm text-[#869585] font-mono">/100</span>
                    </div>
                    {delta_7d !== null && delta_7d !== undefined && (
                      <div
                        className={`text-xs font-semibold mt-0.5 inline-flex items-center gap-0.5 ${
                          delta_7d >= 0 ? 'text-[#4be277]' : 'text-[#ffb4ab]'
                        }`}
                      >
                        <Icon name={delta_7d >= 0 ? 'trending_up' : 'trending_down'} className="text-xs" />
                        <span>
                          {delta_7d >= 0 ? '+' : ''}
                          {delta_7d.toFixed(1)} vs 7d ago
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center px-4">
                    <div className="text-base font-bold text-[#facc15]">Not enough data yet</div>
                    <div className="text-[11px] text-[#869585]">Complete initial practice to calibrate</div>
                  </div>
                )}
              </div>
            </div>

            {/* Component Summary Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full mt-6 pt-5 border-t border-[#1f1f1f]">
              <div className="p-2.5 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a]">
                <div className="label-mono text-[10px] text-[#869585]">
                  ATS RESUME ({Math.round((weights.ats || 0.25) * 100)}%)
                </div>
                <div className="text-base font-bold text-[#e2e2e2] mt-0.5">
                  {components.ats !== null && components.ats !== undefined ? `${Math.round(components.ats)}%` : '—'}
                </div>
              </div>
              <div className="p-2.5 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a]">
                <div className="label-mono text-[10px] text-[#869585]">
                  DSA MASTERY ({Math.round((weights.dsa || 0.35) * 100)}%)
                </div>
                <div className="text-base font-bold text-[#e2e2e2] mt-0.5">
                  {components.dsa !== null && components.dsa !== undefined ? `${Math.round(components.dsa)}%` : '—'}
                </div>
              </div>
              <div className="p-2.5 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a]">
                <div className="label-mono text-[10px] text-[#869585]">
                  MOCK INTERVIEW ({Math.round((weights.interview || 0.30) * 100)}%)
                </div>
                <div className="text-base font-bold text-[#e2e2e2] mt-0.5">
                  {components.interview !== null && components.interview !== undefined
                    ? `${Math.round(components.interview)}%`
                    : '—'}
                </div>
              </div>
              <div className="p-2.5 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a]">
                <div className="label-mono text-[10px] text-[#869585]">
                  CONSISTENCY ({Math.round((weights.consistency || 0.10) * 100)}%)
                </div>
                <div className="text-base font-bold text-[#e2e2e2] mt-0.5">
                  {components.consistency !== null && components.consistency !== undefined
                    ? `${Math.round(components.consistency)}%`
                    : '—'}
                </div>
              </div>
            </div>
          </div>

          {/* "How is this calculated?" Popover */}
          {showCalculationPopover && (
            <div className="absolute inset-x-4 top-16 z-30 p-5 rounded-[8px] bg-[#1f1f1f] border border-[#4be277]/50 shadow-2xl backdrop-blur-md animate-in fade-in duration-150">
              <div className="flex items-center justify-between pb-3 border-b border-[#2a2a2a]">
                <div className="flex items-center gap-2">
                  <Icon name="functions" className="text-[#4be277]" />
                  <h3 className="font-bold text-sm text-[#e2e2e2]">Readiness Mathematical Model</h3>
                </div>
                <button
                  onClick={() => setShowCalculationPopover(false)}
                  className="text-[#869585] hover:text-[#e2e2e2]"
                >
                  <Icon name="close" className="text-lg" />
                </button>
              </div>

              <div className="mt-3 space-y-3 text-xs text-[#bccbb9]">
                <p>
                  Composite formula:{' '}
                  <code className="bg-[#131313] px-1.5 py-0.5 rounded-[2px] text-[#4be277] font-mono">
                    0.25·ATS + 0.35·DSA + 0.30·Interview + 0.10·Consistency
                  </code>
                  .
                </p>
                <div className="p-2.5 rounded-[4px] bg-[#131313] border border-[#2a2a2a]">
                  <div className="font-semibold text-[#e2e2e2] mb-1">
                    Confidence Calibration: {(confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-[11px] text-[#869585]">
                    Missing components are renormalised among active components so your score is never artificially depressed.
                  </div>
                </div>

                {levers && levers.length > 0 && (
                  <div className="pt-2">
                    <div className="label-mono text-[10px] text-[#4be277] mb-1.5 font-bold">
                      TOP 3 SIMULATED LEVERS TO RAISE SCORE
                    </div>
                    <div className="space-y-1.5">
                      {levers.slice(0, 3).map((lever) => (
                        <div
                          key={lever.id}
                          className="flex items-center justify-between p-2 rounded-[2px] bg-[#131313] border border-[#2a2a2a]"
                        >
                          <div className="min-w-0 pr-2">
                            <div className="text-xs font-semibold text-[#e2e2e2] truncate">{lever.title}</div>
                            <div className="text-[10px] text-[#869585] truncate">{lever.description}</div>
                          </div>
                          <span className="text-xs font-mono font-bold text-[#4be277] shrink-0">
                            +{lever.gain.toFixed(1)} pts
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Daily Focus Task Card & Profile Card */}
        <div className="space-y-6 flex flex-col justify-between">
          {/* Daily Focus Task */}
          <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#4be277]/30 flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="label-mono text-[10px] text-[#4be277]">DAILY FOCUS TASK</span>
                <span className="w-2 h-2 rounded-full bg-[#4be277]" />
              </div>
              <h3 className="text-base font-bold text-[#e2e2e2]">
                {daily_focus_task ? daily_focus_task.title : 'Take a Mock Interview'}
              </h3>
              <p className="text-xs text-[#869585] mt-1.5 leading-relaxed">
                {daily_focus_task
                  ? daily_focus_task.description
                  : 'Maintain interview sharpness and calibrate your ability parameters.'}
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#1f1f1f]">
              <button
                onClick={() => navigate(daily_focus_task?.cta_url || '/interview')}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors"
              >
                <span>{daily_focus_task?.cta_label || 'Start Mock Session'}</span>
                <Icon name="arrow_forward" className="text-sm" />
              </button>
            </div>
          </div>

          {/* Profile Quick Stats */}
          <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#2a2a2a] text-[#4be277] flex items-center justify-center font-bold text-sm">
                {(user?.name || summary.user_name || 'C').charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-bold text-[#e2e2e2] truncate">
                  {user?.name || summary.user_name}
                </div>
                <div className="text-xs text-[#869585] truncate">
                  {user?.college || 'Engineering Candidate'}
                </div>
              </div>
            </div>
            {user?.target_companies && user.target_companies.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {user.target_companies.map((c, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-[2px] bg-[#1f1f1f] text-[10px] font-mono text-[#bccbb9] border border-[#2a2a2a]"
                  >
                    {c}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Three Stat Cards with Real Sparklines */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: ATS Trend */}
        <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
          <div className="flex items-center justify-between mb-1">
            <span className="label-mono text-[10px] text-[#869585]">ATS ALIGNMENT TREND</span>
            <Icon name="description" className="text-sm text-[#4be277]" />
          </div>
          <div className="text-2xl font-black text-[#e2e2e2]">
            {ats_average ? `${Math.round(ats_average)}%` : '—'}
          </div>
          <div className="h-14 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={ats_sparkline.map((item, idx) => ({ idx, val: item.value }))}>
                <Line type="monotone" dataKey="val" stroke="#4be277" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 2: DSA Topics & Streak */}
        <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
          <div className="flex items-center justify-between mb-1">
            <span className="label-mono text-[10px] text-[#869585]">DSA TOPICS & STREAK</span>
            <Icon name="local_fire_department" className="text-sm text-[#facc15]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-[#e2e2e2]">{dsa_topics_covered}</span>
            <span className="text-xs text-[#869585]">topics active</span>
            <span className="ml-auto text-xs font-mono font-bold text-[#facc15]">
              {current_streak}d streak
            </span>
          </div>
          <div className="h-14 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dsa_sparkline.map((item, idx) => ({ idx, val: item.value }))}>
                <Line type="monotone" dataKey="val" stroke="#facc15" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card 3: Mock Interview Average */}
        <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
          <div className="flex items-center justify-between mb-1">
            <span className="label-mono text-[10px] text-[#869585]">MOCK INTERVIEW AVG</span>
            <Icon name="psychology" className="text-sm text-[#4be277]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-[#e2e2e2]">
              {mock_average ? `${mock_average.toFixed(1)}/10` : '—'}
            </span>
            <span className="text-xs text-[#869585]">average score</span>
          </div>
          <div className="h-14 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mock_sparkline.map((item, idx) => ({ idx, val: item.value }))}>
                <Line type="monotone" dataKey="val" stroke="#4be277" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity Feed */}
      <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Icon name="history" className="text-[#869585]" />
            <h3 className="font-bold text-sm text-[#e2e2e2]">Recent System Events & Activity</h3>
          </div>
          <span className="label-mono text-[10px] text-[#869585]">REAL-TIME LOG</span>
        </div>

        {recent_activity && recent_activity.length > 0 ? (
          <div className="space-y-3">
            {recent_activity.slice(0, 6).map((event) => (
              <div
                key={event.id}
                className="flex items-center justify-between p-3 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-xs"
              >
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-[2px] bg-[#131313] border border-[#3d4a3d] flex items-center justify-center text-[#4be277]">
                    <Icon
                      name={
                        event.type.includes('ats')
                          ? 'description'
                          : event.type.includes('dsa')
                          ? 'terminal'
                          : 'psychology'
                      }
                      className="text-xs"
                    />
                  </div>
                  <div>
                    <div className="font-semibold text-[#e2e2e2]">{event.title}</div>
                    <div className="text-[10px] text-[#869585] uppercase">{event.type}</div>
                  </div>
                </div>
                <div className="font-mono text-[10px] text-[#869585]">
                  {new Date(event.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-xs text-[#869585]">No activity logged yet.</div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
