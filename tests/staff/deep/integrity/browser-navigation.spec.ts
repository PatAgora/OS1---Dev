/**
 * Deep Tests — Browser Navigation (Back/Forward)
 *
 * Verifies that browser back/forward buttons do not break the app
 * or produce 500 errors across key pages.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { guardSessionExpired } from '../../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

async function assertNoServerError(page: any): Promise<void> {
  const body = await page.textContent('body') || '';
  expect(body).not.toContain('Internal Server Error');
  expect(body).not.toContain('Traceback (most recent call last)');
}

test.describe('Browser Navigation', () => {

  test('back/forward through Dashboard → Workflow → Applications → Placements', async ({ page }) => {
    // Step 1: Dashboard
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    await assertNoServerError(page);

    // Step 2: Workflow
    await page.goto('/workflow', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    await assertNoServerError(page);

    // Step 3: Applications
    await page.goto('/applications', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    await assertNoServerError(page);

    // Step 4: Placements
    await page.goto('/placements', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    await assertNoServerError(page);

    // Now go back through the history
    // Back to Applications
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);
    expect(page.url()).toContain('/applications');

    // Back to Workflow
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);
    expect(page.url()).toContain('/workflow');

    // Back to Dashboard
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);
    // Dashboard is at root — check we're not on workflow
    expect(page.url()).not.toContain('/workflow');

    // Forward to Workflow
    await page.goForward({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);
    expect(page.url()).toContain('/workflow');
  });

  test('back/forward through Resource Pool → Engagements → Jobs', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    await assertNoServerError(page);

    await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);

    await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);

    // Back to Engagements
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);
    expect(page.url()).toContain('/engagements');

    // Back to Resource Pool
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);
    expect(page.url()).toContain('/resource-pool');

    // Forward twice to Jobs
    await page.goForward({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);

    await page.goForward({ waitUntil: 'domcontentloaded' });
    await assertNoServerError(page);
    expect(page.url()).toContain('/jobs');
  });

  test('rapid back/forward does not produce server errors', async ({ page }) => {
    const pages = ['/', '/workflow', '/applications', '/resource-pool', '/engagements'];

    // Navigate through all pages
    for (const url of pages) {
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      await guardSessionExpired(page);
    }

    // Rapid back/forward sequence
    for (let i = 0; i < 4; i++) {
      await page.goBack({ waitUntil: 'domcontentloaded' });
      await assertNoServerError(page);
    }

    for (let i = 0; i < 4; i++) {
      await page.goForward({ waitUntil: 'domcontentloaded' });
      await assertNoServerError(page);
    }
  });
});
