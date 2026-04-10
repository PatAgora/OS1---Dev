/**
 * Staff Portal — Opportunities tests
 *
 * Tests: /opportunities or equivalent
 * Verifies page load and create form if present.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Opportunities', () => {
  test('@smoke /opportunities — loads without 500', async ({ page }) => {
    const response = await page.goto('/opportunities', { waitUntil: 'domcontentloaded' });
    const status = response?.status() ?? 0;
    expect(status).toBeLessThan(500);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback (most recent call last)');
    console.log(`  /opportunities loaded with status ${status}`);
  });

  test('create opportunity form — fill and submit', async ({ page }) => {
    await page.goto('/opportunities', { waitUntil: 'domcontentloaded' });

    // Look for a create/add button or an inline form
    const createBtn = page.locator(
      'a:has-text("New"), a:has-text("Create"), a:has-text("Add"), ' +
      'button:has-text("New"), button:has-text("Create"), button:has-text("Add")'
    ).first();

    const formOnPage = page.locator('form').first();
    let hasForm = false;

    if (await createBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await createBtn.click();
      await page.waitForLoadState('domcontentloaded');
      hasForm = true;
    } else if (await formOnPage.isVisible({ timeout: 2000 }).catch(() => false)) {
      hasForm = true;
    }

    if (!hasForm) {
      console.log('  No create form or button found — skipping creation test');
      return;
    }

    // Fill the form fields
    const clientField = page.locator('[name="client"], [name="client_name"]').first();
    if (await clientField.isVisible({ timeout: 3000 }).catch(() => false)) {
      await clientField.fill('[PW-TEST] Opp Client');
    }

    const roleField = page.locator('[name="role"], [name="role_title"], [name="title"]').first();
    if (await roleField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await roleField.fill('[PW-TEST] Test Role');
    }

    const valueField = page.locator('[name="value"], [name="amount"], [name="estimated_value"]').first();
    if (await valueField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await valueField.fill('50000');
    }

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      expect(body).not.toContain('Traceback (most recent call last)');

      // Check for success indication
      const hasSuccess = body?.includes('[PW-TEST] Opp Client') ||
        body?.includes('success') || body?.includes('created') || body?.includes('Success');
      console.log(`  Opportunity creation — success indicators found: ${hasSuccess}`);
    }
  });
});
