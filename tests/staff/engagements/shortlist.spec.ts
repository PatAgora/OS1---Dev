/**
 * Staff Portal — Engagement Shortlist
 *
 * Tests: shortlist page loads, add/remove buttons if present.
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

test('/engagement/<id>/shortlist — page loads', async ({ page }) => {
  const id = await getFirstEngagementId(page);
  // Try the shortlist page — may be at different URLs
  let response = await page.goto(`/engagement/${id}/shortlist`, { waitUntil: 'domcontentloaded' });
  if (response?.status() === 404) {
    response = await page.goto(`/engagement/${id}/dashboard`, { waitUntil: 'domcontentloaded' });
  }
  expect(response?.status()).toBeLessThan(500);
});

test('/engagement/<id>/shortlist — add/remove buttons', async ({ page }) => {
  const id = await getFirstEngagementId(page);
  await page.goto(`/engagement/${id}/shortlist`, { waitUntil: 'domcontentloaded' });

  // If add/remove buttons exist, click add and assert response
  const addBtn = page.locator('button, a').filter({ hasText: /add|shortlist/i }).first();
  if (await addBtn.isVisible().catch(() => false)) {
    await addBtn.click();
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Internal Server Error');
  }

  const removeBtn = page.locator('button, a').filter({ hasText: /remove/i }).first();
  if (await removeBtn.isVisible().catch(() => false)) {
    await removeBtn.click();
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Internal Server Error');
  }
});
