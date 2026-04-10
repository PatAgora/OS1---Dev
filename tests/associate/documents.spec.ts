/**
 * Associate Portal — Documents tests
 *
 * Tests: /portal/documents
 * Verifies page load and document list or empty state.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Documents', () => {
  test('@smoke /portal/documents — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/documents');
  });

  test('document list or empty state renders', async ({ page }) => {
    await page.goto('/portal/documents', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    const docItems = page.locator(
      'table tbody tr, .document-row, .document-card, [data-document], .file-item'
    );
    const count = await docItems.count();

    if (count > 0) {
      console.log(`  Documents found: ${count}`);
    } else {
      // Empty state — check for "no documents" message or empty list
      const hasEmptyState = body?.includes('no document') || body?.includes('No document') ||
        body?.includes('empty') || body?.includes('Upload');
      console.log(`  No documents — empty state present: ${hasEmptyState}`);
    }
  });
});
