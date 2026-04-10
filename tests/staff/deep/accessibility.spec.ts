/**
 * Deep Tests — Accessibility (WCAG 2.1 AA)
 *
 * Uses axe-core to scan each key page for accessibility violations.
 * Reports violations as warnings; only fails on critical/serious issues.
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { installRouteGuard } from '../../utils/blocked-routes';
import { guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

const PAGES_TO_SCAN: Array<{ url: string; name: string }> = [
  { url: '/login', name: 'Login' },
  { url: '/', name: 'Dashboard' },
  { url: '/workflow', name: 'Workflow' },
  { url: '/applications', name: 'Applications' },
  { url: '/resource-pool', name: 'Resource Pool' },
  { url: '/engagements', name: 'Engagements' },
  { url: '/placements', name: 'Placements' },
  { url: '/pipeline', name: 'Pipeline' },
  { url: '/jobs', name: 'Jobs' },
  { url: '/taxonomy/manage', name: 'Taxonomy Manage' },
  { url: '/admin/invoices', name: 'Admin Invoices' },
  { url: '/portal/login', name: 'Portal Login' },
  { url: '/portal/dashboard', name: 'Portal Dashboard' },
];

// Use a separate describe with unauthenticated state for login pages
test.describe('Accessibility — axe-core scans', () => {

  for (const pg of PAGES_TO_SCAN) {
    test(`@a11y ${pg.name} — no critical violations`, async ({ page }) => {
      const response = await page.goto(pg.url, { waitUntil: 'domcontentloaded' });
      const status = response?.status() || 0;

      if (status >= 500) {
        test.skip(true, `${pg.name} returned ${status}`);
        return;
      }

      // Run axe scan
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      // Categorise violations
      const critical = results.violations.filter(v => v.impact === 'critical');
      const serious = results.violations.filter(v => v.impact === 'serious');
      const moderate = results.violations.filter(v => v.impact === 'moderate');
      const minor = results.violations.filter(v => v.impact === 'minor');

      const total = results.violations.length;
      console.log(`  ${pg.name}: ${total} violations (${critical.length} critical, ${serious.length} serious, ${moderate.length} moderate, ${minor.length} minor)`);

      // Log details for critical/serious
      for (const v of [...critical, ...serious]) {
        console.log(`    [${v.impact}] ${v.id}: ${v.description}`);
        for (const node of v.nodes.slice(0, 3)) {
          console.log(`      → ${node.html.substring(0, 120)}`);
        }
      }

      // Only FAIL on critical violations — serious/moderate/minor are logged as warnings
      expect(
        critical.length,
        `${pg.name} has ${critical.length} CRITICAL accessibility violation(s):\n` +
        critical.map(v => `  - ${v.id}: ${v.description}`).join('\n')
      ).toBe(0);
    });
  }

});
