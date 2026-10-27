/**
 * Centralized API service layer for Placement Copilot.
 * Ensures consistent response unwrapping: all list endpoints guarantee native Javascript arrays.
 * Pages and components consume these typed, JSDoc-annotated functions rather than reading raw envelopes.
 */
import api from './client';

export { api };
export default api;

/**
 * Normalizes an API response to guarantee an array.
 * Unwraps paginated envelopes ({ items: [...], total, limit, offset }) or raw arrays.
 * @template T
 * @param {any} response
 * @returns {T[]}
 */
export const unwrapArray = (response) => {
  if (!response) return [];
  if (Array.isArray(response)) return response;
  if (Array.isArray(response.items)) return response.items;
  return [];
};

// ==========================================
// 1. Data Structures & Algorithms (DSA) API
// ==========================================

/**
 * Fetches all available DSA topics and categories.
 * @returns {Promise<Array<{ id: string, name: string, category: string, slug: string, target_points: number }>>}
 */
export const getDsaTopics = async () => {
  const data = await api.get('/dsa/topics');
  return unwrapArray(data);
};

/**
 * Searches curated DSA problem catalog.
 * @param {Object} [params]
 * @param {string} [params.q] - Search query string
 * @param {string} [params.topic] - Topic slug filter
 * @param {string} [params.difficulty] - 'easy' | 'medium' | 'hard'
 * @param {number} [params.limit=20]
 * @param {number} [params.offset=0]
 * @returns {Promise<Array<{ id: string, title: string, difficulty: string, platform: string, url: string, topic: any }>>}
 */
export const getDsaProblems = async ({ q = '', topic = '', difficulty = '', limit = 20, offset = 0 } = {}) => {
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (topic) params.set('topic', topic);
  if (difficulty) params.set('difficulty', difficulty);
  if (limit) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  const queryStr = params.toString() ? `?${params.toString()}` : '';
  const data = await api.get(`/dsa/problems${queryStr}`);
  return unwrapArray(data);
};

/**
 * Fetches all logged DSA problem attempts for current candidate.
 * @returns {Promise<Array<{ id: string, problem_id: string|null, custom_title: string|null, topic_id: string, difficulty: string, status: string, confidence: number, time_spent_min: number, notes: string|null, attempted_at: string, problem: any, topic: any }>>}
 */
export const getDsaAttempts = async () => {
  const data = await api.get('/dsa/attempts');
  return unwrapArray(data);
};

/**
 * Fetches real-time mastery scores (0–100%) and priorities across DSA topics.
 * @returns {Promise<Array<{ topic_id: string, topic_name: string, category: string, mastery_score: number, problems_solved: number, total_attempts: number, decay_factor: number, priority_level: string, last_attempted_at: string|null }>>}
 */
export const getDsaMastery = async () => {
  const data = await api.get('/dsa/mastery');
  return unwrapArray(data);
};

/**
 * Fetches top recommended problems targeting candidate weak areas.
 * @returns {Promise<Array<{ id: string, title: string, difficulty: string, url: string, topic_name: string, recommendation_reason: string, priority_weight: number }>>}
 */
export const getDsaRecommendations = async () => {
  const data = await api.get('/dsa/recommendations');
  return unwrapArray(data);
};

/**
 * Fetches problems scheduled for SuperMemo SM-2 spaced repetition review.
 * @returns {Promise<Array<{ attempt_id: string, problem_title: string, topic_name: string, difficulty: string, scheduled_for: string, repetitions: number, ease_factor: number }>>}
 */
export const getDsaReviewsDue = async () => {
  const data = await api.get('/dsa/reviews/due');
  return unwrapArray(data);
};

/**
 * Fetches aggregated DSA summary statistics and 7-day velocity chart.
 * @returns {Promise<{ total_solved: number, total_attempted: number, active_streak_days: number, velocity_7d: Array<{ date: string, count: number }>, easy_count: number, medium_count: number, hard_count: number }>}
 */
export const getDsaStats = async () => {
  return api.get('/dsa/stats');
};

/**
 * Records a new problem practice attempt.
 * @param {Object} payload
 * @returns {Promise<any>}
 */
export const logDsaAttempt = async (payload) => {
  return api.post('/dsa/attempts', payload);
};

/**
 * Updates an existing problem attempt.
 * @param {string} id
 * @param {Object} payload
 * @returns {Promise<any>}
 */
export const updateDsaAttempt = async (id, payload) => {
  return api.patch(`/dsa/attempts/${id}`, payload);
};

/**
 * Deletes a recorded problem attempt.
 * @param {string} id
 * @returns {Promise<any>}
 */
export const deleteDsaAttempt = async (id) => {
  return api.delete(`/dsa/attempts/${id}`);
};

// ==========================================
// 2. Resumes & ATS Analysis API
// ==========================================

/**
 * Fetches all resumes saved for the candidate.
 * @returns {Promise<Array<{ id: string, title: string, file_path: string|null, created_at: string, skills: string[] }>>}
 */
export const getResumes = async () => {
  const data = await api.get('/resumes');
  return unwrapArray(data);
};

/**
 * Uploads a candidate resume via multipart FormData or text content.
 * @param {FormData} formData
 * @returns {Promise<{ id: string, title: string, created_at: string }>}
 */
export const uploadResume = async (formData) => {
  return api.post('/resumes', formData);
};

/**
 * Deletes a candidate resume.
 * @param {string} id
 * @returns {Promise<any>}
 */
export const deleteResume = async (id) => {
  return api.delete(`/resumes/${id}`);
};

/**
 * Fetches saved target job descriptions.
 * @returns {Promise<Array<{ id: string, company: string, role: string, created_at: string }>>}
 */
export const getJobDescriptions = async () => {
  const data = await api.get('/job-descriptions');
  return unwrapArray(data);
};

/**
 * Creates a saved target job description.
 * @param {Object} payload
 * @returns {Promise<any>}
 */
export const createJobDescription = async (payload) => {
  return api.post('/job-descriptions', payload);
};

/**
 * Fetches historical deterministic ATS analysis reports.
 * @returns {Promise<Array<{ id: string, resume_id: string, company: string, role: string, overall_match_score: number, semantic_score: number, keyword_score: number, missing_skills: string[], created_at: string }>>}
 */
export const getAtsAnalyses = async () => {
  const data = await api.get('/ats/analyses');
  return unwrapArray(data);
};

/**
 * Performs a deterministic ATS alignment analysis.
 * @param {Object} payload
 * @param {string} payload.resume_id
 * @param {string} [payload.job_description_id]
 * @param {string} [payload.inline_jd_text]
 * @param {string} payload.company
 * @param {string} payload.role
 * @returns {Promise<any>}
 */
export const analyzeAts = async (payload) => {
  return api.post('/ats/analyze', payload);
};

// ==========================================
// 3. Mock Interview API
// ==========================================

/**
 * Fetches candidate mock interview sessions.
 * @returns {Promise<Array<{ id: string, track: string, company: string, role: string, status: string, questions_completed: number, final_theta: number|null, overall_score: number|null, created_at: string }>>}
 */
export const getInterviews = async () => {
  const data = await api.get('/interviews');
  return unwrapArray(data);
};

/**
 * Fetches full details for a mock interview session.
 * @param {string} id
 * @returns {Promise<any>}
 */
export const getInterview = async (id) => {
  return api.get(`/interviews/${id}`);
};

/**
 * Starts a new adaptive mock interview session.
 * @param {Object} payload
 * @param {string} payload.track
 * @param {string} payload.company
 * @param {string} payload.role
 * @param {number} [payload.planned_questions=5]
 * @returns {Promise<any>}
 */
export const startInterview = async (payload) => {
  return api.post('/interviews', payload);
};

/**
 * Submits an answer for the current interview question.
 * @param {string} sessionId
 * @param {Object} payload
 * @param {string} payload.question_id
 * @param {string} payload.answer_text
 * @param {number} [payload.time_taken_sec=60]
 * @returns {Promise<any>}
 */
export const submitInterviewAnswer = async (sessionId, payload) => {
  return api.post(`/interviews/${sessionId}/answers`, payload);
};

/**
 * Requests one adaptive follow-up probe on the active question.
 * @param {string} sessionId
 * @returns {Promise<any>}
 */
export const requestInterviewFollowUp = async (sessionId) => {
  return api.post(`/interviews/${sessionId}/follow-up`);
};

/**
 * Concludes an interview session and computes final report analytics.
 * @param {string} sessionId
 * @returns {Promise<any>}
 */
export const finishInterview = async (sessionId) => {
  return api.post(`/interviews/${sessionId}/finish`);
};

/**
 * Fetches the comprehensive final performance report for a completed interview.
 * @param {string} sessionId
 * @returns {Promise<any>}
 */
export const getInterviewReport = async (sessionId) => {
  return api.get(`/interviews/${sessionId}/report`);
};

// ==========================================
// 4. Candidate Dashboard API
// ==========================================

/**
 * Fetches the analytical candidate readiness dashboard summary.
 * Guarantees all nested arrays are valid Javascript arrays.
 * @param {string} [range='30d'] - '7d' | '30d' | '90d'
 * @returns {Promise<any>}
 */
export const getDashboardSummary = async (range = '30d') => {
  const data = await api.get(`/dashboard/summary?range=${encodeURIComponent(range)}`);
  if (!data) return data;
  return {
    ...data,
    levers: unwrapArray(data.levers),
    ats_sparkline: unwrapArray(data.ats_sparkline),
    dsa_sparkline: unwrapArray(data.dsa_sparkline),
    mock_sparkline: unwrapArray(data.mock_sparkline),
    recent_activity: unwrapArray(data.recent_activity),
    onboarding_checklist: data.onboarding_checklist || {},
  };
};

/**
 * Fetches readiness score trend history.
 * @param {number} [days=30]
 * @returns {Promise<Array<{ date: string, composite: number, ats_score: number, dsa_score: number, mock_score: number }>>}
 */
export const getReadinessHistory = async (days = 30) => {
  const data = await api.get(`/dashboard/readiness/history?days=${days}`);
  return unwrapArray(data);
};

// ==========================================
// 5. User Profile & Account API
// ==========================================

/**
 * Fetches active candidate profile.
 * @returns {Promise<{ id: string, email: string, name: string, college: string|null, grad_year: number|null, target_role: string|null, target_companies: string[] }>}
 */
export const getCurrentUser = async () => {
  return api.get('/users/me');
};

/**
 * Updates candidate profile attributes.
 * @param {Object} payload
 * @returns {Promise<any>}
 */
export const updateUserProfile = async (payload) => {
  return api.patch('/users/me', payload);
};

/**
 * Updates account password.
 * @param {Object} payload
 * @param {string} payload.current_password
 * @param {string} payload.new_password
 * @returns {Promise<any>}
 */
export const changePassword = async (payload) => {
  return api.post('/users/me/password', payload);
};

/**
 * Exports complete candidate preparation portfolio as JSON.
 * @returns {Promise<{ user: any, dsa_attempts: any[], resumes: any[], mock_interviews: any[], ats_analyses: any[] }>}
 */
export const exportUserData = async () => {
  return api.get('/users/me/export');
};

/**
 * Deletes candidate account.
 * @returns {Promise<any>}
 */
export const deleteAccount = async () => {
  return api.delete('/users/me');
};
