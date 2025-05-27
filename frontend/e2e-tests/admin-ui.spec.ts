import { test, expect, Page } from '@playwright/test';

const alice = {
  username: 'AliceSmith',
  password: 'AlicePass1!'
};

const graceId = '00000008-0000-0000-0000-000000000008';
const bobId = '00000003-0000-0000-0000-000000000003';

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

test.describe('Admin Page UI Demos', () => {
  test('Admin Page - should toggle visibility of internal products via Parameter Pollution UI', async ({ page }) => {
    await login(page);
    await enableUiDemos(page);
    await page.reload();
    await page.goto('/admin');
    await expect(page.locator('.parameter-pollution-controls')).toBeVisible();
    const productsBefore = await page.locator('#admin-products-container').innerHTML();
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/api/products') && r.request().method() === 'GET'),
      page.check('#reveal-internal')
    ]);
    await expect(page.locator('#constructed-url-display')).toContainText('status=internal');
    const productsAfterCheck = await page.locator('#admin-products-container').innerHTML();
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/api/products') && r.request().method() === 'GET'),
      page.uncheck('#reveal-internal')
    ]);
    await expect(page.locator('#constructed-url-display')).not.toContainText('status=internal');
    const productsAfterUncheck = await page.locator('#admin-products-container').innerHTML();
    expect(productsAfterCheck).not.toEqual(productsBefore);
    expect(productsAfterUncheck).not.toEqual(productsAfterCheck);
  });

  test('Admin Page - should demonstrate BFLA user deletion UI with protected/non-protected entities', async ({ page }) => {
    await login(page);
    await enableUiDemos(page);
    await page.reload();
    await page.goto('/admin');
    await page.fill('#delete-user-id', graceId);
    page.once('dialog', d => d.accept());
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${graceId}`) && r.request().method() === 'DELETE' && r.status() === 204),
      page.locator('#delete-user-form button[type="submit"]').click()
    ]);
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText(/User .* deleted/i);
    await page.fill('#delete-user-id', bobId);
    page.once('dialog', d => d.accept());
    const [resp] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${bobId}`) && r.request().method() === 'DELETE'),
      page.locator('#delete-user-form button[type="submit"]').click()
    ]);
    expect(resp.status()).toBe(403);
    const warn = page.locator('#global-message-container .global-message.warning-message');
    await expect(warn).toContainText('Action Blocked');
    await expect(warn).toContainText(/protected for demo purposes/i);
  });
});
