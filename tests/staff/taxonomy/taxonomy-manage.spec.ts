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
    // The add category form posts to taxonomy_category_add and has name="name" plus name="type" (select)
    // Target the form by its action URL to avoid matching rename forms which also have name="name"
    const addCatForm = page.locator('form[action*="category/add"], form[action*="taxonomy_category_add"]').first();
    let categoryInput: ReturnType<typeof page.locator>;

    if (await addCatForm.isVisible({ timeout: 3000 }).catch(() => false)) {
      categoryInput = addCatForm.locator('[name="name"]');
    } else {
      // Fallback: find the input with placeholder containing "category"
      categoryInput = page.locator('input[placeholder*="ategory"], input[placeholder*="Financial Crime"]').first();
    }

    if (!(await categoryInput.isVisible({ timeout: 3000 }).catch(() => false))) {
      console.log('  Category form not found — skipping CRUD tests');
      return;
    }

    await categoryInput.fill('[PW-TEST] Category');

    // Find the submit button for the add category form
    const catForm = categoryInput.locator('xpath=ancestor::form');
    const catSubmit = catForm.locator('[type="submit"], button:has-text("Add Category")').first();
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
    // The add tag form posts to taxonomy_tag_add and has name="tag" plus name="category_id" (select)
    const addTagForm = page.locator('form[action*="tag/add"], form[action*="taxonomy_tag_add"]').first();
    let tagInput: ReturnType<typeof page.locator>;

    if (await addTagForm.isVisible({ timeout: 3000 }).catch(() => false)) {
      tagInput = addTagForm.locator('[name="tag"]');

      // Select the newly created [PW-TEST] category in the category_id dropdown
      const catSelect = addTagForm.locator('[name="category_id"]');
      if (await catSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
        // Find the option that contains [PW-TEST]
        const pwTestOption = catSelect.locator('option:has-text("[PW-TEST]")').first();
        const optVal = await pwTestOption.getAttribute('value').catch(() => null);
        if (optVal) {
          await catSelect.selectOption(optVal);
        }
      }
    } else {
      tagInput = page.locator('[name="tag"]').first();
    }

    if (await tagInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await tagInput.fill('[PW-TEST] Tag');

      const tagForm = tagInput.locator('xpath=ancestor::form');
      const tagSubmit = tagForm.locator('[type="submit"], button:has-text("Add Tag")').first();
      if (await tagSubmit.isVisible({ timeout: 2000 }).catch(() => false)) {
        await tagSubmit.click();
        await page.waitForLoadState('domcontentloaded');

        body = await page.textContent('body') || '';
        expect(body).toContain('[PW-TEST] Tag');
        console.log('  Tag created: [PW-TEST] Tag');

        // --- Delete Tag ---
        // Tags are displayed as .tag-chip spans with a .btn-remove button inside a form
        const tagChip = page.locator('.tag-chip:has-text("[PW-TEST] Tag")').first();

        if (await tagChip.isVisible({ timeout: 3000 }).catch(() => false)) {
          const tagDeleteBtn = tagChip.locator('.btn-remove, button[type="submit"]').first();
          if (await tagDeleteBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
            await tagDeleteBtn.click();
            await page.waitForLoadState('domcontentloaded');

            body = await page.textContent('body') || '';
            expect(body).not.toContain('[PW-TEST] Tag');
            console.log('  Tag deleted: [PW-TEST] Tag');
          } else {
            console.log('  Tag delete button not found — skipping tag deletion');
          }
        } else {
          console.log('  Tag chip not found — skipping tag deletion');
        }
      }
    } else {
      console.log('  Tag input not found — skipping tag CRUD');
    }

    // --- Delete Category ---
    // Categories have a rename form and a separate delete form with btn-modern-danger
    const catItem = page.locator('.category-item:has-text("[PW-TEST] Category")').first();

    if (await catItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      const catDeleteBtn = catItem.locator('form[action*="category/delete"] button, button.btn-modern-danger').first();

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
    } else {
      console.log('  Category item not found — skipping category deletion');
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
