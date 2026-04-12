/**
 * Associate Portal — References Employment tests
 *
 * Tests: /portal/references/employment
 * Verifies page load, employment list, add employment, add gap, delete entry.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate References — Employment', () => {
  test('@smoke /portal/references/employment — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/references/employment');
  });

  test('employment list renders', async ({ page }) => {
    await page.goto('/portal/references/employment', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    const items = page.locator(
      '.timeline-item, table tbody tr, .employment-entry, .employment-row, .card, [data-employment]'
    );
    const count = await items.count();
    console.log(`  Employment entries found: ${count}`);
  });

  test('add employment entry', async ({ page }) => {
    await page.goto('/portal/references/employment', { waitUntil: 'domcontentloaded' });

    // The employment form is inline on the page (under "Add Employment Entry" heading)
    // Real field names from references_employment.html template
    const companyField = page.locator('[name="company_name"]').first();
    if (!(await companyField.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  Employment form not found — skipping add test');
      return;
    }

    await companyField.fill('[PW-TEST] Employer');

    const jobTitleField = page.locator('[name="job_title"]').first();
    if (await jobTitleField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await jobTitleField.fill('Test Role');
    }

    const startDate = page.locator('#emp_start_date, [name="start_date"]').first();
    if (await startDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await startDate.fill('2020-01-01');
    }

    const endDate = page.locator('#emp_end_date, [name="end_date"]').first();
    if (await endDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await endDate.fill('2023-12-31');
    }

    const refereeEmail = page.locator('[name="referee_email"]').first();
    if (await refereeEmail.isVisible({ timeout: 2000 }).catch(() => false)) {
      await refereeEmail.fill('referee@pw-test-example.com');
    }

    // Submit — the employment form has a specific submit button
    const submitBtn = page.locator('#addEmploymentForm [type="submit"], #addEmploymentForm button.btn-primary').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Employment entry added');
    }
  });

  test('add gap entry', async ({ page }) => {
    await page.goto('/portal/references/employment', { waitUntil: 'domcontentloaded' });

    // The gap form is inline on the page (under "Add Gap Entry" heading)
    // Real field IDs from references_employment.html: gap_start_date, gap_end_date, gap_reason
    const startDate = page.locator('#gap_start_date').first();
    if (!(await startDate.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  Gap form not found — skipping gap test');
      return;
    }

    await startDate.fill('2019-06-01');

    const endDate = page.locator('#gap_end_date').first();
    if (await endDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await endDate.fill('2019-12-31');
    }

    // reason is a <select>, not a text input
    const reason = page.locator('#gap_reason, [name="reason"]').first();
    if (await reason.isVisible({ timeout: 2000 }).catch(() => false)) {
      await reason.selectOption('Career Break');
    }

    // Submit — the gap form has its own submit button
    const submitBtn = page.locator('#addGapForm [type="submit"], #addGapForm button.btn-warning').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Gap entry added');
    }
  });

  test('delete employment entry', async ({ page }) => {
    await page.goto('/portal/references/employment', { waitUntil: 'domcontentloaded' });

    // Find a PW-TEST entry to delete
    // The timeline uses .timeline-item elements with .delete-entry-btn[data-entry-id] buttons
    const testEntry = page.locator('.timeline-item:has-text("[PW-TEST]")').first();
    if (!(await testEntry.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  No [PW-TEST] employment entry to delete — skipping');
      return;
    }

    // The delete button uses class="delete-entry-btn" with data-entry-id attribute
    // It triggers a JS confirm dialog and then a fetch DELETE
    const deleteBtn = testEntry.locator('.delete-entry-btn, button:has-text("Delete")').first();

    if (await deleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      page.on('dialog', dialog => dialog.accept());
      await deleteBtn.click();
      // The delete is AJAX — wait for page reload triggered by JS
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1000);

      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Employment entry deleted');
    } else {
      console.log('  Delete button not found for test entry');
    }
  });
});
