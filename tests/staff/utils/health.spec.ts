/**
 * Utility endpoints — Health and System Status
 *
 * Tests: /health, /system/status
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /health — returns 200', async ({ page }) => {
  const response = await page.goto('/health', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBe(200);
});

test('@smoke /system/status — returns 200', async ({ page }) => {
  const response = await page.goto('/system/status', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBe(200);
});
