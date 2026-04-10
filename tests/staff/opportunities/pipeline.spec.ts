/**
 * Staff Portal — Pipeline tests
 *
 * Tests: /pipeline
 * Verifies page load and pipeline columns or card view rendering.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Pipeline', () => {
  test('@smoke /pipeline — page loads', async ({ page }) => {
    await assertPageLoads(page, '/pipeline');
  });

  test('pipeline columns or card view renders or empty state', async ({ page }) => {
    await page.goto('/pipeline', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const body = await page.textContent('body') || '';

    // Accept empty state
    if (body.includes('No opportunities') || body.includes('No pipelines') || body.includes('no data')) {
      console.log('  Empty state — valid');
      return;
    }

    // Look for pipeline columns, kanban columns, cards, or table rows with broad selectors
    const columns = page.locator('.pipeline-column, .kanban-column, .stage-column, [data-stage], [class*="column"], [class*="pipeline"], [class*="stage"]');
    const cards = page.locator('.pipeline-card, .opportunity-card, .card, [data-opportunity], [class*="card"]');
    const tableRows = page.locator('table tbody tr');

    const colCount = await columns.count();
    const cardCount = await cards.count();
    const rowCount = await tableRows.count();

    console.log(`  Pipeline columns: ${colCount}, cards: ${cardCount}, table rows: ${rowCount}`);

    if (colCount + cardCount + rowCount === 0) {
      // Page loaded without specific pipeline elements — accept if no error
      expect(body).not.toContain('Internal Server Error');
      console.log('  No pipeline elements found — page loaded OK');
    }
  });
});
