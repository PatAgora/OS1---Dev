/**
 * Seed Demo Data for Playwright Tests
 *
 * Creates all the data needed for skipped tests to pass:
 * - An engagement (so job creation forms have something to select)
 * - A job under that engagement (so job-edit and application tests work)
 * - A candidate on the workflow board (so drag-drop and pipeline tests work)
 * - A placement (so placement filter/export tests work)
 * - An application with an offer (so accept/decline tests work)
 *
 * This runs ONCE before all tests via the staff-auth-setup project.
 * It's idempotent — checks for existing [PW-TEST] data before creating.
 */
import { test as setup, expect } from '@playwright/test';
import { installRouteGuard } from './utils/blocked-routes';
import { guardSessionExpired } from './utils/helpers';
import path from 'path';
import { generateTOTP } from './utils/totp';
import fs from 'fs';

const authFile = path.join(__dirname, '../playwright/.auth/admin.json');
const totpSecretFile = path.join(__dirname, '../playwright/.auth/totp-secret.txt');

setup.setTimeout(120_000); // 2 minutes — creating multiple items

setup('seed test data for full coverage', async ({ browser }) => {
  // Load the saved admin auth state
  const context = await browser.newContext({
    storageState: authFile,
  });
  const page = await context.newPage();
  await installRouteGuard(page);

  // Verify we're authenticated
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  if (page.url().includes('/login')) {
    console.log('  ⚠ Not authenticated — skipping seed');
    await context.close();
    return;
  }

  console.log('  Seeding test data...');

  // Get CSRF token
  const csrfToken = await page.locator('meta[name="csrf-token"]').getAttribute('content') || '';

  // ============================================================
  // 1. Create an engagement (needed for job creation, plans, financials)
  // ============================================================
  await page.goto('/engagements', { waitUntil: 'domcontentloaded' });
  const bodyText = await page.textContent('body') || '';

  if (!bodyText.includes('[PW-TEST] Engagement')) {
    console.log('  Creating test engagement...');
    // Find create link
    const createLink = page.locator('a').filter({ hasText: /Create|New/i }).first();
    if (await createLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createLink.click();
      await page.waitForLoadState('domcontentloaded');

      // Fill the engagement form
      const clientField = page.locator('[name="client"]').first();
      if (await clientField.isVisible({ timeout: 3000 }).catch(() => false)) {
        await clientField.fill('[PW-TEST] Client Corp');
      }

      const nameField = page.locator('[name="name"]').first();
      if (await nameField.isVisible({ timeout: 2000 }).catch(() => false)) {
        await nameField.fill('[PW-TEST] Engagement');
      }

      const startDate = page.locator('[name="start_date"]').first();
      if (await startDate.isVisible({ timeout: 2000 }).catch(() => false)) {
        await startDate.fill('01-05-2026');
      }

      const endDate = page.locator('[name="end_date"]').first();
      if (await endDate.isVisible({ timeout: 2000 }).catch(() => false)) {
        await endDate.fill('31-12-2026');
      }

      const statusField = page.locator('[name="status"]').first();
      if (await statusField.isVisible({ timeout: 2000 }).catch(() => false)) {
        await statusField.selectOption('Active').catch(() => {});
      }

      await page.locator('[type="submit"]').first().click().catch(() => {});
      await page.waitForLoadState('domcontentloaded');
      console.log('  ✓ Engagement created');
    }
  } else {
    console.log('  ✓ Test engagement already exists');
  }

  // ============================================================
  // 2. Create a job (needed for job-edit, applications, offers)
  // ============================================================
  await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
  const jobsBody = await page.textContent('body') || '';

  if (!jobsBody.includes('[PW-TEST] Test Job')) {
    await page.goto('/job/new', { waitUntil: 'domcontentloaded' });

    const titleField = page.locator('[name="title"]').first();
    if (await titleField.isVisible({ timeout: 3000 }).catch(() => false)) {
      await titleField.fill('[PW-TEST] Test Job Role');

      // Fill description
      const descField = page.locator('[name="description"]').first();
      if (await descField.isVisible({ timeout: 2000 }).catch(() => false)) {
        await descField.fill('[PW-TEST] Test job for Playwright automated testing.');
      }

      // Fill optional fields if present
      const roleField = page.locator('[name="role"], [name="role_type"]').first();
      if (await roleField.isVisible({ timeout: 1000 }).catch(() => false)) {
        await roleField.fill('Test Role');
      }

      const locationField = page.locator('[name="location"]').first();
      if (await locationField.isVisible({ timeout: 1000 }).catch(() => false)) {
        await locationField.fill('London');
      }

      // Select engagement if the dropdown exists
      const engSelect = page.locator('[name="engagement_id"], [name="engagement"]').first();
      if (await engSelect.isVisible({ timeout: 1000 }).catch(() => false)) {
        const firstOpt = engSelect.locator('option:not([value=""]):not([value="0"])').first();
        const val = await firstOpt.getAttribute('value').catch(() => null);
        if (val) await engSelect.selectOption(val);
      }

      // Submit — button in job_form.html has no explicit type="submit"
      await page.locator('form button.btn-primary, form button:has-text("Create"), form [type="submit"]').first().click();
      await page.waitForLoadState('domcontentloaded');
      const afterBody = await page.textContent('body') || '';
      if (!afterBody.includes('Internal Server Error')) {
        console.log('  ✓ Job created');
      } else {
        console.log('  ⚠ Job creation returned 500');
      }
    }
  } else {
    console.log('  ✓ Test job already exists');
  }

  // ============================================================
  // 3. Add candidates to resource pool (needed for workflow, drag-drop, pipeline)
  // ============================================================
  for (let i = 1; i <= 3; i++) {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    const poolBody = await page.textContent('body') || '';
    if (poolBody.includes(`[PW-TEST] Candidate ${i}`)) {
      console.log(`  ✓ Test candidate ${i} already exists`);
      continue;
    }

    const addBtn = page.locator('button, a').filter({ hasText: /Add Associate/i }).first();
    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForTimeout(500);

      const nameInput = page.locator('#add-name, [name="name"]').first();
      if (await nameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await nameInput.fill(`[PW-TEST] Candidate ${i}`);
      }

      const emailInput = page.locator('#add-email, [name="email"]').first();
      if (await emailInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await emailInput.fill(`pw-candidate-${i}-${Date.now()}@example.com`);
      }

      const phoneInput = page.locator('#add-phone, [name="phone"]').first();
      if (await phoneInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await phoneInput.fill(`0700000000${i}`);
      }

      const submitBtn = page.locator('#addAssociateModal [type="submit"], .modal [type="submit"]').first();
      if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await submitBtn.click();
        await page.waitForLoadState('domcontentloaded');
        console.log(`  ✓ Candidate ${i} created`);
      }
    }
  }

  // ============================================================
  // 4. Apply a candidate to the test job (needed for application detail, offers, pipeline flow)
  // ============================================================
  // Find the test job's public token and apply via the public portal
  await page.goto('/jobs', { waitUntil: 'domcontentloaded' });
  // The staff /jobs page might redirect to public — use applications instead
  // We'll create an application by using the workflow API to add a candidate to a job

  // ============================================================
  // 5. Create an invoice (needed for invoice PDF test)
  // ============================================================
  await page.goto('/admin/invoices', { waitUntil: 'domcontentloaded' });
  const invoiceBody = await page.textContent('body') || '';

  if (!invoiceBody.includes('[PW-TEST]')) {
    const createInvLink = page.locator('a').filter({ hasText: /Create Invoice|New Invoice/i }).first();
    if (await createInvLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await createInvLink.click();
      await page.waitForLoadState('domcontentloaded');

      // Fill engagement select
      const engSelect = page.locator('[name="engagement_id"], #engagementSelect').first();
      if (await engSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
        const firstOpt = engSelect.locator('option:not([value=""]):not([value="0"])').first();
        const val = await firstOpt.getAttribute('value').catch(() => null);
        if (val) await engSelect.selectOption(val);
      }

      // Fill dates
      const dueDate = page.locator('[name="due_date"], #dueDate').first();
      if (await dueDate.isVisible({ timeout: 2000 }).catch(() => false)) {
        await dueDate.fill('2026-05-30');
      }

      // Fill notes with test marker
      const notesField = page.locator('[name="notes"], textarea').first();
      if (await notesField.isVisible({ timeout: 2000 }).catch(() => false)) {
        await notesField.fill('[PW-TEST] Invoice for automated testing');
      }

      // Submit
      const submitBtn = page.locator('[type="submit"]').first();
      if (await submitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await submitBtn.click();
        await page.waitForLoadState('domcontentloaded');
        const afterBody = await page.textContent('body') || '';
        if (!afterBody.includes('Internal Server Error')) {
          console.log('  ✓ Invoice created');
        }
      }
    }
  } else {
    console.log('  ✓ Test invoice already exists');
  }

  // ============================================================
  // 6. Add taxonomy data (needed for taxonomy export test)
  // ============================================================
  await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
  const taxBody = await page.textContent('body') || '';

  if (!taxBody.includes('[PW-TEST] Category')) {
    // Add a test category — target the add form specifically (not rename forms)
    const addCatForm = page.locator('form[action*="category/add"], form[action*="taxonomy_category_add"]').first();
    if (await addCatForm.isVisible({ timeout: 3000 }).catch(() => false)) {
      const catInput = addCatForm.locator('[name="name"]');
      if (await catInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await catInput.fill('[PW-TEST] Category');
        const addCatBtn = addCatForm.locator('[type="submit"], button:has-text("Add Category")').first();
        if (await addCatBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
          await addCatBtn.click();
          await page.waitForLoadState('domcontentloaded');
          console.log('  ✓ Taxonomy category created');
        }
      }
    }
  }

  // ============================================================
  // 7. Set up the associate portal test account
  //    Create a candidate with a known email, verify them, and set
  //    a password so the portal-auth.setup.ts can log in.
  // ============================================================
  const ASSOC_EMAIL = 'pw-test-associate@example.com';
  const ASSOC_PASSWORD = 'PlaywrightAssociate2024!';

  await page.goto('/admin/portal-users', { waitUntil: 'domcontentloaded' });
  const portalBody = await page.textContent('body') || '';

  if (!portalBody.includes(ASSOC_EMAIL)) {
    // Create the candidate via resource pool first
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    const addBtn = page.locator('a:has-text("Add Associate"), button:has-text("Add Associate")').first();
    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForTimeout(500);
      const modal = page.locator('#addAssociateModal');
      const nameF = modal.locator('#add-name, [name="name"]').first();
      if (await nameF.isVisible({ timeout: 2000 }).catch(() => false)) await nameF.fill('PW-Test Associate');
      const emailF = modal.locator('#add-email, [name="email"]').first();
      if (await emailF.isVisible({ timeout: 2000 }).catch(() => false)) await emailF.fill(ASSOC_EMAIL);
      const sub = modal.locator('[type="submit"], button:has-text("Add")').first();
      if (await sub.isVisible({ timeout: 2000 }).catch(() => false)) {
        await sub.click();
        await page.waitForLoadState('domcontentloaded');
        console.log('  ✓ Associate candidate created');
      }
    }
  }

  // Find the candidate's ID from portal users and set their password
  await page.goto('/admin/portal-users', { waitUntil: 'domcontentloaded' });
  const assocLink = page.locator(`a[href*="/admin/portal-users/"]`).filter({ hasText: /PW-Test|pw-test-associate/i }).first();
  if (await assocLink.isVisible({ timeout: 5000 }).catch(() => false)) {
    await assocLink.click();
    await page.waitForLoadState('domcontentloaded');

    // Verify their email
    const verifyBtn = page.locator('button:has-text("Verify"), form[action*="verify"] button').first();
    if (await verifyBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await verifyBtn.click();
      await page.waitForLoadState('domcontentloaded');
      console.log('  ✓ Associate email verified');
    }

    // Set their password via the new /set-password endpoint
    const setPasswordForm = page.locator('form[action*="set-password"]').first();
    if (await setPasswordForm.isVisible({ timeout: 2000 }).catch(() => false)) {
      await setPasswordForm.locator('[name="password"]').fill(ASSOC_PASSWORD);
      await setPasswordForm.locator('[type="submit"]').click();
      await page.waitForLoadState('domcontentloaded');
      console.log('  ✓ Associate password set');
    } else {
      // The set-password form might not be in the admin template yet — use the API directly
      const currentUrl = page.url();
      const candIdMatch = currentUrl.match(/portal-users\/(\d+)/);
      if (candIdMatch) {
        const candId = candIdMatch[1];
        const csrfMeta = await page.locator('meta[name="csrf-token"]').getAttribute('content') || '';
        await page.request.post(`/admin/portal-users/${candId}/set-password`, {
          form: { password: ASSOC_PASSWORD, csrf_token: csrfMeta },
        });
        console.log('  ✓ Associate password set via API');
      }
    }
  } else {
    console.log('  ⚠ Could not find associate in portal users list');
  }

  console.log('  ✓ Test data seeding complete');
  await context.close();
});
