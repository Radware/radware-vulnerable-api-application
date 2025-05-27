import { test, expect, Page } from '@playwright/test';

const user1 = { username: 'AliceSmith', password: 'AlicePass1!' };
const user2 = { username: 'BobJohnson', password: 'BobPass2@' };

const user1Id = '00000002-0000-0000-0000-000000000002';
const user2Id = '00000003-0000-0000-0000-000000000003';
const user2AddressId = 'ad000003-0001-0000-0000-000000000001';
const user2CardId = 'cc000003-0001-0000-0000-000000000001';

const protectedProductId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

async function login(page: Page, username = user1.username, password = user1.password) {
  await page.goto('/login');
  await expect(page.locator('#username')).toBeVisible({ timeout: 10000 });
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.locator('#login-form button[type="submit"]').click();
  await expect(page).toHaveURL(/\/$/, { timeout: 30000 });
  await expect(page.locator('#logout-link')).toBeVisible({ timeout: 15000 });
}

async function enableUiDemos(page: Page) {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true'));
}

async function addItemToCart(page: Page) {
  await page.goto('/');
  await expect(page.locator('#loading-indicator')).toBeHidden({ timeout: 15000 });
  const firstProduct = page.locator('article.product-card').first();
  await expect(firstProduct).toBeVisible();
  const cartCount = await page.locator('#cart-item-count').textContent();
  await firstProduct.locator('button.add-to-cart-btn').click();
  await expect(page.locator('#global-message-container .global-message.success-message'))
    .toContainText('Added', { timeout: 10000 });
  await expect(page.locator('#cart-item-count')).not.toHaveText(cartCount || '', { timeout: 5000 });
}

test.describe('Vulnerability Demonstrations', () => {
  test('should demonstrate BOLA vulnerability in profile viewing', async ({ page }) => {
    await enableUiDemos(page);
    await login(page, user1.username, user1.password);
    await page.goto('/profile');
    await page.waitForSelector('#discover-users-btn', { timeout: 15000 });
    await page.click('#discover-users-btn');
    const bobBtn = page.locator('.select-victim-btn[data-victim-id="' + user2Id + '"]');
    await bobBtn.waitFor({ state: 'visible', timeout: 15000 });
    await bobBtn.click();
    await expect(page.locator('#bola-demo-active-banner')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('#profile-view-indicator')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#current-viewing-username-span')).toContainText(user2.username);
    await expect(page.locator('#return-to-my-profile-btn')).toBeVisible();
  });

  test('should demonstrate BOLA vulnerability in order viewing', async ({ page }) => {
    await enableUiDemos(page);
    await login(page, user1.username, user1.password);
    await addItemToCart(page);
    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.waitForSelector('#credit-card-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await page.check('#order-for-other-user');
    await page.fill('#target-user-id', user2Id);
    await page.fill('#target-address-id', user2AddressId);
    await page.fill('#target-credit-card-id', user2CardId);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${user2Id}/orders`) && r.status() === 201, { timeout: 20000 }),
      page.locator('#place-order-btn').click()
    ]);
    await expect(page.locator('#global-message-container .global-message'))
      .toContainText('BOLA EXPLOIT', { timeout: 15000 });

    await page.goto('/orders');
    await page.fill('#target-user-id', user2Id);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${user2Id}/orders`) && r.status() === 200, { timeout: 15000 }),
      page.locator('form#view-orders-form button[type="submit"]').click()
    ]);
    await expect(page.locator('#viewing-user-id-orders')).toHaveValue(user2Id, { timeout: 10000 });
    await expect(page.locator('#current-viewing')).toBeVisible({ timeout: 10000 });
    const orderRows = page.locator('#orders-container table tbody tr');
    await expect(orderRows.first()).toBeVisible({ timeout: 15000 });
    await page.locator('#return-to-own-orders').click();
    await expect(page.locator('#current-viewing')).toBeHidden();
  });

  test('should demonstrate Parameter Pollution for admin escalation', async ({ page }) => {
    await enableUiDemos(page);
    await login(page, user1.username, user1.password);
    await page.goto('/profile');
    page.once('dialog', d => d.accept());
    await page.locator('#attempt-admin-escalation-btn').click();
    const successMessages = page.locator('#global-message-container .global-message.success-message');
    await expect(successMessages).toContainText(['Admin escalation attempt successful', 'Your privileges have been updated to Admin'], { timeout: 15000 });
    await expect(page.locator('#profile-info-content .admin-badge')).toBeVisible({ timeout: 10000 });
  });

  test('should demonstrate BFLA vulnerability for product management', async ({ page }) => {
    await enableUiDemos(page);
    await login(page, user1.username, user1.password);
    await page.goto('/admin');
    await page.check('#admin-escalation');
    await expect(page.locator('#vulnerability-banner-admin')).toBeVisible({ timeout: 10000 });

    await page.waitForSelector('#add-product-form', { timeout: 15000 });

    const productName = `Test Product ${Date.now()}`;
    await page.fill('#new-product-name', productName);
    await page.fill('#new-product-description', 'Demo product added by test');
    await page.fill('#new-product-price', '99.99');
    await page.fill('#new-product-category', 'Demo');

    await page.locator('#add-product-submit').click();
    await expect(page.locator('#global-message-container .global-message.success-message'))
      .toContainText('Product added', { timeout: 15000 });
    await expect(page.locator('#admin-products-container tr', { hasText: productName })).toBeVisible({ timeout: 10000 });

    // delete created product
    page.once('dialog', dialog => dialog.accept());
    await page.locator(`#admin-products-container tr:has-text("${productName}") button.delete-product-btn`).click();
    await expect(page.locator('#global-message-container .global-message.success-message'))
      .toContainText('deleted', { timeout: 15000 });
    await expect(page.locator('#admin-products-container tr', { hasText: productName })).toHaveCount(0, { timeout: 10000 });

    // attempt to delete protected product
    page.once('dialog', dialog => dialog.accept());
    await page.locator(`#admin-products-container tr:has-text("Laptop Pro 15") button.delete-product-btn`).click();
    await expect(page.locator('#global-message-container .global-message.warning-message'))
      .toContainText('protected', { timeout: 15000 });
  });

  test('should show error when reducing stock below minimum for protected product', async ({ page }) => {
    await enableUiDemos(page);
    await login(page, user1.username, user1.password);
    await page.goto('/admin');
    await page.check('#admin-escalation');
    await page.waitForSelector('#update-stock-form', { timeout: 15000 });
    await page.fill('#stock-product-id', protectedProductId);
    await page.fill('#new-stock-qty', '100');
    await page.locator('#update-stock-submit').click();
    await expect(page.locator('#global-message-container .global-message.warning-message', { hasText: 'stock reduced below' }))
      .toBeVisible({ timeout: 15000 });
  });
});

