/**
 * Staff Portal — Kanban tests
 *
 * Tests: /kanban
 * The /kanban route may redirect to /workflow. Assert no 500.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Kanban', () => {
  test('@smoke /kanban — loads without 500 (may redirect to /workflow)', async ({ page }) => {
    const response = await page.goto('/kanban', { waitUntil: 'domcontentloaded' });
    const status = response?.status() ?? 0;
    expect(status).toBeLessThan(500);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback (most recent call last)');

    const finalUrl = page.url();
    console.log(`  /kanban landed on: ${finalUrl} (status ${status})`);
  });
});
