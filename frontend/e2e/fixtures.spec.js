import { test, expect } from '@playwright/test';

test.describe('Frontend Live Fixtures Contract Rendering Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Inject mock session
    await page.addInitScript(() => {
      localStorage.setItem('has_session', 'true');
    });

    // Intercept auth refresh
    await page.route('**/api/v1/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: 'mock-valid-jwt-token', token_type: 'bearer' }),
      });
    });

    // Intercept user profile
    await page.route('**/api/v1/users/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'mock-user-uuid',
          email: 'demo@placementcopilot.com',
          name: 'Demo Candidate',
          college: 'University of Engineering',
          grad_year: 2026,
          target_role: 'Software Engineer',
          target_companies: ['Google', 'Stripe'],
          created_at: '2026-10-22T00:00:00Z',
        }),
      });
    });

    // Intercept DSA endpoints with real live API envelope fixtures
    await page.route('**/api/v1/dsa/topics', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            { id: 'topic-1', name: 'Arrays & Two Pointers', category: 'Core', slug: 'arrays', target_points: 100 },
            { id: 'topic-2', name: 'Binary Trees & Graphs', category: 'Non-linear', slug: 'graphs', target_points: 120 },
          ],
          total: 2,
          limit: 20,
          offset: 0,
        }),
      });
    });

    await page.route('**/api/v1/dsa/attempts', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'attempt-1',
              problem_id: null,
              custom_title: '3Sum Problem',
              topic_id: 'topic-1',
              difficulty: 'medium',
              status: 'solved',
              confidence: 4,
              time_spent_min: 25,
              notes: 'Two-pointer sorted search',
              attempted_at: '2026-10-22T10:00:00Z',
              problem: null,
              topic: { id: 'topic-1', name: 'Arrays & Two Pointers' },
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    await page.route('**/api/v1/dsa/mastery', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              topic_id: 'topic-1',
              topic_name: 'Arrays & Two Pointers',
              category: 'Core',
              mastery_score: 84.5,
              problems_solved: 3,
              total_attempts: 4,
              decay_factor: 0.98,
              priority_level: 'medium',
              last_attempted_at: '2026-10-22T10:00:00Z',
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    await page.route('**/api/v1/dsa/recommendations', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, limit: 5, offset: 0 }),
      });
    });

    await page.route('**/api/v1/dsa/reviews/due', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, limit: 10, offset: 0 }),
      });
    });

    await page.route('**/api/v1/dsa/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_attempts: 4,
          total_solved: 3,
          solved_by_difficulty: { easy: 1, medium: 2, hard: 0 },
          topics_covered: 1,
          current_streak: 2,
          best_streak: 4,
          solved_7d: 3,
          solved_30d: 3,
        }),
      });
    });

    // Intercept Resume & ATS endpoints
    await page.route('**/api/v1/resumes*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'resume-1',
              title: 'Software Engineer Resume',
              file_path: null,
              created_at: '2026-10-20T00:00:00Z',
              skills: ['Python', 'FastAPI', 'PostgreSQL'],
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    await page.route('**/api/v1/ats/analyses*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'ats-1',
              resume_id: 'resume-1',
              company: 'Target Tech',
              role: 'Software Engineer',
              overall: 82.5,
              overall_match_score: 82.5,
              keyword_score: 85.0,
              tfidf_score: 80.0,
              semantic_score: 82.0,
              matched_skills: ['Python', 'FastAPI', 'PostgreSQL'],
              missing_skills: ['AWS'],
              created_at: '2026-10-21T00:00:00Z',
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    // Intercept Mock Interview history
    await page.route('**/api/v1/interviews*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'interview-1',
              track: 'dsa_concepts',
              company: 'Google',
              role: 'Software Engineer',
              status: 'completed',
              questions_completed: 3,
              ability: 3.15,
              final_theta: 3.15,
              final_score: 84.0,
              overall_score: 84.0,
              started_at: '2026-10-21T00:00:00Z',
              created_at: '2026-10-21T00:00:00Z',
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    // Intercept Dashboard summary
    await page.route('**/api/v1/dashboard/summary*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user_name: 'Demo Candidate',
          composite: 81.4,
          confidence: 0.88,
          has_enough_data: true,
          delta_7d: 4.2,
          components: { dsa: 84.5, ats: 82.5, mock: 80.0, consistency: 75.0 },
          weights: { dsa: 0.35, ats: 0.25, mock: 0.3, consistency: 0.1 },
          levers: [
            {
              action_title: 'Solve 2 Dynamic Programming Problems',
              category: 'dsa',
              expected_lift: 3.5,
              reason: 'Targets weak retention area with high syllabus weight',
            },
          ],
          ats_sparkline: [{ date: '2026-10-20', score: 80 }, { date: '2026-10-21', score: 82.5 }],
          dsa_sparkline: [{ date: '2026-10-20', score: 80 }, { date: '2026-10-22', score: 84.5 }],
          mock_sparkline: [{ date: '2026-10-21', score: 80 }],
          ats_average: 82.5,
          dsa_topics_covered: 1,
          current_streak: 2,
          mock_average: 8.0,
          daily_focus_task: 'Complete scheduled spaced repetition reviews',
          recent_activity: [
            {
              id: 'act-1',
              type: 'dsa',
              title: 'Solved 3Sum Problem',
              subtitle: 'Arrays & Two Pointers (medium)',
              score: 84.5,
              timestamp: '2026-10-22T10:00:00Z',
            },
          ],
          onboarding_checklist: {
            has_uploaded_resume: true,
            has_logged_3_problems: true,
            has_taken_mock: true,
          },
        }),
      });
    });
  });

  test('DSA Tracker page renders gracefully without "attempts.filter is not a function"', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));

    await page.goto('/dsa');
    await expect(page.locator('text=Algorithmic Problem Tracker')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=3Sum Problem')).toBeVisible({ timeout: 10000 });

    expect(errors.filter((e) => e.includes('filter is not a function'))).toEqual([]);
    expect(errors).toEqual([]);
  });

  test('Resume ATS page renders saved resumes and analyses from paginated fixtures', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));

    await page.goto('/resume');
    await expect(page.locator('text=Deterministic ATS Analyzer')).toBeVisible({ timeout: 10000 });
    const savedBtn = page.locator('button:has-text("Saved")');
    await expect(savedBtn).toBeVisible({ timeout: 10000 });
    await savedBtn.click();
    await expect(page.locator('select')).toBeVisible({ timeout: 10000 });

    expect(errors).toEqual([]);
  });

  test('Mock Interview page renders session history from paginated fixtures', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));

    await page.goto('/interview');
    await expect(page.locator('text=Adaptive Mock Interview')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=PAST INTERVIEW SESSIONS')).toBeVisible({ timeout: 10000 });

    expect(errors).toEqual([]);
  });

  test('Dashboard page renders metrics and sparklines from summary fixture', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));

    await page.goto('/');
    await expect(page.locator('text=Welcome back, Demo')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Placement Readiness Score')).toBeVisible({ timeout: 10000 });

    expect(errors).toEqual([]);
  });
});
