/**
 * Deep Tests — Session Security
 *
 * Verifies session handling: logout clears state, protected routes
 * redirect to login, and session cookies have appropriate security flags.
 *
 * These tests intentionally start UNAUTHENTICATED and manage their own login.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { generateTOTP } from '../../../utils/totp';
import fs from 'fs';
import path from 'path';

// Start fresh — no stored session
test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

const TOTP_SECRET_FILE = path.join(__dirname, '../../../../playwright/.auth/totp-secret.txt');

/** Log in as the test admin user, handling 2FA automatically */
async function loginAsTestAdmin(page: import('@playwright/test').Page): Promise<boolean> {
  await page.goto('/login', { waitUntil: 'domcontentloaded' });

  const emailInput = page.locator('input[name="email"]').first();
  if (await emailInput.count() === 0) return false;

  await emailInput.fill('playwright@test.example.com');
  await page.locator('input[name="password"]').first().fill('Testuser1234!');
  await page.locator('button[type="submit"], input[type="submit"]').first().click();
  await page.waitForLoadState('domcontentloaded');

  // Handle 2FA
  if (page.url().includes('2fa') || page.url().includes('verify')) {
    if (fs.existsSync(TOTP_SECRET_FILE)) {
      const secret = fs.readFileSync(TOTP_SECRET_FILE, 'utf-8').trim();
      const code = generateTOTP(secret);
      const totpInput = page.locator('input[name="totp_code"], input[name="code"], input[name="token"]').first();
      if (await totpInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await totpInput.fill(code);
        await page.locator('[type="submit"]').first().click();
        await page.waitForLoadState('domcontentloaded');
      }
    } else {
      return false;
    }
  }

  // Handle backup codes page
  if (page.url().includes('backup')) {
    const continueBtn = page.locator('a:has-text("Continue"), button:has-text("Continue")').first();
    if (await continueBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await continueBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }
  }

  return !page.url().includes('/login');
}

test.describe('Session Security', () => {

  test('logout clears session and redirects to login', async ({ page }) => {
    const loggedIn = await loginAsTestAdmin(page);
    expect(loggedIn, 'Login must succeed for logout test').toBeTruthy();

    // Now log out
    await page.goto('/logout', { waitUntil: 'domcontentloaded' });

    // After logout, should redirect to login
    const url = page.url();
    const body = (await page.textContent('body') || '').toLowerCase();
    expect(
      url.includes('/login') || body.includes('sign in') || body.includes('password'),
      `After logout, expected login page but got ${url}`
    ).toBeTruthy();

    // Navigating to dashboard should redirect to login
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const dashUrl = page.url();
    expect(
      dashUrl.includes('/login') || dashUrl.includes('/auth'),
      `Dashboard should redirect to login after logout, got ${dashUrl}`
    ).toBeTruthy();
  });

  test('protected routes redirect to login when unauthenticated', async ({ page }) => {
    const protectedRoutes = ['/applications', '/resource-pool', '/engagements'];

    for (const route of protectedRoutes) {
      await page.goto(route, { waitUntil: 'domcontentloaded' });
      const url = page.url();
      const body = (await page.textContent('body') || '').toLowerCase();

      const isOnLogin = url.includes('login') || url.includes('auth') || url.includes('signin');
      const showsLoginForm = body.includes('sign in') || body.includes('password') ||
        (await page.locator('input[type="password"]').count()) > 0;

      expect(
        isOnLogin || showsLoginForm,
        `Expected redirect to login for ${route}, but ended up at ${url}`
      ).toBe(true);
    }
  });

  test('session cookie has httponly flag', async ({ page }) => {
    const loggedIn = await loginAsTestAdmin(page);
    expect(loggedIn, 'Login must succeed for cookie test').toBeTruthy();

    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find(c => c.name === 'session' || c.name.includes('session'));

    expect(sessionCookie, 'Session cookie should exist after login').toBeTruthy();
    if (sessionCookie) {
      expect(sessionCookie.httpOnly, 'Session cookie should have httpOnly flag').toBe(true);
      console.log(`  ✓ Session cookie: httpOnly=${sessionCookie.httpOnly}, secure=${sessionCookie.secure}, sameSite=${sessionCookie.sameSite}`);
    }
  });

  test('/applications returns login page after logout', async ({ page }) => {
    const loggedIn = await loginAsTestAdmin(page);
    expect(loggedIn, 'Login must succeed').toBeTruthy();

    // Logout
    await page.goto('/logout', { waitUntil: 'domcontentloaded' });

    // Try accessing a protected route
    await page.goto('/applications', { waitUntil: 'domcontentloaded' });
    const url = page.url();
    const body = (await page.textContent('body') || '').toLowerCase();

    expect(
      url.includes('/login') || body.includes('sign in') || body.includes('password'),
      `Expected login after logout+/applications, got ${url}`
    ).toBeTruthy();
  });

});
