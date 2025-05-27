import { test, expect, Page } from '@playwright/test';

const user = { username: 'AliceSmith', password: 'AlicePass1!' };

async function login(page: Page, username = user.username, password = user.password) {
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
  await expect(page.locator('#global-message-container .global-message.success-message'))
    .toContainText('Added', { timeout: 10000 });
  await expect(page.locator('#cart-item-count')).not.toHaveText(startCount || '', { timeout: 5000 });
}

test.describe('UI Vulnerability Demos Global Toggle', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.evaluate(() => {
      localStorage.setItem('uiVulnerabilityFeaturesEnabled', 'false');
    });
    await page.reload();
    await addItemToCart(page);
  });

  test('should correctly toggle UI vulnerability demo features and persist state', async ({ page }) => {
    // Step 1: Verify Initial State (Demos OFF)
    await expect(page.locator('#ui-vulnerability-features-toggle-switch')).not.toBeChecked();
    await expect(page.locator('#ui-vulnerability-features-toggle-status')).toHaveText('OFF');

    await page.goto('/profile');
    await expect(page.locator('#discover-users-btn')).toBeHidden();
    await expect(page.locator('#attempt-admin-escalation-btn')).toBeHidden();

    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await expect(page.locator('#bola-demo-section')).toBeHidden();

    await page.goto('/admin');
    await expect(page.locator('.parameter-pollution-controls')).toBeHidden();

    // Step 2: Enable Demos via UI Toggle
    await page.goto('/');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.locator('#ui-vulnerability-features-toggle-switch + .slider').click({ force: true });
    await expect(page.locator('#ui-vulnerability-features-toggle-switch')).toBeChecked();
    await expect(page.locator('#ui-vulnerability-features-toggle-status')).toHaveText('ON');
    expect(await page.evaluate(() => localStorage.getItem('uiVulnerabilityFeaturesEnabled'))).toBe('true');

    // Step 3: Verify Demo Sections Visible After Enabling
    await page.goto('/profile');
    await expect(page.locator('#discover-users-btn')).toBeVisible();
    await expect(page.locator('#attempt-admin-escalation-btn')).toBeVisible();

    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await expect(page.locator('#bola-demo-section')).toBeVisible();

    await page.goto('/admin');
    await expect(page.locator('.parameter-pollution-controls')).toBeVisible();

    // Step 4: Disable Demos via UI Toggle
    await page.goto('/');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.locator('#ui-vulnerability-features-toggle-switch + .slider').click({ force: true });
    await expect(page.locator('#ui-vulnerability-features-toggle-switch')).not.toBeChecked();
    await expect(page.locator('#ui-vulnerability-features-toggle-status')).toHaveText('OFF');
    expect(await page.evaluate(() => localStorage.getItem('uiVulnerabilityFeaturesEnabled'))).toBe('false');

    // Step 5: Verify Demo Sections Hidden After Disabling
    await page.goto('/profile');
    await expect(page.locator('#discover-users-btn')).toBeHidden();
    await expect(page.locator('#attempt-admin-escalation-btn')).toBeHidden();

    await page.goto('/checkout');
    await page.waitForSelector('#address-id option[value]:not([value=""])', { state: 'attached', timeout: 30000 });
    await expect(page.locator('#bola-demo-section')).toBeHidden();

    await page.goto('/admin');
    await expect(page.locator('.parameter-pollution-controls')).toBeHidden();
  });
});

