/**
 * Staff admin auth setup — runs before all staff portal tests.
 *
 * Handles three scenarios:
 *   1. Login → dashboard (no 2FA) — just save session
 *   2. Login → 2FA SETUP page (first time) — extract secret, save it, generate code, submit
 *   3. Login → 2FA VERIFY page (already set up) — read saved secret, generate code, submit
 */
import { test as setup, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { generateTOTP } from './utils/totp';

const authFile = path.join(__dirname, '../playwright/.auth/admin.json');
const totpSecretFile = path.join(__dirname, '../playwright/.auth/totp-secret.txt');

setup('authenticate as staff admin', async ({ page }) => {
  // Navigate to login
  await page.goto('/login');
  await expect(page.locator('[name="email"]')).toBeVisible();

  // Fill credentials
  await page.fill('[name="email"]', 'playwright@test.example.com');
  await page.fill('[name="password"]', 'Testuser1234!');
  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  const url = page.url();

  // Scenario 1: no 2FA — straight to dashboard
  if (!url.includes('2fa') && !url.includes('mfa') && !url.includes('verify')) {
    console.log('  No 2FA required — saving auth state');
    await page.context().storageState({ path: authFile });
    console.log('✓ Staff admin auth state saved');
    return;
  }

  // Detect if this is SETUP (has QR code / secret display) or VERIFY (just a code input)
  const hasQR = await page.locator('img[src*="qr"], img[alt*="QR"], .qr-code, canvas').first()
    .isVisible({ timeout: 3000 }).catch(() => false);
  const hasSecretText = await page.locator('code, .totp-secret, .secret-key, .manual-key')
    .first().isVisible({ timeout: 2000 }).catch(() => false);
  const isSetupPage = hasQR || hasSecretText || url.includes('setup') || url.includes('mandatory');

  let totpSecret = '';

  if (isSetupPage && !url.includes('verify-2fa') && !url.includes('verify_2fa')) {
    console.log('  2FA SETUP page detected — extracting secret...');

    // Click "Start" button if present
    const startBtn = page.locator('button:has-text("Start"), button:has-text("Set Up"), button:has-text("Begin")').first();
    if (await startBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await startBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }

    // Find the TOTP secret
    const secretEl = page.locator('code, .totp-secret, .secret-key, .manual-key, input[name="secret"]').first();
    if (await secretEl.isVisible({ timeout: 5000 }).catch(() => false)) {
      const tag = await secretEl.evaluate(el => el.tagName.toLowerCase());
      totpSecret = tag === 'input' ? await secretEl.inputValue() : ((await secretEl.textContent()) || '').trim();
    }

    // Fallback: regex for base32 string in page body
    if (!totpSecret) {
      const body = await page.textContent('body');
      const match = body?.match(/[A-Z2-7]{16,64}/);
      if (match) totpSecret = match[0];
    }

    // Fallback: QR src
    if (!totpSecret) {
      const qr = page.locator('img[src*="secret="]').first();
      if (await qr.isVisible({ timeout: 2000 }).catch(() => false)) {
        const src = await qr.getAttribute('src') || '';
        const m = src.match(/secret=([A-Z2-7]+)/i);
        if (m) totpSecret = m[1].toUpperCase();
      }
    }

    if (totpSecret) {
      // Save the secret for future runs
      fs.writeFileSync(totpSecretFile, totpSecret, 'utf-8');
      console.log(`  Saved TOTP secret to ${totpSecretFile}`);
    }
  } else {
    // Scenario 3: 2FA VERIFY page — read previously saved secret
    console.log('  2FA VERIFY page detected — reading saved secret...');
    if (fs.existsSync(totpSecretFile)) {
      totpSecret = fs.readFileSync(totpSecretFile, 'utf-8').trim();
      console.log(`  Read saved TOTP secret: ${totpSecret.substring(0, 4)}...`);
    }
  }

  if (!totpSecret) {
    await page.screenshot({ path: 'test-results/2fa-debug.png' });
    throw new Error(
      'Could not find or read TOTP secret. The test user has 2FA enabled but no saved secret.\n' +
      'Fix: go to /admin/list-users → find playwright@test.example.com → click "Disable 2FA".\n' +
      'Then re-run the tests — the first run will set up 2FA and save the secret.\n' +
      'Screenshot saved to test-results/2fa-debug.png'
    );
  }

  // Generate and submit TOTP code
  const totpCode = generateTOTP(totpSecret);
  console.log(`  Generated TOTP code: ${totpCode}`);

  const totpInput = page.locator(
    'input[name="totp_code"], input[name="token"], input[name="code"], ' +
    'input[name="otp"], input[type="text"][maxlength="6"], input[type="number"], ' +
    'input[placeholder*="code"], input[placeholder*="digit"]'
  ).first();

  await expect(totpInput).toBeVisible({ timeout: 5000 });
  await totpInput.fill(totpCode);

  await page.click('[type="submit"]');
  await page.waitForLoadState('domcontentloaded');

  // Handle backup codes page if shown
  const currentUrl = page.url();
  if (currentUrl.includes('backup') || currentUrl.includes('recovery')) {
    console.log('  Backup codes page — clicking through...');
    const continueBtn = page.locator('a:has-text("Continue"), a:has-text("Dashboard"), button:has-text("Continue")').first();
    if (await continueBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await continueBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }
  }

  const finalUrl = page.url();
  console.log(`  Final URL: ${finalUrl}`);

  if (finalUrl.includes('/login')) {
    throw new Error('Auth failed — still on login page after 2FA.');
  }

  await page.context().storageState({ path: authFile });
  console.log('✓ Staff admin auth state saved');
});
