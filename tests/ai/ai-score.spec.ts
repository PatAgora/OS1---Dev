/**
 * AI — Score & Summarise tests
 *
 * Tests: AI Score and Summarise buttons on application detail page
 * Uses staff admin auth. Waits up to 30s for AI responses.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('AI Score & Summarise', () => {
  test('navigate to application detail — score and summarise', async ({ page }) => {
    // Go to applications list
    const response = await page.goto('/applications', { waitUntil: 'domcontentloaded' });
    expect(response?.status()).toBeLessThan(500);

    // Find the first application with a detail link
    const detailLink = page.locator(
      'a[href*="/application/"], a:has-text("View"), a:has-text("Detail"), ' +
      'table tbody tr a'
    ).first();

    if (!(await detailLink.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  No application detail links found — skipping AI tests');
      return;
    }

    await detailLink.click();
    await page.waitForLoadState('domcontentloaded');

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    const currentUrl = page.url();
    console.log(`  Application detail page: ${currentUrl}`);

    // --- AI Score ---
    const scoreBtn = page.locator(
      'button:has-text("Score"), a:has-text("Score"), ' +
      'button:has-text("AI Score"), a:has-text("AI Score")'
    ).first();

    if (await scoreBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('  Clicking Score button...');
      await scoreBtn.click();

      // Wait up to 30s for response
      await page.waitForLoadState('domcontentloaded', { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(2000); // Allow AJAX to complete

      const afterScoreBody = await page.textContent('body');
      expect(afterScoreBody).not.toContain('Internal Server Error');
      expect(afterScoreBody).not.toContain('Traceback (most recent call last)');

      // Check for score value update (could be a number, percentage, or text)
      const scoreValue = page.locator(
        '.score, .ai-score, [data-score], .match-score, ' +
        '[class*="score"]'
      ).first();

      if (await scoreValue.isVisible({ timeout: 5000 }).catch(() => false)) {
        const scoreText = await scoreValue.textContent();
        console.log(`  AI Score result: ${scoreText?.trim().substring(0, 100)}`);
      } else {
        console.log('  Score completed — no dedicated score element found');
      }
    } else {
      console.log('  Score button not found on application detail page');
    }

    // --- AI Summarise ---
    const summariseBtn = page.locator(
      'button:has-text("Summarise"), a:has-text("Summarise"), ' +
      'button:has-text("Summarize"), a:has-text("Summarize"), ' +
      'button:has-text("AI Summary"), a:has-text("AI Summary")'
    ).first();

    if (await summariseBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('  Clicking Summarise button...');
      await summariseBtn.click();

      // Wait up to 30s for response
      await page.waitForLoadState('domcontentloaded', { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(2000); // Allow AJAX to complete

      const afterSumBody = await page.textContent('body');
      expect(afterSumBody).not.toContain('Internal Server Error');
      expect(afterSumBody).not.toContain('Traceback (most recent call last)');

      // Check for summary text
      const summaryEl = page.locator(
        '.summary, .ai-summary, [data-summary], [class*="summary"], ' +
        '.candidate-summary, .generated-summary'
      ).first();

      if (await summaryEl.isVisible({ timeout: 5000 }).catch(() => false)) {
        const summaryText = await summaryEl.textContent();
        console.log(`  AI Summary result: ${summaryText?.trim().substring(0, 150)}`);
      } else {
        console.log('  Summarise completed — no dedicated summary element found');
      }
    } else {
      console.log('  Summarise button not found on application detail page');
    }
  });
});
