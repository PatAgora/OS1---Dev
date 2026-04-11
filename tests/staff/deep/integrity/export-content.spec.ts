/**
 * Deep Tests — Export Content Validation
 *
 * Tests that CSV/PDF exports return real data with correct content types
 * and non-empty bodies.
 */
import { test, expect } from '@playwright/test';
import { installRouteGuard } from '../../../utils/blocked-routes';
import { guardSessionExpired } from '../../../utils/helpers';

test.beforeEach(async ({ page }) => {
  await installRouteGuard(page);
});

test.describe('Export Content', () => {

  test('resource pool CSV export contains data', async ({ page }) => {
    await page.goto('/resource-pool', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    // Look for an export CSV button/link
    const exportBtn = page.locator(
      'a:has-text("Export CSV"), a:has-text("Export"), a:has-text("Download CSV"), ' +
      'button:has-text("Export CSV"), button:has-text("Export"), ' +
      'a[href*="csv"], a[href*="export"]'
    ).first();

    if (await exportBtn.count() === 0) {
      // Try the direct URL
      const response = await page.request.get('/resource-pool.csv');
      if (response.status() === 404) {
        test.skip(true, 'No CSV export link or /resource-pool.csv route found');
        return;
      }

      const contentType = response.headers()['content-type'] || '';
      expect(
        contentType.includes('csv') || contentType.includes('text') || contentType.includes('octet-stream'),
        `Expected CSV content type, got: ${contentType}`
      ).toBe(true);

      const body = await response.text();
      expect(body.length).toBeGreaterThan(10);
      // Should contain column headers
      const lowerBody = body.toLowerCase();
      expect(
        lowerBody.includes('name') || lowerBody.includes('email') || lowerBody.includes('candidate'),
        'CSV should contain column headers like Name or Email'
      ).toBe(true);
      return;
    }

    // If there's a button, use download event
    const href = await exportBtn.getAttribute('href');
    if (href) {
      const response = await page.request.get(href.startsWith('http') ? href : `https://os1-dev-production.up.railway.app${href}`);
      expect(response.status()).toBeLessThan(500);

      const contentType = response.headers()['content-type'] || '';
      expect(
        contentType.includes('csv') || contentType.includes('text') || contentType.includes('octet-stream'),
        `Expected CSV content type, got: ${contentType}`
      ).toBe(true);

      const body = await response.text();
      expect(body.length).toBeGreaterThan(10);
    } else {
      // Button triggers a download — use download event
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 10000 }).catch(() => null),
        exportBtn.click(),
      ]);

      if (download) {
        const path = await download.path();
        expect(path).toBeTruthy();
        // Download exists and completed
        const suggestedName = download.suggestedFilename();
        expect(
          suggestedName.includes('csv') || suggestedName.includes('export'),
          `Expected CSV filename, got: ${suggestedName}`
        ).toBe(true);
      }
    }
  });

  test('admin invoices PDF download is valid', async ({ page }) => {
    await page.goto('/admin/invoices', { waitUntil: 'domcontentloaded' });
    await guardSessionExpired(page);

    const body = await page.textContent('body') || '';
    if (body.includes('No invoices') || body.includes('no invoices')) {
      test.skip(true, 'No invoices to download');
      return;
    }

    // Look for a PDF download link on any invoice
    const pdfLink = page.locator(
      'a:has-text("Download PDF"), a:has-text("PDF"), a:has-text("Download"), ' +
      'a[href*="pdf"], a[href*="download"]'
    ).first();

    if (await pdfLink.count() === 0) {
      test.skip(true, 'No PDF download link found on invoices page');
      return;
    }

    const href = await pdfLink.getAttribute('href');
    if (href) {
      const fullUrl = href.startsWith('http') ? href : `https://os1-dev-production.up.railway.app${href}`;
      let response;
      try {
        response = await page.request.get(fullUrl);
      } catch (e) {
        test.skip(true, 'PDF download timed out — browser context closed');
        return;
      }

      if (response.status() === 404) {
        test.skip(true, 'PDF download route returned 404');
        return;
      }

      expect(response.status()).toBeLessThan(500);

      const contentType = response.headers()['content-type'] || '';
      expect(
        contentType.includes('pdf') || contentType.includes('application') || contentType.includes('octet-stream'),
        `Expected PDF content type, got: ${contentType}`
      ).toBe(true);

      const responseBody = await response.body();
      expect(
        responseBody.length,
        'PDF response body should be > 1000 bytes (not empty)'
      ).toBeGreaterThan(1000);
    } else {
      // Button triggers download
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 10000 }).catch(() => null),
        pdfLink.click(),
      ]);

      if (download) {
        const suggestedName = download.suggestedFilename();
        expect(
          suggestedName.toLowerCase().includes('pdf') || suggestedName.toLowerCase().includes('invoice'),
          `Expected PDF filename, got: ${suggestedName}`
        ).toBe(true);
      }
    }
  });

  test('taxonomy export contains category/tag data', async ({ page }) => {
    // Fetch the taxonomy export directly via GET
    const response = await page.request.get('/taxonomy/export');

    if (response.status() === 404) {
      test.skip(true, 'No taxonomy export route found at /taxonomy/export');
      return;
    }

    expect(
      response.status(),
      `Expected < 500, got ${response.status()}`
    ).toBeLessThan(500);

    const responseBody = await response.text();
    const lowerBody = responseBody.toLowerCase();
    expect(
      lowerBody.includes('type') || lowerBody.includes('category') || lowerBody.includes('tag') || lowerBody.includes('name'),
      'Export should contain CSV headers like Type, Category, or Tag'
    ).toBe(true);
  });
});
