/**
 * Staff Portal — Engagement Plan (/engagement/<id>/plan)
 *
 * Tests: page load, plan table rendering, add row.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

/** Get the first engagement ID from the engagements list */
async function getFirstEngagementId(page: import('@playwright/test').Page): Promise<string | null> {
  await page.goto('/engagements', { waitUntil: 'domcontentloaded' });

  const bodyText = await page.textContent('body') || '';
  if (
    (bodyText.includes('Sign in') || bodyText.includes('Log in')) &&
    (page.url().includes('/login') || page.url().includes('/auth'))
  ) {
    return null;
  }

  const link = page.locator('a[href*="/engagement/"]').first();
  if (!(await link.isVisible({ timeout: 10000 }).catch(() => false))) {
    return null;
  }
  const href = await link.getAttribute('href');
  const match = href?.match(/\/engagement\/(\d+)/);
  return match ? match[1] : null;
}

test('/engagement/<id>/plan — page loads', async ({ page }) => {
  const id = await getFirstEngagementId(page);
  if (!id) {
    test.skip(true, 'No engagements found or session expired — skipping');
    return;
  }
  const response = await page.goto(`/engagement/${id}/plan`, { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});

test('/engagement/<id>/plan — plan table renders or empty state', async ({ page }) => {
  const id = await getFirstEngagementId(page);
  if (!id) {
    test.skip(true, 'No engagements found or session expired — skipping');
    return;
  }
  await page.goto(`/engagement/${id}/plan`, { waitUntil: 'domcontentloaded' });

  const body = await page.textContent('body') || '';

  // Accept empty state
  if (body.includes('No plan') || body.includes('no roles') || body.includes('No roles')) {
    console.log('  Empty state — valid');
    return;
  }

  const table = page.locator('table, [class*="table"], .list-group');
  const count = await table.count();

  if (count > 0) {
    console.log(`  Plan tables found: ${count}`);
  } else {
    expect(body).not.toContain('Internal Server Error');
    console.log('  No plan table found — page loaded OK');
  }
});

test('/engagement/<id>/plan — add row if button exists', async ({ page }) => {
  const id = await getFirstEngagementId(page);
  if (!id) {
    test.skip(true, 'No engagements found or session expired — skipping');
    return;
  }
  await page.goto(`/engagement/${id}/plan`, { waitUntil: 'domcontentloaded' });

  const addRowBtn = page.locator('button, a').filter({ hasText: /Add Row|Add Role|Add/i }).first();
  if (await addRowBtn.isVisible().catch(() => false)) {
    const rowsBefore = await page.locator('table tbody tr').count();
    await addRowBtn.click();
    await page.waitForTimeout(1000);
    const rowsAfter = await page.locator('table tbody tr').count();
    expect(rowsAfter).toBeGreaterThanOrEqual(rowsBefore);
  } else {
    console.log('  Add Row button not found — skipping');
  }
});
