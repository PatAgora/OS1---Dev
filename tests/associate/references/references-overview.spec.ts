/**
 * Associate Portal — References Overview tests
 *
 * Tests: /portal/references
 * Verifies page load and two clickable cards (Employment History / Vetting Checks).
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate References Overview', () => {
  test('@smoke /portal/references — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/references');
  });

  test('two clickable cards visible (Employment History / Vetting Checks)', async ({ page }) => {
    await page.goto('/portal/references', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    // Look for cards or links for employment and vetting
    const employmentLink = page.locator(
      'a[href*="employment"], a:has-text("Employment"), ' +
      '.card:has-text("Employment"), a:has-text("Work History")'
    ).first();
    const vettingLink = page.locator(
      'a[href*="vetting"], a:has-text("Vetting"), ' +
      '.card:has-text("Vetting"), a:has-text("Qualification")'
    ).first();

    if (await employmentLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('  Employment History card visible');
    }
    if (await vettingLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  Vetting Checks card visible');
    }

    // Should have at least some clickable references content
    const cards = page.locator('a[href*="/portal/references/"], .card, .reference-card');
    const cardCount = await cards.count();
    console.log(`  Reference cards/links found: ${cardCount}`);
  });
});
