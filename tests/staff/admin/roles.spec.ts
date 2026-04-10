/**
 * Staff Portal — Admin Roles (/admin/roles or equivalent)
 *
 * Tests: page loads without server error.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/roles — page loads', async ({ page }) => {
  // Try /admin/roles first, fall back to /config/roles or /config_roles
  let response = await page.goto('/admin/roles', { waitUntil: 'domcontentloaded' });
  if (response?.status() === 404) {
    response = await page.goto('/config/roles', { waitUntil: 'domcontentloaded' });
  }
  if (response?.status() === 404) {
    response = await page.goto('/config-roles', { waitUntil: 'domcontentloaded' });
  }
  expect(response?.status()).toBeLessThan(500);
});
