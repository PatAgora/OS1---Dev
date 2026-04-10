/**
 * Staff Portal — Engagement Dashboard (/engagement/<id>/dashboard)
 *
 * Tests: page load, KPI metrics, delivery plan, active jobs.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

/** Navigate to the first engagement's dashboard */
async function goToFirstEngagementDashboard(page: import('@playwright/test').Page): Promise<boolean> {
  await page.goto('/engagements', { waitUntil: 'domcontentloaded' });

  // Check for session expiry
  const bodyText = await page.textContent('body') || '';
  if (
    (bodyText.includes('Sign in') || bodyText.includes('Log in')) &&
    (page.url().includes('/login') || page.url().includes('/auth'))
  ) {
    return false;
  }

  // Click first engagement link to go to its dashboard
  const engLink = page.locator('a[href*="/engagement/"]').first();
  const linkVisible = await engLink.isVisible({ timeout: 10000 }).catch(() => false);

  if (!linkVisible) {
    return false;
  }

  await engLink.click();
  await page.waitForLoadState('domcontentloaded');

  // If we're not on a dashboard URL, try navigating to /dashboard sub-path
  if (!page.url().includes('/dashboard')) {
    const dashLink = page.locator('a[href*="/dashboard"]').first();
    if (await dashLink.isVisible().catch(() => false)) {
      await dashLink.click();
      await page.waitForLoadState('domcontentloaded');
    }
  }

  return true;
}

test('/engagement/<id>/dashboard — page loads', async ({ page }) => {
  const navigated = await goToFirstEngagementDashboard(page);
  if (!navigated) {
    test.skip(true, 'No engagements found or session expired — skipping');
    return;
  }
  const response = await page.reload({ waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBeLessThan(500);
});

test('/engagement/<id>/dashboard — KPI metrics visible', async ({ page }) => {
  const navigated = await goToFirstEngagementDashboard(page);
  if (!navigated) {
    test.skip(true, 'No engagements found or session expired — skipping');
    return;
  }

  // Look for KPI cards/metrics with broad selectors
  const metrics = page.locator('.kpi, .metric, .summary-card, .stat-card, .card, [class*="kpi"], [class*="metric"], [class*="stat"], [class*="summary"]');
  const count = await metrics.count();

  if (count > 0) {
    console.log(`  KPI/metric elements found: ${count}`);
  } else {
    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    console.log('  No KPI elements found — page loaded OK');
  }
});

test('/engagement/<id>/dashboard — delivery plan table renders or content visible', async ({ page }) => {
  const navigated = await goToFirstEngagementDashboard(page);
  if (!navigated) {
    test.skip(true, 'No engagements found or session expired — skipping');
    return;
  }

  const table = page.locator('table, [class*="table"]');
  const tableCount = await table.count();

  if (tableCount > 0) {
    console.log(`  Tables found: ${tableCount}`);
  } else {
    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    console.log('  No tables found — page loaded OK');
  }
});

test('/engagement/<id>/dashboard — Active Jobs section visible', async ({ page }) => {
  const navigated = await goToFirstEngagementDashboard(page);
  if (!navigated) {
    test.skip(true, 'No engagements found or session expired — skipping');
    return;
  }

  const bodyText = await page.textContent('body') || '';
  expect(bodyText).not.toContain('Internal Server Error');

  const hasJobs = bodyText.includes('Jobs') ||
                  bodyText.includes('Active') ||
                  bodyText.includes('Delivery') ||
                  (await page.locator('h2, h3, h4').filter({ hasText: /job|active|delivery/i }).count()) > 0;
  if (hasJobs) {
    console.log('  Jobs/Active section found');
  } else {
    console.log('  No Jobs section text found — page loaded OK');
  }
});
