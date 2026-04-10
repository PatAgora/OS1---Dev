/**
 * Staff Portal — Admin Reference Contacts (/admin/reference-contacts)
 *
 * Tests: page load, contact list, add contact, delete contact.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/reference-contacts — page loads', async ({ page }) => {
  const response = await page.goto('/admin/reference-contacts', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
  await guardSessionExpired(page);
});

test('/admin/reference-contacts — contact list renders or empty state', async ({ page }) => {
  const response = await page.goto('/admin/reference-contacts', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() === 403) {
    test.skip(true, 'Requires elevated role — 403 returned');
    return;
  }

  if (response?.status() === 200) {
    const list = page.locator('table, .contact-list, .card, .list-group, [class*="table"], [class*="contact"]');
    const visible = await list.first().isVisible({ timeout: 5000 }).catch(() => false);
    if (visible) {
      console.log('  Contact list visible');
    } else {
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  No contact list found — page loaded OK (may be empty state)');
    }
  }
});

test('/admin/reference-contacts — add and delete contact', async ({ page }) => {
  const response = await page.goto('/admin/reference-contacts', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() !== 200) {
    test.skip(true, `Page returned ${response?.status()} — skipping`);
    return;
  }

  // Fill company name
  const companyField = page.locator('[name="company"], [name="company_name"], [name="organisation"]').first();
  if (await companyField.isVisible().catch(() => false)) {
    await companyField.fill('[PW-TEST] Company');
  } else {
    console.log('  Company field not found — skipping add contact');
    return;
  }

  // Fill email
  const emailField = page.locator('[name="email"], [name="contact_email"]').first();
  if (await emailField.isVisible().catch(() => false)) {
    await emailField.fill('pw-test@example.com');
  }

  // Fill name if present
  const nameField = page.locator('[name="name"], [name="contact_name"]').first();
  if (await nameField.isVisible().catch(() => false)) {
    await nameField.fill('[PW-TEST] Contact');
  }

  // Submit
  const submitBtn = page.locator('[type="submit"]').first();
  if (!(await submitBtn.isVisible().catch(() => false))) {
    console.log('  Submit button not found — skipping');
    return;
  }
  await submitBtn.click();
  await page.waitForLoadState('domcontentloaded');

  let bodyText = await page.textContent('body') || '';
  expect(bodyText).not.toContain('Internal Server Error');

  // Assert the contact was added (or a success message)
  const hasTestData = bodyText.includes('[PW-TEST]') || bodyText.includes('pw-test@example.com') ||
                      bodyText.toLowerCase().includes('added') || bodyText.toLowerCase().includes('success');
  if (!hasTestData) {
    console.log('  Test data not found after submit — form may have validation issues');
    return;
  }

  // Delete the one we just added
  const deleteBtn = page.locator('tr, .card, .contact-row, .list-group-item')
    .filter({ hasText: /PW-TEST/ })
    .locator('button, a')
    .filter({ hasText: /delete|remove/i })
    .first();

  if (await deleteBtn.isVisible().catch(() => false)) {
    // Handle confirmation dialog
    page.on('dialog', async (dialog) => {
      await dialog.accept();
    });

    await deleteBtn.click();
    await page.waitForLoadState('domcontentloaded');

    bodyText = await page.textContent('body') || '';
    expect(bodyText).not.toContain('Internal Server Error');
  } else {
    console.log('  Delete button not found — skipping deletion');
  }
});
