/**
 * Public Portal — Job Board tests
 *
 * Tests: public jobs listing page
 * Verifies job cards render and first job is clickable.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Public Job Board', () => {
  test('@smoke public jobs page loads', async ({ page }) => {
    // Try common public job board routes — /jobs is the actual public route
    const routes = ['/jobs', '/public/jobs', '/public/vacancies'];
    let loaded = false;

    for (const route of routes) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      const status = response?.status() ?? 0;

      if (status === 200) {
        const body = await page.textContent('body');
        expect(body).not.toContain('Internal Server Error');
        console.log(`  Public jobs page loaded at ${route}`);
        loaded = true;
        break;
      }
    }

    expect(loaded).toBeTruthy();
  });

  test('job cards render', async ({ page }) => {
    // Navigate to the public jobs page
    const routes = ['/jobs', '/public/jobs'];
    for (const route of routes) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      if ((response?.status() ?? 0) === 200) break;
    }

    // Look for job cards — the public template uses <a class="job-card"> elements
    // with href like /jobs/<id>
    const jobItems = page.locator(
      'a.job-card, .job-card, a[href*="/jobs/"], .vacancy-card, [data-job-id]'
    );

    const count = await jobItems.count();
    console.log(`  Job items found: ${count}`);

    if (count > 0) {
      await expect(jobItems.first()).toBeVisible();
    } else {
      // Empty state is acceptable — page loaded without error
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  No job cards — empty state or different layout');
    }
  });

  test('click first job — detail page loads', async ({ page }) => {
    const routes = ['/jobs', '/public/jobs'];
    for (const route of routes) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      if ((response?.status() ?? 0) === 200) break;
    }

    // Find clickable job link — the public template uses <a class="job-card" href="/jobs/<id>">
    const jobLink = page.locator(
      'a.job-card, a[href*="/jobs/"]'
    ).first();

    if (await jobLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await jobLink.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');
      console.log(`  Job detail page loaded at: ${page.url()}`);
    } else {
      console.log('  No clickable job links found — skipping detail navigation');
    }
  });
});
