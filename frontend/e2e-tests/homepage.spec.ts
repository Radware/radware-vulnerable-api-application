import { test, expect } from '@playwright/test';

test.describe('Homepage and Product Listing', () => {
  test('should load the homepage with header, search bar, and products', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/RVA eCommerce|Radware/i, { timeout: 10000 });

    await expect(page.locator('main h1')).toBeVisible();
    await expect(page.locator('#search-term')).toBeVisible();
    await expect(page.locator('form#search-form button[type="submit"]')).toBeVisible();

    const loading = page.locator('#loading-indicator');
    await expect(loading).toBeHidden({ timeout: 15000 });

    const products = page.locator('#products-container .product-card');
    await expect(products.first()).toBeVisible({ timeout: 10000 });
    expect(await products.count()).toBeGreaterThan(0);

    const firstCard = products.first();
    await expect(firstCard.locator('img.product-image')).toBeVisible();
    await expect(firstCard.locator('h3.product-title')).toBeVisible();
    await expect(firstCard.locator('p.price')).toBeVisible();
    await expect(firstCard.locator('button.add-to-cart-btn')).toBeVisible();
  });
  
  test('should be able to search for products', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true');
    });
    await page.goto('/');

    const loading = page.locator('#loading-indicator');
    await expect(loading).toBeHidden({ timeout: 15000 });

    const productLocator = page.locator('#products-container .product-card');
    await expect(productLocator.first()).toBeVisible({ timeout: 10000 });
    const initialCount = await productLocator.count();

    await page.fill('#search-term', 'Laptop');
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('/api/products/search') && r.status() === 200),
      page.locator('form#search-form button[type="submit"]').click()
    ]);
    expect(response.ok()).toBeTruthy();

    await expect(productLocator.first()).toBeVisible({ timeout: 10000 });
    const filteredCount = await productLocator.count();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
    await expect(productLocator.locator('h3.product-title')).toContainText(/Laptop/i);
    await expect(page.locator('#search-info')).toBeVisible();
  });
  
  test('should add a product to cart and show feedback', async ({ page }) => {
    await page.goto('/');

    const loading = page.locator('#loading-indicator');
    await expect(loading).toBeHidden({ timeout: 15000 });

    const cartBadge = page.locator('#cart-item-count');
    const startCount = parseInt((await cartBadge.innerText()) || '0', 10);

    const firstProduct = page.locator('#products-container .product-card').first();
    await firstProduct.locator('button.add-to-cart-btn').click();

    const successMessage = page.locator('#global-message-container .global-message.success-message');
    await expect(successMessage).toContainText('Added', { timeout: 10000 });

    const endCount = parseInt((await cartBadge.innerText()) || '0', 10);
    expect(endCount).toBeGreaterThan(startCount);
  });
  
  test('should demonstrate potential injection vulnerability in search', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true');
    });
    await page.goto('/');

    const loading = page.locator('#loading-indicator');
    await expect(loading).toBeHidden({ timeout: 15000 });

    await page.fill('#search-term', "' OR 1=1 --");
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/api/products/search') && r.status() === 200),
      page.locator('form#search-form button[type="submit"]').click()
    ]);

    await expect(page.locator('#search-info')).toBeVisible();
  });
  
  test('should have responsive design for different screen sizes', async ({ page }) => {
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/');

    const loading = page.locator('#loading-indicator');
    await expect(loading).toBeHidden({ timeout: 15000 });

    const desktopGridStyle = await page.evaluate(() => {
      const container = document.querySelector('#products-container');
      return container ? window.getComputedStyle(container).gridTemplateColumns : '';
    });

    await page.setViewportSize({ width: 480, height: 800 });

    const mobileGridStyle = await page.evaluate(() => {
      const container = document.querySelector('#products-container');
      return container ? window.getComputedStyle(container).gridTemplateColumns : '';
    });

    expect(desktopGridStyle).not.toBe(mobileGridStyle);
  });
});
