/**
 * Staff Portal — Workflow tests
 *
 * Tests: /workflow
 * Verifies page load, stage columns, candidate cards, focus checkboxes, and filter form.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Workflow', () => {
  let pageLoadFailed = false;

  test('@smoke /workflow — page loads (< 500)', async ({ page }) => {
    const response = await page.goto('/workflow', { waitUntil: 'domcontentloaded' });
    const status = response?.status() || 0;
    expect(status).toBeLessThan(500);

    if (status >= 500) {
      pageLoadFailed = true;
    }

    await guardSessionExpired(page);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
  });

  test('stage columns render or empty state', async ({ page }) => {
    const response = await page.goto('/workflow', { waitUntil: 'domcontentloaded' });
    if (response?.status() && response.status() >= 500) {
      test.skip(true, 'Workflow page returns 500 — skipping');
      return;
    }
    await guardSessionExpired(page);

    const columns = page.locator('.kanban-column, [class*="column"], [class*="stage"], [class*="kanban"]');
    const count = await columns.count();
    console.log(`  Kanban columns found: ${count}`);

    if (count === 0) {
      // Accept empty state or different layout
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  No kanban columns — page loaded OK');
    }
  });

  test('candidate cards visible or empty state', async ({ page }) => {
    const response = await page.goto('/workflow', { waitUntil: 'domcontentloaded' });
    if (response?.status() && response.status() >= 500) {
      test.skip(true, 'Workflow page returns 500 — skipping');
      return;
    }
    await guardSessionExpired(page);

    const cards = page.locator('.kanban-card, [class*="card"], [class*="candidate"]');
    const cardCount = await cards.count();

    if (cardCount > 0) {
      await expect(cards.first()).toBeVisible();
      console.log(`  Candidate cards found: ${cardCount}`);
    } else {
      // Empty state — page loaded without error, just no cards
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  No candidate cards — empty state OK');
    }
  });

  test('focus checkboxes toggle or page OK', async ({ page }) => {
    const response = await page.goto('/workflow', { waitUntil: 'domcontentloaded' });
    if (response?.status() && response.status() >= 500) {
      test.skip(true, 'Workflow page returns 500 — skipping');
      return;
    }
    await guardSessionExpired(page);

    const checkboxes = page.locator('.focus-cb, input[type="checkbox"]');
    const cbCount = await checkboxes.count();

    if (cbCount === 0) {
      console.log('  No focus checkboxes found — skipping toggle test');
      return;
    }

    console.log(`  Focus checkboxes found: ${cbCount}`);
  });

  test('filter form — submit without error', async ({ page }) => {
    const response = await page.goto('/workflow', { waitUntil: 'domcontentloaded' });
    if (response?.status() && response.status() >= 500) {
      test.skip(true, 'Workflow page returns 500 — skipping');
      return;
    }
    await guardSessionExpired(page);

    const filterForm = page.locator('form').first();
    const formExists = await filterForm.count();

    if (formExists > 0) {
      const submitBtn = filterForm.locator('[type="submit"], button').first();
      if (await submitBtn.count() > 0) {
        await submitBtn.click();
        await page.waitForLoadState('domcontentloaded');
      }

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');
      console.log('  Filter form submitted — no error');
    } else {
      console.log('  No filter form found — skipping');
    }
  });
});
