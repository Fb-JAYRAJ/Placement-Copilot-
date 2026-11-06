import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDsaTopics,
  getDsaAttempts,
  getDsaMastery,
  getDsaRecommendations,
  getDsaReviewsDue,
  getDsaStats,
  getDsaProblems,
  logDsaAttempt,
  updateDsaAttempt,
  deleteDsaAttempt,
} from '@/lib/api';
import Icon from '@/components/common/Icon';
import { toast } from '@/components/common/toastStore';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

/**
 * Algorithmic Problem Tracker.
 * Manages problem practice attempts, topic-level mastery scores with exponential decay,
 * SuperMemo SM-2 spaced repetition review schedules, and 7-day velocity.
 */
export const DSATrackerPage = () => {
  const queryClient = useQueryClient();

  // Filters state
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingAttempt, setEditingAttempt] = useState(null);

  // Form state
  const [problemMode, setProblemMode] = useState('catalog');
  const [catalogSearch, setCatalogSearch] = useState('');
  const [selectedProblemId, setSelectedProblemId] = useState('');
  const [customTitle, setCustomTitle] = useState('');
  const [formTopicId, setFormTopicId] = useState('');
  const [formDifficulty, setFormDifficulty] = useState('medium');
  const [formStatus, setFormStatus] = useState('solved');
  const [formTimeSpent, setFormTimeSpent] = useState(30);
  const [formConfidence, setFormConfidence] = useState(3);
  const [formNotes, setFormNotes] = useState('');

  // Queries
  const { data: topics = [] } = useQuery({
    queryKey: ['dsa-topics'],
    queryFn: getDsaTopics,
  });

  const { data: attempts = [], isLoading: attemptsLoading } = useQuery({
    queryKey: ['dsa-attempts'],
    queryFn: getDsaAttempts,
  });

  const { data: masteryList = [] } = useQuery({
    queryKey: ['dsa-mastery'],
    queryFn: getDsaMastery,
  });

  const { data: recommendations = [] } = useQuery({
    queryKey: ['dsa-recommendations'],
    queryFn: getDsaRecommendations,
  });

  const { data: reviewsDue = [] } = useQuery({
    queryKey: ['dsa-reviews-due'],
    queryFn: getDsaReviewsDue,
  });

  const { data: stats } = useQuery({
    queryKey: ['dsa-stats'],
    queryFn: getDsaStats,
  });

  const { data: catalogProblems = [] } = useQuery({
    queryKey: ['dsa-problems-catalog', catalogSearch],
    queryFn: () => getDsaProblems({ q: catalogSearch, limit: 20 }),
    enabled: problemMode === 'catalog' && drawerOpen,
  });

  // Mutations with optimistic updates
  const logAttemptMutation = useMutation({
    mutationFn: async (payload) => {
      if (editingAttempt) {
        return updateDsaAttempt(editingAttempt.id, payload);
      }
      return logDsaAttempt(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dsa-attempts'] });
      queryClient.invalidateQueries({ queryKey: ['dsa-mastery'] });
      queryClient.invalidateQueries({ queryKey: ['dsa-recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['dsa-reviews-due'] });
      queryClient.invalidateQueries({ queryKey: ['dsa-stats'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      toast.success(editingAttempt ? 'Attempt updated' : 'Problem attempt logged successfully!');
      closeDrawer();
    },
    onError: (err) => {
      toast.error(err?.message || 'Failed to record attempt');
    },
  });

  const deleteAttemptMutation = useMutation({
    mutationFn: (id) => deleteDsaAttempt(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dsa-attempts'] });
      queryClient.invalidateQueries({ queryKey: ['dsa-mastery'] });
      queryClient.invalidateQueries({ queryKey: ['dsa-stats'] });
      toast.success('Attempt removed');
    },
  });

  /**
   * Opens log drawer, optionally prefilling problem details.
   * @param {Object} [prefill]
   */
  const openDrawerForNew = (prefill) => {
    setEditingAttempt(null);
    if (prefill && prefill.problem_id) {
      setProblemMode('catalog');
      setSelectedProblemId(prefill.problem_id);
      setCatalogSearch(prefill.title || '');
      setFormTopicId(prefill.topic_id || '');
      setFormDifficulty(prefill.difficulty || 'medium');
    } else {
      setProblemMode('catalog');
      setSelectedProblemId('');
      setCatalogSearch('');
      setCustomTitle('');
      setFormTopicId(topics[0]?.id || '');
      setFormDifficulty('medium');
    }
    setFormStatus('solved');
    setFormTimeSpent(30);
    setFormConfidence(3);
    setFormNotes('');
    setDrawerOpen(true);
  };

  /**
   * Opens drawer populated with existing attempt details for editing.
   * @param {Object} attempt
   */
  const openDrawerForEdit = (attempt) => {
    setEditingAttempt(attempt);
    if (attempt.problem_id) {
      setProblemMode('catalog');
      setSelectedProblemId(attempt.problem_id);
      setCatalogSearch(attempt.problem?.title || '');
    } else {
      setProblemMode('custom');
      setCustomTitle(attempt.custom_title || '');
    }
    setFormTopicId(attempt.topic_id);
    setFormDifficulty(attempt.difficulty);
    setFormStatus(attempt.status);
    setFormTimeSpent(attempt.time_spent_min || 30);
    setFormConfidence(attempt.confidence);
    setFormNotes(attempt.notes || '');
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setEditingAttempt(null);
  };

  const handleDrawerSubmit = (e) => {
    e.preventDefault();
    if (problemMode === 'catalog' && !selectedProblemId) {
      toast.error('Please select a problem from the catalog or switch to custom title.');
      return;
    }
    if (problemMode === 'custom' && !customTitle.trim()) {
      toast.error('Please specify the problem title.');
      return;
    }
    if (!formTopicId) {
      toast.error('Please choose a DSA topic.');
      return;
    }

    logAttemptMutation.mutate({
      problem_id: problemMode === 'catalog' ? selectedProblemId : null,
      custom_title: problemMode === 'custom' ? customTitle.trim() : null,
      topic_id: formTopicId,
      difficulty: formDifficulty,
      status: formStatus,
      confidence: formConfidence,
      time_spent_min: formTimeSpent,
      notes: formNotes,
    });
  };

  // Filtered attempts
  const filteredAttempts = attempts.filter((att) => {
    if (activeTab !== 'all' && att.status !== activeTab) return false;
    if (selectedTopic !== 'all' && att.topic_id !== selectedTopic) return false;
    if (selectedDifficulty !== 'all' && att.difficulty !== selectedDifficulty) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const title = (att.problem?.title || att.custom_title || '').toLowerCase();
      const topicName = (att.topic?.name || '').toLowerCase();
      if (!title.includes(q) && !topicName.includes(q)) return false;
    }
    return true;
  });

  const getDifficultyBadge = (diff) => {
    switch (diff) {
      case 'easy':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-primary">
            <span className="w-1.5 h-1.5 rounded-full bg-primary" /> Easy
          </span>
        );
      case 'hard':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-error">
            <span className="w-1.5 h-1.5 rounded-full bg-error" /> Hard
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-warning">
            <span className="w-1.5 h-1.5 rounded-full bg-warning" /> Medium
          </span>
        );
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'solved':
        return <span className="px-2 py-0.5 rounded-[2px] bg-primary/10 text-primary text-[10px] font-mono uppercase">Solved</span>;
      case 'in_progress':
        return <span className="px-2 py-0.5 rounded-[2px] bg-warning/10 text-warning text-[10px] font-mono uppercase">In Progress</span>;
      case 'failed':
        return <span className="px-2 py-0.5 rounded-[2px] bg-error/10 text-error text-[10px] font-mono uppercase">Failed</span>;
      default:
        return <span className="px-2 py-0.5 rounded-[2px] bg-surface-container-high text-outline text-[10px] font-mono uppercase">To-Do</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-container pb-5">
        <div>
          <div className="label-mono text-xs text-primary mb-1">DSA PRACTICE TRACKER</div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight">
            Algorithmic Problem Tracker
          </h1>
          <p className="text-xs text-outline mt-0.5">
            Exponential decay modeling (τ=45d) with SM-2 spaced repetition schedules.
          </p>
        </div>

        <button
          onClick={() => openDrawerForNew()}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-[4px] bg-primary text-on-primary text-xs font-bold uppercase tracking-wider hover:bg-primary-container transition-colors self-start sm:self-auto shadow-sm"
        >
          <Icon name="add" className="text-base" />
          <span>Log New Problem</span>
        </button>
      </div>

      {/* Main Grid: Left Problem Table (2 cols) & Right Insights (1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Attempts Table & Filters */}
        <div className="lg:col-span-2 space-y-4">
          {/* Tabs & Search Controls */}
          <div className="p-4 rounded-[8px] bg-surface-container-low border border-surface-container-high space-y-3">
            {/* Tabs */}
            <div className="flex flex-wrap items-center gap-1.5 border-b border-surface-container pb-3">
              {[
                { id: 'all', label: 'All Problems' },
                { id: 'solved', label: 'Solved' },
                { id: 'in_progress', label: 'In Progress' },
                { id: 'todo', label: 'To-Do' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-[4px] transition-all ${
                    activeTab === tab.id
                      ? 'bg-primary text-on-primary'
                      : 'text-outline hover:text-on-surface hover:bg-surface-container'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Filter Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search problem or topic..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-[2px] bg-surface border border-outline-variant text-xs text-on-surface placeholder-outline focus:border-primary focus:outline-hidden"
                />
                <Icon name="search" className="absolute left-2.5 top-2 text-sm text-outline" />
              </div>

              <select
                value={selectedTopic}
                onChange={(e) => setSelectedTopic(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-[2px] bg-surface border border-outline-variant text-xs text-on-surface focus:border-primary focus:outline-hidden"
              >
                <option value="all">All Topics</option>
                {topics.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>

              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-[2px] bg-surface border border-outline-variant text-xs text-on-surface focus:border-primary focus:outline-hidden"
              >
                <option value="all">All Difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="rounded-[8px] bg-surface-container-low border border-surface-container-high overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-surface-container-high bg-surface-container/60 text-[10px] label-mono text-outline">
                    <th className="py-3 px-4">PROBLEM TITLE</th>
                    <th className="py-3 px-3">TOPIC</th>
                    <th className="py-3 px-3">DIFFICULTY</th>
                    <th className="py-3 px-3">STATUS</th>
                    <th className="py-3 px-3">CONFIDENCE</th>
                    <th className="py-3 px-3">NEXT REVIEW</th>
                    <th className="py-3 px-4 text-right">ACTIONS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container text-xs">
                  {attemptsLoading ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-outline">
                        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                        Loading tracked attempts...
                      </td>
                    </tr>
                  ) : filteredAttempts.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-outline space-y-2">
                        <Icon name="search_off" className="text-2xl text-outline" />
                        <div className="text-sm font-medium text-on-surface">No problems match your filters</div>
                        <p className="text-xs">Log a new practice attempt to start building mastery.</p>
                      </td>
                    </tr>
                  ) : (
                    filteredAttempts.map((att) => {
                      const title = att.problem?.title || att.custom_title || 'Untitled Problem';
                      const topicName = att.topic?.name || 'General';
                      const isReviewOverdue =
                        att.next_review_at && new Date(att.next_review_at).getTime() <= Date.now();

                      return (
                        <tr key={att.id} className="hover:bg-surface-container/50 transition-colors">
                          <td className="py-3 px-4 font-medium text-on-surface">
                            <div className="flex items-center gap-1.5">
                              {att.problem?.url ? (
                                <a
                                  href={att.problem.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="hover:text-primary transition-colors truncate max-w-[200px]"
                                >
                                  {title}
                                </a>
                              ) : (
                                <span className="truncate max-w-[200px]">{title}</span>
                              )}
                              {att.problem?.url && (
                                <Icon name="open_in_new" className="text-[12px] text-outline" />
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded-[2px] bg-surface border border-surface-container-high text-[10px] text-on-surface-variant">
                              {topicName}
                            </span>
                          </td>
                          <td className="py-3 px-3">{getDifficultyBadge(att.difficulty)}</td>
                          <td className="py-3 px-3">{getStatusBadge(att.status)}</td>
                          <td className="py-3 px-3">
                            <div className="flex items-center gap-0.5 text-xs text-warning">
                              {Array.from({ length: 5 }).map((_, i) => (
                                <span key={i} className={i < att.confidence ? 'opacity-100' : 'opacity-20'}>
                                  ★
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="py-3 px-3 font-mono text-[11px]">
                            {att.next_review_at ? (
                              <span className={isReviewOverdue ? 'text-error font-bold' : 'text-outline'}>
                                {new Date(att.next_review_at).toLocaleDateString(undefined, {
                                  month: 'short',
                                  day: 'numeric',
                                })}
                                {isReviewOverdue && ' (due)'}
                              </span>
                            ) : (
                              <span className="text-outline">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="inline-flex items-center gap-1">
                              <button
                                onClick={() => openDrawerForEdit(att)}
                                className="p-1 text-outline hover:text-primary transition-colors"
                                title="Edit attempt"
                              >
                                <Icon name="edit" className="text-sm" />
                              </button>
                              <button
                                onClick={() => deleteAttemptMutation.mutate(att.id)}
                                className="p-1 text-outline hover:text-error transition-colors"
                                title="Delete attempt"
                              >
                                <Icon name="delete" className="text-sm" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Mastery, Recommendations, Reviews Due, 7d Chart */}
        <div className="space-y-6">
          {/* Weak Areas Mastery Bars */}
          <div className="p-5 rounded-[8px] bg-surface-container-low border border-surface-container-high">
            <div className="flex items-center justify-between mb-3">
              <span className="label-mono text-[10px] text-outline">TOPIC MASTERY & WEAK SPOTS</span>
              <Icon name="analytics" className="text-sm text-primary" />
            </div>
            <div className="space-y-3">
              {masteryList.slice(0, 6).map((m) => {
                const masteryPct = Math.round(m.mastery * 100);
                // Color codes: red < 40%, amber 40–70%, green > 70%
                let barColor = 'bg-error';
                if (masteryPct >= 70) barColor = 'bg-primary';
                else if (masteryPct >= 40) barColor = 'bg-warning';

                return (
                  <div key={m.topic_id} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-on-surface font-medium">{m.topic_name}</span>
                      <span className="font-mono text-outline">{masteryPct}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
                      <div
                        className={`h-full ${barColor} transition-all duration-500`}
                        style={{ width: `${masteryPct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 5 Recommended Practice Problems */}
          <div className="p-5 rounded-[8px] bg-surface-container-low border border-primary/30">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5">
                <Icon name="auto_awesome" className="text-sm text-primary" />
                <span className="label-mono text-[10px] text-primary font-bold">ALGORITHMIC RECOMMENDATIONS</span>
              </div>
              <span className="text-[10px] text-outline font-mono">5 TARGETS</span>
            </div>
            <div className="space-y-2.5">
              {recommendations.slice(0, 5).map((rec) => (
                <div
                  key={rec.problem_id}
                  className="p-3 rounded-[4px] bg-surface-container border border-surface-container-high flex items-start justify-between gap-2"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-on-surface truncate">{rec.title}</span>
                      {getDifficultyBadge(rec.difficulty)}
                    </div>
                    <div className="text-[11px] text-outline mt-0.5 line-clamp-1">{rec.reason}</div>
                  </div>
                  <button
                    onClick={() => openDrawerForNew(rec)}
                    className="p-1 text-outline hover:text-primary shrink-0"
                    title="Log attempt"
                  >
                    <Icon name="add_circle" className="text-base" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Reviews Due (SM-2 Spaced Repetition) */}
          {reviewsDue && reviewsDue.length > 0 && (
            <div className="p-5 rounded-[8px] bg-surface-container-low border border-error/30">
              <div className="flex items-center justify-between mb-3">
                <span className="label-mono text-[10px] text-error">SM-2 REVIEWS DUE ({reviewsDue.length})</span>
                <Icon name="schedule" className="text-sm text-error" />
              </div>
              <div className="space-y-2">
                {reviewsDue.slice(0, 3).map((r) => (
                  <div
                    key={r.attempt_id}
                    className="p-2.5 rounded-[4px] bg-surface-container border border-surface-container-high flex items-center justify-between"
                  >
                    <div className="min-w-0 pr-2">
                      <div className="text-xs font-semibold text-on-surface truncate">{r.title}</div>
                      <div className="text-[10px] text-outline">{r.topic_name}</div>
                    </div>
                    <button
                      onClick={() => openDrawerForNew({ problem_id: r.attempt_id, title: r.title })}
                      className="px-2 py-1 rounded-[2px] bg-error/20 text-error text-[10px] font-mono font-bold uppercase hover:bg-error/30"
                    >
                      Review
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 7-Day Solved Bar Chart */}
          {stats && stats.daily_solved_7d && (
            <div className="p-5 rounded-[8px] bg-surface-container-low border border-surface-container-high">
              <div className="flex items-center justify-between mb-2">
                <span className="label-mono text-[10px] text-outline">7-DAY SOLVED VELOCITY</span>
                <span className="text-xs font-mono font-bold text-primary">
                  {stats.solved_count} Total Solved
                </span>
              </div>
              <div className="h-28 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.daily_solved_7d}>
                    <XAxis
                      dataKey="date"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fill: '#869585', fontSize: 10 }}
                    />
                    <YAxis hide allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f1f1f', borderColor: '#3d4a3d', borderRadius: 4, fontSize: 11 }}
                    />
                    <Bar dataKey="count" fill="#4be277" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Slide-over Right Drawer for Logging / Editing Attempts */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="fixed inset-0 bg-black/70 backdrop-blur-xs" onClick={closeDrawer} />
          <div className="relative w-full max-w-md bg-surface border-l border-outline-variant h-full overflow-y-auto p-6 z-50 animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between border-b border-surface-container pb-4 mb-5">
              <div>
                <h3 className="text-lg font-bold text-on-surface">
                  {editingAttempt ? 'Edit Practice Attempt' : 'Log New Practice Attempt'}
                </h3>
                <div className="label-mono text-[10px] text-primary">MATHEMATICAL MASTERY MODEL</div>
              </div>
              <button onClick={closeDrawer} className="text-outline hover:text-on-surface">
                <Icon name="close" className="text-xl" />
              </button>
            </div>

            <form onSubmit={handleDrawerSubmit} className="space-y-4">
              {/* Mode switch */}
              {!editingAttempt && (
                <div className="p-1 rounded-[4px] bg-surface-container-low border border-surface-container-high flex">
                  <button
                    type="button"
                    onClick={() => setProblemMode('catalog')}
                    className={`flex-1 py-1 text-xs font-semibold rounded-[2px] ${
                      problemMode === 'catalog' ? 'bg-primary text-on-primary' : 'text-outline'
                    }`}
                  >
                    Curated Catalog
                  </button>
                  <button
                    type="button"
                    onClick={() => setProblemMode('custom')}
                    className={`flex-1 py-1 text-xs font-semibold rounded-[2px] ${
                      problemMode === 'custom' ? 'bg-primary text-on-primary' : 'text-outline'
                    }`}
                  >
                    Custom Title
                  </button>
                </div>
              )}

              {/* Problem Selection */}
              {problemMode === 'catalog' ? (
                <div>
                  <label className="block label-mono text-[11px] text-on-surface-variant mb-1">
                    SEARCH CATALOG PROBLEMS
                  </label>
                  <input
                    type="text"
                    placeholder="Search 140+ Blind-75 & curated problems..."
                    value={catalogSearch}
                    onChange={(e) => {
                      setCatalogSearch(e.target.value);
                      setSelectedProblemId('');
                    }}
                    className="w-full px-3 py-2 rounded-[2px] bg-surface-container-low border border-outline-variant text-xs text-on-surface placeholder-outline focus:border-primary"
                  />
                  {catalogProblems.length > 0 && !selectedProblemId && (
                    <div className="mt-1.5 max-h-48 overflow-y-auto rounded-[2px] bg-surface-container-low border border-surface-container-high divide-y divide-surface-container-high">
                      {catalogProblems.map((prob) => (
                        <button
                          key={prob.id}
                          type="button"
                          onClick={() => {
                            setSelectedProblemId(prob.id);
                            setCatalogSearch(prob.title);
                            setFormDifficulty(prob.difficulty);
                            if (prob.topics && prob.topics.length > 0) {
                              setFormTopicId(prob.topics[0].id);
                            }
                          }}
                          className="w-full text-left p-2 hover:bg-surface-container-high flex items-center justify-between text-xs"
                        >
                          <span className="text-on-surface font-medium">{prob.title}</span>
                          <span className="text-[10px] font-mono text-outline uppercase">{prob.difficulty}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <label className="block label-mono text-[11px] text-on-surface-variant mb-1">CUSTOM PROBLEM TITLE</label>
                  <input
                    type="text"
                    placeholder="e.g., Minimum Window Substring with Duplicates"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    className="w-full px-3 py-2 rounded-[2px] bg-surface-container-low border border-outline-variant text-xs text-on-surface placeholder-outline focus:border-primary"
                  />
                </div>
              )}

              {/* Topic Select */}
              <div>
                <label className="block label-mono text-[11px] text-on-surface-variant mb-1">DSA TOPIC CATEGORY</label>
                <select
                  value={formTopicId}
                  onChange={(e) => setFormTopicId(e.target.value)}
                  className="w-full px-3 py-2 rounded-[2px] bg-surface-container-low border border-outline-variant text-xs text-on-surface focus:border-primary"
                >
                  <option value="">Select Topic...</option>
                  {topics.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.category})
                    </option>
                  ))}
                </select>
              </div>

              {/* Difficulty & Status */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block label-mono text-[11px] text-on-surface-variant mb-1">DIFFICULTY</label>
                  <select
                    value={formDifficulty}
                    onChange={(e) => setFormDifficulty(e.target.value)}
                    className="w-full px-3 py-2 rounded-[2px] bg-surface-container-low border border-outline-variant text-xs text-on-surface focus:border-primary"
                  >
                    <option value="easy">Easy (1.0 wt)</option>
                    <option value="medium">Medium (2.0 wt)</option>
                    <option value="hard">Hard (3.5 wt)</option>
                  </select>
                </div>
                <div>
                  <label className="block label-mono text-[11px] text-on-surface-variant mb-1">STATUS</label>
                  <select
                    value={formStatus}
                    onChange={(e) => setFormStatus(e.target.value)}
                    className="w-full px-3 py-2 rounded-[2px] bg-surface-container-low border border-outline-variant text-xs text-on-surface focus:border-primary"
                  >
                    <option value="solved">Solved</option>
                    <option value="in_progress">In Progress</option>
                    <option value="failed">Failed / Stuck</option>
                    <option value="todo">To-Do</option>
                  </select>
                </div>
              </div>

              {/* Confidence Slider */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="label-mono text-[11px] text-on-surface-variant">CONFIDENCE SCORE: {formConfidence}/5</label>
                  <span className="text-[10px] text-outline">
                    {formConfidence === 5
                      ? 'Mastered'
                      : formConfidence >= 4
                      ? 'Solid'
                      : formConfidence >= 3
                      ? 'Decent'
                      : 'Needs Revision'}
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={formConfidence}
                  onChange={(e) => setFormConfidence(Number(e.target.value))}
                  className="w-full accent-primary"
                />
              </div>

              {/* Time Spent */}
              <div>
                <label className="block label-mono text-[11px] text-on-surface-variant mb-1">
                  TIME SPENT (MINUTES)
                </label>
                <input
                  type="number"
                  min={1}
                  max={300}
                  value={formTimeSpent}
                  onChange={(e) => setFormTimeSpent(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-[2px] bg-surface-container-low border border-outline-variant text-xs text-on-surface focus:border-primary"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block label-mono text-[11px] text-on-surface-variant mb-1">
                  SOLUTION NOTES / TIME & SPACE COMPLEXITY
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Used two pointers with sliding window. O(N) time, O(1) space."
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-[2px] bg-surface-container-low border border-outline-variant text-xs text-on-surface placeholder-outline focus:border-primary"
                />
              </div>

              {/* Action buttons */}
              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={closeDrawer}
                  className="px-4 py-2 rounded-[4px] bg-surface-container-low border border-surface-container-high text-xs text-outline hover:text-on-surface"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={logAttemptMutation.isPending}
                  className="px-5 py-2 rounded-[4px] bg-primary text-on-primary text-xs font-bold uppercase tracking-wider hover:bg-primary-container transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  {logAttemptMutation.isPending && (
                    <div className="w-3.5 h-3.5 border-2 border-on-primary border-t-transparent rounded-full animate-spin" />
                  )}
                  <span>{editingAttempt ? 'Save Changes' : 'Log Attempt'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DSATrackerPage;
