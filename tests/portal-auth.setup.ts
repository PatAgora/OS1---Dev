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
  // Try logging in first (in case the account already exists)
  await page.goto('/portal/login');
  await page.fill('[name="email"]', TEST_EMAIL);
  await page.fill('[name="password"]', TEST_PASSWORD);
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  const afterLoginUrl = page.url();

  // If login succeeded (dashboard or 2FA page), save and return
  if (afterLoginUrl.includes('/portal/dashboard') || afterLoginUrl.includes('/portal/')) {
    // Handle 2FA if required
    if (afterLoginUrl.includes('2fa') || afterLoginUrl.includes('verify')) {
      console.log('  Associate login requires 2FA — skipping (session may be limited)');
    }

    if (!afterLoginUrl.includes('/portal/login')) {
      await page.context().storageState({ path: authFile });
      console.log('✓ Associate auth state saved (existing account) to', authFile);
      return;
    }
  }

  // Login failed — register a new account
  console.log('  Associate login failed, registering new account...');
  await page.goto('/portal/register');
  await page.waitForLoadState('domcontentloaded');

  // Fill registration form (field names vary — try common patterns)
  const firstNameField = page.locator('[name="first_name"], [name="firstName"], [name="name"]').first();
  if (await firstNameField.isVisible()) {
    await firstNameField.fill(TEST_FIRST_NAME);
  }

  const lastNameField = page.locator('[name="last_name"], [name="lastName"], [name="surname"]').first();
  if (await lastNameField.isVisible()) {
    await lastNameField.fill(TEST_LAST_NAME);
  }

  await page.fill('[name="email"]', TEST_EMAIL);

  const passwordField = page.locator('[name="password"]').first();
  if (await passwordField.isVisible()) {
    await passwordField.fill(TEST_PASSWORD);
  }

  const confirmField = page.locator('[name="confirm_password"], [name="password_confirm"], [name="confirmPassword"]').first();
  if (await confirmField.isVisible()) {
    await confirmField.fill(TEST_PASSWORD);
  }

  // Submit
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  // After registration, the app may redirect to check-email, dashboard, or login
  // Since SMTP is not configured, the user may be auto-verified or stuck at check-email
  const afterRegUrl = page.url();
  console.log(`  After registration, landed on: ${afterRegUrl}`);

  // If we're on the portal dashboard, we're authenticated
  if (afterRegUrl.includes('/portal/dashboard') || afterRegUrl.includes('/portal/personal')) {
    await page.context().storageState({ path: authFile });
    console.log('✓ Associate auth state saved (new account) to', authFile);
    return;
  }

  // If stuck at check-email or login, try logging in with the new credentials
  await page.goto('/portal/login');
  await page.fill('[name="email"]', TEST_EMAIL);
  await page.fill('[name="password"]', TEST_PASSWORD);
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  // Save whatever state we have
  await page.context().storageState({ path: authFile });
  console.log('✓ Associate auth state saved to', authFile);
});
