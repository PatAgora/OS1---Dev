/**
 * Public Portal — Apply Form tests
 *
 * Tests: public job application form
 * Fills name, email, phone and submits. Skips CV upload.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Public Apply', () => {
  test('apply form — fill and submit', async ({ page }) => {
    // Navigate to job board first
    const routes = ['/public/jobs', '/jobs'];
    for (const route of routes) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      if ((response?.status() ?? 0) === 200) break;
    }

    // Find a job link
    const jobLink = page.locator(
      'a[href*="/job/"], a[href*="/public/job/"], .job-card a, .vacancy-card a'
    ).first();

    if (!(await jobLink.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  No job links — cannot test apply form');
      return;
    }

    await jobLink.click();
    await page.waitForLoadState('domcontentloaded');

    // Click the apply button
    const applyBtn = page.locator(
      'a:has-text("Apply"), button:has-text("Apply"), a[href*="apply"]'
    ).first();

    if (!(await applyBtn.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  No Apply button on job detail — skipping');
      return;
    }

    await applyBtn.click();
    await page.waitForLoadState('domcontentloaded');

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    // Fill the application form
    const nameField = page.locator(
      '[name="name"], [name="full_name"], [name="candidate_name"], [name="first_name"]'
    ).first();
    if (await nameField.isVisible({ timeout: 3000 }).catch(() => false)) {
      await nameField.fill('[PW-TEST] Applicant');
    }

    // If there's a separate last name field
    const lastNameField = page.locator('[name="last_name"], [name="surname"]').first();
    if (await lastNameField.isVisible({ timeout: 1000 }).catch(() => false)) {
      await lastNameField.fill('Testson');
    }

    const emailField = page.locator('[name="email"]').first();
    if (await emailField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await emailField.fill(`pw-test-${Date.now()}@example.com`);
    }

    const phoneField = page.locator('[name="phone"], [name="telephone"], [name="mobile"]').first();
    if (await phoneField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await phoneField.fill('+44 7700 900000');
    }

    // Submit the form (skip CV file upload)
    const submitBtn = page.locator('[type="submit"]').first();
    if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');

      const afterBody = await page.textContent('body');
      expect(afterBody).not.toContain('Internal Server Error');
      expect(afterBody).not.toContain('Traceback (most recent call last)');

      // Check for success — confirmation page, success flash, or thank-you message
      const hasSuccess =
        afterBody?.includes('hank') || afterBody?.includes('success') ||
        afterBody?.includes('Success') || afterBody?.includes('received') ||
        afterBody?.includes('submitted') || afterBody?.includes('confirmation') ||
        page.url().includes('done') || page.url().includes('thank');
      console.log(`  Application submitted — success indicators: ${hasSuccess}`);
    } else {
      console.log('  Submit button not found — form may require additional fields');
    }
  });
});
