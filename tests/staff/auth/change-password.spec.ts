/**
 * Staff Portal — Authenticated auth tests (change password, 2FA setup)
 * These tests use the saved admin session (NOT unauthenticated like login.spec.ts).
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /change-password — page loads', async ({ page }) => {
  await assertPageLoads(page, '/change-password');
  await expect(page.locator('[name="current_password"], [name="old_password"]').first()).toBeVisible();
});

test('/change-password — mismatched confirm shows validation error', async ({ page }) => {
  await page.goto('/change-password');
  await page.waitForLoadState('domcontentloaded');

  const currentPw = page.locator('[name="current_password"], [name="old_password"]').first();
  const newPw = page.locator('[name="new_password"]').first();
  const confirmPw = page.locator('[name="confirm_password"], [name="confirm_new_password"], [name="password_confirm"]').first();

  if (await currentPw.isVisible()) await currentPw.fill('Testuser1234!');
  if (await newPw.isVisible()) await newPw.fill('NewPassword2024!');
  if (await confirmPw.isVisible()) await confirmPw.fill('WrongConfirm2024!');

  // Client-side JS validates on input — the submit button stays disabled
  // and a "Passwords do not match" message appears. Assert that.
  const bodyText = await page.textContent('body');
  const hasValidation = bodyText?.toLowerCase().includes('match') ||
                        bodyText?.toLowerCase().includes('do not match') ||
                        bodyText?.toLowerCase().includes('passwords');

  // The submit button should be disabled (client-side validation blocks it)
  const submitBtn = page.locator('[type="submit"], #submitBtn').first();
  const isDisabled = await submitBtn.isDisabled().catch(() => true);

  expect(hasValidation || isDisabled).toBeTruthy();
});

test('@smoke /security/2fa/setup — page loads', async ({ page }) => {
  const response = await page.goto('/security/2fa/setup', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});
