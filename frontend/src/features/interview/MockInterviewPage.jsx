import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import {
  getInterviews,
  getInterview,
  getInterviewReport,
  startInterview,
  submitInterviewAnswer,
  requestInterviewFollowUp,
  finishInterview,
} from '@/lib/api';
import Icon from '@/components/common/Icon';
import { toast } from '@/components/common/toastStore';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

/**
 * Adaptive Mock Interview page powered by Item Response Theory (IRT).
 * Adapts questions dynamically to candidate latent capability θ,
 * provides multidimensional scoring, exemplary model answers, and performance audits.
 */
export const MockInterviewPage = () => {
  const { id: routeInterviewId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Mode: Setup, Session, or Report
  const [activeSessionId, setActiveSessionId] = useState(routeInterviewId || null);

  // Setup form state
  const [selectedTrack, setSelectedTrack] = useState('dsa_concepts');
  const [targetCompany, setTargetCompany] = useState('Google');
  const [targetRole, setTargetRole] = useState('Software Engineer');
  const [plannedQuestions, setPlannedQuestions] = useState(5);

  // Active Session state
  const [candidateAnswer, setCandidateAnswer] = useState('');
  const [elapsedSec, setElapsedSec] = useState(0);
  const [latestEvaluation, setLatestEvaluation] = useState(null);
  const [showImprovedAnswer, setShowImprovedAnswer] = useState(false);

  // Timer
  useEffect(() => {
    let interval = null;
    if (activeSessionId) {
      interval = setInterval(() => {
        setElapsedSec((s) => s + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeSessionId]);

  // Query: Sessions History
  const { data: sessionHistory = [] } = useQuery({
    queryKey: ['mock-interviews-history'],
    queryFn: getInterviews,
    enabled: !activeSessionId,
  });

  // Query: Active Session Details
  const { data: currentSession, refetch: refetchSession } = useQuery({
    queryKey: ['mock-interview', activeSessionId],
    queryFn: () => getInterview(activeSessionId),
    enabled: !!activeSessionId,
  });

  // Query: Report (if session completed)
  const { data: reportData } = useQuery({
    queryKey: ['mock-interview-report', activeSessionId],
    queryFn: () => getInterviewReport(activeSessionId),
    enabled: !!activeSessionId && currentSession?.status === 'completed',
  });

  // Mutation: Start Interview
  const startInterviewMutation = useMutation({
    mutationFn: () =>
      startInterview({
        track: selectedTrack,
        company: targetCompany.trim() || undefined,
        role: targetRole.trim() || undefined,
        planned_questions: plannedQuestions,
      }),
    onSuccess: (session) => {
      setActiveSessionId(session.id);
      setLatestEvaluation(null);
      setCandidateAnswer('');
      setElapsedSec(0);
      navigate(`/interview/${session.id}`);
      toast.success('Interview session started! Dynamic IRT calibrator active.');
    },
    onError: (err) => {
      toast.error(err?.message || 'Failed to start interview');
    },
  });

  // Mutation: Submit Answer
  const submitAnswerMutation = useMutation({
    mutationFn: async () => {
      if (!currentSession || !activeSessionId) throw new Error('No active session');
      const curQ =
        currentSession.current_question ||
        (currentSession.questions && currentSession.questions[currentSession.questions.length - 1]);
      if (!curQ) throw new Error('No current question found');

      return submitInterviewAnswer(activeSessionId, {
        question_id: curQ.id,
        answer_text: candidateAnswer.trim(),
        time_taken_sec: Math.max(1, elapsedSec),
      });
    },
    onSuccess: (res) => {
      setLatestEvaluation(res.evaluation);
      queryClient.invalidateQueries({ queryKey: ['mock-interview', activeSessionId] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      toast.success(
        res.evaluation?.overall !== undefined
          ? `Answer evaluated! Score: ${res.evaluation.overall.toFixed(1)}/10.`
          : 'Answer evaluated successfully!'
      );
    },
    onError: (err) => {
      toast.error(err?.message || 'Answer submission failed');
    },
  });

  // Mutation: Follow Up
  const followUpMutation = useMutation({
    mutationFn: async () => {
      if (!activeSessionId) return;
      return requestInterviewFollowUp(activeSessionId);
    },
    onSuccess: () => {
      setCandidateAnswer('');
      setLatestEvaluation(null);
      refetchSession();
      toast.success('Follow-up question generated!');
    },
    onError: (err) => {
      toast.error(err?.message || 'Follow-up unavailable');
    },
  });

  // Mutation: Finish Early
  const finishInterviewMutation = useMutation({
    mutationFn: () => finishInterview(activeSessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mock-interview', activeSessionId] });
      queryClient.invalidateQueries({ queryKey: ['mock-interviews-history'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      toast.success('Interview session completed! Report generated.');
    },
  });

  const handleNextQuestion = () => {
    setCandidateAnswer('');
    setLatestEvaluation(null);
    setShowImprovedAnswer(false);
    refetchSession();
  };

  /**
   * Formats elapsed seconds into mm:ss display string.
   * @param {number} seconds
   * @returns {string}
   */
  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  /**
   * Maps numerical ability θ (1..5) to human-readable difficulty tier.
   * @param {number} theta
   * @returns {{ label: string, color: string }}
   */
  const getDifficultyLabel = (theta) => {
    if (theta < 2.0) return { label: 'Novice (Level 1)', color: 'text-[#4be277]' };
    if (theta < 3.0) return { label: 'Intermediate (Level 2)', color: 'text-[#4be277]' };
    if (theta < 4.0) return { label: 'Advanced (Level 3)', color: 'text-[#facc15]' };
    return { label: 'Senior Mastery (Level 4+)', color: 'text-[#ffb4ab]' };
  };

  const tracksConfig = [
    {
      id: 'dsa_concepts',
      title: 'DSA Concepts & Edge Cases',
      desc: 'Algorithmic paradigms, time/space complexity, invariant preservation, edge cases.',
      icon: 'terminal',
    },
    {
      id: 'cs_fundamentals',
      title: 'CS Core Fundamentals',
      desc: 'OS process vs thread, virtual memory, ACID transactions, TCP/UDP sockets.',
      icon: 'storage',
    },
    {
      id: 'system_design',
      title: 'System Design & Scalability',
      desc: 'Horizontal scaling, CDN caching, database sharding, rate limiting, CAP theorem.',
      icon: 'hub',
    },
    {
      id: 'behavioral',
      title: 'Behavioral & Leadership',
      desc: 'STAR framework responses, ambiguity handling, conflict resolution, project leadership.',
      icon: 'groups',
    },
  ];

  /* ------------------------------------------------------------- */
  /* VIEW 1: SETUP SCREEN                                         */
  /* ------------------------------------------------------------- */
  if (!activeSessionId) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="border-b border-[#1f1f1f] pb-5">
          <div className="label-mono text-xs text-[#4be277] mb-1">DYNAMIC IRT EVALUATOR</div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#e2e2e2] tracking-tight">
            Adaptive Mock Interview
          </h1>
          <p className="text-xs text-[#869585] mt-0.5">
            Questions adapt live to candidate capability θ using Item Response Theory.
          </p>
        </div>

        {/* Setup Configuration */}
        <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-6">
          {/* Track Selection Cards */}
          <div>
            <label className="block label-mono text-xs text-[#bccbb9] mb-3">SELECT INTERVIEW TRACK</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tracksConfig.map((track) => (
                <div
                  key={track.id}
                  onClick={() => setSelectedTrack(track.id)}
                  className={`p-4 rounded-[4px] border cursor-pointer transition-all ${
                    selectedTrack === track.id
                      ? 'bg-[#4be277]/10 border-[#4be277]'
                      : 'bg-[#1f1f1f] border-[#2a2a2a] hover:border-[#3d4a3d]'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className={`w-8 h-8 rounded-[4px] flex items-center justify-center ${
                        selectedTrack === track.id
                          ? 'bg-[#4be277] text-[#003915]'
                          : 'bg-[#131313] text-[#4be277]'
                      }`}
                    >
                      <Icon name={track.icon} className="text-lg" />
                    </div>
                    <div className="text-sm font-bold text-[#e2e2e2]">{track.title}</div>
                  </div>
                  <p className="text-xs text-[#869585] leading-relaxed">{track.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Company & Role inputs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block label-mono text-[10px] text-[#869585] mb-1">TARGET COMPANY</label>
              <input
                type="text"
                value={targetCompany}
                onChange={(e) => setTargetCompany(e.target.value)}
                placeholder="Google / Microsoft / Amazon"
                className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
              />
            </div>
            <div>
              <label className="block label-mono text-[10px] text-[#869585] mb-1">TARGET ROLE</label>
              <input
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="Software Engineer"
                className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
              />
            </div>
          </div>

          {/* Number of Planned Questions */}
          <div className="pt-2">
            <label className="block label-mono text-[10px] text-[#869585] mb-2">SESSION LENGTH</label>
            <div className="inline-flex p-1 rounded-[4px] bg-[#131313] border border-[#2a2a2a]">
              {[5, 8, 10].map((qCount) => (
                <button
                  key={qCount}
                  type="button"
                  onClick={() => setPlannedQuestions(qCount)}
                  className={`px-4 py-1.5 text-xs font-semibold rounded-[2px] transition-all ${
                    plannedQuestions === qCount
                      ? 'bg-[#4be277] text-[#003915]'
                      : 'text-[#869585] hover:text-[#e2e2e2]'
                  }`}
                >
                  {qCount} Questions (~{qCount * 4} mins)
                </button>
              ))}
            </div>
          </div>

          {/* Start CTA */}
          <div className="pt-4 border-t border-[#1f1f1f] flex justify-end">
            <button
              onClick={() => startInterviewMutation.mutate()}
              disabled={startInterviewMutation.isPending}
              className="px-6 py-2.5 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors flex items-center gap-2 disabled:opacity-50 shadow-sm"
            >
              {startInterviewMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#003915] border-t-transparent rounded-full animate-spin" />
                  <span>Calibrating Ability θ...</span>
                </>
              ) : (
                <>
                  <Icon name="play_arrow" className="text-base" />
                  <span>Start Interview Session</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Past Sessions History */}
        {sessionHistory.length > 0 && (
          <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
            <div className="flex items-center justify-between mb-4">
              <span className="label-mono text-xs text-[#869585]">PAST INTERVIEW SESSIONS</span>
              <span className="text-xs font-mono text-[#4be277]">{sessionHistory.length} Sessions Logged</span>
            </div>
            <div className="divide-y divide-[#1f1f1f]">
              {sessionHistory.map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <div className="font-semibold text-[#e2e2e2] flex items-center gap-2">
                      <span>{s.track.replace('_', ' ').toUpperCase()}</span>
                      <span className="text-[10px] text-[#869585]">
                        ({s.company || 'Tech Company'} · {s.role || 'SWE'})
                      </span>
                    </div>
                    <div className="text-[11px] text-[#869585] font-mono">
                      {new Date(s.started_at || s.created_at || Date.now()).toLocaleDateString()} · Final θ:{' '}
                      {(s.ability ?? s.final_theta ?? 2.5).toFixed(2)} · Score:{' '}
                      {s.final_score !== null && s.final_score !== undefined
                        ? `${Math.round(s.final_score)}%`
                        : s.overall_score !== null && s.overall_score !== undefined
                        ? `${Math.round(s.overall_score)}%`
                        : 'In Progress'}
                    </div>
                  </div>
                  <div>
                    {s.status === 'completed' ? (
                      <button
                        onClick={() => {
                          setActiveSessionId(s.id);
                          navigate(`/interview/${s.id}`);
                        }}
                        className="px-3 py-1 rounded-[2px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs text-[#4be277] hover:bg-[#4be277]/10"
                      >
                        View Report
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setActiveSessionId(s.id);
                          navigate(`/interview/${s.id}`);
                        }}
                        className="px-3 py-1 rounded-[2px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase"
                      >
                        Resume
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  /* ------------------------------------------------------------- */
  /* VIEW 2: FINAL REPORT VIEW                                     */
  /* ------------------------------------------------------------- */
  if (currentSession?.status === 'completed') {
    const report = reportData || currentSession.report;

    return (
      <div className="space-y-6">
        {/* Report Header */}
        <div className="flex items-center justify-between border-b border-[#1f1f1f] pb-5">
          <div>
            <div className="label-mono text-xs text-[#4be277] mb-1">INTERVIEW PERFORMANCE AUDIT</div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#e2e2e2] tracking-tight">
              Evaluation Report & Calibrated Ability
            </h1>
            <p className="text-xs text-[#869585] mt-0.5">
              {currentSession.track.replace('_', ' ').toUpperCase()} Track · Calibrated Ability Final θ:{' '}
              {(report?.final_theta ?? report?.final_ability ?? currentSession?.ability ?? 2.5).toFixed(2)}
            </p>
          </div>
          <button
            onClick={() => {
              setActiveSessionId(null);
              navigate('/interview');
            }}
            className="px-4 py-2 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs text-[#bccbb9] hover:text-[#e2e2e2]"
          >
            ← Back to Tracks
          </button>
        </div>

        {/* High-Level Score Banner */}
        <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-center">
            <div className="label-mono text-[10px] text-[#869585] mb-1">DIFFICULTY-WEIGHTED SCORE</div>
            <div className="text-4xl font-black text-[#4be277]">
              {report?.overall_score !== undefined
                ? `${Math.round(report.overall_score)}%`
                : currentSession?.final_score !== null && currentSession?.final_score !== undefined
                ? `${Math.round(currentSession.final_score)}%`
                : '—'}
            </div>
            {report?.delta_vs_previous !== null && report?.delta_vs_previous !== undefined && (
              <div
                className={`text-[11px] font-mono mt-1 ${
                  report.delta_vs_previous >= 0 ? 'text-[#4be277]' : 'text-[#ffb4ab]'
                }`}
              >
                {report.delta_vs_previous >= 0 ? '+' : ''}
                {report.delta_vs_previous.toFixed(1)}% vs last session
              </div>
            )}
          </div>

          <div className="p-4 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-center">
            <div className="label-mono text-[10px] text-[#869585] mb-1">CALIBRATED ABILITY θ</div>
            <div className="text-4xl font-black text-[#e2e2e2]">
              {(report?.final_theta ?? report?.final_ability ?? currentSession?.ability ?? 2.5).toFixed(2)}
            </div>
            <div className="text-[10px] text-[#869585] font-mono mt-1">Scale [1.0 to 5.0]</div>
          </div>

          <div className="p-4 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] flex flex-col justify-between">
            <div>
              <div className="label-mono text-[10px] text-[#869585] mb-1">NEXT ACTION</div>
              <div className="text-xs text-[#bccbb9]">Target weak topics identified during session.</div>
            </div>
            <button
              onClick={() => navigate('/dsa')}
              className="mt-3 w-full py-2 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e]"
            >
              Practise Weak Topics →
            </button>
          </div>
        </div>

        {/* θ Trajectory Chart */}
        {report && report.theta_trajectory && report.theta_trajectory.length > 0 && (
          <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
            <div className="flex items-center justify-between mb-3">
              <span className="label-mono text-xs text-[#869585]">
                ABILITY θ TRAJECTORY (LIVE IRT ADAPTATION PER QUESTION)
              </span>
              <span className="text-xs font-mono text-[#4be277]">
                Start 2.50 → Final {(report?.final_theta ?? report?.final_ability ?? currentSession?.ability ?? 2.5).toFixed(2)}
              </span>
            </div>
            <div className="h-44">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={report.theta_trajectory.map((val, idx) => ({
                    question: `Q${idx + 1}`,
                    theta: Number(val.toFixed(2)),
                  }))}
                >
                  <XAxis dataKey="question" tickLine={false} tick={{ fill: '#869585', fontSize: 11 }} />
                  <YAxis domain={[1, 5]} tick={{ fill: '#869585', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f1f1f', borderColor: '#3d4a3d', borderRadius: 4, fontSize: 11 }}
                  />
                  <Line type="monotone" dataKey="theta" stroke="#4be277" strokeWidth={2.5} dot={{ fill: '#4be277', r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Top 3 Gaps & 3 Grounded Action Items */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#ffb4ab]/30 space-y-3">
            <div className="flex items-center gap-2">
              <Icon name="warning" className="text-sm text-[#ffb4ab]" />
              <span className="label-mono text-xs text-[#ffb4ab] font-bold">TOP IDENTIFIED GAPS</span>
            </div>
            <ul className="space-y-2 text-xs text-[#bccbb9]">
              {report?.top_gaps ? (
                report.top_gaps.map((gap, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[#ffb4ab] font-mono">•</span>
                    <span>{gap}</span>
                  </li>
                ))
              ) : (
                <li className="text-[#869585]">No critical gaps recorded.</li>
              )}
            </ul>
          </div>

          <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#4be277]/30 space-y-3">
            <div className="flex items-center gap-2">
              <Icon name="task_alt" className="text-sm text-[#4be277]" />
              <span className="label-mono text-xs text-[#4be277] font-bold">GROUNDED ACTION ITEMS</span>
            </div>
            <ul className="space-y-2 text-xs text-[#bccbb9]">
              {report?.action_items ? (
                report.action_items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[#4be277] font-mono">•</span>
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-[#869585]">Review weak areas and continue daily practice.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    );
  }

  /* ------------------------------------------------------------- */
  /* VIEW 3: ACTIVE INTERVIEW SESSION                              */
  /* ------------------------------------------------------------- */
  const curQuestion =
    currentSession?.current_question ||
    (currentSession?.questions && currentSession.questions[currentSession.questions.length - 1]);
  const currentAbility = currentSession?.ability ?? 2.5;
  const diffInfo = getDifficultyLabel(currentAbility);
  const wordCount = candidateAnswer.trim() ? candidateAnswer.trim().split(/\s+/).length : 0;
  const charCount = candidateAnswer.length;

  return (
    <div className="space-y-6">
      {/* Session Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1f1f1f] pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (window.confirm('Leave active interview session? Your progress will be saved.')) {
                setActiveSessionId(null);
                navigate('/interview');
              }
            }}
            className="p-1.5 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-[#869585] hover:text-[#e2e2e2]"
            title="Leave Session"
          >
            <Icon name="arrow_back" className="text-lg" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-[#e2e2e2]">
                {currentSession?.track.replace('_', ' ').toUpperCase()}
              </h2>
              <span className={`label-mono text-[10px] font-bold ${diffInfo.color}`}>
                [{diffInfo.label}]
              </span>
            </div>
            <div className="text-xs text-[#869585]">
              Question {curQuestion?.seq || 1} of {currentSession?.planned_questions || 5} · Ability θ:{' '}
              {currentAbility.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Timer & Finish Early Button */}
        <div className="flex items-center gap-3 self-end sm:self-auto">
          <div className="px-3 py-1.5 rounded-[4px] bg-[#1b1b1b] border border-[#2a2a2a] font-mono text-xs text-[#e2e2e2] flex items-center gap-2">
            <Icon name="timer" className="text-sm text-[#4be277]" />
            <span>{formatTimer(elapsedSec)}</span>
          </div>
          <button
            onClick={() => finishInterviewMutation.mutate()}
            className="px-3 py-1.5 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs text-[#ffb4ab] hover:bg-[#93000a]/20"
          >
            Finish Early
          </button>
        </div>
      </div>

      {/* Main Grid: Left Question/Answer (Chat panel) & Right Live Feedback */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Left Column: Question & Answer Workspace */}
        <div className="space-y-4">
          {/* Question Card */}
          <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-3 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#4be277] animate-pulse" />
                <span className="label-mono text-xs text-[#4be277] font-bold">
                  INTERVIEW QUESTION #{curQuestion?.seq || 1}
                </span>
              </div>
              <span className="text-[10px] font-mono text-[#869585] uppercase">
                {curQuestion?.topic}
              </span>
            </div>

            <p className="text-sm sm:text-base font-semibold text-[#e2e2e2] leading-relaxed">
              {curQuestion ? curQuestion.text : 'Loading question...'}
            </p>
          </div>

          {/* Candidate Answer Input */}
          <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-3">
            <div className="flex items-center justify-between">
              <label className="label-mono text-xs text-[#bccbb9]">YOUR TECHNICAL RESPONSE</label>
              <span className="text-[11px] font-mono text-[#869585]">
                {wordCount} words · {charCount}/4,000 chars
              </span>
            </div>

            <textarea
              rows={8}
              value={candidateAnswer}
              onChange={(e) => setCandidateAnswer(e.target.value.slice(0, 4000))}
              placeholder="State your approach, assumptions, trade-offs, and time/space complexity..."
              className="w-full p-3.5 rounded-[4px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] placeholder-[#869585] focus:border-[#4be277] focus:outline-hidden leading-relaxed font-sans"
            />

            <div className="flex items-center justify-between pt-1">
              <span className="text-[10px] text-[#869585]">
                Evaluator checks correctness, depth, structure, and communication.
              </span>
              <button
                onClick={() => submitAnswerMutation.mutate()}
                disabled={submitAnswerMutation.isPending || !candidateAnswer.trim()}
                className="px-5 py-2 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {submitAnswerMutation.isPending ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-[#003915] border-t-transparent rounded-full animate-spin" />
                    <span>Evaluating Answer...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Answer</span>
                    <Icon name="send" className="text-sm" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Live Feedback Panel or Pending Analysis State */}
        <div className="space-y-4">
          {latestEvaluation ? (
            <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#4be277]/40 space-y-5 animate-in fade-in duration-200">
              {/* Score Header */}
              <div className="flex items-center justify-between pb-3 border-b border-[#2a2a2a]">
                <div>
                  <div className="label-mono text-xs text-[#4be277]">LLM JUDGE EVALUATION</div>
                  <div className="text-xl font-bold text-[#e2e2e2]">Answer Evaluated</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-[#4be277]">
                    {latestEvaluation.overall.toFixed(1)}/10
                  </div>
                  <div className="text-[10px] text-[#869585] font-mono">DIMENSION WEIGHTED</div>
                </div>
              </div>

              {/* Dimension Scores */}
              <div className="space-y-2.5">
                {[
                  { name: 'Correctness', score: latestEvaluation.scores.correctness },
                  { name: 'Technical Depth', score: latestEvaluation.scores.depth },
                  { name: 'Structure & Coherence', score: latestEvaluation.scores.structure },
                  { name: 'Communication', score: latestEvaluation.scores.communication },
                ].map((dim, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-[#bccbb9]">{dim.name}</span>
                      <span className="font-mono text-[#e2e2e2]">{dim.score.toFixed(1)}/10</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#131313] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#4be277]"
                        style={{ width: `${Math.min(100, (dim.score / 10) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Strengths & Gaps */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                <div className="p-3 rounded-[4px] bg-[#1f1f1f] border border-[#4be277]/20">
                  <div className="label-mono text-[10px] text-[#4be277] mb-1 font-bold">STRENGTHS</div>
                  <ul className="space-y-1 text-[#bccbb9]">
                    {latestEvaluation.feedback.strengths.map((s, idx) => (
                      <li key={idx} className="line-clamp-2">• {s}</li>
                    ))}
                  </ul>
                </div>
                <div className="p-3 rounded-[4px] bg-[#1f1f1f] border border-[#ffb4ab]/20">
                  <div className="label-mono text-[10px] text-[#ffb4ab] mb-1 font-bold">AREAS FOR IMPROVEMENT</div>
                  <ul className="space-y-1 text-[#bccbb9]">
                    {latestEvaluation.feedback.gaps.map((g, idx) => (
                      <li key={idx} className="line-clamp-2">• {g}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Improved Answer Accordion */}
              {latestEvaluation.feedback.improved_answer && (
                <div className="p-3.5 rounded-[4px] bg-[#131313] border border-[#2a2a2a] space-y-2">
                  <button
                    onClick={() => setShowImprovedAnswer(!showImprovedAnswer)}
                    className="w-full flex items-center justify-between text-xs font-bold text-[#e2e2e2]"
                  >
                    <span>Exemplary Senior-Level Answer</span>
                    <Icon name={showImprovedAnswer ? 'expand_less' : 'expand_more'} className="text-base" />
                  </button>
                  {showImprovedAnswer && (
                    <p className="text-xs text-[#bccbb9] leading-relaxed pt-1">
                      {latestEvaluation.feedback.improved_answer}
                    </p>
                  )}
                </div>
              )}

              {/* Follow-up & Next Actions */}
              <div className="pt-2 flex items-center justify-between border-t border-[#2a2a2a]">
                <button
                  onClick={() => followUpMutation.mutate()}
                  disabled={followUpMutation.isPending}
                  className="px-3 py-1.5 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs text-[#bccbb9] hover:text-[#e2e2e2] flex items-center gap-1.5"
                >
                  <Icon name="question_answer" className="text-sm text-[#4be277]" />
                  <span>Request Follow-up Question</span>
                </button>

                <button
                  onClick={handleNextQuestion}
                  className="px-4 py-1.5 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] flex items-center gap-1"
                >
                  <span>Next Question</span>
                  <Icon name="arrow_forward" className="text-sm" />
                </button>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] text-center space-y-4">
              <div className="w-12 h-12 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] flex items-center justify-center text-[#869585] mx-auto">
                <Icon name="psychology" className="text-2xl" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#e2e2e2]">Pending Candidate Submission</h4>
                <p className="text-xs text-[#869585] mt-1 max-w-xs mx-auto">
                  Type your complete solution in the editor on the left and submit to trigger schema-validated LLM evaluation.
                </p>
              </div>

              {/* Pro-Tip Card */}
              <div className="p-4 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-left space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#4be277]">
                  <Icon name="lightbulb" className="text-sm" />
                  <span>Technical Interview Pro-Tip</span>
                </div>
                <p className="text-[11px] text-[#bccbb9] leading-relaxed">
                  Start by clarifying assumptions and edge cases (e.g. null inputs, integer overflow). Outline your high-level approach before writing detailed logic, and explicitly state time and space complexity.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MockInterviewPage;
