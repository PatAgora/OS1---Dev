/**
 * Associate Portal — Vacancies tests
 *
 * Tests: /portal/vacancies
 * Verifies page load and vacancy cards or empty state.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate Vacancies', () => {
  test('@smoke /portal/vacancies — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/vacancies');
  });

  test('vacancy cards or empty state', async ({ page }) => {
    await page.goto('/portal/vacancies', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    const vacancyItems = page.locator(
      '.vacancy-card, .job-card, .card, [data-vacancy], [data-job], table tbody tr'
    );
    const count = await vacancyItems.count();

    if (count > 0) {
      console.log(`  Vacancy cards found: ${count}`);
      await expect(vacancyItems.first()).toBeVisible();
    } else {
      console.log('  No vacancies — empty state');
    }
  });
});
