import { test, expect } from '@playwright/test';

async function login(page, username = 'AliceSmith', password = 'AlicePass1!') {
  await page.goto('/login');
  await expect(page.locator('#username')).toBeVisible({ timeout: 10000 });
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.locator('#login-form button[type="submit"]').click();
  await expect(page).toHaveURL(/\/$/, { timeout: 30000 });
  await expect(page.locator('#logout-link')).toBeVisible({ timeout: 15000 });
}

async function clearCart(page) {
  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
}

async function addProduct(page, priceLimit = Infinity) {
  await page.goto('/');
  await expect(page.locator('#loading-indicator')).toBeHidden({ timeout: 15000 });
  const products = page.locator('article.product-card');
  await expect(products.first()).toBeVisible({ timeout: 10000 });
  const count = await products.count();
  for (let i = 0; i < count; i++) {
    const card = products.nth(i);
    const priceAttr = await card.locator('button.add-to-cart-btn').getAttribute('data-product-price');
    const price = parseFloat(priceAttr || '0');
    if (price <= priceLimit) {
      const name = await card.locator('h3.product-title').innerText();
      await card.locator('button.add-to-cart-btn').click();
      await expect(page.locator('#global-message-container .global-message.success-message')).toBeVisible({ timeout: 10000 });
      return { name, price };
    }
  }
  const fallback = products.first();
  const priceAttr = await fallback.locator('button.add-to-cart-btn').getAttribute('data-product-price');
  const name = await fallback.locator('h3.product-title').innerText();
  const price = parseFloat(priceAttr || '0');
  await fallback.locator('button.add-to-cart-btn').click();
  await expect(page.locator('#global-message-container .global-message.success-message')).toBeVisible({ timeout: 10000 });
  return { name, price };
}

async function getMoney(page, selector) {
  const text = await page.locator(selector).innerText();
  return parseFloat(text.replace(/[^0-9.]/g, ''));
}

test.describe('Shopping Cart', () => {
  test.beforeEach(async ({ page }) => {
    await clearCart(page);
  });

  test('should display empty cart state correctly', async ({ page }) => {
    await page.goto('/cart');
    await expect(page.locator('#cart-items-container')).toContainText('Your cart is empty');
    await expect(page.getByRole('link', { name: /start shopping/i })).toBeVisible();
    await expect(page.locator('#cart-subtotal')).toHaveText('$0.00');
    await expect(page.locator('#cart-shipping')).toHaveText('$0.00');
    await expect(page.locator('#cart-total')).toHaveText('$0.00');
    await expect(page.locator('#checkout-btn')).toHaveClass(/disabled/);
  });

  test('should add product, update quantity, and reflect totals', async ({ page }) => {
    const { name, price } = await addProduct(page);
    await expect(page.locator('#cart-item-count')).toHaveText('1');

    await page.goto('/cart');
    await expect(page.locator('#cart-table')).toBeVisible();
    const row = page.locator('.cart-item').first();
    await expect(row).toContainText(name);

    let subtotal = await getMoney(page, '#cart-subtotal');
    let shipping = await getMoney(page, '#cart-shipping');
    let total = await getMoney(page, '#cart-total');
    expect(subtotal).toBeCloseTo(price, 2);
    expect(total).toBeCloseTo(subtotal + shipping, 2);

    await row.locator('[data-testid="increase-quantity"]').click();
    await expect(page.locator('#cart-item-count')).toHaveText('2');
    await expect(page.locator('#cart-subtotal')).toHaveText(`$${(price * 2).toFixed(2)}`);

    subtotal = await getMoney(page, '#cart-subtotal');
    shipping = await getMoney(page, '#cart-shipping');
    total = await getMoney(page, '#cart-total');
    expect(subtotal).toBeCloseTo(price * 2, 2);
    expect(total).toBeCloseTo(subtotal + shipping, 2);

    const qtyInput = row.locator('input.cart-quantity');
    await qtyInput.fill('3');
    await qtyInput.blur();
    await expect(page.locator('#cart-item-count')).toHaveText('3');
    await expect(page.locator('#cart-subtotal')).toHaveText(`$${(price * 3).toFixed(2)}`);

    subtotal = await getMoney(page, '#cart-subtotal');
    shipping = await getMoney(page, '#cart-shipping');
    total = await getMoney(page, '#cart-total');
    expect(subtotal).toBeCloseTo(price * 3, 2);
    expect(total).toBeCloseTo(subtotal + shipping, 2);
  });

  test('should remove item from cart', async ({ page }) => {
    await addProduct(page);
    await page.goto('/cart');
    await expect(page.locator('.cart-item')).toHaveCount(1);
    page.once('dialog', d => d.accept());
    await page.locator('.remove-item-btn').click();
    await expect(page.locator('#cart-items-container')).toContainText('Your cart is empty');
    await expect(page.locator('#cart-item-count')).toHaveText('0');
  });

  test('should apply valid coupon during checkout', async ({ page }) => {
    await login(page);
    await addProduct(page);
    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', {
      state: 'attached',
      timeout: 30000,
    });
    await page.waitForSelector('#credit-card-id option[value]:not([value=""])', {
      state: 'attached',
      timeout: 30000,
    });
    await page.evaluate(() => {
      const addr = document.querySelector<HTMLSelectElement>('#address-id');
      if (addr) addr.selectedIndex = 1;
      const card = document.querySelector<HTMLSelectElement>('#credit-card-id');
      if (card) card.selectedIndex = 1;
    });
    const initialTotal = await getMoney(page, '#checkout-grand-total');
    await page.fill('#coupon-code', 'TESTCODE');
    await page.locator('#apply-coupon-btn').click();
    await expect(
      page.locator('#global-message-container .global-message.success-message')
    ).toBeVisible();
    await expect(page.locator('#discount-info')).toBeVisible();
    const finalTotal = await getMoney(page, '#checkout-grand-total');
    expect(finalTotal).toBeLessThan(initialTotal);
  });

  test('should handle free shipping threshold', async ({ page }) => {
    const { price } = await addProduct(page, 49.99);
    await page.goto('/cart');
    const row = page.locator('.cart-item').first();
    await expect(page.locator('#cart-shipping')).toHaveText('$5.00');
    let quantity = 1;
    while (price * quantity <= 50) {
      await row.locator('[data-testid="increase-quantity"]').click();
      quantity++;
    }
    await expect(page.locator('#cart-shipping')).toHaveText('$0.00');
  });

  test('should persist cart contents across navigation', async ({ page }) => {
    const { name } = await addProduct(page);
    await expect(page.locator('#cart-item-count')).toHaveText('1');
    await page.goto('/products/f47ac10b-58cc-4372-a567-0e02b2c3d479');
    await expect(page.locator('#cart-item-count')).toHaveText('1');
    await page.goto('/cart');
    await expect(page.locator('.cart-item')).toContainText(name);
  });

  test('should clear cart upon logout', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'AliceSmith');
    await page.fill('#password', 'AlicePass1!');
    await page.locator('#login-form button[type="submit"]').click();
    await expect(page.locator('#logout-link')).toBeVisible({ timeout: 15000 });
    await addProduct(page);
    await expect(page.locator('#cart-item-count')).not.toHaveText('0');
    await page.locator('#logout-link').click();
    await expect(page.locator('#dynamic-nav-links a[href="/login"]')).toBeVisible({ timeout: 15000 });
    await page.goto('/cart');
    await expect(page.locator('#cart-items-container')).toContainText('Your cart is empty');
    await expect(page.locator('#cart-item-count')).toHaveText('0');
  });

  test('should require login to proceed to checkout', async ({ page }) => {
    await addProduct(page);
    await page.goto('/cart');
    await page.locator('#checkout-btn').click();
    await page.waitForURL(/\/login/, { timeout: 10000 });
    await expect(page).toHaveURL(/\/login/);
  });
});
