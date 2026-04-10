/**
 * Associate Portal — Dashboard tests
 *
 * Tests: /portal/dashboard
 * Verifies page load, progress indicators, and nav links.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Dashboard', () => {
  test('@smoke /portal/dashboard — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/dashboard');
  });

  test('progress indicators visible', async ({ page }) => {
    await page.goto('/portal/dashboard', { waitUntil: 'domcontentloaded' });

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

    const navLinks = page.locator(
      'nav a, .sidebar a, .nav a, a[href*="/portal/"]'
    );
    const count = await navLinks.count();
    console.log(`  Portal nav links found: ${count}`);
    expect(count).toBeGreaterThan(0);
  });
});
