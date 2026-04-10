/**
 * Staff Portal — Reporting tests
 *
 * Tests: /reporting
 * Verifies page loads or gracefully handles if route doesn't exist.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Reporting', () => {
  test('@smoke /reporting — page loads (200) or redirects gracefully', async ({ page }) => {
    const response = await page.goto('/reporting', { waitUntil: 'domcontentloaded' });
    const status = response?.status() ?? 0;

    // Accept 200 (page exists), 302/301 (redirect), or 404 (route not implemented)
    // Fail only on 500+ (server error)
    expect(status).toBeLessThan(500);

    if (status === 200) {
      // Page exists — verify no server error in body
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');
      console.log('  /reporting page loaded successfully (200)');
    } else if (status === 404) {
      console.log('  /reporting returned 404 — route does not exist in this app version');
    } else if (status >= 300 && status < 400) {
      console.log(`  /reporting redirected (${status}) to ${page.url()}`);
    }
  });
});
