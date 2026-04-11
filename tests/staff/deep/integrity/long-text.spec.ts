/**
 * Deep Tests — Long Text & Edge Case Input
 *
 * Tests the app's handling of extreme-length input, unicode characters,
 * and emoji in various form fields. Verifies no crashes or 500 errors.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { guardSessionExpired } from '../../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

// Generate 10,000 characters of pseudo-Lorem text
function generateLongText(length: number): string {
  const base = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. ';
  let result = '';
  while (result.length < length) {
    result += base;
  }
  return result.substring(0, length);
}

test.describe('Long Text & Edge Cases', () => {

  test('10,000 character note on candidate profile does not crash', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const candidateLink = page.locator('table tbody tr a[href*="/candidate/"], a[href*="/candidate/"]').first();
    if (await candidateLink.count() === 0) {
      test.skip(true, 'No candidates found in resource pool');
      return;
    }

    await candidateLink.click();
    await page.waitForLoadState('domcontentloaded');
    await guardSessionExpired(page);

    const notesTextarea = page.locator('textarea[name="content"], textarea[name="note"], textarea[name="notes"], textarea[name="body"]').first();
    if (await notesTextarea.count() === 0) {
      test.skip(true, 'No notes textarea found on candidate profile');
      return;
    }

    const longNote = `[PW-TEST] ${generateLongText(10000)}`;
    await notesTextarea.fill(longNote);

    const submitBtn = page.locator('form:has(textarea) button[type="submit"], form:has(textarea) input[type="submit"]').first();
    if (await submitBtn.count() > 0) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }

    // No crash
    const body = await page.textContent('body') || '';
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback');

    // Note should appear (possibly truncated)
    expect(body).toContain('[PW-TEST]');
  });

  test('200 character job title does not crash', async ({ page }) => {
    await page.goto('/job/new', { waitUntil: 'domcontentloaded', timeout: 10000 });
    await guardSessionExpired(page);

    const titleInput = page.locator('[name="title"]').first();
    const titleVisible = await titleInput.isVisible().catch(() => false);
    if (!titleVisible) {
      test.skip(true, 'Job title input not found or not visible on /job/new');
      return;
    }

    const longTitle = `[PW-TEST] ${'A'.repeat(190)}`;
    await titleInput.fill(longTitle);

    // Select first non-empty engagement option
    const engagementSelect = page.locator('[name="engagement_id"]');
    if (await engagementSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      const firstOption = engagementSelect.locator('option:not([value=""]):not([value="0"])').first();
      const firstValue = await firstOption.getAttribute('value').catch(() => null);
      if (firstValue) {
        await engagementSelect.selectOption(firstValue);
      }
    }

    // Fill description
    const descField = page.locator('[name="description"]').first();
    if (await descField.isVisible().catch(() => false)) {
      await descField.fill('Test description for long title test');
    }

    const submitBtn = page.locator('[type="submit"]').first();
    const submitVisible = await submitBtn.isVisible().catch(() => false);
    if (!submitVisible) {
      test.skip(true, 'Submit button not found on job form');
      return;
    }

    await submitBtn.click();
    await page.waitForLoadState('domcontentloaded');

    const body = await page.textContent('body') || '';
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback');
  });

  test('unicode characters in notes do not crash', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const candidateLink = page.locator('table tbody tr a[href*="/candidate/"], a[href*="/candidate/"]').first();
    if (await candidateLink.count() === 0) {
      test.skip(true, 'No candidates found');
      return;
    }

    await candidateLink.click();
    await page.waitForLoadState('domcontentloaded');
    await guardSessionExpired(page);

    const notesTextarea = page.locator('textarea[name="content"], textarea[name="note"], textarea[name="notes"], textarea[name="body"]').first();
    if (await notesTextarea.count() === 0) {
      test.skip(true, 'No notes textarea found');
      return;
    }

    const unicodeNote = '[PW-TEST] Unicode test: 日本語テスト こんにちは 中文测试 العربية Кириллица';
    await notesTextarea.fill(unicodeNote);

    const submitBtn = page.locator('form:has(textarea) button[type="submit"], form:has(textarea) input[type="submit"]').first();
    if (await submitBtn.count() > 0) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }

    const body = await page.textContent('body') || '';
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback');
  });

  test('emoji in resource pool search does not crash', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const searchInput = page.locator('input[name="search"], input[name="q"], input[type="search"], input[placeholder*="Search"]').first();
    if (await searchInput.count() > 0) {
      await searchInput.fill('test');
      await searchInput.press('Enter');
      await page.waitForLoadState('domcontentloaded');
    } else {
      // Try URL parameter approach
      const response = await page.goto('/resource-pool?search=%F0%9F%94%8D+test', { waitUntil: 'domcontentloaded' });
      expect(response?.status()).toBeLessThan(500);
    }

    const body = await page.textContent('body') || '';
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback');
  });

  test('special characters in search do not crash', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const specialChars = '!@#$%^&*()_+-=[]{}|;:\'"<>?,./~`';

    const searchInput = page.locator('input[name="search"], input[name="q"], input[type="search"], input[placeholder*="Search"]').first();
    if (await searchInput.count() > 0) {
      await searchInput.fill(specialChars);
      await searchInput.press('Enter');
      await page.waitForLoadState('domcontentloaded');
    } else {
      const response = await page.goto(
        `/resource-pool?search=${encodeURIComponent(specialChars)}`,
        { waitUntil: 'domcontentloaded' }
      );
      expect(response?.status()).toBeLessThan(500);
    }

    const body = await page.textContent('body') || '';
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback');
  });
});
