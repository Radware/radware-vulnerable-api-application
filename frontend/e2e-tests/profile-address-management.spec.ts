import { test, expect, Page } from '@playwright/test';

const alice = {
  username: 'AliceSmith',
  password: 'AlicePass1!',
  id: '00000002-0000-0000-0000-000000000002'
};
const bob = {
  username: 'BobJohnson',
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
  await page.reload();
}

test.describe.configure({ mode: 'serial' });

let createdStreet = '';

test.describe('Profile Page - Address and Card Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
    await enableUiDemos(page);
    await login(page, alice.username, alice.password);
    await page.goto('/profile');
    await expect(page.locator('#profile-info-content p')).toHaveCountGreaterThan(0, { timeout: 15000 });
    await expect(page.locator('#address-list-container')).toBeVisible();
    await expect(page.locator('#card-list-container')).toBeVisible();
  });

  test('should allow adding, editing, and deleting a new (non-protected) address', async ({ page }) => {
    const unique = Date.now();
    createdStreet = `Test Street ${unique}`;
    await page.locator('#toggle-address-form-btn').click();
    await expect(page.locator('#address-form-container')).toBeVisible();
    await page.fill('#address-street', createdStreet);
    await page.fill('#address-city', 'Testville');
    await page.fill('#address-country', 'USA');
    await page.fill('#address-zip', '99999');
    await page.locator('#address-form-submit-btn').click();
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Address', { timeout: 15000 });
    const card = page.locator('.address-card', { hasText: createdStreet });
    await expect(card).toBeVisible();

    await card.locator('.edit-address-btn').click();
    await expect(page.locator('#address-form-container')).toBeVisible();
    await expect(page.locator('#address-edit-mode-indicator')).toBeVisible();
    await page.fill('#address-street', `${createdStreet} Updated`);
    await page.locator('#address-form-submit-btn').click();
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('updated', { timeout: 15000 });
    const updatedCard = page.locator('.address-card', { hasText: `${createdStreet} Updated` });
    await expect(updatedCard).toBeVisible();

    await updatedCard.locator('.delete-address-btn').click();
    page.once('dialog', dialog => dialog.accept());
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('deleted', { timeout: 15000 });
    await expect(updatedCard).toHaveCount(0);
  });

  test('should allow setting a new default address', async ({ page }) => {
    const target = page.locator('.address-card', { hasText: '456 Maple Drive' });
    await expect(target.locator('.set-default-btn')).toBeVisible();
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${alice.id}/addresses/`) && r.request().method() === 'PUT' && r.url().includes('is_default=true') && r.status() === 200, { timeout: 20000 }),
      target.locator('.set-default-btn').click()
    ]);
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Default address', { timeout: 15000 });
    await expect(target.locator('.default-badge')).toBeVisible();
  });

  test('should prevent editing critical fields of a protected address via UI', async ({ page }) => {
    const protectedCard = page.locator('.address-card', { hasText: '123 Oak Street' });
    await protectedCard.locator('.edit-address-btn').click();
    await expect(page.locator('#address-form-container')).toBeVisible();
    await expect(page.locator('#address-protected-note')).toBeVisible();
    await expect(page.locator('#address-street')).toBeDisabled();
    await page.locator('#address-form-cancel-btn').click();
  });

  test('should prevent deleting a protected address via UI', async ({ page }) => {
    const protectedCard = page.locator('.address-card', { hasText: '123 Oak Street' });
    await protectedCard.locator('.delete-address-btn').click();
    page.once('dialog', dialog => dialog.accept());
    await expect(page.locator('#global-message-container .global-message.warning-message')).toContainText('protected', { timeout: 15000 });
    await expect(protectedCard).toBeVisible();
  });

  test('should allow adding, setting default, editing (limited), and deleting a new (non-protected) credit card', async ({ page }) => {
    const unique = Date.now();
    const name = `Test Card ${unique}`;
    await page.locator('#toggle-card-form-btn').click();
    await expect(page.locator('#card-form-container')).toBeVisible();
    await page.fill('#card-cardholder-name', name);
    await page.fill('#card-number-input', '4111111111111111');
    await page.fill('#card-expiry-month', '12');
    await page.fill('#card-expiry-year', '2030');
    await page.fill('#card-cvv-input', '123');
    await page.locator('#card-form-submit-btn').click();
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Credit card', { timeout: 15000 });
    const card = page.locator('.credit-card-card', { hasText: name });
    await expect(card).toBeVisible();

    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${alice.id}/credit-cards/`) && r.request().method() === 'PUT' && r.url().includes('is_default=true') && r.status() === 200, { timeout: 20000 }),
      card.locator('.set-default-btn').click()
    ]);
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Default credit card', { timeout: 15000 });
    await expect(card.locator('.default-badge')).toBeVisible();

    await card.locator('.edit-card-btn').click();
    await expect(page.locator('#card-form-container')).toBeVisible();
    await expect(page.locator('#card-edit-mode-indicator')).toBeVisible();
    await page.fill('#card-cardholder-name', `${name} Updated`);
    await page.fill('#card-expiry-year', '2031');
    await page.locator('#card-form-submit-btn').click();
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('updated', { timeout: 15000 });
    const updatedCard = page.locator('.credit-card-card', { hasText: `${name} Updated` });
    await expect(updatedCard).toBeVisible();

    await updatedCard.locator('.delete-card-btn').click();
    page.once('dialog', dialog => dialog.accept());
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('deleted', { timeout: 15000 });
    await expect(updatedCard).toHaveCount(0);
  });

  test('should prevent editing/deleting a protected credit card and show warning', async ({ page }) => {
    const protectedCard = page.locator('.credit-card-card', { hasText: 'Alice Smith' });
    await protectedCard.locator('.edit-card-btn').click();
    await expect(page.locator('#card-protected-note')).toBeVisible();
    await expect(page.locator('#card-cardholder-name')).toBeDisabled();
    await page.locator('#card-form-cancel-btn').click();
    await protectedCard.locator('.delete-card-btn').click();
    page.once('dialog', dialog => dialog.accept());
    await expect(page.locator('#global-message-container .global-message.warning-message')).toContainText('protected', { timeout: 15000 });
    await expect(protectedCard).toBeVisible();
  });

  test('should allow editing own email', async ({ page }) => {
    const newEmail = `alice${Date.now()}@example.com`;
    await page.locator('#toggle-edit-email-form-btn').click();
    await page.fill('#new-email-input', newEmail);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${alice.id}`) && r.request().method() === 'PUT' && r.url().includes('email'), { timeout: 20000 }),
      page.locator('#edit-email-form button[type="submit"]').click()
    ]);
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Email', { timeout: 15000 });
    await expect(page.locator('#profile-info-content')).toContainText(newEmail);
  });

  test('should allow editing own username (via BOLA demo form)', async ({ page }) => {
    const newName = `Alice${Date.now()}`;
    await page.fill('#update-username-input', newName);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${alice.id}`) && r.request().method() === 'PUT' && r.url().includes('username'), { timeout: 20000 }),
      page.locator('#update-profile-form button[type="submit"]').click()
    ]);
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('Profile', { timeout: 15000 });
    await expect(page.locator('#dynamic-nav-links a[href="/profile"]')).toContainText(newName);
  });

  test('BOLA Exploit: should add address FOR another user (Bob) via profile page UI', async ({ page }) => {
    await page.locator('#discover-users-btn').click();
    const bobBtn = page.locator(`.select-victim-btn[data-victim-id="${bob.id}"]`);
    await bobBtn.click();
    await expect(page.locator('#bola-demo-active-banner')).toBeVisible();
    await page.locator('#toggle-address-form-btn').click();
    const street = `Bola Addr ${Date.now()}`;
    await page.fill('#address-street', street);
    await page.fill('#address-city', 'Bolatown');
    await page.fill('#address-country', 'USA');
    await page.fill('#address-zip', '10101');
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${bob.id}/addresses`) && r.request().method() === 'POST' && r.status() === 201, { timeout: 20000 }),
      page.locator('#address-form-submit-btn').click()
    ]);
    await expect(page.locator('#global-message-container .global-message.success-message')).toContainText('successfully', { timeout: 15000 });
    await expect(page.locator('.address-card', { hasText: street })).toBeVisible();
    await page.locator('#return-to-my-profile-btn').click();
    await expect(page.locator('#profile-view-indicator')).toBeHidden();
    await expect(page.locator('.address-card', { hasText: street })).toHaveCount(0);
  });
});

