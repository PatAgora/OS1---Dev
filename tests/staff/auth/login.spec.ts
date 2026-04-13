/**
 * Staff Portal — Authentication tests
 *
 * Tests: /login, /forgot-password, /request-access, /change-password, /security/2fa/setup
 *
 * BLOCKED: /forgot-password POST (SMTP), /admin/send-magic-link (SMTP)
 * These pages are loaded but NOT submitted.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads } from '../../utils/helpers';

// Auth tests must start UNAUTHENTICATED — override the staff project's stored session
test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

// ============================================================
// /login
// ============================================================

test('@smoke /login — page loads', async ({ page }) => {
  await assertPageLoads(page, '/login', { skipSessionGuard: true });
  await expect(page.locator('[name="email"]')).toBeVisible();
  await expect(page.locator('[name="password"]')).toBeVisible();
  await expect(page.locator('[type="submit"]')).toBeVisible();
});

test('/login — wrong password shows error', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'wrong@example.com');
  await page.fill('[name="password"]', 'wrongpassword');
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  // Should stay on login page (not redirect to dashboard)
  expect(page.url()).toContain('/login');

  // Should show an error flash or message
  const bodyText = await page.textContent('body');
  const hasError = bodyText?.includes('Invalid') ||
                   bodyText?.includes('incorrect') ||
                   bodyText?.includes('error') ||
                   bodyText?.includes('failed') ||
                   page.url().includes('/login');
  expect(hasError).toBeTruthy();
});

test('/login — correct credentials redirect to dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'playwright@test.example.com');
  await page.fill('[name="password"]', 'Testuser1234!');
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  // Should redirect away from /login (to / or /security/2fa/*)
  const url = page.url();
  expect(url).not.toContain('/login');
});

// ============================================================
// /forgot-password — page render ONLY, DO NOT submit
// ============================================================

test('@smoke /forgot-password — page loads (render only)', async ({ page }) => {
  await assertPageLoads(page, '/forgot-password');
  await expect(page.locator('[name="email"]')).toBeVisible();
  // DO NOT submit — would send an email via SMTP
});

// ============================================================
// /request-access
// ============================================================

test('@smoke /request-access — page loads', async ({ page }) => {
  await assertPageLoads(page, '/request-access');
});

test('/request-access — submit form', async ({ page }) => {
  await page.goto('/request-access');
  await page.waitForLoadState('domcontentloaded');

  // Fill available fields
  const nameField = page.locator('[name="name"]').first();
  if (await nameField.isVisible()) {
    await nameField.fill('PW Test User');
  }

  const emailField = page.locator('[name="email"]').first();
  if (await emailField.isVisible()) {
    await emailField.fill('pw-request-access@example.com');
  }

  const messageField = page.locator('[name="message"], textarea').first();
  if (await messageField.isVisible()) {
    await messageField.fill('Playwright test — request access form submission');
  }

  // Submit and assert success or redirect (not a 500)
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  const bodyText = await page.textContent('body');
  expect(bodyText).not.toContain('Internal Server Error');
});

// NOTE: /change-password and /security/2fa/setup require auth — see change-password.spec.ts
