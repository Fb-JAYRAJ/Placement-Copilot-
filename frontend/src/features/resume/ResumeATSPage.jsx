import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getResumes,
  getAtsAnalyses,
  uploadResume,
  analyzeAts,
} from '@/lib/api';
import Icon from '@/components/common/Icon';
import { toast } from '@/components/common/toastStore';
import { ResponsiveContainer, LineChart, Line, XAxis, Tooltip } from 'recharts';

/**
 * Deterministic ATS Resume Alignment page.
 * Evaluates resumes against target job descriptions via 1-4-gram skill extraction,
 * TF-IDF vector cosine similarity, and semantic requirement embeddings.
 */
export const ResumeATSPage = () => {
  const queryClient = useQueryClient();

  // Mode: 'upload' | 'paste' | 'saved'
  const [resumeMode, setResumeMode] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const [pastedResumeText, setPastedResumeText] = useState('');
  const [resumeTitle, setResumeTitle] = useState('My Resume');
  const [selectedSavedResumeId, setSelectedSavedResumeId] = useState('');

  // JD Inputs
  const [company, setCompany] = useState('Target Tech');
  const [role, setRole] = useState('Software Engineer');
  const [jdText, setJdText] = useState(
    'Requirements:\n- Proficient in Python, FastAPI, and PostgreSQL\n- Experience building RESTful APIs and distributed systems\n- Solid knowledge of Data Structures and Algorithms\n- Familiarity with Docker, Git, and cloud services (AWS or GCP)\n- Strong communication skills and collaborative mindset'
  );

  // Active / selected analysis view
  const [activeAnalysis, setActiveAnalysis] = useState(null);
  const [hoveredMatchedSkill, setHoveredMatchedSkill] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Queries
  const { data: savedResumes = [] } = useQuery({
    queryKey: ['resumes-list'],
    queryFn: getResumes,
  });

  const { data: history = [] } = useQuery({
    queryKey: ['ats-analyses'],
    queryFn: async () => {
      const data = await getAtsAnalyses();
      if (data && data.length > 0 && !activeAnalysis) {
        setActiveAnalysis(data[0]);
      }
      return data;
    },
  });

  // Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: async () => {
      let resumeIdToUse = selectedSavedResumeId;

      // If user uploaded a file or pasted text, upload resume first
      if (resumeMode === 'upload') {
        if (!selectedFile) throw new Error('Please select a PDF or DOCX file to upload');
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('title', resumeTitle || selectedFile.name);
        const res = await uploadResume(formData);
        resumeIdToUse = res.id;
      } else if (resumeMode === 'paste') {
        if (!pastedResumeText.trim()) throw new Error('Please enter your resume text');
        const formData = new FormData();
        formData.append('title', resumeTitle || 'Pasted Resume');
        formData.append('content_text', pastedResumeText.trim());
        const res = await uploadResume(formData);
        resumeIdToUse = res.id;
      }

      if (!resumeIdToUse) {
        throw new Error('Please select or upload a resume');
      }
      if (!jdText.trim()) {
        throw new Error('Please paste the job description text');
      }

      // Run ATS Analysis
      const analysis = await analyzeAts({
        resume_id: resumeIdToUse,
        inline_jd_text: jdText.trim(),
        company: company.trim() || 'Target Company',
        role: role.trim() || 'Software Engineer',
      });

      return analysis;
    },
    onSuccess: (data) => {
      setActiveAnalysis(data);
      queryClient.invalidateQueries({ queryKey: ['ats-analyses'] });
      queryClient.invalidateQueries({ queryKey: ['resumes-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      toast.success('ATS alignment analysis completed!');
    },
    onError: (err) => {
      toast.error(err?.message || 'ATS analysis failed');
    },
  });

  const handleCopyRewrite = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    toast.success('Suggestion copied to clipboard');
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setResumeTitle(file.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setResumeTitle(file.name.replace(/\.[^/.]+$/, ''));
    }
  };

  // Find delta vs previous analysis in history
  const previousAnalysis =
    history.length > 1 && activeAnalysis
      ? history.find((h) => h.id !== activeAnalysis.id)
      : null;
  const deltaVsPrevious =
    activeAnalysis && previousAnalysis
      ? activeAnalysis.overall - previousAnalysis.overall
      : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-[#1f1f1f] pb-5">
        <div className="label-mono text-xs text-[#4be277] mb-1">RESUME ALIGNMENT INTELLIGENCE</div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#e2e2e2] tracking-tight">
          Deterministic ATS Analyzer
        </h1>
        <p className="text-xs text-[#869585] mt-0.5">
          Taxonomy-based skill extraction, TF-IDF cosine similarity, and semantic embedding alignment.
        </p>
      </div>

      {/* Official Disclaimer Banner */}
      <div className="p-3.5 rounded-[4px] bg-[#1b1b1b] border border-[#3d4a3d] flex items-start gap-3 text-xs text-[#bccbb9]">
        <Icon name="info" className="text-base text-[#4be277] shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong className="text-[#e2e2e2]">Estimate Disclaimer:</strong> Placement Copilot scores estimate technical alignment using deterministic natural language processing. Scores are explainable and calibrated, not an endorsement from or replication of any vendor’s proprietary ATS.
        </div>
      </div>

      {/* Two Columns Input Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Resume Input */}
        <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-4">
          <div className="flex items-center justify-between">
            <span className="label-mono text-[10px] text-[#4be277] font-bold">1. CANDIDATE RESUME</span>
            <div className="p-0.5 rounded-[4px] bg-[#131313] border border-[#2a2a2a] flex">
              <button
                type="button"
                onClick={() => setResumeMode('upload')}
                className={`px-2.5 py-1 text-xs font-semibold rounded-[2px] transition-all ${
                  resumeMode === 'upload' ? 'bg-[#4be277] text-[#003915]' : 'text-[#869585]'
                }`}
              >
                Upload File
              </button>
              <button
                type="button"
                onClick={() => setResumeMode('paste')}
                className={`px-2.5 py-1 text-xs font-semibold rounded-[2px] transition-all ${
                  resumeMode === 'paste' ? 'bg-[#4be277] text-[#003915]' : 'text-[#869585]'
                }`}
              >
                Paste Text
              </button>
              {savedResumes.length > 0 && (
                <button
                  type="button"
                  onClick={() => setResumeMode('saved')}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-[2px] transition-all ${
                    resumeMode === 'saved' ? 'bg-[#4be277] text-[#003915]' : 'text-[#869585]'
                  }`}
                >
                  Saved ({savedResumes.length})
                </button>
              )}
            </div>
          </div>

          {resumeMode === 'upload' && (
            <div className="space-y-3">
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                className="border-2 border-dashed border-[#3d4a3d] hover:border-[#4be277] rounded-[4px] p-8 text-center transition-all bg-[#131313]/60 cursor-pointer"
                onClick={() => document.getElementById('resume-file-input')?.click()}
              >
                <input
                  id="resume-file-input"
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileInput}
                  className="hidden"
                />
                <Icon name="upload_file" className="text-3xl text-[#4be277] mb-2" />
                <div className="text-xs font-semibold text-[#e2e2e2]">
                  {selectedFile ? selectedFile.name : 'Drag & drop PDF / DOCX resume or click to browse'}
                </div>
                <div className="text-[11px] text-[#869585] mt-1">
                  Validated via magic bytes · Maximum 5 MB
                </div>
              </div>

              <div>
                <label className="block label-mono text-[10px] text-[#869585] mb-1">RESUME TITLE</label>
                <input
                  type="text"
                  value={resumeTitle}
                  onChange={(e) => setResumeTitle(e.target.value)}
                  placeholder="e.g. SDE Resume v2"
                  className="w-full px-3 py-1.5 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
                />
              </div>
            </div>
          )}

          {resumeMode === 'paste' && (
            <div className="space-y-3">
              <div>
                <label className="block label-mono text-[10px] text-[#869585] mb-1">RESUME TITLE</label>
                <input
                  type="text"
                  value={resumeTitle}
                  onChange={(e) => setResumeTitle(e.target.value)}
                  placeholder="e.g. Pasted Resume"
                  className="w-full px-3 py-1.5 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
                />
              </div>
              <textarea
                rows={9}
                value={pastedResumeText}
                onChange={(e) => setPastedResumeText(e.target.value)}
                placeholder="Paste your complete resume text including education, experience bullets, and skills..."
                className="w-full p-3 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] placeholder-[#869585] focus:border-[#4be277]"
              />
            </div>
          )}

          {resumeMode === 'saved' && (
            <div className="space-y-3">
              <label className="block label-mono text-[10px] text-[#869585]">
                SELECT PREVIOUSLY UPLOADED RESUME
              </label>
              <select
                value={selectedSavedResumeId}
                onChange={(e) => setSelectedSavedResumeId(e.target.value)}
                className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
              >
                <option value="">Select a saved resume...</option>
                {savedResumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title} ({r.file_type || 'text'})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Right Column: Job Description Input */}
        <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-4">
          <div className="flex items-center justify-between">
            <span className="label-mono text-[10px] text-[#4be277] font-bold">2. JOB DESCRIPTION & TARGET</span>
            <span className="text-[10px] text-[#869585] font-mono">WEIGHTED EXTRACTION</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block label-mono text-[10px] text-[#869585] mb-1">COMPANY</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="Google / Stripe"
                className="w-full px-3 py-1.5 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
              />
            </div>
            <div>
              <label className="block label-mono text-[10px] text-[#869585] mb-1">TARGET ROLE</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Software Engineer"
                className="w-full px-3 py-1.5 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
              />
            </div>
          </div>

          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">
              JOB DESCRIPTION / REQUIREMENTS TEXT
            </label>
            <textarea
              rows={6}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste requirements, tech stack, and responsibilities..."
              className="w-full p-3 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] placeholder-[#869585] focus:border-[#4be277]"
            />
          </div>

          <button
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
            className="w-full py-2.5 px-4 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 shadow-sm"
          >
            {analyzeMutation.isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-[#003915] border-t-transparent rounded-full animate-spin" />
                <span>Extracting Skills & Computing ATS Cosine...</span>
              </>
            ) : (
              <>
                <Icon name="search_check" className="text-base" />
                <span>Run ATS Alignment Analysis</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {activeAnalysis && (
        <div className="space-y-6 pt-4 border-t border-[#1f1f1f]">
          {/* Top Score Banner: Overall Circular Gauge + Subscore Bars */}
          <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
            {/* Circular Overall Score */}
            <div className="flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-[#2a2a2a] pb-4 md:pb-0 pr-0 md:pr-6">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-32 h-32 -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#2a2a2a" strokeWidth="8" />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke="#4be277"
                    strokeWidth="8"
                    strokeDasharray={263.89}
                    strokeDashoffset={263.89 - (activeAnalysis.overall / 100) * 263.89}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute text-center flex flex-col items-center">
                  <span className="text-3xl font-black text-[#e2e2e2]">
                    {Math.round(activeAnalysis.overall)}
                  </span>
                  <span className="text-[10px] text-[#869585] font-mono">/ 100</span>
                </div>
              </div>
              <div className="mt-2 text-center">
                <div className="label-mono text-xs text-[#4be277] font-bold">OVERALL ATS MATCH</div>
                {deltaVsPrevious !== null && (
                  <div
                    className={`text-[11px] font-mono mt-0.5 ${
                      deltaVsPrevious >= 0 ? 'text-[#4be277]' : 'text-[#ffb4ab]'
                    }`}
                  >
                    {deltaVsPrevious >= 0 ? '+' : ''}
                    {deltaVsPrevious.toFixed(1)}% vs previous run
                  </div>
                )}
                {activeAnalysis.degraded && (
                  <span className="inline-block mt-1 px-2 py-0.5 rounded-[2px] bg-[#facc15]/10 text-[#facc15] text-[10px] font-mono">
                    Degraded Mode (TF-IDF Renormalised)
                  </span>
                )}
              </div>
            </div>

            {/* Sub-Score Bars (2 cols) */}
            <div className="md:col-span-2 space-y-3.5">
              <div className="flex items-center justify-between">
                <span className="label-mono text-xs text-[#869585]">SUB-SCORE METRIC BREAKDOWN</span>
                <span className="text-[11px] font-mono text-[#869585]">WEIGHTED FORMULA</span>
              </div>

              {/* Keyword Score */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-[#e2e2e2] font-medium">Keyword Coverage (40%)</span>
                  <span className="font-mono text-[#4be277]">{Math.round(activeAnalysis.keyword_score)}%</span>
                </div>
                <div className="w-full h-2 bg-[#131313] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#4be277] transition-all"
                    style={{ width: `${Math.round(activeAnalysis.keyword_score)}%` }}
                  />
                </div>
              </div>

              {/* Semantic Score */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-[#e2e2e2] font-medium">
                    Semantic Requirement Alignment (25%){activeAnalysis.semantic_score === null && ' [Fallback]'}
                  </span>
                  <span className="font-mono text-[#4be277]">
                    {activeAnalysis.semantic_score !== null
                      ? `${Math.round(activeAnalysis.semantic_score)}%`
                      : '—'}
                  </span>
                </div>
                <div className="w-full h-2 bg-[#131313] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#4be277] transition-all"
                    style={{
                      width: `${activeAnalysis.semantic_score ? Math.round(activeAnalysis.semantic_score) : 0}%`,
                    }}
                  />
                </div>
              </div>

              {/* TF-IDF Score */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-[#e2e2e2] font-medium">TF-IDF Vector Cosine (15%)</span>
                  <span className="font-mono text-[#4be277]">{Math.round(activeAnalysis.tfidf_score)}%</span>
                </div>
                <div className="w-full h-2 bg-[#131313] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#4be277] transition-all"
                    style={{ width: `${Math.round(activeAnalysis.tfidf_score)}%` }}
                  />
                </div>
              </div>

              {/* Content Quality Score */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-[#e2e2e2] font-medium">Content Quality & Metrics (20%)</span>
                  <span className="font-mono text-[#4be277]">{Math.round(activeAnalysis.quality_score)}%</span>
                </div>
                <div className="w-full h-2 bg-[#131313] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#4be277] transition-all"
                    style={{ width: `${Math.round(activeAnalysis.quality_score)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Matched Skills vs Missing Skills */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Matched Skills with Evidence Hover */}
            <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon name="check_circle" className="text-sm text-[#4be277]" />
                  <span className="label-mono text-xs text-[#e2e2e2] font-bold">
                    MATCHED SKILLS ({activeAnalysis.matched?.length || 0})
                  </span>
                </div>
                <span className="text-[10px] text-[#869585]">Hover skill for evidence</span>
              </div>

              <div className="flex flex-wrap gap-2">
                {activeAnalysis.matched && activeAnalysis.matched.length > 0 ? (
                  activeAnalysis.matched.map((skill, idx) => (
                    <div
                      key={idx}
                      onMouseEnter={() => setHoveredMatchedSkill(skill)}
                      onMouseLeave={() => setHoveredMatchedSkill(null)}
                      className="group relative cursor-pointer px-2.5 py-1 rounded-[2px] bg-[#4be277]/10 border border-[#4be277]/40 text-xs font-medium text-[#4be277] hover:bg-[#4be277]/20 transition-colors"
                    >
                      <span>{skill.name}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-[#869585]">No taxonomy skills matched.</div>
                )}
              </div>

              {/* Active Hover Evidence Box */}
              {hoveredMatchedSkill && (
                <div className="p-3 rounded-[4px] bg-[#131313] border border-[#4be277]/50 text-xs animate-in fade-in duration-100">
                  <div className="label-mono text-[10px] text-[#4be277] mb-1">
                    RESUME EVIDENCE SNIPPET ({hoveredMatchedSkill.name})
                  </div>
                  <p className="text-[#bccbb9] italic font-mono text-[11px] leading-relaxed">
                    &ldquo;{hoveredMatchedSkill.evidence}&rdquo;
                  </p>
                </div>
              )}
            </div>

            {/* Missing Skills Ranked by Importance */}
            <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon name="error" className="text-sm text-[#ffb4ab]" />
                  <span className="label-mono text-xs text-[#e2e2e2] font-bold">
                    MISSING SKILLS ({activeAnalysis.missing?.length || 0})
                  </span>
                </div>
                <span className="text-[10px] text-[#869585]">Ranked by JD Weight</span>
              </div>

              <div className="flex flex-wrap gap-2">
                {activeAnalysis.missing && activeAnalysis.missing.length > 0 ? (
                  activeAnalysis.missing.map((skill, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-[2px] bg-[#ffb4ab]/10 border border-[#ffb4ab]/30 text-xs font-medium text-[#ffb4ab]"
                    >
                      <span>{skill.name}</span>
                      <span className="text-[10px] font-mono opacity-70">
                        {skill.weight >= 1.5 ? '★ req' : skill.weight < 1 ? 'pref' : ''}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-[#4be277]">Outstanding! All job skills matched.</div>
                )}
              </div>
            </div>
          </div>

          {/* Actionable Grounded Suggestion Cards */}
          {activeAnalysis.suggestions && activeAnalysis.suggestions.length > 0 && (
            <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon name="auto_fix_high" className="text-base text-[#4be277]" />
                  <h3 className="text-base font-bold text-[#e2e2e2]">
                    Grounded Resume Bullet Rewrite Suggestions
                  </h3>
                </div>
                <span className="label-mono text-xs text-[#869585]">NO HALLUCINATED EXPERIENCE</span>
              </div>

              <div className="space-y-3">
                {activeAnalysis.suggestions.map((sug, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] space-y-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[#ffb4ab] flex items-center gap-1">
                        <Icon name="priority_high" className="text-xs" />
                        {sug.issue}
                      </span>
                      <button
                        onClick={() => handleCopyRewrite(sug.rewrite, idx)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-[2px] bg-[#131313] border border-[#3d4a3d] hover:border-[#4be277] text-xs text-[#bccbb9] hover:text-[#4be277] transition-all"
                      >
                        <Icon name={copiedIndex === idx ? 'check' : 'content_copy'} className="text-xs" />
                        <span>{copiedIndex === idx ? 'Copied' : 'Copy Rewrite'}</span>
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-2.5 rounded-[2px] bg-[#131313] border border-[#2a2a2a]">
                        <div className="label-mono text-[10px] text-[#869585] mb-1">ORIGINAL BULLET</div>
                        <div className="text-[#bccbb9] line-through opacity-75">{sug.target_bullet}</div>
                      </div>
                      <div className="p-2.5 rounded-[2px] bg-[#131313] border border-[#4be277]/40">
                        <div className="label-mono text-[10px] text-[#4be277] mb-1">PROPOSED REWRITE</div>
                        <div className="text-[#e2e2e2] font-medium">{sug.rewrite}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Historical Trend */}
          {history.length > 1 && (
            <div className="p-5 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a]">
              <div className="flex items-center justify-between mb-3">
                <span className="label-mono text-xs text-[#869585]">ATS MATCH TRAJECTORY ACROSS ITERATIONS</span>
                <span className="text-xs font-mono text-[#4be277]">{history.length} Runs Logged</span>
              </div>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={history
                      .slice()
                      .reverse()
                      .map((h, i) => ({
                        run: `#${i + 1}`,
                        overall: Math.round(h.overall),
                      }))}
                  >
                    <XAxis dataKey="run" tickLine={false} tick={{ fill: '#869585', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f1f1f', borderColor: '#3d4a3d', borderRadius: 4, fontSize: 11 }}
                    />
                    <Line type="monotone" dataKey="overall" stroke="#4be277" strokeWidth={2} dot={{ fill: '#4be277', r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ResumeATSPage;
