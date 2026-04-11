/**
 * Deep Tests — SQL Injection Resistance
 *
 * Submits classic SQL injection payloads into search/filter fields and
 * verifies the app does not crash or expose data.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { guardSessionExpired } from '../../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

const SQL_PAYLOADS = [
  `'; DROP TABLE users; --`,
  `" OR 1=1 --`,
  `Robert'); DROP TABLE applications;--`,
];

async function assertNoServerError(page: any): Promise<void> {
  const body = await page.textContent('body');
  expect(body).not.toContain('Internal Server Error');
  expect(body).not.toContain('Traceback (most recent call last)');
  expect(body).not.toContain('OperationalError');
  expect(body).not.toContain('ProgrammingError');
}

test.describe('SQL Injection Resistance', () => {

  for (const payload of SQL_PAYLOADS) {
    test(`/applications search resists: ${payload.substring(0, 30)}...`, async ({ page }) => {
      await page.goto('/applications', { waitUntil: 'domcontentloaded' });
      await guardSessionExpired(page);

      const searchInput = page.locator('input[name="search"], input[name="q"], input[type="search"], input[placeholder*="Search"]').first();
      if (await searchInput.count() === 0) {
        // Try URL parameter approach
        await page.goto(`/applications?search=${encodeURIComponent(payload)}`, { waitUntil: 'domcontentloaded' });
      } else {
        await searchInput.fill(payload);
        await searchInput.press('Enter');
        await page.waitForLoadState('domcontentloaded');
      }

      await assertNoServerError(page);

      // Verify page still works on reload
      const response = await page.goto('/applications', { waitUntil: 'domcontentloaded' });
      expect(response?.status()).toBeLessThan(500);
      await assertNoServerError(page);
    });
  }

  for (const payload of SQL_PAYLOADS) {
    test(`/resource-pool search resists: ${payload.substring(0, 30)}...`, async ({ page }) => {
      await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
      await guardSessionExpired(page);

      const searchInput = page.locator('input[name="search"], input[name="q"], input[type="search"], input[placeholder*="Search"]').first();
      if (await searchInput.count() === 0) {
        await page.goto(`/resource-pool?search=${encodeURIComponent(payload)}`, { waitUntil: 'domcontentloaded' });
      } else {
        await searchInput.fill(payload);
        await searchInput.press('Enter');
        await page.waitForLoadState('domcontentloaded');
      }

      await assertNoServerError(page);

      // Verify the page still works
      const response = await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
      expect(response?.status()).toBeLessThan(500);
    });
  }

  for (const payload of SQL_PAYLOADS) {
    test(`/admin/reference-contacts search resists: ${payload.substring(0, 30)}...`, async ({ page }) => {
      const response = await page.goto(
        `/admin/reference-contacts?search=${encodeURIComponent(payload)}`,
        { waitUntil: 'domcontentloaded' }
      );
      await guardSessionExpired(page);

      // Allow 404 if route doesn't exist, but not 500
      if (response?.status() === 404) {
        test.skip(true, '/admin/reference-contacts route does not exist');
        return;
      }
      expect(response?.status()).toBeLessThan(500);
      await assertNoServerError(page);

      // Verify page still works
      const response2 = await page.goto('/admin/reference-contacts', { waitUntil: 'domcontentloaded' });
      if (response2?.status() !== 404) {
        expect(response2?.status()).toBeLessThan(500);
      }
    });
  }

  for (const payload of SQL_PAYLOADS) {
    test(`/engagements search resists: ${payload.substring(0, 30)}...`, async ({ page }) => {
      await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
      await guardSessionExpired(page);

      const searchInput = page.locator('input[name="search"], input[name="q"], input[type="search"], input[placeholder*="Search"]').first();
      if (await searchInput.count() > 0) {
        await searchInput.fill(payload);
        await searchInput.press('Enter');
        await page.waitForLoadState('domcontentloaded');
        await assertNoServerError(page);
      } else {
        // Try via URL parameter
        const response = await page.goto(
          `/engagements?search=${encodeURIComponent(payload)}`,
          { waitUntil: 'domcontentloaded' }
        );
        expect(response?.status()).toBeLessThan(500);
        await assertNoServerError(page);
      }

      // Verify page still functional after injection
      const response = await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
      expect(response?.status()).toBeLessThan(500);
    });
  }
});
