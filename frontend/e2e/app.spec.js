import { test, expect } from '@playwright/test';

// There is no shared demo account (production has none). Test (a) signs up one brand-new user
// per run, and every later test logs in as that user through the real login form.
// Signups are limited to 5 per hour per IP, so keep it to one registration per run.
test.describe('Placement Copilot End-to-End Test Suite', () => {
  test.describe.configure({ mode: 'serial' });

  let creds = null;

  const loginAsTestUser = async (page) => {
    expect(creds, 'test (a) must create the e2e user first').not.toBeNull();
    await page.goto('/login');
    await page.locator('input[type="email"]').fill(creds.email);
    await page.locator('input[type="password"]').fill(creds.password);
    await page.locator('button[type="submit"]:has-text("Sign In")').click();
    await expect(page).toHaveURL('/', { timeout: 15000 });
    await expect(page.locator('#logout-button')).toBeVisible({ timeout: 10000 });
  };

  // Test (a): Sign up as a new user and see the onboarding checklist
  test('(a) sign up as a new user and see the onboarding checklist', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/signup');
    await page.evaluate(() => localStorage.clear());
    await page.goto('/signup');

    const email = `e2e_${Date.now()}@university.edu`;
    const password = 'ValidPassword123!';
    await page.locator('input[placeholder="Full Name"]').fill('New Candidate');
    await page.locator('input[placeholder="name@university.edu"]').fill(email);
    await page.locator('input[placeholder="Min. 10 characters"]').fill(password);
    await page.locator('button[type="submit"]:has-text("Create Account")').click();

    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/', { timeout: 15000 });
    creds = { email, password };
    await expect(page.locator('text=Placement Readiness Onboarding')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Upload your PDF or DOCX resume')).toBeVisible({ timeout: 10000 });
  });

  // Test (b): Visit all primary routes without console errors, failed network requests, and verify specific content
  test('(b) visit /, /dsa, /resume, /interview, and /profile with clean logs and visible content', async ({ page }) => {
    const consoleErrors = [];
    const failedCalls = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('response', (res) => {
      if (res.status() >= 400 && !res.url().includes('/404')) {
        failedCalls.push(`${res.status()} ${res.url()}`);
      }
    });

    await loginAsTestUser(page);

    // 1. Dashboard (a brand-new user may see the onboarding view instead of the overview)
    await expect(
      page.locator('text=CANDIDATE INTELLIGENCE OVERVIEW').or(page.locator('text=Placement Readiness Onboarding')).first()
    ).toBeVisible({ timeout: 10000 });

    // 2. DSA Tracker
    await page.goto('/dsa');
    await expect(page.locator('text=Algorithmic Problem Tracker')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Log New Problem')).toBeVisible({ timeout: 10000 });

    // 3. Resume ATS
    await page.goto('/resume');
    await expect(page.locator('text=Deterministic ATS Analyzer')).toBeVisible({ timeout: 10000 });

    // 4. Mock Interview
    await page.goto('/interview');
    await expect(page.locator('text=Adaptive Mock Interview')).toBeVisible({ timeout: 10000 });

    // 5. Profile
    await page.goto('/profile');
    await expect(page.locator('text=Candidate Profile & Settings')).toBeVisible({ timeout: 10000 });

    expect(consoleErrors).toEqual([]);
    expect(failedCalls).toEqual([]);
  });

  // Test (c): Log a DSA problem and see it in the table and mastery bars
  test('(c) log a DSA problem and see it in the table and in the mastery bars', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto('/dsa');
    await expect(page.locator('text=Algorithmic Problem Tracker')).toBeVisible({ timeout: 10000 });

    // Open drawer
    await page.locator('button:has-text("Log New Problem")').click();
    await expect(page.locator('text=Log New Practice Attempt')).toBeVisible({ timeout: 10000 });

    // Switch to custom title
    await page.locator('button:has-text("Custom Title")').click();
    const problemTitle = `Two Pointers Interval Merging ${Date.now()}`;
    await page.locator('input[placeholder*="Minimum Window Substring"]').fill(problemTitle);

    // Select topic
    const topicSelect = page.locator('form select').first();
    await topicSelect.selectOption({ index: 1 });

    // Submit attempt
    await page.locator('button[type="submit"]:has-text("Log Attempt")').click();

    // Verify it appears in attempts table
    await expect(page.locator(`text=${problemTitle}`)).toBeVisible({ timeout: 10000 });
    // Verify mastery matrix section is visible
    await expect(page.locator('text=TOPIC MASTERY & WEAK SPOTS')).toBeVisible({ timeout: 10000 });
  });

  // Test (d): Upload sample resume plus job description and see a score
  test('(d) upload sample resume plus job description and see an ATS score', async ({ page }) => {
    test.setTimeout(90000);
    await loginAsTestUser(page);

    await page.goto('/resume');
    await expect(page.locator('text=Deterministic ATS Analyzer')).toBeVisible({ timeout: 10000 });

    // Switch to paste mode
    await page.locator('button:has-text("Paste Text")').click();
    await page.locator('textarea[placeholder*="Paste your complete resume text"]').fill(
      'Full Stack Developer with strong expertise in Python, FastAPI, PostgreSQL, Docker, Git, REST APIs, and algorithms.'
    );

    // Provide target job description
    await page.locator('textarea[placeholder*="Paste requirements, tech stack"]').fill(
      'Full Stack Developer with strong expertise in Python, FastAPI, PostgreSQL, Docker, Git, REST APIs, and algorithms.'
    );

    // Click Analyze
    await page.locator('button:has-text("Run ATS Alignment Analysis")').click();

    // Verify score card is displayed (the LLM step can take up to its time budget before falling back)
    await expect(page.locator('text=OVERALL ATS MATCH')).toBeVisible({ timeout: 45000 });
    await expect(page.locator('text=Keyword Coverage')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=TF-IDF Vector Cosine')).toBeVisible({ timeout: 10000 });
  });

  // Test (e): Finish a 3-question mock interview and see the report
  test('(e) finish a 3-question mock interview and see the report', async ({ page }) => {
    test.setTimeout(240000);
    await loginAsTestUser(page);

    await page.goto('/interview');
    await expect(page.locator('button:has-text("Start Interview Session")')).toBeVisible({ timeout: 10000 });

    // Start interview
    await page.locator('button:has-text("Start Interview Session")').click();
    await expect(page.locator('text=INTERVIEW QUESTION #1')).toBeVisible({ timeout: 30000 });

    // Question 1
    await page.locator('textarea[placeholder*="State your approach"]').fill(
      'We use an array of size 26 or a hash map to count character frequencies in O(N) time and O(1) auxiliary space.'
    );
    await page.locator('button:has-text("Submit Answer")').click();
    await expect(page.getByText('Answer Evaluated', { exact: true })).toBeVisible({ timeout: 40000 });
    await page.locator('button:has-text("Next Question")').click();

    // Question 2
    await expect(page.locator('text=INTERVIEW QUESTION #2')).toBeVisible({ timeout: 30000 });
    await page.locator('textarea[placeholder*="State your approach"]').fill(
      'We maintain two pointers left and right, expanding the window until all criteria are satisfied.'
    );
    await page.locator('button:has-text("Submit Answer")').click();
    await expect(page.getByText('Answer Evaluated', { exact: true })).toBeVisible({ timeout: 40000 });
    await page.locator('button:has-text("Next Question")').click();

    // Question 3
    await expect(page.locator('text=INTERVIEW QUESTION #3')).toBeVisible({ timeout: 30000 });
    await page.locator('textarea[placeholder*="State your approach"]').fill(
      'We initialize dynamic programming table dp[i] representing optimal solution for prefix of length i.'
    );
    await page.locator('button:has-text("Submit Answer")').click();
    await expect(page.getByText('Answer Evaluated', { exact: true })).toBeVisible({ timeout: 40000 });

    // Finish session
    await page.locator('button:has-text("Finish Early")').click();

    // Assert comprehensive performance report is displayed
    await expect(page.locator('text=INTERVIEW PERFORMANCE AUDIT')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=DIFFICULTY-WEIGHTED SCORE')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=GROUNDED ACTION ITEMS')).toBeVisible({ timeout: 10000 });
  });

  // Test (f): Repeated form logins are reliable (5 times in a row)
  test('(f) signing in through the form works 5 times in a row', async ({ page }) => {
    test.setTimeout(120000);
    expect(creds, 'test (a) must create the e2e user first').not.toBeNull();
    for (let i = 1; i <= 5; i++) {
      await page.context().clearCookies();
      await page.goto('/login');
      await page.evaluate(() => localStorage.clear());
      await loginAsTestUser(page);
    }
  });

  // Test (g): Log out and in
  test('(g) log out and in', async ({ page }) => {
    await loginAsTestUser(page);

    // Log out via sidebar button
    const logoutBtn = page.locator('#logout-button');
    await expect(logoutBtn).toBeVisible({ timeout: 10000 });
    await logoutBtn.click();

    // Must be on /login
    await expect(page).toHaveURL('/login', { timeout: 10000 });

    // Log back in with the same credentials
    await loginAsTestUser(page);
  });

  // Test (h): Page reload keeps the session
  test('(h) a page reload keeps the session', async ({ page }) => {
    await loginAsTestUser(page);

    // Reload browser page
    await page.reload();

    // Session must persist
    await expect(page).toHaveURL('/', { timeout: 10000 });
    await expect(page.locator('#logout-button')).toBeVisible({ timeout: 10000 });
  });
});
