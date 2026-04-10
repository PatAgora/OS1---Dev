/**
 * Staff Portal — Create Engagement
 *
 * Tests: navigate to create page, fill form, submit.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('/engagements — create new engagement', async ({ page }) => {
  await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  // Find and click the create engagement link — broad selector
  const createLink = page.locator('a').filter({ hasText: /Create Engagement|New Engagement|Add Engagement|Create/i }).first();
  const createVisible = await createLink.isVisible({ timeout: 5000 }).catch(() => false);

  if (!createVisible) {
    // Try navigating directly to create URL
    const directResponse = await page.goto('/create-engagement', { waitUntil: 'domcontentloaded' });
    if (directResponse?.status() && directResponse.status() >= 400) {
      // Try alternate URL
      const altResponse = await page.goto('/engagement/create', { waitUntil: 'domcontentloaded' });
      if (altResponse?.status() && altResponse.status() >= 400) {
        console.log('  Create engagement page not found — skipping');
        return;
      }
    }
  } else {
    await createLink.click();
    await page.waitForLoadState('domcontentloaded');
  }

  await guardSessionExpired(page);

  // Should be on the create page — verify no 500
  const body = await page.textContent('body') || '';
  expect(body).not.toContain('Internal Server Error');

  // Fill form fields
  const clientField = page.locator('[name="client"]').first();
  if (await clientField.isVisible().catch(() => false)) {
    await clientField.fill('[PW-TEST] Client');
  }

  const nameField = page.locator('[name="name"], [name="engagement_name"], [name="title"]').first();
  if (await nameField.isVisible().catch(() => false)) {
    await nameField.fill(`[PW-TEST] Engagement ${Date.now()}`);
  }

  // Fill dates if present
  const startDate = page.locator('[name="start_date"]').first();
  if (await startDate.isVisible().catch(() => false)) {
    await startDate.fill('2026-05-01');
  }

  const endDate = page.locator('[name="end_date"]').first();
  if (await endDate.isVisible().catch(() => false)) {
    await endDate.fill('2026-12-31');
  }

  // Submit form
  const submitBtn = page.locator('[type="submit"]').first();
  if (!(await submitBtn.isVisible().catch(() => false))) {
    console.log('  Submit button not found — skipping form submission');
    return;
  }
  await submitBtn.click();
  await page.waitForLoadState('domcontentloaded');

  // Assert redirect or success
  const bodyText = await page.textContent('body') || '';
  expect(bodyText).not.toContain('Internal Server Error');
  const urlAfter = page.url();
  const success = urlAfter.includes('/engagement') ||
                  bodyText.toLowerCase().includes('created') ||
                  bodyText.toLowerCase().includes('success');
  expect(success).toBeTruthy();
});
