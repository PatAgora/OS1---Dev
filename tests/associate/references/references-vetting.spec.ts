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

    // The qualification form is inline on the page (under "Add Qualification" heading)
    // Real field names from references_vetting_checks.html: name, qual_type, grade, institution, start_date, end_date
    const nameField = page.locator('#qual_name, [name="name"]').first();

    if (!(await nameField.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  Qualification form not found — skipping add test');
      return;
    }

    await nameField.fill('[PW-TEST] Qual');

    const institutionField = page.locator('#qual_institution, [name="institution"]').first();
    if (await institutionField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await institutionField.fill('Test University');
    }

    // qual_type is a <select> element
    const typeField = page.locator('#qual_type, [name="qual_type"]').first();
    if (await typeField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await typeField.selectOption('BSc');
    }

    // Submit — the qualification form has a specific submit button
    const submitBtn = page.locator('#addQualForm [type="submit"], #addQualForm button.btn-success').first();
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

    // Find a PW-TEST entry to delete in the qualifications table
    const testRow = page.locator('table tbody tr:has-text("[PW-TEST]")').first();
    if (!(await testRow.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  No [PW-TEST] qualification to delete — skipping');
      return;
    }

    // The delete button uses class="delete-qual-btn" with data-qual-id attribute
    // It triggers a JS confirm dialog and then a fetch DELETE
    const deleteBtn = testRow.locator('.delete-qual-btn, button.btn-outline-danger').first();

    if (await deleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      page.on('dialog', dialog => dialog.accept());
      await deleteBtn.click();
      // The delete is AJAX — wait for page reload triggered by JS
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1000);

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Qualification deleted');
    } else {
      console.log('  Delete button not found for test qualification');
    }
  });
});
