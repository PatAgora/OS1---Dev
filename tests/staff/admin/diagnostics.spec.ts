/**
 * Staff Portal — Admin System Diagnostics (/admin/system-diagnostics)
 *
 * Tests: page load.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/system-diagnostics — page loads', async ({ page }) => {
  const response = await page.goto('/admin/system-diagnostics', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});
