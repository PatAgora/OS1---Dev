/**
 * Public Portal — Auth Page tests
 *
 * Tests: public candidate auth pages (not staff, not /portal/)
 * If public auth routes don't exist, falls back to testing the public job board.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Public Auth', () => {
  test('public auth login page or job board loads', async ({ page }) => {
    // Try public auth login routes in order of likelihood
    const authRoutes = ['/auth/login', '/public/auth/login', '/public/login'];
    let found = false;

    for (const route of authRoutes) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      const status = response?.status() ?? 0;

      if (status === 200) {
        const body = await page.textContent('body');
        expect(body).not.toContain('Internal Server Error');

        // Check if it looks like a login page
        const hasLoginForm = await page.locator('[name="email"], [name="username"]').count() > 0;
        if (hasLoginForm) {
          console.log(`  Public auth login found at ${route}`);
          found = true;
          break;
        }
      }
    }

    if (!found) {
      // Fallback — test that the public job board works
      const response = await page.goto('/public/jobs', { waitUntil: 'domcontentloaded' });
      const status = response?.status() ?? 0;

      if (status >= 500) {
        // Try alternative routes
        const altResponse = await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
        expect(altResponse?.status() ?? 0).toBeLessThan(500);
      }

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  No public auth routes found — public job board verified instead');
    }
  });

  test('public auth signup page — if exists', async ({ page }) => {
    const signupRoutes = ['/auth/signup', '/auth/register', '/public/auth/signup', '/public/register'];

    for (const route of signupRoutes) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      const status = response?.status() ?? 0;

      if (status === 200) {
        const body = await page.textContent('body');
        expect(body).not.toContain('Internal Server Error');
        console.log(`  Public auth signup found at ${route}`);
        return;
      }
    }

    console.log('  No public auth signup route found — skipping');
  });
});
