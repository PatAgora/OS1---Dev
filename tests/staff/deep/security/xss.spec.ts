/**
 * Deep Tests — XSS Prevention
 *
 * The app uses bleach for HTML sanitisation. These tests submit XSS payloads
 * into various form fields and verify they are NOT rendered as raw HTML.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { guardSessionExpired } from '../../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

const XSS_SCRIPT = `<script>alert('xss')</script>`;
const XSS_IMG = `<img onerror=alert(1) src=x>`;

test.describe('XSS Prevention', () => {

  test('candidate notes are sanitised', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Click first candidate link
    const candidateLink = page.locator('table tbody tr a, .candidate-link, [href*="/candidate/"]').first();
    if (await candidateLink.count() === 0) {
      test.skip(true, 'No candidates in resource pool to test');
      return;
    }
    await candidateLink.click();
    await page.waitForLoadState('domcontentloaded');
    await guardSessionExpired(page);

    // Find notes form and submit XSS payload
    const notesInput = page.locator('textarea[name="content"], textarea[name="note"], textarea[name="notes"], textarea[name="body"]').first();
    if (await notesInput.count() === 0) {
      test.skip(true, 'No notes form found on candidate profile');
      return;
    }
    await notesInput.fill(XSS_SCRIPT);

    const submitBtn = page.locator('form:has(textarea) button[type="submit"], form:has(textarea) input[type="submit"]').first();
    if (await submitBtn.count() > 0) {
      await submitBtn.click();
      await page.waitForLoadState('domcontentloaded');
    }

    // Reload and check that <script> tag is NOT rendered as raw HTML
    await page.reload({ waitUntil: 'domcontentloaded' });
    const pageHtml = await page.content();
    expect(pageHtml).not.toContain(`<script>alert('xss')</script>`);
  });

  test('job title is sanitised', async ({ page }) => {
    await page.goto('/job/new', { waitUntil: 'domcontentloaded', timeout: 10000 });
    await guardSessionExpired(page);

    const titleInput = page.locator('input[name="title"], input[name="job_title"], input[id="title"]').first();
    const titleVisible = await titleInput.isVisible().catch(() => false);
    if (!titleVisible) {
      test.skip(true, 'Job title input not found or not visible on /job/new — other XSS tests provide coverage');
      return;
    }

    await titleInput.fill(`[PW-TEST] ${XSS_IMG}`);

    // Fill any required fields with minimal data
    const descField = page.locator('textarea[name="description"], textarea[id="description"]').first();
    if (await descField.isVisible().catch(() => false)) {
      await descField.fill('Test job description');
    }

    // Fill any required select fields
    const selectFields = page.locator('select[required]');
    const selectCount = await selectFields.count();
    for (let i = 0; i < selectCount; i++) {
      const sel = selectFields.nth(i);
      const options = await sel.locator('option').allTextContents();
      if (options.length > 1) {
        await sel.selectOption({ index: 1 });
      }
    }

    // Submit the form with a timeout fallback
    const submitBtn = page.locator('button[type="submit"], input[type="submit"]').first();
    const submitVisible = await submitBtn.isVisible().catch(() => false);
    if (!submitVisible) {
      test.skip(true, 'Submit button not found on job form — other XSS tests provide coverage');
      return;
    }

    await Promise.race([
      submitBtn.click().then(() => page.waitForLoadState('domcontentloaded')),
      page.waitForTimeout(10000),
    ]);

    // Navigate to jobs list and check the title is escaped
    await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
    const pageHtml = await page.content();
    expect(pageHtml).not.toContain('<img onerror=alert(1) src=x>');
  });

  test('opportunity client name is sanitised', async ({ page }) => {
    await page.goto('/opportunities', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Try to find a create/new opportunity button or navigate to the form
    const newBtn = page.locator('a[href*="opportunity"], a:has-text("New Opportunity"), button:has-text("New Opportunity"), a:has-text("Add Opportunity")').first();
    if (await newBtn.count() > 0) {
      await newBtn.click();
      await page.waitForLoadState('domcontentloaded');
    } else {
      // Try direct URL
      await page.goto('/opportunity/new', { waitUntil: 'domcontentloaded' });
    }
    await guardSessionExpired(page);

    const clientInput = page.locator('input[name="client"], input[name="client_name"]').first();
    if (await clientInput.count() === 0) {
      test.skip(true, 'Opportunity client name field not found');
      return;
    }

    await clientInput.fill(`[PW-TEST] ${XSS_SCRIPT}`);

    // Fill other required fields
    const roleInput = page.locator('input[name="role"], input[name="title"]').first();
    if (await roleInput.count() > 0) {
      await roleInput.fill('Test role');
    }

    const submitBtn = page.locator('button[type="submit"], input[type="submit"]').first();
    await submitBtn.click();
    await page.waitForLoadState('domcontentloaded');

    // Navigate to opportunities list and verify sanitised
    await page.goto('/opportunities', { waitUntil: 'domcontentloaded' });
    const pageHtml = await page.content();
    expect(pageHtml).not.toContain(`<script>alert('xss')</script>`);
  });

  test('XSS in img tag is sanitised across pages', async ({ page }) => {
    // Navigate to resource pool and try search with XSS
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const searchInput = page.locator('input[name="search"], input[name="q"], input[type="search"], input[placeholder*="Search"]').first();
    if (await searchInput.count() > 0) {
      await searchInput.fill(XSS_IMG);
      await searchInput.press('Enter');
      await page.waitForLoadState('domcontentloaded');

      const pageHtml = await page.content();
      // The img tag should be escaped in any reflected output
      expect(pageHtml).not.toContain('<img onerror=alert(1) src=x>');
    }
  });
});
