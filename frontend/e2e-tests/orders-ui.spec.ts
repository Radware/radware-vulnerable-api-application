import { test, expect, Page } from '@playwright/test';

const alice = {
  username: 'AliceSmith',
  password: 'AlicePass1!',
  id: '00000002-0000-0000-0000-000000000002'
};
const bob = {
  username: 'BobJohnson',
  password: 'BobPass2@',
  id: '00000003-0000-0000-0000-000000000003'
};

async function login(page: Page, username = alice.username, password = alice.password) {
  await page.goto('/login');
  await expect(page.locator('#username')).toBeVisible({ timeout: 10000 });
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.locator('#login-form button[type="submit"]').click();
  await expect(page).toHaveURL(/\/$/, { timeout: 30000 });
  await expect(page.locator('#logout-link')).toBeVisible({ timeout: 15000 });
}

async function enableUiDemos(page: Page) {
  await page.evaluate(() => {
    localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true');
  });
}

async function addItemToCart(page: Page) {
  await page.goto('/');
  await expect(page.locator('#loading-indicator')).toBeHidden({ timeout: 15000 });
  const firstProduct = page.locator('article.product-card').first();
  await expect(firstProduct).toBeVisible();
  const startCount = await page.locator('#cart-item-count').textContent();
  await firstProduct.locator('button.add-to-cart-btn').click();
  await expect(page.locator('#global-message-container .global-message.success-message'))
    .toBeVisible({ timeout: 10000 });
  await expect(page.locator('#cart-item-count')).not.toHaveText(startCount || '', { timeout: 5000 });
}

async function completeCheckout(page: Page, forUserId = alice.id) {
  await page.goto('/checkout');
  await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
  await page.waitForSelector('#credit-card-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
  await page.waitForSelector('form#checkout-form', { state: 'attached', timeout: 30000 });
  await page.waitForSelector('#place-order-btn', { state: 'visible', timeout: 30000 });
  await page.selectOption('#address-id', { index: 1 });
  await page.selectOption('#credit-card-id', { index: 1 });
  await Promise.all([
    page.waitForResponse(
      r => r.url().includes(`/api/users/${forUserId}/orders`) && r.request().method() === 'POST' && r.status() === 201,
      { timeout: 25000 }
    ),
    page.locator('#place-order-btn').click()
  ]);
  await page.waitForURL(/\/orders/, { timeout: 25000 });
  const firstRow = page.locator('#orders-container table tbody tr').first();
  await firstRow.waitFor({ state: 'visible', timeout: 15000 });
  return (await firstRow.getAttribute('data-order-id')) || '';
}

test.describe('Orders Page UI', () => {
  test.describe('should display own order history correctly', () => {
    test.beforeEach(async ({ page }) => {
      await login(page, alice.username, alice.password);
      await addItemToCart(page);
      await completeCheckout(page, alice.id);
      await addItemToCart(page);
      await completeCheckout(page, alice.id);
    });

    test('should display own order history correctly', async ({ page }) => {
      await page.goto('/orders');
      const rows = page.locator('#orders-container table tbody tr');
      await expect(rows.first()).toBeVisible({ timeout: 15000 });
      expect(await rows.count()).toBeGreaterThan(1);
      await expect(page.locator('#current-viewing')).toBeHidden();
    });
  });

  test.describe('Order Detail IDOR/BOLA demo', () => {
    let bobOrderId = '';

    test.beforeEach(async ({ page }) => {
      await login(page, bob.username, bob.password);
      await addItemToCart(page);
      bobOrderId = await completeCheckout(page, bob.id);
      await page.locator('#logout-link').click();
      await page.waitForURL(/\/login/, { timeout: 20000 });
      await login(page, alice.username, alice.password);
      await enableUiDemos(page);
      await page.reload();
    });

    test('should demonstrate UI for Order Detail IDOR/BOLA demo', async ({ page }) => {
      await page.goto('/orders');
      await page.fill('#detail-user-id', bob.id);
      await page.fill('#detail-order-id', bobOrderId);
      await Promise.all([
        page.waitForResponse(r => r.url().includes(`/api/users/${bob.id}/orders/${bobOrderId}`) && r.status() === 200),
        page.locator('#order-detail-form button[type="submit"]').click()
      ]);
      await expect(page.locator('#order-detail-result')).toContainText(bobOrderId.substring(0, 8));
    });
  });
});
