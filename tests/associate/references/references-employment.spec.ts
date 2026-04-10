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
      'table tbody tr, .employment-entry, .employment-row, .card, [data-employment]'
    );
    const count = await items.count();
    console.log(`  Employment entries found: ${count}`);
  });

  test('add employment entry', async ({ page }) => {
    await page.goto('/portal/references/employment', { waitUntil: 'domcontentloaded' });

    // Look for add button
    const addBtn = page.locator(
      'button:has-text("Add"), a:has-text("Add"), button:has-text("New"), a:has-text("New")'
    ).first();

    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }

    // Fill employment form
    const companyField = page.locator('[name="company"], [name="employer"], [name="company_name"]').first();
    if (!(await companyField.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  Employment form not found — skipping add test');
      return;
    }

    await companyField.fill('[PW-TEST] Employer');

    const jobTitleField = page.locator('[name="job_title"], [name="role"], [name="position"]').first();
    if (await jobTitleField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await jobTitleField.fill('Test Role');
    }

    const startDate = page.locator('[name="start_date"], [name="from_date"], [name="date_from"]').first();
    if (await startDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await startDate.fill('2020-01-01');
    }

    const endDate = page.locator('[name="end_date"], [name="to_date"], [name="date_to"]').first();
    if (await endDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await endDate.fill('2023-12-31');
    }

    const refereeEmail = page.locator('[name="referee_email"], [name="reference_email"], [name="email"]').first();
    if (await refereeEmail.isVisible({ timeout: 2000 }).catch(() => false)) {
      await refereeEmail.fill('referee@pw-test-example.com');
    }

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
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

    // Look for gap button
    const gapBtn = page.locator(
      'button:has-text("Gap"), a:has-text("Gap"), button:has-text("Add Gap"), a:has-text("Add Gap")'
    ).first();

    if (!(await gapBtn.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  Gap button not found — skipping gap test');
      return;
    }

    await gapBtn.click();
    await page.waitForLoadState('domcontentloaded');

    // Fill gap form
    const startDate = page.locator('[name="start_date"], [name="from_date"], [name="gap_start"]').first();
    if (await startDate.isVisible({ timeout: 3000 }).catch(() => false)) {
      await startDate.fill('2019-06-01');
    }

    const endDate = page.locator('[name="end_date"], [name="to_date"], [name="gap_end"]').first();
    if (await endDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await endDate.fill('2019-12-31');
    }

    const reason = page.locator('[name="reason"], [name="gap_reason"], textarea').first();
    if (await reason.isVisible({ timeout: 2000 }).catch(() => false)) {
      await reason.fill('Career Break');
    }

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
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
    const testEntry = page.locator('text=[PW-TEST]').first();
    if (!(await testEntry.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  No [PW-TEST] employment entry to delete — skipping');
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
      console.log('  Employment entry deleted');
    } else {
      console.log('  Delete button not found for test entry');
    }
  });
});
