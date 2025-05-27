import { test, expect, Page } from '@playwright/test';

const user = { username: 'AliceSmith', password: 'AlicePass1!' };

async function login(page: Page) {
  await page.goto('/login');
  await expect(page.locator('#username')).toBeVisible({ timeout: 10000 });
  await page.fill('#username', user.username);
  await page.fill('#password', user.password);
  await page.locator('#login-form button[type="submit"]').click();
  await expect(page).toHaveURL(/\/$/, { timeout: 30000 });
  await expect(page.locator('#logout-link')).toBeVisible({ timeout: 15000 });
  await expect(
    page.locator(`#dynamic-nav-links a[href="/profile"]:has-text("${user.username}")`)
  ).toBeVisible({ timeout: 15000 });
}

async function addItemToCart(page: Page) {
  await page.goto('/');
  await expect(page.locator('#loading-indicator')).toBeHidden({ timeout: 15000 });
  const firstProduct = page.locator('article.product-card').first();
  await expect(firstProduct).toBeVisible();
  const initialCartCount = await page.locator('#cart-item-count').textContent();
  await firstProduct.locator('button.add-to-cart-btn').click();
  await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Added', { timeout: 10000 });
  await expect(page.locator('#cart-item-count')).not.toHaveText(initialCartCount || '', { timeout: 5000 });
}

test.describe('Checkout Process', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
      localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true');
    });
    await login(page);
    await addItemToCart(page);
  });

  test('should show checkout form with cart summary', async ({ page }) => {
    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.waitForSelector('#credit-card-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await expect(page.locator('h1')).toHaveText(/Checkout/);
    await expect(page.locator('#cart-summary')).toBeVisible();
    const itemRows = page.locator('#cart-summary tbody tr');
    expect(await itemRows.count()).toBeGreaterThan(0);
    const addrOptions = page.locator('#address-id option:not([value=""])');
    expect(await addrOptions.count()).toBeGreaterThan(0);
    const cardOptions = page.locator('#credit-card-id option:not([value=""])');
    expect(await cardOptions.count()).toBeGreaterThan(0);
  });

  test('should validate required fields in checkout form', async ({ page }) => {
    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.waitForSelector('#credit-card-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.waitForSelector('form#checkout-form', { state: 'attached', timeout: 15000 });
    await page.selectOption('#address-id', { value: '' });
    await page.selectOption('#credit-card-id', { value: '' });
    await page.locator('#place-order-btn').click({ force: true });
    await expect(page.locator('#global-message-container .global-message.error-message')).toBeVisible();
    await expect(page).toHaveURL(/\/checkout/);
  });

  test('should successfully complete an order', async ({ page }) => {
    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.waitForSelector('#credit-card-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.waitForSelector('form#checkout-form', { state: 'attached', timeout: 15000 });
    await page.evaluate(() => {
      const addr = document.querySelector<HTMLSelectElement>('#address-id');
      if (addr) addr.selectedIndex = 1;
      const card = document.querySelector<HTMLSelectElement>('#credit-card-id');
      if (card) card.selectedIndex = 1;
    });
    await page.locator('#place-order-btn').click();
    await expect(page.locator('#global-message-container .global-message')).toContainText(/Order/);
    await expect(page).toHaveURL(/\/orders/, { timeout: 20000 });
  });

  test('should demonstrate BOLA vulnerability UI on checkout page', async ({ page }) => {
    await page.evaluate(() => localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true'));
    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.waitForSelector('#credit-card-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await expect(page.locator('#bola-demo-section')).toBeVisible();
    await page.check('#order-for-other-user');
    await expect(page.locator('#bola-demo-fields')).toBeVisible();
    await expect(page.locator('#target-user-id')).toBeEnabled();
    await expect(page.locator('#bola-warning-container')).toBeVisible();
    await expect(page.locator('#theft-preview')).toBeVisible();
  });

  test('should handle checkout with empty cart', async ({ page }) => {
    await page.evaluate(() => localStorage.setItem('cart', '[]'));
    await page.goto('/checkout');
    await expect(page.locator('#global-message-container .global-message.info-message')).toBeVisible();
    await page.waitForURL('/', { timeout: 15000 });
  });
});
