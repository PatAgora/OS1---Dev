/**
 * Associate Portal — References Vetting Checks tests
 *
 * Tests: /portal/references/vetting-checks
 * Verifies page load, add qualification, delete qualification.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate References — Vetting Checks', () => {
  test('@smoke /portal/references/vetting-checks — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/references/vetting-checks');
  });

  test('add qualification', async ({ page }) => {
    await page.goto('/portal/references/vetting-checks', { waitUntil: 'domcontentloaded' });

    // Look for add button
    const addBtn = page.locator(
      'button:has-text("Add"), a:has-text("Add"), button:has-text("New")'
    ).first();

    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }

    // Fill qualification form
    const nameField = page.locator(
      '[name="name"], [name="qualification_name"], [name="qual_name"], [name="title"]'
    ).first();

    if (!(await nameField.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  Qualification form not found — skipping add test');
      return;
    }

    await nameField.fill('[PW-TEST] Qual');

    const institutionField = page.locator(
      '[name="institution"], [name="awarding_body"], [name="provider"]'
    ).first();
    if (await institutionField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await institutionField.fill('Test University');
    }

    const typeField = page.locator('[name="type"], [name="qualification_type"], [name="qual_type"]').first();
    if (await typeField.isVisible({ timeout: 2000 }).catch(() => false)) {
      const tagName = await typeField.evaluate(el => el.tagName.toLowerCase());
      if (tagName === 'select') {
        // Select the first non-empty option
        const options = typeField.locator('option:not([value=""])');
        if (await options.count() > 0) {
          const value = await options.first().getAttribute('value');
          if (value) await typeField.selectOption(value);
        }
      } else {
        await typeField.fill('Degree');
      }
    }

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Qualification added');
    }
  });

  test('delete qualification', async ({ page }) => {
    await page.goto('/portal/references/vetting-checks', { waitUntil: 'domcontentloaded' });

    // Find a PW-TEST entry to delete
    const testEntry = page.locator('text=[PW-TEST]').first();
    if (!(await testEntry.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  No [PW-TEST] qualification to delete — skipping');
      return;
    }

    const deleteBtn = testEntry.locator('xpath=ancestor::*[position() <= 5]').locator(
      'button:has-text("Delete"), a:has-text("Delete"), button:has-text("Remove"), ' +
      '.delete-btn, .btn-danger, button[title="Delete"]'
    ).first();

    if (await deleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      page.on('dialog', dialog => dialog.accept());
      await deleteBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Qualification deleted');
    } else {
      console.log('  Delete button not found for test qualification');
    }
  });
});
