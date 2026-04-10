/**
 * Associate Portal — Timesheets tests
 *
 * Tests: /portal/timesheets
 * Verifies page load and timesheet list or empty state.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Timesheets', () => {
  test('@smoke /portal/timesheets — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/timesheets');
  });

  test('timesheet list or empty state', async ({ page }) => {
    await page.goto('/portal/timesheets', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    const timesheetItems = page.locator(
      'table tbody tr, .timesheet-row, .timesheet-card, [data-timesheet]'
    );
    const count = await timesheetItems.count();

    if (count > 0) {
      console.log(`  Timesheet entries found: ${count}`);
    } else {
      console.log('  No timesheets — empty state');
    }
  });
});
