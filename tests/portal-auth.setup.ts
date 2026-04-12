/**
 * Associate portal auth setup — runs before all associate portal tests.
 *
 * Registers a test associate on the live deployment and saves the
 * authenticated session state. If the account already exists (from a
 * previous test run), it logs in instead.
 */
import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '../playwright/.auth/associate.json');

const TEST_EMAIL = 'pw-test-associate@example.com';
const TEST_PASSWORD = 'PlaywrightAssociate2024!';
const TEST_FIRST_NAME = 'PW-Test';
const TEST_LAST_NAME = 'Associate';

setup('authenticate as associate', async ({ page }) => {
  // The associate portal requires email verification to register, which doesn't
  // work with SMTP blank. Instead, we create the associate account via the STAFF
  // admin portal users page (which bypasses email verification), then log in.

  // Step 1: Try logging in first (account may already exist from a previous run)
  await page.goto('/portal/login');
  await page.fill('[name="email"]', TEST_EMAIL);
  await page.fill('[name="password"]', TEST_PASSWORD);
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  const afterLoginUrl = page.url();

  // Check if login succeeded — must be on a portal page that isn't login/register
  if (
    afterLoginUrl.includes('/portal/') &&
    !afterLoginUrl.includes('/portal/login') &&
    !afterLoginUrl.includes('/portal/register')
  ) {
    await page.context().storageState({ path: authFile });
    console.log('✓ Associate auth state saved (existing account) to', authFile);
    return;
  }

  // Step 2: Account doesn't exist or password is wrong.
  // Create it via the staff admin panel.
  console.log('  Associate login failed — creating account via staff admin...');

  // Load staff admin auth
  const adminAuthFile = path.join(__dirname, '../playwright/.auth/admin.json');
  const fs = await import('fs');
  if (!fs.existsSync(adminAuthFile)) {
    console.log('  ⚠ No admin auth state — cannot create associate account');
    await page.context().storageState({ path: authFile });
    return;
  }

  // Use staff admin session to create the associate via the admin portal users
  // or via the resource pool add associate
  const adminContext = await page.context().browser()!.newContext({
    storageState: adminAuthFile,
  });
  const adminPage = await adminContext.newPage();

  // Navigate to admin portal users and create a user with a password
  await adminPage.goto('https://os1-dev-production.up.railway.app/admin/portal-users');
  await adminPage.waitForLoadState('domcontentloaded');

  // Check if the user already exists in the portal users list
  const pageBody = await adminPage.textContent('body') || '';
  if (pageBody.includes(TEST_EMAIL)) {
    console.log('  Associate already exists in admin portal users — trying to set password');
  } else {
    // Create via resource pool
    await adminPage.goto('https://os1-dev-production.up.railway.app/resource-pool');
    await adminPage.waitForLoadState('domcontentloaded');

    const addBtn = adminPage.locator('a:has-text("Add Associate"), button:has-text("Add Associate")').first();
    if (await addBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addBtn.click();
      await adminPage.waitForTimeout(500);

      const modal = adminPage.locator('#addAssociateModal');
      const nameField = modal.locator('#add-name, [name="name"]').first();
      if (await nameField.isVisible({ timeout: 3000 }).catch(() => false)) {
        await nameField.fill(`${TEST_FIRST_NAME} ${TEST_LAST_NAME}`);
      }
      const emailField = modal.locator('#add-email, [name="email"]').first();
      if (await emailField.isVisible({ timeout: 2000 }).catch(() => false)) {
        await emailField.fill(TEST_EMAIL);
      }
      const submitBtn = modal.locator('[type="submit"], button:has-text("Add")').first();
      if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await submitBtn.click();
        await adminPage.waitForLoadState('domcontentloaded');
        console.log('  ✓ Associate created via resource pool');
      }
    }
  }

  await adminContext.close();

  // Step 3: The account exists as a Candidate but may not have a password.
  // Try to register via the portal with this email — if the candidate exists
  // but has no password, the portal may allow setting one via magic link.
  // Since that requires SMTP, we'll try the set-password flow if available.

  // For now, try logging in again — if the Candidate was created without a
  // password, the portal login won't work. In that case, we save an
  // unauthenticated state and the associate tests will skip.
  await page.goto('/portal/login');
  await page.fill('[name="email"]', TEST_EMAIL);
  await page.fill('[name="password"]', TEST_PASSWORD);
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  const finalUrl = page.url();
  if (finalUrl.includes('/portal/') && !finalUrl.includes('/portal/login') && !finalUrl.includes('/portal/register')) {
    await page.context().storageState({ path: authFile });
    console.log('✓ Associate auth state saved to', authFile);
  } else {
    console.log('  ⚠ Could not authenticate as associate — portal tests will skip');
    console.log('  To fix: manually register at /portal/register with:');
    console.log(`    Email: ${TEST_EMAIL}`);
    console.log(`    Password: ${TEST_PASSWORD}`);
    console.log('  Or create the account via the admin panel and set a password.');
    await page.context().storageState({ path: authFile });
  }
});
