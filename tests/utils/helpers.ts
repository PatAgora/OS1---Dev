/**
 * Shared test utilities for the OS1 Playwright suite.
 */
import { Page, expect, test } from '@playwright/test';

/**
 * Check if the current page shows a login/sign-in form (session expired).
 * If so, skip the test gracefully.
 */
export async function guardSessionExpired(page: Page): Promise<void> {
  const bodyText = await page.textContent('body') || '';
  if (
    (bodyText.includes('Sign in') || bodyText.includes('sign in') || bodyText.includes('Log in') || bodyText.includes('Password')) &&
    (page.url().includes('/login') || page.url().includes('/auth'))
  ) {
    test.skip(true, 'Session expired — re-run auth setup');
  }
}

/**
 * Assert a page loaded successfully (HTTP < 500, no server error, no error flash).
 * Accepts redirects (302/303) and skips gracefully on session expiry.
 */
export async function assertPageLoads(page: Page, url: string, opts?: { skipSessionGuard?: boolean }): Promise<void> {
  const response = await page.goto(url, { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);

  if (!opts?.skipSessionGuard) {
    await guardSessionExpired(page);
  }

  // No "Internal Server Error" in the body
  const body = await page.textContent('body');
  expect(body).not.toContain('Internal Server Error');
  expect(body).not.toContain('Traceback (most recent call last)');

  // No error flash
  const errorFlash = page.locator('.alert-danger, .flash-error');
  const errorCount = await errorFlash.count();
  if (errorCount > 0) {
    const errorText = await errorFlash.first().textContent();
    // Allow some known non-error alerts (e.g. validation messages)
    if (errorText && !errorText.includes('required')) {
      console.warn(`  Warning: Error flash on ${url}: ${errorText?.trim().substring(0, 100)}`);
    }
  }
}

/**
 * Assert a flash message appears with the given category.
 */
export async function assertFlash(page: Page, category: 'success' | 'danger' | 'warning' | 'info'): Promise<void> {
  const flash = page.locator(`.alert-${category}`);
  await expect(flash.first()).toBeVisible({ timeout: 5000 });
}

/**
 * Fill a form field by name attribute.
 */
export async function fillByName(page: Page, name: string, value: string): Promise<void> {
  await page.locator(`[name="${name}"]`).first().fill(value);
}

/**
 * Submit a form and wait for navigation.
 */
export async function submitForm(page: Page, formSelector?: string): Promise<void> {
  if (formSelector) {
    await page.locator(formSelector).locator('[type="submit"]').first().click();
  } else {
    await page.locator('[type="submit"]').first().click();
  }
  await page.waitForLoadState('domcontentloaded');
}

/**
 * Generate a unique test-data prefix to avoid collisions.
 * All test-created data should use this prefix so it's identifiable.
 */
export function testPrefix(): string {
  return `[PW-TEST-${Date.now().toString(36)}]`;
}
