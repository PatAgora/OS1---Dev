/**
 * Staff Portal — Engagement Financials (/engagement/<id>/financials)
 *
 * Tests: page loads without server error.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

async function getFirstEngagementId(page: import('@playwright/test').Page): Promise<string> {
  await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
  const link = page.locator('a[href*="/engagement/"]').first();
  const href = await link.getAttribute('href');
  const match = href?.match(/\/engagement\/(\d+)/);
  return match ? match[1] : '1';
}

test('/engagement/<id>/financials — page loads', async ({ page }) => {
  const id = await getFirstEngagementId(page);
  const response = await page.goto(`/engagement/${id}/financials`, { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});
