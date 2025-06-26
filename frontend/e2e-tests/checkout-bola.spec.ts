import { test, expect, Page } from '@playwright/test';

const user1 = { username: 'AliceSmith', password: 'AlicePass1!' };
const user2 = { username: 'BobJohnson', password: 'BobPass2@' };

const user1Id = '00000002-0000-0000-0000-000000000002';
const user2Id = '00000003-0000-0000-0000-000000000003';
const user2AddressId = 'ad000003-0001-0000-0000-000000000001';
const user2CardId = 'cc000003-0001-0000-0000-000000000001';

async function login(page: Page, username = user1.username, password = user1.password) {
  await page.goto('/login');
  await expect(page.locator('#username')).toBeVisible({ timeout: 10000 });
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.locator('#login-form button[type="submit"]').click();
  await expect(page).toHaveURL(/\/$/, { timeout: 30000 });
  await expect(page.locator('#logout-link')).toBeVisible({ timeout: 15000 });
}

async function addItemToCart(page: Page) {
  await page.goto('/');
  await expect(page.locator('#loading-indicator')).toBeHidden({ timeout: 15000 });
  const firstProduct = page.locator('article.product-card').first();
  await expect(firstProduct).toBeVisible();
  const startCount = await page.locator('#cart-item-count').textContent();
  await firstProduct.locator('button.add-to-cart-btn').click();
  await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Added', {
    timeout: 10000
  });
  await expect(page.locator('#cart-item-count')).not.toHaveText(startCount || '', { timeout: 5000 });
}

test.describe('Checkout BOLA Vulnerability', () => {
  test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
    localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'true');
  });
  await login(page);
  await addItemToCart(page);
  await page.goto('/checkout');
  await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
  await page.waitForSelector('#credit-card-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
  });

  test('order FOR victim using their address and card', async ({ page }) => {
    await expect(page.locator('#bola-demo-section')).toBeVisible();
    await page.check('#order-for-other-user');
    await expect(page.locator('#bola-demo-fields')).toBeVisible();
    await expect(page.locator('#bola-warning-container')).toBeVisible();

    await page.fill('#target-user-id', user2Id);
    await page.fill('#target-address-id', user2AddressId);
    await page.fill('#target-credit-card-id', user2CardId);

    await Promise.all([
      page.waitForResponse(
        r => r.url().includes(`/api/users/${user1Id}/orders`) && r.status() === 201,
        { timeout: 20000 }
      ),
      page.locator('#place-order-btn').click()
    ]);

    await expect(page.locator('#global-message-container .global-message')).toContainText(
      /Order .* placed successfully!/i,
      { timeout: 15000 }
    );

    await page.waitForURL(/\/orders/, { timeout: 20000 });
    await page.fill('#target-user-id', user2Id);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${user2Id}/orders`) && r.status() === 200, { timeout: 15000 }),
      page.locator('form#view-orders-form button[type="submit"]').click()
    ]);
    const orderRowsVictim = page.locator('#orders-container table tbody tr');
    await expect(orderRowsVictim).toHaveCount(0);
  });

  test('order for self using victim credit card', async ({ page }) => {
    await expect(page.locator('#bola-demo-section')).toBeVisible();
    await page.check('#order-for-other-user');
    await expect(page.locator('#bola-demo-fields')).toBeVisible();
    await expect(page.locator('#bola-warning-container')).toBeVisible();

    await page.fill('#target-credit-card-id', user2CardId);

    await Promise.all([
      page.waitForResponse(
        r => r.url().includes(`/api/users/${user1Id}/orders`) && r.status() === 201,
        { timeout: 20000 }
      ),
      page.locator('#place-order-btn').click()
    ]);

    await expect(page.locator('#global-message-container .global-message')).toContainText(
      /Order .* placed successfully!/i,
      { timeout: 15000 }
    );

    await page.waitForURL(/\/orders/, { timeout: 20000 });
    await expect(page.locator('#current-viewing')).toBeHidden();
    const orderRows = page.locator('#orders-container table tbody tr');
    expect(await orderRows.count()).toBeGreaterThan(0);
  });
});
