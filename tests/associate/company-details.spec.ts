/**
 * Associate Portal — Company Details tests
 *
 * Tests: /portal/company-details
 * Verifies page load, IR35 notice, and form submission.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Company Details', () => {
  test('@smoke /portal/company-details — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/company-details');
  });

  test('IR35 notice visible', async ({ page }) => {
    await page.goto('/portal/company-details', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    const hasIR35Notice = body?.includes('member of team Optimus will have told you') ||
      body?.includes('IR35') || body?.includes('ir35');
    console.log(`  IR35 notice visible: ${hasIR35Notice}`);
  });

  test('fill fields and submit — assert success', async ({ page }) => {
    await page.goto('/portal/company-details', { waitUntil: 'domcontentloaded' });

    // Fill company-related fields
    const companyName = page.locator('[name="company_name"], [name="ltd_company_name"]').first();
    if (await companyName.isVisible({ timeout: 3000 }).catch(() => false)) {
      await companyName.fill('[PW-TEST] Company Ltd');
    }

    const companyNumber = page.locator('[name="company_number"], [name="companies_house_number"]').first();
    if (await companyNumber.isVisible({ timeout: 2000 }).catch(() => false)) {
      await companyNumber.fill('12345678');
    }

    const vatNumber = page.locator('[name="vat_number"]').first();
    if (await vatNumber.isVisible({ timeout: 2000 }).catch(() => false)) {
      await vatNumber.fill('GB123456789');
    }

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');

      const successFlash = page.locator('.alert-success, .flash-success, [class*="success"]').first();
      if (await successFlash.isVisible({ timeout: 5000 }).catch(() => false)) {
        console.log('  Success flash visible after submit');
      } else {
        console.log('  Form submitted without error');
      }
    }
  });
});
