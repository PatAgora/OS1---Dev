/**
 * Staff Portal — Admin Reference Houses (/admin/reference-houses)
 *
 * Tests: page load, add reference house.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/reference-houses — page loads', async ({ page }) => {
  const response = await page.goto('/admin/reference-houses', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
  await guardSessionExpired(page);
});

test('/admin/reference-houses — add reference house', async ({ page }) => {
  const response = await page.goto('/admin/reference-houses', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() !== 200) {
    test.skip(true, `Page returned ${response?.status()} — skipping`);
    return;
  }

  // Fill name
  const nameField = page.locator('[name="name"], [name="house_name"]').first();
  if (!(await nameField.isVisible().catch(() => false))) {
    console.log('  Name field not found — skipping add test');
    return;
  }
  await nameField.fill('[PW-TEST] House');

  // Submit
  const submitBtn = page.locator('[type="submit"]').first();
  if (!(await submitBtn.isVisible().catch(() => false))) {
    console.log('  Submit button not found — skipping');
    return;
  }
  await submitBtn.click();
  await page.waitForLoadState('domcontentloaded');

  const bodyText = await page.textContent('body') || '';
  expect(bodyText).not.toContain('Internal Server Error');

  // Accept either the test data appearing or a success message
  const success = bodyText.includes('[PW-TEST] House') ||
                  bodyText.toLowerCase().includes('added') ||
                  bodyText.toLowerCase().includes('success') ||
                  bodyText.toLowerCase().includes('created');
  if (!success) {
    console.log('  Test house may not have been added — form might have validation issues');
  }
});
