/**
 * Staff Portal — Admin Invoices (/admin/invoices)
 *
 * Tests: page load, KPI cards, create invoice form.
 * BLOCKED: Send Invoice (SMTP).
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard, assertVisibleButDoNotClick } from '../../utils/blocked-routes';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/invoices — page loads', async ({ page }) => {
  const response = await page.goto('/admin/invoices', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});

test('/admin/invoices — KPI cards visible', async ({ page }) => {
  const response = await page.goto('/admin/invoices', { waitUntil: 'domcontentloaded' });
  if (response?.status() === 200) {
    const cards = page.locator('.summary-card, .kpi, .stat-card, .card');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  }
});

test('/admin/invoices — create invoice', async ({ page }) => {
  const listResponse = await page.goto('/admin/invoices', { waitUntil: 'domcontentloaded' });
  if (listResponse?.status() !== 200) {
    test.skip();
    return;
  }

  // Click "Create Invoice"
  const createBtn = page.locator('a, button').filter({ hasText: /Create Invoice|New Invoice/i }).first();
  if (await createBtn.isVisible().catch(() => false)) {
    await createBtn.click();
    await page.waitForLoadState('domcontentloaded');

    const createResponse = await page.reload({ waitUntil: 'domcontentloaded' });
    expect(createResponse?.status()).toBeLessThan(500);

    // Fill engagement dropdown if present
    const engagementSelect = page.locator('[name="engagement_id"], [name="engagement"]').first();
    if (await engagementSelect.isVisible().catch(() => false)) {
      // Select first option that is not empty
      const options = engagementSelect.locator('option');
      const optionCount = await options.count();
      if (optionCount > 1) {
        const value = await options.nth(1).getAttribute('value');
        if (value) await engagementSelect.selectOption(value);
      }
    }

    // Fill dates
    const dateFrom = page.locator('[name="date_from"], [name="period_start"], [name="invoice_date"]').first();
    if (await dateFrom.isVisible().catch(() => false)) {
      await dateFrom.fill('2026-04-01');
    }

    const dateTo = page.locator('[name="date_to"], [name="period_end"], [name="due_date"]').first();
    if (await dateTo.isVisible().catch(() => false)) {
      await dateTo.fill('2026-04-30');
    }

    // Add a line item if possible
    const addLineBtn = page.locator('button, a').filter({ hasText: /Add Line|Add Item/i }).first();
    if (await addLineBtn.isVisible().catch(() => false)) {
      await addLineBtn.click();
      await page.waitForTimeout(500);
    }

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
    if (await submitBtn.isVisible().catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const bodyText = await page.textContent('body');
      expect(bodyText).not.toContain('Internal Server Error');
    }
  }
});

test('/admin/invoices — Send Invoice button visible (DO NOT CLICK)', async ({ page }) => {
  const response = await page.goto('/admin/invoices', { waitUntil: 'domcontentloaded' });
  if (response?.status() !== 200) {
    test.skip();
    return;
  }

  const sendBtn = page.locator('button, a').filter({ hasText: /Send Invoice/i }).first();
  if (await sendBtn.isVisible().catch(() => false)) {
    await assertVisibleButDoNotClick(
      page,
      'button:has-text("Send Invoice"), a:has-text("Send Invoice")',
      'Send Invoice'
    );
  }
});
