import { test, expect, Page } from '@playwright/test';

const alice = {
  username: 'AliceSmith',
  password: 'AlicePass1!'
};

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
    const unique = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const newUserResponse = await page.request.post(
      `http://localhost:8000/api/auth/register?username=UiDelete${unique}&email=ui-delete-${unique}@example.com&password=UiDeletePass1!`
    );
    expect(newUserResponse.status()).toBe(201);
    const newUser = await newUserResponse.json();
    const newUserId = newUser.user_id;
    await page.goto('/admin');
    await page.fill('#delete-user-id', newUserId);
    page.once('dialog', d => d.accept());
    const [delResp] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${newUserId}`) && r.request().method() === 'DELETE' && r.status() === 200),
      page.locator('#delete-user-form button[type="submit"]').click()
    ]);
    const delBody = await delResp.json();
    expect(delBody.message).toMatch(/user deleted/i);
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText(/User .* deleted/i);
    await page.fill('#delete-user-id', bobId);
    page.once('dialog', d => d.accept());
    const [resp] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${bobId}`) && r.request().method() === 'DELETE'),
      page.locator('#delete-user-form button[type="submit"]').click()
    ]);
    expect(resp.status()).toBe(403);
    const warn = page
      .locator('#global-message-container .global-message.warning-message')
      .filter({ hasText: 'Action Blocked' })
      .first();
    await expect(warn).toContainText(/Action Blocked/);
    await expect(warn).toContainText(/protected for demo purposes/i);
  });
});
