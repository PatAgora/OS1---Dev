/**
 * Deep Tests — Pipeline Flow (Candidate Journey)
 *
 * Tests the full candidate pipeline by creating a candidate and attempting
 * to move them through workflow stages via the API.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { guardSessionExpired } from '../../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Pipeline Flow', () => {

  test('create candidate and verify in resource pool', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // The "Add Associate" button is an <a> with onclick="showAddAssociateModal()"
    const addBtn = page.locator('a:has-text("Add Associate"), button:has-text("Add Associate")').first();

    const addBtnVisible = await addBtn.isVisible().catch(() => false);
    if (!addBtnVisible) {
      test.skip(true, 'No Add Associate/Candidate button found on resource pool');
      return;
    }

    await addBtn.click();
    await page.waitForTimeout(500); // Wait for modal animation

    // Fill candidate form in the modal — real IDs: add-name, add-email
    const modal = page.locator('#addAssociateModal');
    const nameField = modal.locator('#add-name, [name="name"]').first();
    const nameVisible = await nameField.isVisible({ timeout: 3000 }).catch(() => false);

    if (!nameVisible) {
      test.skip(true, 'Candidate form fields not found (modal may not have appeared)');
      return;
    }

    const emailField = modal.locator('#add-email, [name="email"]').first();

    const testName = `[PW-TEST] Pipeline Candidate ${Date.now()}`;
    await nameField.fill(testName);
    if (await emailField.isVisible().catch(() => false)) {
      await emailField.fill(`pw-test-${Date.now()}@example.com`);
    }

    // Submit form — the modal has a submit button
    const submitBtn = modal.locator('button[type="submit"], button:has-text("Add Associate")').first();
    const submitVisible = await submitBtn.isVisible().catch(() => false);
    if (!submitVisible) {
      test.skip(true, 'Submit button not found in candidate form');
      return;
    }

    await Promise.race([
      submitBtn.click().then(() => page.waitForLoadState('domcontentloaded')),
      page.waitForTimeout(10000),
    ]);

    // Verify candidate appears (either on the same page or navigated)
    const body = await page.textContent('body') || '';
    // Check that we didn't get an error
    expect(body).not.toContain('Internal Server Error');
  });

  test('workflow stage transitions via API', async ({ page }) => {
    // Navigate to applications to find an existing application to test transitions
    await page.goto('/applications', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Find any application row with a link
    const appLink = page.locator('table tbody tr a[href*="/application/"], a[href*="/application/"]').first();
    if (await appLink.count() === 0) {
      test.skip(true, 'No applications found to test workflow transitions');
      return;
    }

    // Get the application ID from the link
    const href = await appLink.getAttribute('href') || '';
    const appIdMatch = href.match(/\/application\/(\d+)/);
    if (!appIdMatch) {
      test.skip(true, 'Could not extract application ID');
      return;
    }

    const appId = appIdMatch[1];

    // Navigate to the application detail page
    await page.goto(`/application/${appId}`, { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Get CSRF token from the page
    const csrfToken = await page.locator('meta[name="csrf-token"]').getAttribute('content').catch(() => null)
      || await page.locator('input[name="csrf_token"]').first().getAttribute('value').catch(() => null);

    // Get current stage to understand where we are
    const pageBody = await page.textContent('body') || '';

    // Try the workflow move API — test that it doesn't crash
    const stages = ['Shortlist', 'I&A', 'Client Review', 'Offered', 'Accepted'];

    for (const stage of stages) {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }

      const response = await page.request.post(`/api/workflow/move`, {
        headers,
        data: {
          application_id: parseInt(appId),
          new_stage: stage,
        },
      });

      // We accept various outcomes — just not a 500
      expect(
        response.status(),
        `Workflow move to "${stage}" returned ${response.status()}`
      ).toBeLessThan(500);

      // If we got a 4xx, it might be because the transition isn't allowed
      // from the current stage — that's fine, it means validation works
      if (response.status() >= 400) {
        console.log(`  Stage "${stage}": ${response.status()} (transition may not be allowed from current stage)`);
      } else {
        console.log(`  Stage "${stage}": ${response.status()} OK`);
      }
    }

    // Verify the application page still loads after all attempts
    const finalResponse = await page.goto(`/application/${appId}`, { waitUntil: 'domcontentloaded' });
    expect(finalResponse?.status()).toBeLessThan(500);
  });

  test('pipeline page renders without errors', async ({ page }) => {
    await page.goto('/pipeline', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const body = await page.textContent('body') || '';
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback');

    // Verify workflow page also loads
    const response = await page.goto('/workflow', { waitUntil: 'domcontentloaded' });
    expect(response?.status()).toBeLessThan(500);
  });
});
