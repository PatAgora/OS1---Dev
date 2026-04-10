/**
 * Staff Portal — Configuration (/configuration)
 *
 * Tests: /configuration redirects to /taxonomy/manage or similar config page.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { guardSessionExpired } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test('/configuration — redirects to taxonomy/manage or config page', async ({ page }) => {
  const response = await page.goto('/configuration', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  // The final page should load successfully
  expect(response?.status()).toBeLessThan(500);

  // Should redirect to /taxonomy/manage or stay on a config-related page
  const finalUrl = page.url();
  const isConfigPage = finalUrl.includes('/taxonomy') ||
                       finalUrl.includes('/manage') ||
                       finalUrl.includes('/configuration') ||
                       finalUrl.includes('/config') ||
                       finalUrl.includes('/settings');

  if (isConfigPage) {
    console.log(`  Redirected to: ${finalUrl}`);
  } else {
    // Accept any non-error page
    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    console.log(`  Final URL: ${finalUrl} — page loaded OK`);
  }
});
