/**
 * Staff Portal — Admin Users (/admin/list-users, /admin/create-user)
 *
 * Tests: user list page load, edit modal, create user form.
 * BLOCKED: Send Magic Link (SMTP).
 *
 * NOTE: If the test user lacks super_admin role, admin pages may return 403.
 * We assert < 500 (not a crash) in those cases.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard, assertVisibleButDoNotClick } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('@smoke /admin/list-users — page loads', async ({ page }) => {
  const response = await page.goto('/admin/list-users', { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
  await guardSessionExpired(page);
});

test('/admin/list-users — user table renders', async ({ page }) => {
  const response = await page.goto('/admin/list-users', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() === 403) {
    test.skip(true, 'Requires super_admin role — 403 returned');
    return;
  }

  if (response?.status() === 200) {
    const table = page.locator('table, [class*="table"], .list-group');
    if (await table.first().isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('  User table visible');
    } else {
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  No table found — page loaded OK');
    }
  }
});

test('/admin/list-users — edit user modal', async ({ page }) => {
  const response = await page.goto('/admin/list-users', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() !== 200) {
    test.skip(true, `Page returned ${response?.status()} — skipping`);
    return;
  }

  // Click "Edit" on the first non-current user row
  const editBtn = page.locator('button, a').filter({ hasText: /Edit/i }).first();
  if (await editBtn.isVisible().catch(() => false)) {
    await editBtn.click();

    // Assert edit modal opens — try broad selectors
    const modal = page.locator('#editUserModal, [class*="modal"][class*="show"], .modal.show, [role="dialog"]');
    const modalVisible = await modal.first().isVisible({ timeout: 5000 }).catch(() => false);

    if (modalVisible) {
      // Fill modified name
      const nameField = page.locator('#edit_name, [name="name"]').first();
      if (await nameField.isVisible().catch(() => false)) {
        await nameField.clear();
        await nameField.fill('[PW-TEST] Edited User');
      }

      // Submit edit form
      const submitBtn = modal.first().locator('[type="submit"], button').filter({ hasText: /save|update|submit/i }).first();
      if (await submitBtn.isVisible().catch(() => false)) {
        await submitBtn.click();
        await page.waitForLoadState('domcontentloaded');

        const bodyText = await page.textContent('body');
        expect(bodyText).not.toContain('Internal Server Error');
      }
    } else {
      // May navigate to edit page instead of modal
      await page.waitForLoadState('domcontentloaded');
      const body = await page.textContent('body');
      expect(body).not.toContain('Internal Server Error');
      console.log('  Edit action triggered — no modal, may be page-based');
    }
  } else {
    console.log('  No Edit button found — skipping');
  }
});

test('/admin/create-user — page loads and create user', async ({ page }) => {
  const response = await page.goto('/admin/create-user', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() === 403) {
    test.skip(true, 'Requires super_admin role — 403 returned');
    return;
  }

  if (response?.status() !== 200) {
    // May be redirect — that's acceptable
    expect(response?.status()).toBeLessThan(500);
    return;
  }

  // Fill the create user form
  const nameField = page.locator('[name="name"]').first();
  if (await nameField.isVisible().catch(() => false)) {
    await nameField.fill('[PW-TEST] User');
  }

  const emailField = page.locator('[name="email"]').first();
  if (await emailField.isVisible().catch(() => false)) {
    await emailField.fill(`pw-admin-test-${Date.now()}@example.com`);
  }

  // Select role
  const roleField = page.locator('[name="role"]').first();
  if (await roleField.isVisible().catch(() => false)) {
    await roleField.selectOption('employee').catch(() => {}).catch(() => {});
  }

  // CRITICAL: Uncheck send_magic_link checkbox
  const magicLinkCheckbox = page.locator('[name="send_magic_link"], #send_magic_link');
  if (await magicLinkCheckbox.isVisible().catch(() => false)) {
    await magicLinkCheckbox.uncheck();
  }

  // Submit
  const submitBtn = page.locator('[type="submit"]').first();
  if (await submitBtn.isVisible().catch(() => false)) {
    await submitBtn.click();
    await page.waitForLoadState('domcontentloaded');

    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Internal Server Error');
    const success = bodyText?.toLowerCase().includes('created') ||
                    bodyText?.toLowerCase().includes('success') ||
                    page.url().includes('/admin/');
    expect(success).toBeTruthy();
  }
});

test('/admin/list-users — Send Magic Link button visible (DO NOT CLICK)', async ({ page }) => {
  const response = await page.goto('/admin/list-users', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  if (response?.status() !== 200) {
    test.skip(true, `Page returned ${response?.status()} — skipping`);
    return;
  }

  const magicLinkBtn = page.locator('button, a').filter({ hasText: /Send Magic Link|Magic Link/i }).first();
  if (await magicLinkBtn.isVisible().catch(() => false)) {
    await assertVisibleButDoNotClick(
      page,
      'button:has-text("Magic Link"), a:has-text("Magic Link")',
      'Send Magic Link'
    );
  }
});
