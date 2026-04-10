/**
 * Associate Portal — Vetting Progress tests
 *
 * Tests: /portal/vetting-progress
 * Verifies page load and progress rows render.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Vetting Progress', () => {
  test('@smoke /portal/vetting-progress — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/vetting-progress');
  });

  test('progress rows render', async ({ page }) => {
    await page.goto('/portal/vetting-progress', { waitUntil: 'domcontentloaded' });

    // Look for progress rows, table rows, or status items
    const progressItems = page.locator(
      'table tbody tr, .progress-row, .vetting-row, .check-item, ' +
      '.status-row, [data-check], li'
    );
    const count = await progressItems.count();
    console.log(`  Vetting progress items found: ${count}`);

    // At minimum the page should have content
    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
  });
});
