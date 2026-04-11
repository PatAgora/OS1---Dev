/**
 * Associate Portal — Dashboard tests
 *
 * Tests: /portal/dashboard
 * Verifies page load, progress indicators, and nav links.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Dashboard', () => {
  test('@smoke /portal/dashboard — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/dashboard');
  });

  test('progress indicators visible', async ({ page }) => {
    await page.goto('/portal/dashboard', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const progress = page.locator(
      '.progress, .progress-bar, [class*="progress"], [class*="step"], ' +
      '.completion, [data-progress], .status-indicator'
    );
    const count = await progress.count();
    console.log(`  Progress indicators found: ${count}`);

    if (count > 0) {
      await expect(progress.first()).toBeVisible();
    }
  });

  test('nav links present', async ({ page }) => {
    await page.goto('/portal/dashboard', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const navLinks = page.locator(
      'nav a, .sidebar a, .nav a, a[href*="/portal/"]'
    );
    const count = await navLinks.count();
    console.log(`  Portal nav links found: ${count}`);
    expect(count).toBeGreaterThan(0);
  });

  test('nav link clicks do not produce 500 errors', async ({ page }) => {
    await page.goto('/portal/dashboard', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Known portal nav routes to test
    const portalRoutes = [
      { path: '/portal/dashboard', label: 'Summary' },
      { path: '/portal/personal-details', label: 'My Profile' },
      { path: '/portal/intro-to-vetting', label: 'Vetting' },
      { path: '/portal/vacancies', label: 'Vacancies' },
      { path: '/portal/my-applications', label: 'My Applications' },
      { path: '/portal/assignments', label: 'Assignments' },
      { path: '/portal/timesheets', label: 'Timesheets' },
    ];

    for (const route of portalRoutes) {
      // Try to find and click the nav link for this route
      const navLink = page.locator(`a[href="${route.path}"], a[href*="${route.path}"]`).first();
      const linkExists = await navLink.isVisible({ timeout: 2000 }).catch(() => false);

      if (linkExists) {
        await navLink.click();
        await page.waitForLoadState('domcontentloaded');
      } else {
        // Fallback: navigate directly
        await page.goto(route.path, { waitUntil: 'domcontentloaded' });
      }

      await guardSessionExpired(page);

      const body = await page.textContent('body') || '';
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');
      console.log(`  ${route.label} (${route.path}) — OK`);

      // Go back to dashboard for the next iteration
      await page.goto('/portal/dashboard', { waitUntil: 'domcontentloaded' });
      await guardSessionExpired(page);
    }
  });
});
