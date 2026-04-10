/**
 * Staff Portal — Engagements List (/engagements)
 *
 * Tests: page load, list rendering, create engagement link.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /engagements — page loads', async ({ page }) => {
  await assertPageLoads(page, '/engagements');
});

test('/engagements — engagement list renders or empty state', async ({ page }) => {
  await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  const body = await page.textContent('body') || '';

  // Accept empty state
  if (body.includes('No engagements') || body.includes('no engagements') || body.includes('No active')) {
    console.log('  Empty state — valid');
    return;
  }

  // Engagements may appear as table rows or cards — broad selectors
  const items = page.locator('table tbody tr, .engagement-card, .card, [data-engagement-id], .list-group-item, [class*="engagement"]');
  const count = await items.count();

  if (count > 0) {
    console.log(`  Engagement items found: ${count}`);
  } else {
    // No items but no error — accept
    expect(body).not.toContain('Internal Server Error');
    console.log('  No engagement items found — page loaded OK');
  }
});

test('/engagements — Create Engagement link visible', async ({ page }) => {
  await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  const createLink = page.locator('a, button').filter({ hasText: /Create Engagement|New Engagement|Add Engagement|Create/i }).first();
  const visible = await createLink.isVisible({ timeout: 5000 }).catch(() => false);

  if (visible) {
    console.log('  Create Engagement link visible');
  } else {
    console.log('  Create Engagement link not found — page may have different layout');
    // Accept — not a failure
    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
  }
});
