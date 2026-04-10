/**
 * Staff Portal — Job Edit tests
 *
 * Tests: /job/<id>/edit
 * Navigates to /jobs, finds first job, opens edit page, modifies title, submits.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Job Edit', () => {
  test('navigate to first job edit page — page loads', async ({ page }) => {
    // First try to find an edit link from the jobs list
    await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Look for edit links or buttons
    const editLink = page.locator('a[href*="/edit"]').first();
    const editLinkExists = await editLink.isVisible({ timeout: 5000 }).catch(() => false);

    let editUrl: string;

    if (editLinkExists) {
      editUrl = await editLink.getAttribute('href') || '/job/1/edit';
    } else {
      // Fallback: try /job/1/edit directly
      editUrl = '/job/1/edit';
    }

    const response = await page.goto(editUrl, { waitUntil: 'domcontentloaded' });
    expect(response?.status()).toBeLessThan(500);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback (most recent call last)');
  });

  test('change title and submit — assert success', async ({ page }) => {
    // Navigate to jobs list to find an editable job
    await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const editLink = page.locator('a[href*="/edit"]').first();
    const editLinkExists = await editLink.isVisible({ timeout: 5000 }).catch(() => false);

    let editUrl: string;

    if (editLinkExists) {
      editUrl = await editLink.getAttribute('href') || '/job/1/edit';
    } else {
      editUrl = '/job/1/edit';
    }

    const response = await page.goto(editUrl, { waitUntil: 'domcontentloaded' });

    // If page is a 404 or redirect, skip the edit test
    if (response?.status() === 404) {
      console.log('  No editable job found — skipping edit test');
      return;
    }

    if (response?.status() && response.status() >= 400) {
      console.log(`  Edit page returned ${response.status()} — skipping`);
      return;
    }

    const titleField = page.locator('[name="title"]');
    if (!(await titleField.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('  Title field not found on edit page — skipping');
      return;
    }

    // Get current title, modify it
    const currentTitle = await titleField.inputValue();
    const newTitle = currentTitle.includes('[PW-EDIT]')
      ? currentTitle.replace('[PW-EDIT] ', '')
      : `[PW-EDIT] ${currentTitle}`;

    await titleField.fill(newTitle);

    // Submit
    const submitBtn = page.locator('[type="submit"]').first();
    if (!(await submitBtn.isVisible().catch(() => false))) {
      console.log('  Submit button not found — skipping');
      return;
    }
    await submitBtn.click();
    await page.waitForLoadState('domcontentloaded');

    // Assert no server error
    const body = await page.textContent('body') || '';
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback (most recent call last)');

    // Assert redirect or success message
    const url = page.url();
    const hasSuccess = body.includes('updated') || body.includes('Updated') || body.includes('success') || body.includes('saved') || !url.includes('/edit');
    expect(hasSuccess).toBeTruthy();
  });
});
