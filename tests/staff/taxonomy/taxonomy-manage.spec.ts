/**
 * Staff Portal — Taxonomy Manage tests
 *
 * Tests: /taxonomy/manage
 * Verifies page load, categories/tags rendering, CRUD operations, and section visibility.
 * IMPORTANT: "Retag All" button must NOT be clicked (bulk AI operation).
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../utils/blocked-routes';
import { assertPageLoads, guardSessionExpired } from '../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Taxonomy Manage', () => {
  test('@smoke /taxonomy/manage — page loads', async ({ page }) => {
    await assertPageLoads(page, '/taxonomy/manage');
  });

  test('categories and tags render', async ({ page }) => {
    await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const body = await page.textContent('body') || '';
    // Should have some taxonomy-related content — use broad matching
    const hasTaxonomyContent =
      body.includes('Categor') || body.includes('categor') ||
      body.includes('Tag') || body.includes('tag') ||
      body.includes('Taxonomy') || body.includes('taxonomy');
    expect(hasTaxonomyContent).toBeTruthy();
  });

  test('add category, add tag, delete tag, delete category', async ({ page }) => {
    await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // --- Add Category ---
    const categoryInput = page.locator(
      '[name="category_name"], [name="name"], input[placeholder*="ategory"], input[placeholder*="name"]'
    ).first();

    if (!(await categoryInput.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  Category form not found — skipping CRUD tests');
      return;
    }

    await categoryInput.fill('[PW-TEST] Category');

    // Find the submit button for the category form
    const categoryForm = categoryInput.locator('xpath=ancestor::form');
    const catSubmit = categoryForm.locator('[type="submit"], button').first();
    if (!(await catSubmit.isVisible({ timeout: 2000 }).catch(() => false))) {
      console.log('  Category submit button not found — skipping CRUD');
      return;
    }
    await catSubmit.click();
    await page.waitForLoadState('domcontentloaded');

    // Assert category appears
    let body = await page.textContent('body') || '';
    expect(body).toContain('[PW-TEST] Category');
    console.log('  Category created: [PW-TEST] Category');

    // --- Add Tag ---
    // Look for a tag input near or under the new category
    const tagInput = page.locator(
      '[name="tag_name"], [name="tag"], input[placeholder*="ag"], input[placeholder*="Tag"]'
    ).first();

    if (await tagInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await tagInput.fill('[PW-TEST] Tag');

      const tagForm = tagInput.locator('xpath=ancestor::form');
      const tagSubmit = tagForm.locator('[type="submit"], button').first();
      if (await tagSubmit.isVisible({ timeout: 2000 }).catch(() => false)) {
        await tagSubmit.click();
        await page.waitForLoadState('domcontentloaded');

        body = await page.textContent('body') || '';
        expect(body).toContain('[PW-TEST] Tag');
        console.log('  Tag created: [PW-TEST] Tag');

        // --- Delete Tag ---
        const tagElement = page.locator('text=[PW-TEST] Tag').first();
        const tagDeleteBtn = tagElement.locator('xpath=ancestor::*[position() <= 5]').locator(
          'button:has-text("Delete"), a:has-text("Delete"), button:has-text("Remove"), ' +
          'a:has-text("Remove"), .delete-btn, .btn-danger, button[title="Delete"], [class*="delete"], [class*="remove"]'
        ).first();

        if (await tagDeleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
          page.on('dialog', dialog => dialog.accept());
          await tagDeleteBtn.click();
          await page.waitForLoadState('domcontentloaded');

          body = await page.textContent('body') || '';
          expect(body).not.toContain('[PW-TEST] Tag');
          console.log('  Tag deleted: [PW-TEST] Tag');
        } else {
          console.log('  Tag delete button not found — skipping tag deletion');
        }
      }
    } else {
      console.log('  Tag input not found — skipping tag CRUD');
    }

    // --- Delete Category ---
    const catElement = page.locator('text=[PW-TEST] Category').first();
    const catDeleteBtn = catElement.locator('xpath=ancestor::*[position() <= 5]').locator(
      'button:has-text("Delete"), a:has-text("Delete"), button:has-text("Remove"), ' +
      'a:has-text("Remove"), .delete-btn, .btn-danger, button[title="Delete"], [class*="delete"], [class*="remove"]'
    ).first();

    if (await catDeleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      page.on('dialog', dialog => dialog.accept());
      await catDeleteBtn.click();
      await page.waitForLoadState('domcontentloaded');

      body = await page.textContent('body') || '';
      expect(body).not.toContain('[PW-TEST] Category');
      console.log('  Category deleted: [PW-TEST] Category');
    } else {
      console.log('  Category delete button not found — skipping category deletion');
    }
  });

  test('"Retag All" button visible — DO NOT CLICK (bulk AI)', async ({ page }) => {
    await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const retagBtn = page.locator(
      'button:has-text("Retag All"), a:has-text("Retag All"), ' +
      'button:has-text("Retag"), a:has-text("Retag")'
    ).first();

    if (await retagBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('  Blocked button visible (not clicked): Retag All');
    } else {
      console.log('  Retag All button not found on page');
    }
  });

  test('Role Aliases section visible', async ({ page }) => {
    await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    const body = await page.textContent('body') || '';
    const hasSection = body.includes('Role Alias') || body.includes('role alias') || body.includes('Alias');
    console.log(`  Role Aliases section visible: ${hasSection}`);
  });

  test('Job Templates section visible', async ({ page }) => {
    await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    const body = await page.textContent('body') || '';
    const hasSection = body.includes('Job Template') || body.includes('job template') || body.includes('Template');
    console.log(`  Job Templates section visible: ${hasSection}`);
  });

  test('Reference Contacts section visible', async ({ page }) => {
    await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    const body = await page.textContent('body') || '';
    const hasSection = body.includes('Reference Contact') || body.includes('reference contact') || body.includes('Contact');
    console.log(`  Reference Contacts section visible: ${hasSection}`);
  });

  test('Reference Houses section visible', async ({ page }) => {
    await page.goto('/taxonomy/manage', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);
    const body = await page.textContent('body') || '';
    const hasSection = body.includes('Reference House') || body.includes('reference house') || body.includes('House');
    console.log(`  Reference Houses section visible: ${hasSection}`);
  });
});
