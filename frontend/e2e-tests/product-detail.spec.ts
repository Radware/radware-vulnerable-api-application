import { test, expect } from '@playwright/test';

const testData = {
  validProductId: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
  nonExistentProductId: '00000000-0000-0000-0000-000000000000'
};

test.describe('Product Detail Page', () => {
  async function waitForProductLoad(page) {
    await expect(page.locator('#product-loading')).toBeHidden({ timeout: 15000 });
    await expect(page.locator('#product-detail-container')).toBeVisible({ timeout: 10000 });
  }

  test('should display product details correctly', async ({ page }) => {
    await page.goto(`/products/${testData.validProductId}`);

    await waitForProductLoad(page);

    await expect(page.locator('#product-name-detail')).toBeVisible();
    await expect(page.locator('#product-price-detail')).toBeVisible();
    await expect(page.locator('#add-to-cart-form button[type="submit"]')).toBeVisible();
  });

  test('should handle quantity changes correctly', async ({ page }) => {
    await page.goto(`/products/${testData.validProductId}`);

    await waitForProductLoad(page);

    const quantityInput = page.locator('#quantity-detail');
    await expect(quantityInput).toHaveValue('1');

    const increaseBtn = page.locator('.quantity-btn.increase');
    await increaseBtn.click();
    await expect(quantityInput).toHaveValue('2');
  });

  test('should add product to cart successfully', async ({ page }) => {
    await page.goto(`/products/${testData.validProductId}`);

    await waitForProductLoad(page);

    const cartBadge = page.locator('#cart-item-count');
    const startCount = parseInt((await cartBadge.innerText()) || '0', 10);

    await page.locator('#add-to-cart-btn-detail').click();

    await expect(
      page.locator('#global-message-container .global-message.success-message')
    ).toContainText('Added', { timeout: 10000 });

    const endCount = parseInt((await cartBadge.innerText()) || '0', 10);
    expect(endCount).toBeGreaterThan(startCount);
  });

  test('should expand and collapse accordion sections', async ({ page }) => {
    await page.goto(`/products/${testData.validProductId}`);

    await waitForProductLoad(page);

    const headers = page.locator('.accordion-header');
    const count = await headers.count();
    if (count === 0) {
      test.skip(true, 'No accordion sections found');
    } else {
      const firstHeader = headers.first();
      const contentId = await firstHeader.getAttribute('aria-controls');
      const content = page.locator(`#${contentId}`);

      await firstHeader.click();
      await expect(firstHeader).toHaveAttribute('aria-expanded', 'true');
      await expect(content).toBeVisible();

      await firstHeader.click();
      await expect(firstHeader).toHaveAttribute('aria-expanded', 'false');
    }
  });

  test('should show proper error state for non-existent product', async ({ page }) => {
    await page.goto(`/products/${testData.nonExistentProductId}`);

    await expect(page.locator('#product-detail-container')).toContainText(
      /sorry, we couldn't load|product not found/i,
      { timeout: 10000 }
    );
  });

  test('should show parameter pollution demo section when logged in', async ({ page }) => {
    await page.goto('/login');
    await page.evaluate(() => localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true'));
    await page.fill('#username', 'AliceSmith');
    await page.fill('#password', 'AlicePass1!');
    await page.locator('#login-form button[type="submit"]').click();

    await expect(page.locator('#logout-link')).toBeVisible({ timeout: 15000 });

    await page.goto(`/products/${testData.validProductId}`);
    await waitForProductLoad(page);

    await expect(page.locator('#parameter-pollution-form')).toBeVisible();
  });

  test('should handle out of stock products correctly', async ({ page }) => {
    await page.goto(`/products/${testData.validProductId}`);

    await waitForProductLoad(page);

    const stockBadge = page.locator('.stock-badge');
    const text = (await stockBadge.innerText()).toLowerCase();

    if (text.includes('out of stock')) {
      await expect(page.locator('#add-to-cart-btn-detail')).toBeDisabled();
    }
  });
});
