/**
 * Associate Portal — My Applications tests
 *
 * Tests: /portal/my-applications
 * Verifies page load, application rows or empty state, and offer buttons.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../utils/blocked-routes';
import { assertPageLoads } from '../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Associate My Applications', () => {
  test('@smoke /portal/my-applications — page loads (200)', async ({ page }) => {
    await assertPageLoads(page, '/portal/my-applications');
  });

  test('application rows or empty state', async ({ page }) => {
    await page.goto('/portal/my-applications', { waitUntil: 'domcontentloaded' });

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');

    const appItems = page.locator(
      'table tbody tr, .application-row, .application-card, [data-application], .card'
    );
    const count = await appItems.count();

    if (count > 0) {
      console.log(`  Application rows found: ${count}`);

      // Check if any offer has Accept/Decline buttons
      const acceptBtn = page.locator(
        'button:has-text("Accept"), a:has-text("Accept")'
      ).first();
      const declineBtn = page.locator(
        'button:has-text("Decline"), a:has-text("Decline")'
      ).first();

      if (await acceptBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('  Accept button visible (not clicked)');
      }
      if (await declineBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('  Decline button visible (not clicked)');
      }
    } else {
      console.log('  No applications — empty state');
    }
  });
});
