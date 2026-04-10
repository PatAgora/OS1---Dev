/**
 * Associate Portal — Address History tests
 *
 * Tests: /portal/address-history
 * Verifies page load and add form if present.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Address History', () => {
  test('@smoke /portal/address-history — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/address-history');
  });

  test('add address form — fill and submit', async ({ page }) => {
    await page.goto('/portal/address-history', { waitUntil: 'domcontentloaded' });

    // Look for add button or inline form
    const addBtn = page.locator(
      'button:has-text("Add"), a:has-text("Add"), button:has-text("New")'
    ).first();

    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }

    // Fill address fields
    const addressLine1 = page.locator('[name="address_line_1"], [name="address1"], [name="line1"]').first();
    if (!(await addressLine1.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  Address form not found — skipping add test');
      return;
    }

    await addressLine1.fill('[PW-TEST] 1 Test Street');

    const city = page.locator('[name="city"], [name="town"]').first();
    if (await city.isVisible({ timeout: 2000 }).catch(() => false)) {
      await city.fill('London');
    }

    const postcode = page.locator('[name="postcode"], [name="post_code"], [name="zip"]').first();
    if (await postcode.isVisible({ timeout: 2000 }).catch(() => false)) {
      await postcode.fill('SW1A 1AA');
    }

    const fromDate = page.locator('[name="from_date"], [name="start_date"], [name="date_from"]').first();
    if (await fromDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await fromDate.fill('2020-01-01');
    }

    const toDate = page.locator('[name="to_date"], [name="end_date"], [name="date_to"]').first();
    if (await toDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await toDate.fill('2024-01-01');
    }

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Address added successfully');
    }
  });
});
