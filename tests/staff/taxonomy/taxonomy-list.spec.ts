/**
 * Staff Portal — Taxonomy List tests
 *
 * Tests: /taxonomy
 * Verifies page loads without 500.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Taxonomy List', () => {
  test('@smoke /taxonomy — loads without 500', async ({ page }) => {
    const response = await page.goto('/taxonomy', { waitUntil: 'domcontentloaded' });
    const status = response?.status() ?? 0;
    expect(status).toBeLessThan(500);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback (most recent call last)');
    console.log(`  /taxonomy loaded with status ${status}`);
  });
});
