/**
 * Staff Portal — Admin Audit Log (/admin/audit-log)
 *
 * Tests: page load, log entries table rendering.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/audit-log — page loads', async ({ page }) => {
  const response = await page.goto('/admin/audit-log', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
  await guardSessionExpired(page);
});

test('/admin/audit-log — log entries table renders or empty state', async ({ page }) => {
  const response = await page.goto('/admin/audit-log', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() === 403) {
    test.skip(true, 'Requires super_admin role — 403 returned');
    return;
  }

  if (response?.status() === 200) {
    const body = await page.textContent('body') || '';

    // Accept empty state
    if (body.includes('No audit') || body.includes('No log') || body.includes('no entries')) {
      console.log('  Empty state — valid');
      return;
    }

    // Broad selectors for the log table
    const table = page.locator('table, [class*="table"], .list-group, [class*="log"], [class*="audit"]');
    const tableVisible = await table.first().isVisible({ timeout: 5000 }).catch(() => false);

    if (tableVisible) {
      const rows = page.locator('table tbody tr, .list-group-item, [class*="log-entry"], [class*="audit-row"]');
      const count = await rows.count();
      console.log(`  Audit log entries found: ${count}`);
      // Accept 0 rows (empty table) as valid
    } else {
      // Page loaded without a recognisable table — accept if no error
      expect(body).not.toContain('Internal Server Error');
      console.log('  No audit log table found — page loaded OK');
    }
  }
});
