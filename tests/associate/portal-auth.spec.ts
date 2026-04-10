/**
 * Associate Portal — Auth Page tests
 *
 * Tests: /portal/login, /portal/register, /portal/forgot-password
 * Uses empty storage state (unauthenticated).
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Portal Auth Pages', () => {
  test('@smoke /portal/login — loads (200), email/password fields visible', async ({ page }) => {
    const response = await page.goto('/portal/login', { waitUntil: 'domcontentloaded' });
    expect(response?.status()).toBe(200);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    const emailField = page.locator('[name="email"]');
    const passwordField = page.locator('[name="password"]');

    await expect(emailField).toBeVisible({ timeout: 5000 });
    await expect(passwordField).toBeVisible({ timeout: 5000 });
    console.log('  /portal/login — email and password fields visible');
  });

  test('@smoke /portal/register — loads (200)', async ({ page }) => {
    const response = await page.goto('/portal/register', { waitUntil: 'domcontentloaded' });
    expect(response?.status()).toBe(200);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    console.log('  /portal/register loaded');
  });

  test('/portal/forgot-password — loads, DO NOT submit', async ({ page }) => {
    const response = await page.goto('/portal/forgot-password', { waitUntil: 'domcontentloaded' });
    const status = response?.status() ?? 0;
    expect(status).toBeLessThan(500);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    console.log(`  /portal/forgot-password loaded (status ${status}) — not submitting`);
  });
});
