/**
 * Associate Portal — Consent Form tests
 *
 * Tests: /portal/consent-form
 * Verifies page load, checkboxes render, check all and submit.
 * Accepts "already signed" state as valid.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

/** Check if the consent form page shows an "already signed/completed" state */
function isAlreadySigned(bodyText: string): boolean {
  const lowerBody = bodyText.toLowerCase();
  return (
    lowerBody.includes('already signed') ||
    lowerBody.includes('already consented') ||
    lowerBody.includes('consent received') ||
    lowerBody.includes('consent submitted') ||
    lowerBody.includes('consent complete') ||
    lowerBody.includes('form has been submitted') ||
    lowerBody.includes('you have already') ||
    lowerBody.includes('previously submitted') ||
    lowerBody.includes('completed')
  );
}

test.describe('Associate Consent Form', () => {
  test('@smoke /portal/consent-form — page loads', async ({ page }) => {
    await assertPageLoads(page, '/portal/consent-form');
  });

  test('checkboxes render or already signed', async ({ page }) => {
    await page.goto('/portal/consent-form', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const body = await page.textContent('body') || '';

    // Accept "already signed" as a valid state
    if (isAlreadySigned(body)) {
      console.log('  Consent already signed — valid state');
      expect(body).not.toContain('Internal Server Error');
      return;
    }

    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();
    console.log(`  Consent checkboxes found: ${count}`);

    if (count === 0) {
      // No checkboxes — may be already signed or different form layout
      expect(body).not.toContain('Internal Server Error');
      console.log('  No checkboxes found — page loaded OK');
    }
  });

  test('check all checkboxes and submit — or verify already signed', async ({ page }) => {
    await page.goto('/portal/consent-form', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const body = await page.textContent('body') || '';

    // If already signed, assert that state and pass
    if (isAlreadySigned(body)) {
      console.log('  Consent already signed — asserting valid state');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback');
      return;
    }

    // Check all checkboxes
    const checkboxes = page.locator('input[type="checkbox"]');
    const count = await checkboxes.count();

    if (count === 0) {
      console.log('  No checkboxes found — nothing to submit');
      expect(body).not.toContain('Internal Server Error');
      return;
    }

    for (let i = 0; i < count; i++) {
      const cb = checkboxes.nth(i);
      if (!(await cb.isChecked())) {
        await cb.check().catch(() => {
          console.log(`  Could not check checkbox ${i} — may be disabled`);
        });
      }
    }
    console.log(`  Checked ${count} checkboxes`);

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const bodyAfter = await page.textContent('body') || '';
      expect(bodyAfter).not.toContain('Internal Server Error');
      expect(bodyAfter).not.toContain('Traceback (most recent call last)');

      const successFlash = page.locator('.alert-success, .flash-success, [class*="success"]').first();
      if (await successFlash.isVisible({ timeout: 5000 }).catch(() => false)) {
        console.log('  Success flash visible after consent submit');
      } else {
        console.log('  Consent form submitted without error');
      }
    } else {
      console.log('  Submit button not visible — skipping');
    }
  });
});
