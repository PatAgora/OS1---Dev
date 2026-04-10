/**
 * Staff Portal — Revenue tests
 *
 * Tests: /revenue
 * Verifies page load, revenue summary, and quarter period buttons.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Revenue', () => {
  test('@smoke /revenue — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/revenue');
  });

  test('revenue summary visible', async ({ page }) => {
    await page.goto('/revenue', { waitUntil: 'domcontentloaded' });

    // Look for revenue summary elements — numbers, totals, headings
    const bodyText = await page.textContent('body');
    const hasRevenueSummary =
      bodyText?.includes('Revenue') ||
      bodyText?.includes('revenue') ||
      bodyText?.includes('Total') ||
      bodyText?.includes('total') ||
      bodyText?.match(/£[\d,]+/) !== null;

    expect(hasRevenueSummary).toBeTruthy();
  });

  test('click quarter/period buttons — no error', async ({ page }) => {
    await page.goto('/revenue', { waitUntil: 'domcontentloaded' });

    // Look for period filter buttons
    const periodBtns = page.locator('.period-btn, button:has-text("Q1"), button:has-text("Q2"), button:has-text("Q3"), button:has-text("Q4"), [data-period]');
    const btnCount = await periodBtns.count();

    if (btnCount > 0) {
      console.log(`  Found ${btnCount} period buttons`);

      // Click each button and assert no error
      for (let i = 0; i < btnCount; i++) {
        const btn = periodBtns.nth(i);
        if (await btn.isVisible()) {
          await btn.click();

          // Wait for any dynamic update or page load
          await page.waitForTimeout(500);
          await page.waitForLoadState('domcontentloaded');

          // Assert no server error
          const body = await page.textContent('body');
          expect(body).not.toContain('Internal Server Error');
          expect(body).not.toContain('Traceback (most recent call last)');
        }
      }
    } else {
      console.log('  No period buttons found on /revenue');
    }
  });
});
