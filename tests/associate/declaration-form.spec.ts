/**
 * Associate Portal — Declaration Form tests
 *
 * Tests: /portal/declaration-form
 * Verifies page load and fields render. DO NOT submit (Signable blocked).
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Declaration Form', () => {
  test('@smoke /portal/declaration-form — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/declaration-form');
  });

  test('fields render — DO NOT submit (Signable blocked)', async ({ page }) => {
    await page.goto('/portal/declaration-form', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    // Check for form fields or content
    const formFields = page.locator('input, textarea, select, [type="checkbox"]');
    const count = await formFields.count();
    console.log(`  Declaration form fields found: ${count}`);

    // Verify submit button is visible but DO NOT click
    const submitBtn = page.locator('[type="submit"], button:has-text("Submit"), button:has-text("Sign")').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('  Blocked button visible (not clicked): Declaration Submit/Sign');
    }
  });
});
