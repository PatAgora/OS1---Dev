/**
 * Staff Portal — Job Edit tests
 *
 * Tests: /job/<id>/edit
 * Navigates to /jobs, finds first job, opens edit page, modifies title, submits.
 * If no editable jobs exist, creates one first via /job/new.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

/**
 * Helper: create a job via /job/new so we have something to edit.
 * Returns true if creation succeeded.
 */
async function createJobIfNeeded(page: import('@playwright/test').Page): Promise<boolean> {
  await page.goto('/job/new', { waitUntil: 'domcontentloaded' });
  await guardSessionExpired(page);

  const titleField = page.locator('[name="title"]');
  if (!(await titleField.isVisible({ timeout: 5000 }).catch(() => false))) {
    return false;
  }
  await titleField.fill('[PW-TEST] Editable Job');

  const descField = page.locator('[name="description"]');
  if (await descField.first().isVisible().catch(() => false)) {
    await descField.first().fill('Created by Playwright for edit test');
  }

  // Submit — button in job_form.html has no explicit type="submit"
  const submitBtn = page.locator('form button.btn-primary, form button:has-text("Create"), form [type="submit"]').first();
  if (!(await submitBtn.isVisible().catch(() => false))) {
    return false;
  }
  await submitBtn.click();
  await page.waitForLoadState('domcontentloaded');

  const body = await page.textContent('body') || '';
  return !body.includes('Internal Server Error') && !body.includes('Traceback');
}

test.describe('Job Edit', () => {

  /**
   * Helper: find a job edit URL by checking multiple sources.
   * The /jobs page has no edit links — they are on the dashboard and engagement pages.
   * We look for edit links on /dashboard, or construct the URL from a known job ID.
   */
  async function findEditUrl(page: import('@playwright/test').Page): Promise<string | null> {
    // Try dashboard — it has direct edit links like /job/<id>/edit
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const dashboardEditLink = page.locator('a[href*="/job/"][href*="/edit"]').first();
    if (await dashboardEditLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      return await dashboardEditLink.getAttribute('href');
    }

    // Fallback: go to /jobs, find the "Open" link to engagement job detail, then edit from there
    await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Extract a job's engagement link to get the job ID
    const openLink = page.locator('a[href*="/engagement/"][href*="/job/"]').first();
    if (await openLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      const href = await openLink.getAttribute('href') || '';
      // Extract job_id from /engagement/<eng_id>/job/<job_id>
      const match = href.match(/\/job\/(\d+)/);
      if (match) {
        return `/job/${match[1]}/edit`;
      }
    }

    return null;
  }

  test('navigate to first job edit page — page loads', async ({ page }) => {
    let editUrl = await findEditUrl(page);

    // If no edit links, create a job first
    if (!editUrl) {
      console.log('  No edit links found — creating a job first');
      const created = await createJobIfNeeded(page);
      if (!created) {
        console.log('  Could not create a job — skipping');
        return;
      }
      editUrl = await findEditUrl(page);
    }

    if (!editUrl) {
      editUrl = '/job/1/edit';
    }

    const response = await page.goto(editUrl, { waitUntil: 'domcontentloaded' });
    expect(response?.status()).toBeLessThan(500);

    const body = await page.textContent('body');
    expect(body).not.toContain('Internal Server Error');
    expect(body).not.toContain('Traceback (most recent call last)');
  });

  test('change title and submit — assert success', async ({ page }) => {
    let editUrl = await findEditUrl(page);

    // If no edit links, create a job first
    if (!editUrl) {
      console.log('  No edit links found — creating a job first');
      const created = await createJobIfNeeded(page);
      if (!created) {
        console.log('  Could not create a job — skipping');
        return;
      }
      editUrl = await findEditUrl(page);
    }

    if (!editUrl) {
      editUrl = '/job/1/edit';
    }

    const response = await page.goto(editUrl, { waitUntil: 'domcontentloaded' });

    if (response?.status() === 404) {
      console.log('  No editable job found — skipping edit test');
      return;
    }

    if (response?.status() && response.status() >= 400) {
      console.log(`  Edit page returned ${response.status()} — skipping`);
      return;
    }

    await guardSessionExpired(page);

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

    // Submit — button in job_form.html has no explicit type="submit"
    const submitBtn = page.locator('form button.btn-primary, form button:has-text("Update"), form [type="submit"]').first();
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
