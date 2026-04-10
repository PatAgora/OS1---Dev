/**
 * Staff Portal — Applications List tests
 *
 * Tests: /applications
 * Verifies page load, table rendering, and navigation to detail page.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Applications List', () => {
  test('@smoke /applications — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/applications');
  });

  test('applications table renders', async ({ page }) => {
    await page.goto('/applications', { waitUntil: 'domcontentloaded' });

    // Look for a table or application list items
    const table = page.locator('table');
    const cards = page.locator('.application-card, .card, [data-application-id]');

    const tableCount = await table.count();
    const cardCount = await cards.count();

    expect(tableCount + cardCount).toBeGreaterThan(0);

    if (tableCount > 0) {
      const rows = table.first().locator('tbody tr');
      const rowCount = await rows.count();
      console.log(`  Applications table found with ${rowCount} rows`);
      expect(rowCount).toBeGreaterThan(0);
    }
  });

  test('click first application row — navigates to detail page', async ({ page }) => {
    await page.goto('/applications', { waitUntil: 'domcontentloaded' });

    // Find the first clickable application link
    const appLink = page.locator('a[href*="/application/"]').first();
    const appLinkExists = await appLink.count();

    if (appLinkExists > 0) {
      await appLink.click();
      await page.waitForLoadState('domcontentloaded');

      // Assert we navigated to an application detail page
      const url = page.url();
      expect(url).toContain('/application/');

      // Assert no server error
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');
    } else {
      console.log('  No application links found — skipping navigation test');
    }
  });
});
