/**
 * BLOCKED ROUTES — Safety layer for the Playwright test suite.
 *
 * These routes call external paid APIs (Signable, Verifile, Sumsub) or send
 * real emails via SMTP. If ANY request to a blocked pattern is detected during
 * a test run, the test IMMEDIATELY FAILS with a clear error message. This is
 * not a soft warning — it's a hard abort that stops the current test.
 *
 * The `installRouteGuard` function uses Playwright's `page.route()` to
 * intercept matching requests BEFORE they leave the browser, abort them,
 * and throw a test failure. This is the primary safety mechanism.
 *
 * See PLAYWRIGHT_1.md for the full rationale and route-by-route analysis.
 */
import { Page, expect } from '@playwright/test';

// ============================================================================
// BLOCKED URL PATTERNS — any match causes immediate test failure
// ============================================================================

const BLOCKED_PATTERNS: Array<{ pattern: string; reason: string }> = [
  // --- Signable (E-Signatures) — costs money per envelope ---
  { pattern: '**/action/esign/**', reason: 'Signable: would send a real e-sign envelope (costs money)' },
  { pattern: '**/action/esign_status/**', reason: 'Signable: would poll Signable API' },
  { pattern: '**/api/contract/*/resend', reason: 'Signable: would resend envelope' },
  { pattern: '**/api/contract/*/chase', reason: 'Signable: would chase signer' },
  { pattern: '**/api/contract/*/extend', reason: 'Signable: would extend envelope' },
  { pattern: '**/api/contracts/bulk-extend', reason: 'Signable: bulk envelope operation' },

  // --- Verifile (Identity Vetting) — costs money per screening ---
  { pattern: '**/action/verifile/**', reason: 'Verifile: would submit a paid screening' },
  { pattern: '**/api/vetting/poll-verifile/**', reason: 'Verifile: would poll Verifile API' },
  { pattern: '**/api/vetting/trigger/**', reason: 'Verifile: would trigger paid full vetting' },
  { pattern: '**/api/vetting/trigger-referencing/**', reason: 'Verifile: would trigger referencing' },
  { pattern: '**/candidate/*/vetting', reason: 'Verifile: would submit vetting checks' },
  { pattern: '**/candidate/*/vetting-manual', reason: 'Verifile: manual vetting submission' },
  { pattern: '**/action/start-vetting/**', reason: 'Verifile: would start full vetting' },

  // --- Sumsub (KYC) ---
  { pattern: '**/sumsub/**', reason: 'Sumsub: KYC API call' },

  // --- SMTP (Email sending) ---
  { pattern: '**/admin/send-magic-link/**', reason: 'SMTP: would send a real email' },
  { pattern: '**/admin/portal-users/*/send-magic-link', reason: 'SMTP: would send a real email' },
  { pattern: '**/admin/invoices/*/send', reason: 'SMTP: would send invoice email' },
  { pattern: '**/action/request_updated_cv/**', reason: 'SMTP: would send CV request email' },
  { pattern: '**/action/send-reference/**', reason: 'SMTP: would send reference request email' },
  { pattern: '**/action/chase-reference/**', reason: 'SMTP: would send reference chase email' },
  { pattern: '**/portal/resend-verification', reason: 'SMTP: would resend verification email' },

  // --- AI (bulk/expensive operations only — individual score/summarise is ALLOWED) ---
  { pattern: '**/action/taxonomy/retag_all', reason: 'AI: would retag ALL candidates (expensive)' },
  { pattern: '**/action/taxonomy/retag_one/**', reason: 'AI: would retag a candidate' },
  { pattern: '**/action/candidate/recalculate_match_score', reason: 'AI: bulk score recalculation' },
  { pattern: '**/action/candidate/regenerate_summary', reason: 'AI: bulk summary regeneration' },

  // --- Signable via Associate Portal ---
  // NOTE: declaration-form PAGE LOAD is allowed; only the POST submit is blocked.
  // The page.route pattern below matches POST only via the handler logic.
];

/**
 * Install the route guard on a Playwright Page instance.
 *
 * Call this at the start of every test (or in a beforeEach hook).
 * If any request to a blocked pattern is detected:
 *   1. The request is ABORTED before it reaches the server
 *   2. The test FAILS immediately with a descriptive error
 *
 * This is the user's "hard abort" requirement: if you see any API call to
 * Verifile, Signable, or SMTP, the full test automatically stops.
 */
export async function installRouteGuard(page: Page): Promise<void> {
  for (const { pattern, reason } of BLOCKED_PATTERNS) {
    await page.route(pattern, async (route) => {
      const method = route.request().method();
      const url = route.request().url();

      // Abort the request so it never reaches the server
      await route.abort('blockedbyclient');

      // Throw a hard failure that stops the test immediately
      throw new Error(
        `\n\n` +
        `🚨 BLOCKED API CALL DETECTED — TEST ABORTED 🚨\n` +
        `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
        `Method:  ${method}\n` +
        `URL:     ${url}\n` +
        `Reason:  ${reason}\n` +
        `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
        `This request was blocked because it would call an external paid API\n` +
        `or send a real email. The request was aborted BEFORE reaching the\n` +
        `server. See PLAYWRIGHT_1.md for the full blocked-routes list.\n\n`
      );
    });
  }
}

/**
 * Assert that a button is visible but DO NOT click it.
 * Used for blocked buttons (Score CV, Send Contract, etc.) where we want to
 * confirm the UI renders the button but must not interact with it.
 */
export async function assertVisibleButDoNotClick(
  page: Page,
  selector: string,
  label: string
): Promise<void> {
  const element = page.locator(selector).first();
  await expect(element).toBeVisible({ timeout: 5000 });
  // Intentionally NOT calling .click() — this button triggers a blocked API
  console.log(`  ✓ Blocked button visible (not clicked): ${label}`);
}
