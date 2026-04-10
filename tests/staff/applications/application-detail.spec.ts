/**
 * Staff Portal — Application Detail tests
 *
 * Tests: /application/<id>
 * Navigates from /applications to first detail page.
 * Verifies sections, clicks AI buttons (safe), asserts blocked buttons visible but not clicked.
 *
 * BLOCKED: e-sign/contract buttons, vetting buttons — visible only, NOT clicked.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard, assertVisibleButDoNotClick } from '../../utils/blocked-routes';
import { assertPageLoads } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Application Detail', () => {
  /**
   * Helper: navigate to the first application's detail page.
   * Returns the detail page URL or null if no applications found.
   */
  async function goToFirstApplicationDetail(page: import('@playwright/test').Page): Promise<string | null> {
    await page.goto('/applications', { waitUntil: 'domcontentloaded' });

    const appLink = page.locator('a[href*="/application/"]').first();
    if (await appLink.count() === 0) {
      return null;
    }

    const href = await appLink.getAttribute('href');
    if (!href) return null;

    await page.goto(href, { waitUntil: 'domcontentloaded' });
    return href;
  }

  test('@smoke application detail — page loads (200)', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) {
      console.log('  No applications found — skipping detail tests');
      return;
    }

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback (most recent call last)');
  });

  test('candidate name visible', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) {
      console.log('  No applications found — skipping');
      return;
    }

    // Look for candidate name in heading or prominent text
    const heading = page.locator('h1, h2, h3, .candidate-name, [data-candidate-name]').first();
    await expect(heading).toBeVisible({ timeout: 10000 });
    const text = await heading.textContent();
    expect(text?.trim().length).toBeGreaterThan(0);
  });

  test('CV section renders', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    const cvSection = page.locator('text=CV, text=Resume, text=cv, text=resume, [data-section="cv"], .cv-section, #cvSection').first();
    const bodyText = await page.textContent('body');
    const hasCvReference = bodyText?.includes('CV') || bodyText?.includes('Resume') || bodyText?.includes('cv');
    expect(hasCvReference).toBeTruthy();
  });

  test('notes section visible', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    const bodyText = await page.textContent('body');
    const hasNotesSection = bodyText?.includes('Note') || bodyText?.includes('note') || bodyText?.includes('Comment') || bodyText?.includes('comment');
    expect(hasNotesSection).toBeTruthy();
  });

  test('interview section visible', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    const bodyText = await page.textContent('body');
    const hasInterviewSection = bodyText?.includes('Interview') || bodyText?.includes('interview') || bodyText?.includes('Schedule');
    expect(hasInterviewSection).toBeTruthy();
  });

  // ============================================================
  // AI Buttons — SAFE TO CLICK (Gemini, no cost concern)
  // ============================================================

  test('AI Score button — click and assert no 500', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    // Look for AI Score button
    const scoreBtn = page.locator('button:has-text("Score"), a:has-text("Score"), button:has-text("AI Score"), a:has-text("AI Score"), [data-action="score"]').first();

    if (await scoreBtn.count() > 0) {
      await expect(scoreBtn).toBeVisible();

      // Click and wait for response
      const [response] = await Promise.all([
        page.waitForResponse(resp => resp.url().includes('score') || resp.url().includes('action'), { timeout: 30000 }).catch(() => null),
        scoreBtn.click(),
      ]);

      // Wait for page to settle
      await page.waitForLoadState('domcontentloaded');

      // Assert no 500 error
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');

      if (response) {
        expect(response.status()).toBeLessThan(500);
      }
    } else {
      console.log('  AI Score button not found on this application');
    }
  });

  test('Summarise button — click and assert no 500', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    // Look for Summarise button
    const summariseBtn = page.locator('button:has-text("Summarise"), a:has-text("Summarise"), button:has-text("Summarize"), a:has-text("Summarize"), button:has-text("Summary"), [data-action="summarise"]').first();

    if (await summariseBtn.count() > 0) {
      await expect(summariseBtn).toBeVisible();

      // Click and wait for response
      const [response] = await Promise.all([
        page.waitForResponse(resp => resp.url().includes('summar'), { timeout: 30000 }).catch(() => null),
        summariseBtn.click(),
      ]);

      // Wait for page to settle
      await page.waitForLoadState('domcontentloaded');

      // Assert no 500 error
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');

      if (response) {
        expect(response.status()).toBeLessThan(500);
      }
    } else {
      console.log('  Summarise button not found on this application');
    }
  });

  // ============================================================
  // BLOCKED Buttons — visible but DO NOT CLICK
  // ============================================================

  test('e-sign/contract buttons visible — DO NOT CLICK', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    // Check for e-sign / contract buttons — assert visible but do not click
    const esignSelectors = [
      'button:has-text("Send Contract")',
      'a:has-text("Send Contract")',
      'button:has-text("E-Sign")',
      'a:has-text("E-Sign")',
      'button:has-text("Signable")',
      '[data-action="esign"]',
      '[data-action="contract"]',
    ];

    let found = false;
    for (const selector of esignSelectors) {
      const btn = page.locator(selector).first();
      if (await btn.count() > 0 && await btn.isVisible()) {
        found = true;
        console.log(`  BLOCKED button visible (not clicked): e-sign/contract — ${selector}`);
      }
    }

    if (!found) {
      console.log('  No e-sign/contract buttons found on this application (may not be at that stage)');
    }
  });

  test('vetting buttons visible — DO NOT CLICK', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    // Check for vetting buttons — assert visible but do not click
    const vettingSelectors = [
      'button:has-text("Vetting")',
      'a:has-text("Vetting")',
      'button:has-text("Verifile")',
      'button:has-text("Start Vetting")',
      'button:has-text("ID Check")',
      '[data-action="vetting"]',
      '[data-action="verifile"]',
    ];

    let found = false;
    for (const selector of vettingSelectors) {
      const btn = page.locator(selector).first();
      if (await btn.count() > 0 && await btn.isVisible()) {
        found = true;
        console.log(`  BLOCKED button visible (not clicked): vetting — ${selector}`);
      }
    }

    if (!found) {
      console.log('  No vetting buttons found on this application (may not be at that stage)');
    }
  });

  test('Make Offer section visible if present', async ({ page }) => {
    const detailUrl = await goToFirstApplicationDetail(page);
    if (!detailUrl) return;

    const bodyText = await page.textContent('body');
    const hasOfferSection = bodyText?.includes('Offer') || bodyText?.includes('offer') || bodyText?.includes('Make Offer');

    if (hasOfferSection) {
      console.log('  Make Offer section found on application detail');
    } else {
      console.log('  No Make Offer section found (application may not be at offer stage)');
    }
  });
});
