/**
 * Staff Portal — Admin Portal Users (/admin/portal-users)
 *
 * Tests: page load, user list rendering.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/portal-users — page loads', async ({ page }) => {
  const response = await page.goto('/admin/portal-users', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});

test('/admin/portal-users — user list renders', async ({ page }) => {
  const response = await page.goto('/admin/portal-users', { waitUntil: 'domcontentloaded' });
  if (response?.status() === 200) {
    const list = page.locator('table, .user-list, .card');
    await expect(list.first()).toBeVisible({ timeout: 5000 });
  }
});
