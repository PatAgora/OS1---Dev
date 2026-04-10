/**
 * Associate Portal — Vetting Intro tests
 *
 * Tests: /portal/intro-to-vetting
 * Verifies page load and content renders.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Vetting Intro', () => {
  test('@smoke /portal/intro-to-vetting — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/intro-to-vetting');
  });

  test('content renders', async ({ page }) => {
    await page.goto('/portal/intro-to-vetting', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    // Should have some content about vetting
    const hasContent = (body?.length ?? 0) > 100;
    expect(hasContent).toBeTruthy();
    console.log(`  Vetting intro content length: ${body?.length ?? 0} chars`);
  });
});
