/**
 * Deep Tests — Concurrent Edit Safety
 *
 * Opens two browser contexts simultaneously, both editing the same
 * candidate, and verifies that notes from both are preserved (no
 * silent overwrite).
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { guardSessionExpired } from '../../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Concurrent Edits', () => {

  test('two contexts adding notes to same candidate preserves both', async ({ page, browser }) => {
    // First, find a candidate to test with
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const candidateLink = page.locator('table tbody tr a[href*="/candidate/"], a[href*="/candidate/"]').first();
    if (await candidateLink.count() === 0) {
      test.skip(true, 'No candidates found in resource pool');
      return;
    }

    const candidateHref = await candidateLink.getAttribute('href') || '';
    const candidateUrl = candidateHref.startsWith('http')
      ? candidateHref
      : `https://os1-dev-production.up.railway.app${candidateHref}`;

    // Navigate to candidate to verify notes form exists
    await page.goto(candidateUrl, { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const notesTextarea = page.locator('textarea[name="content"], textarea[name="note"], textarea[name="notes"], textarea[name="body"]').first();
    if (await notesTextarea.count() === 0) {
      test.skip(true, 'No notes form found on candidate profile');
      return;
    }

    // Get the storage state from the current context
    const storageState = await page.context().storageState();

    // Create Context A
    const contextA = await browser.newContext({ storageState });
    const pageA = await contextA.newPage();
    await installRouteGuard(pageA);

    // Create Context B
    const contextB = await browser.newContext({ storageState });
    const pageB = await contextB.newPage();
    await installRouteGuard(pageB);

    try {
      // Both navigate to the same candidate
      await pageA.goto(candidateUrl, { waitUntil: 'domcontentloaded' });
      await pageB.goto(candidateUrl, { waitUntil: 'domcontentloaded' });

      const timestamp = Date.now();
      const noteA = `[PW-TEST] Context A note ${timestamp}`;
      const noteB = `[PW-TEST] Context B note ${timestamp}`;

      // Context A: add a note
      const textareaA = pageA.locator('textarea[name="content"], textarea[name="note"], textarea[name="notes"], textarea[name="body"]').first();
      if (await textareaA.count() > 0) {
        await textareaA.fill(noteA);
        const submitA = pageA.locator('form:has(textarea) button[type="submit"], form:has(textarea) input[type="submit"]').first();
        if (await submitA.count() > 0) {
          await submitA.click();
          await pageA.waitForLoadState('domcontentloaded');
        }
      }

      // Context B: add a different note (while A's is already saved)
      const textareaB = pageB.locator('textarea[name="content"], textarea[name="note"], textarea[name="notes"], textarea[name="body"]').first();
      if (await textareaB.count() > 0) {
        await textareaB.fill(noteB);
        const submitB = pageB.locator('form:has(textarea) button[type="submit"], form:has(textarea) input[type="submit"]').first();
        if (await submitB.count() > 0) {
          await submitB.click();
          await pageB.waitForLoadState('domcontentloaded');
        }
      }

      // Reload Context A and check both notes are present
      await pageA.reload({ waitUntil: 'domcontentloaded' });
      const bodyA = await pageA.textContent('body') || '';

      // Both notes should be present — no silent overwrite
      expect(bodyA).toContain(noteA);
      expect(bodyA).toContain(noteB);

    } finally {
      await contextA.close();
      await contextB.close();
    }
  });
});
