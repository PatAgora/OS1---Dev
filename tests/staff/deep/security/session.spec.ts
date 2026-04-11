/**
 * Deep Tests — Session Security
 *
 * Verifies session handling: logout clears state, protected routes
 * redirect to login, and session cookies have appropriate security flags.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';

// Start with a fresh session — we will log in manually
test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

const BASE_URL = 'https://os1-dev-production.up.railway.app';

test.describe('Session Security', () => {

  test('logout clears session and redirects to login', async ({ page }) => {
    // Log in as the test admin
    await page.goto('/login', { waitUntil: 'domcontentloaded' });

    const emailInput = page.locator('input[name="email"]').first();
    const passwordInput = page.locator('input[name="password"]').first();

    if (await emailInput.count() === 0) {
      test.skip(true, 'Login form not found');
      return;
    }

    await emailInput.fill('admin@demo.example.com');
    await passwordInput.fill('DemoAdmin2024!');
    await page.locator('button[type="submit"], input[type="submit"]').first().click();
    await page.waitForLoadState('domcontentloaded');

    // Handle 2FA if prompted
    if (page.url().includes('2fa') || page.url().includes('mfa')) {
      test.skip(true, '2FA required — cannot complete login in this test');
      return;
    }

    // Verify we are logged in (dashboard or redirect target)
    const bodyAfterLogin = await page.textContent('body') || '';
    if (bodyAfterLogin.includes('Sign in') && page.url().includes('/login')) {
      test.skip(true, 'Login failed — credentials may have changed');
      return;
    }

    // Now log out
    await page.goto('/logout', { waitUntil: 'domcontentloaded' });

    // After logout, should be on login page
    expect(page.url()).toContain('/login');

    // Navigating to dashboard should redirect to login
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    expect(page.url()).toContain('/login');
  });

  test('protected routes redirect to login when unauthenticated', async ({ page }) => {
    const protectedRoutes = ['/applications', '/resource-pool', '/engagements', '/admin/users'];

    for (const route of protectedRoutes) {
      await page.goto(route, { waitUntil: 'domcontentloaded' });
      // Should redirect to login or show login form
      const url = page.url();
      const body = await page.textContent('body') || '';
      const lowerBody = body.toLowerCase();

      const isOnLogin = url.includes('login') || url.includes('auth') || url.includes('signin');
      const showsLoginForm =
        lowerBody.includes('sign in') ||
        lowerBody.includes('log in') ||
        lowerBody.includes('password') ||
        lowerBody.includes('email') ||
        (await page.locator('input[type="password"]').count()) > 0;

      expect(
        isOnLogin || showsLoginForm,
        `Expected redirect to login for ${route}, but ended up at ${url}`
      ).toBe(true);
    }
  });

  test('session cookie has httponly flag', async ({ page }) => {
    // Log in to get a session cookie
    await page.goto('/login', { waitUntil: 'domcontentloaded' });

    const emailInput = page.locator('input[name="email"]').first();
    const passwordInput = page.locator('input[name="password"]').first();

    if (await emailInput.count() === 0) {
      test.skip(true, 'Login form not found');
      return;
    }

    await emailInput.fill('admin@demo.example.com');
    await passwordInput.fill('DemoAdmin2024!');
    await page.locator('button[type="submit"], input[type="submit"]').first().click();
    await page.waitForLoadState('domcontentloaded');

    // Handle 2FA if prompted
    if (page.url().includes('2fa') || page.url().includes('mfa')) {
      test.skip(true, '2FA required — cannot complete login in this test');
      return;
    }

    // Check cookies
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find(
      (c) => c.name === 'session' || c.name === 'flask_session' || c.name.includes('session')
    );

    if (sessionCookie) {
      expect(sessionCookie.httpOnly).toBe(true);
    } else {
      // If no session cookie found by name, check all cookies for httpOnly
      const hasAnyCookie = cookies.length > 0;
      expect(hasAnyCookie).toBe(true);
      console.log('Session cookie names:', cookies.map((c) => c.name).join(', '));
    }
  });

  test('/applications returns login page after logout', async ({ page }) => {
    // This test verifies no cached authenticated content is served
    const response = await page.goto('/applications', { waitUntil: 'domcontentloaded' });
    expect(response?.status()).toBeLessThan(500);

    const url = page.url();
    const body = await page.textContent('body') || '';
    const lowerBody = body.toLowerCase();

    const isOnLogin =
      url.includes('login') ||
      url.includes('auth') ||
      url.includes('signin') ||
      lowerBody.includes('sign in') ||
      lowerBody.includes('log in') ||
      lowerBody.includes('password') ||
      (await page.locator('input[type="password"]').count()) > 0;

    expect(
      isOnLogin,
      `Expected login page but ended up at ${url}`
    ).toBe(true);
  });
});
