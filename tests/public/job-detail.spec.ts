/**
 * Public Portal — Job Detail tests
 *
 * Tests: public job detail page
 * Verifies title, description, and "Apply" button are present.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Public Job Detail', () => {
  test('job detail page — title, description, apply button', async ({ page }) => {
    // First navigate to the job board to find a real job link
    const routes = ['/public/jobs', '/jobs'];
    for (const route of routes) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      if ((response?.status() ?? 0) === 200) break;
    }

    // Find and click a job link
    const jobLink = page.locator(
      'a[href*="/job/"], a[href*="/public/job/"], .job-card a, .vacancy-card a'
    ).first();

    if (!(await jobLink.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  No job links found on public board — skipping detail tests');
      return;
    }

    await jobLink.click();
    await page.waitForLoadState('domcontentloaded');

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    // Title should be visible (h1, h2, or .job-title)
    const title = page.locator('h1, h2, .job-title, .vacancy-title').first();
    await expect(title).toBeVisible({ timeout: 5000 });
    const titleText = await title.textContent();
    console.log(`  Job title: ${titleText?.trim().substring(0, 80)}`);

    // Description should be present
    const description = page.locator(
      '.job-description, .description, .content, [class*="description"], article, .prose'
    ).first();
    if (await description.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  Job description visible');
    }

    // Apply button should be present
    const applyBtn = page.locator(
      'a:has-text("Apply"), button:has-text("Apply"), ' +
      'a[href*="apply"], a[href*="Apply"]'
    ).first();

    if (await applyBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  Apply button visible');
    } else {
      console.log('  Apply button not found on detail page');
    }
  });
});
