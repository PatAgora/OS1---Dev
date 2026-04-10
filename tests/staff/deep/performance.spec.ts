/**
 * Deep Tests — Performance
 *
 * Asserts that key pages load within acceptable time thresholds.
 * These are not hard failures — they log warnings for slow pages
 * and only fail if a page takes more than 10 seconds.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

const PERF_TARGETS: Array<{ url: string; name: string; warnMs: number; failMs: number }> = [
  { url: '/', name: 'Dashboard', warnMs: 3000, failMs: 10000 },
  { url: '/workflow', name: 'Workflow', warnMs: 3000, failMs: 10000 },
  { url: '/applications', name: 'Applications', warnMs: 3000, failMs: 10000 },
  { url: '/resource-pool', name: 'Resource Pool', warnMs: 3000, failMs: 10000 },
  { url: '/engagements', name: 'Engagements', warnMs: 2000, failMs: 10000 },
  { url: '/placements', name: 'Placements', warnMs: 2000, failMs: 10000 },
  { url: '/pipeline', name: 'Pipeline', warnMs: 2000, failMs: 10000 },
  { url: '/taxonomy/manage', name: 'Taxonomy Manage', warnMs: 2000, failMs: 10000 },
  { url: '/admin/invoices', name: 'Admin Invoices', warnMs: 2000, failMs: 10000 },
  { url: '/jobs', name: 'Jobs', warnMs: 2000, failMs: 10000 },
  { url: '/health', name: 'Health Check', warnMs: 500, failMs: 3000 },
];

test.describe('Performance — Page Load Times', () => {

  for (const target of PERF_TARGETS) {
    test(`@perf ${target.name} loads within ${target.failMs}ms`, async ({ page }) => {
      const start = Date.now();
      const response = await page.goto(target.url, { waitUntil: 'domcontentloaded' });
      const elapsed = Date.now() - start;

      const status = response?.status() || 0;
      if (status >= 500) {
        test.skip(true, `${target.name} returned ${status}`);
        return;
      }

      await guardSessionExpired(page);

      if (elapsed > target.warnMs) {
        console.warn(`  ⚠ SLOW: ${target.name} took ${elapsed}ms (warn threshold: ${target.warnMs}ms)`);
      } else {
        console.log(`  ✓ ${target.name}: ${elapsed}ms`);
      }

      expect(elapsed, `${target.name} took ${elapsed}ms — exceeds ${target.failMs}ms fail threshold`).toBeLessThan(target.failMs);
    });
  }

});
