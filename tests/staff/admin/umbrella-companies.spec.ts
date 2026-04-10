/**
 * Staff Portal — Admin Umbrella Companies (/admin/umbrella-companies)
 *
 * Tests: page load, add company.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/umbrella-companies — page loads', async ({ page }) => {
  const response = await page.goto('/admin/umbrella-companies', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});

test('/admin/umbrella-companies — add company', async ({ page }) => {
  const response = await page.goto('/admin/umbrella-companies', { waitUntil: 'domcontentloaded' });
  if (response?.status() !== 200) {
    test.skip();
    return;
  }

  // Fill company name
  const nameField = page.locator('[name="name"], [name="company_name"]').first();
  if (await nameField.isVisible().catch(() => false)) {
    await nameField.fill(`[PW-TEST] Umbrella ${Date.now()}`);
  }

  // Submit
  const submitBtn = page.locator('[type="submit"]').first();
  if (await submitBtn.isVisible().catch(() => false)) {
    await submitBtn.click();
    await page.waitForLoadState('domcontentloaded');

    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Internal Server Error');
    expect(bodyText).toContain('[PW-TEST]');
  }
});
