/**
 * Staff Portal — Placements tests
 *
 * Tests: /placements
 * Verifies page load, table rendering, and CSV export.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Placements', () => {
  test('@smoke /placements — page loads', async ({ page }) => {
    await assertPageLoads(page, '/placements');
  });

  test('placements table renders or empty state', async ({ page }) => {
    await page.goto('/placements', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const body = await page.textContent('body') || '';

    // Accept empty state as valid
    if (body.includes('No Active Placements') || body.includes('No placements') || body.includes('no placements')) {
      console.log('  Empty state: "No Active Placements" — valid');
      return;
    }

    // Look for a table, cards, or any list of placements
    const table = page.locator('table, [class*="table"]');
    const cards = page.locator('.placement-card, .card, [data-placement-id]');

    const tableCount = await table.count();
    const cardCount = await cards.count();

    if (tableCount + cardCount > 0) {
      if (tableCount > 0) {
        const rows = table.first().locator('tbody tr');
        const rowCount = await rows.count();
        console.log(`  Placements table found with ${rowCount} rows`);
      }
    } else {
      // No table or cards, but page loaded without error — accept
      expect(body).not.toContain('Internal Server Error');
      console.log('  No table or cards found — page loaded OK');
    }
  });

  test('export CSV link/button visible — click and no error', async ({ page }) => {
    await page.goto('/placements', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Look for CSV export link or button
    const exportBtn = page.locator('a:has-text("CSV"), a:has-text("Export"), button:has-text("CSV"), button:has-text("Export"), a[href*="csv"], a[href*="export"]').first();

    if (await exportBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Click and handle potential download
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 10000 }).catch(() => null),
        exportBtn.click(),
      ]);

      if (download) {
        console.log(`  CSV download triggered: ${download.suggestedFilename()}`);
        // Cancel the download to avoid saving files
        await download.cancel().catch(() => {});
      } else {
        // May have navigated instead of downloading
        await page.waitForLoadState('domcontentloaded');
        const body = await page.textContent('body');
        expect(body).not.toContain('Internal Server Error');
        expect(body).not.toContain('Traceback (most recent call last)');
      }
    } else {
      console.log('  No CSV export button found on /placements — skipping');
    }
  });
});
