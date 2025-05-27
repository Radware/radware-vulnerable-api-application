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

let createdStreet = '';

test.describe.serial('Profile Page - Address Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
    await enableUiDemos(page);
    await login(page, alice.username, alice.password);
    await page.goto('/profile');
    await expect(page.locator('#profile-info-content p').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('#address-list-container .address-card').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('#card-list-container .credit-card-card').first()).toBeVisible({ timeout: 15000 });
  });

  test('should allow adding, editing, and deleting a new (non-protected) address', async ({ page }) => {
    const uniqueStreet = `Test Street ${Date.now()}`;
    createdStreet = uniqueStreet;

    await page.locator('#toggle-address-form-btn').click();
    await expect(page.locator('#address-form-container')).toBeVisible();
    await page.fill('#address-street', uniqueStreet);
    await page.fill('#address-city', 'Testville');
    await page.fill('#address-country', 'USA');
    await page.fill('#address-zip', '99999');

    await Promise.all([
      page.waitForResponse(r => r.url().includes('/addresses') && r.request().method() === 'POST' && r.status() === 201, { timeout: 20000 }),
      page.locator('#address-form-submit-btn').click()
    ]);

    const successMsg = page.locator('#global-message-container .global-message.success-message');
    await expect(successMsg.filter({ hasText: /Address for AliceSmith added successfully/i })).toBeVisible({ timeout: 15000 });

    const newCard = page.locator('#address-list-container .address-card', { hasText: uniqueStreet });
    await expect(newCard).toBeVisible();

    await newCard.locator('.edit-address-btn').click();
    await expect(page.locator('#address-form-container')).toBeVisible();
    await expect(page.locator('#address-edit-mode-indicator')).toBeVisible();
    await page.fill('#address-street', 'Updated Test Street');

    await page.route('**/addresses/**', async (route, request) => {
      if (request.method() === 'PUT' && !request.url().includes('is_default')) {
        await route.continue({ url: request.url() + '&is_default=false' });
      } else {
        await route.continue();
      }
    });

    await Promise.all([
      page.waitForResponse(r => r.url().includes('/addresses/') && r.request().method() === 'PUT', { timeout: 20000 }),
      page.locator('#address-form-submit-btn').click()
    ]);

    await expect(successMsg.filter({ hasText: /Address for AliceSmith updated successfully/i })).toBeVisible({ timeout: 15000 });
    const updatedCard = page.locator('#address-list-container .address-card', { hasText: 'Updated Test Street' });
    await expect(updatedCard).toBeVisible({ timeout: 20000 });
    await page.unroute('**/addresses/**');

    page.once('dialog', d => d.accept());
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/addresses/') && r.request().method() === 'DELETE' && r.status() === 204, { timeout: 20000 }),
      updatedCard.locator('.delete-address-btn').click()
    ]);
    await expect(successMsg.filter({ hasText: /Address deleted successfully/i })).toBeVisible({ timeout: 15000 });
    await expect(page.locator('#address-list-container .address-card', { hasText: 'Updated Test Street' })).toHaveCount(0);
  });

  test('should show warning when trying to set a new default address due to protected existing default', async ({ page }) => {
    const street = `Default Test ${Date.now()}`;
    await page.locator('#toggle-address-form-btn').click();
    await page.fill('#address-street', street);
    await page.fill('#address-city', 'DefaultCity');
    await page.fill('#address-country', 'USA');
    await page.fill('#address-zip', '22222');
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/addresses') && r.request().method() === 'POST' && r.status() === 201, { timeout: 20000 }),
      page.locator('#address-form-submit-btn').click()
    ]);
    const newCard = page.locator('.address-card', { hasText: street });
    await expect(newCard).toBeVisible();

    const onclick = await newCard.locator('.set-default-btn').getAttribute('onclick');
    const addrId = onclick?.match(/'([^']+)'/)[1];

    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${alice.id}/addresses/`) &&
        r.request().method() === 'PUT' &&
        r.status() === 403 &&
        r.url().includes('is_default=false'), { timeout: 20000 }),
      page.evaluate(id => (window as any).setDefaultAddress(id), addrId)
    ]);

    const warning = page.locator('#global-message-container .global-message.warning-message').filter({ hasText: 'Action Blocked: Address ID' });
    await expect(warning).toBeVisible({ timeout: 15000 });

    await expect(newCard.locator('.default-badge')).toHaveCount(0);
    await expect(page.locator('.address-card', { hasText: '123 Oak Street' }).locator('.default-badge')).toBeVisible();

    page.once('dialog', d => d.accept());
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/addresses/${addrId}`) && r.request().method() === 'DELETE' && r.status() === 204, { timeout: 20000 }),
      newCard.locator('.delete-address-btn').click()
    ]);
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
    page.once('dialog', dialog => dialog.accept());
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/addresses/') && r.request().method() === 'DELETE' && r.status() === 403, { timeout: 20000 }),
      protectedCard.locator('.delete-address-btn').click()
    ]);
    const warning = page.locator('#global-message-container .global-message.warning-message').filter({ hasText: 'protected' }).first();
    await expect(warning).toBeVisible({ timeout: 15000 });
    await expect(protectedCard).toBeVisible();
  });

  test('should allow adding a new credit card but show warning when attempting to set it as default', async ({ page }) => {
    const unique = Date.now();
    const name = `Test Card ${unique}`;
    await page.locator('#toggle-card-form-btn').click();
    await expect(page.locator('#card-form-container')).toBeVisible();
    await page.fill('#card-cardholder-name', name);
    await page.fill('#card-number-input', '4111111111111111');
    await page.fill('#card-expiry-month', '12');
    await page.fill('#card-expiry-year', '2030');
    await page.fill('#card-cvv-input', '123');
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/credit-cards') && r.request().method() === 'POST' && r.status() === 201, { timeout: 20000 }),
      page.locator('#card-form-submit-btn').click()
    ]);
    const cardSuccess = page.locator('#global-message-container .global-message.success-message');
    await expect(cardSuccess.filter({ hasText: /Credit card for AliceSmith added successfully/i })).toBeVisible({ timeout: 15000 });

    const card = page.locator('.credit-card-card', { hasText: name });
    await expect(card).toBeVisible();
    const cardId = await card.locator('.edit-card-btn').getAttribute('data-card-id');

    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${alice.id}/credit-cards/`) &&
        r.request().method() === 'PUT' &&
        r.status() === 403 &&
        r.url().includes('is_default=false'), { timeout: 20000 }),
      card.locator('.set-default-btn').click()
    ]);

    const warning = page.locator('#global-message-container .global-message.warning-message').filter({ hasText: 'Action Blocked: Credit Card ID' });
    await expect(warning).toBeVisible({ timeout: 15000 });

    await expect(card.locator('.default-badge')).toHaveCount(0);
    await expect(page.locator('.credit-card-card', { hasText: 'Alice Smith' }).locator('.default-badge')).toBeVisible();

    page.once('dialog', d => d.accept());
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/credit-cards/${cardId}`) && r.request().method() === 'DELETE' && r.status() === 204, { timeout: 20000 }),
      card.locator(`.delete-card-btn[data-card-id="${cardId}"]`).click()
    ]);
  });

  test('should prevent editing/deleting a protected credit card and show warning', async ({ page }) => {
    const protectedCard = page.locator('.credit-card-card', { hasText: 'Alice Smith' });
    await protectedCard.locator('.edit-card-btn').click();
    await expect(page.locator('#card-protected-note')).toBeVisible();
    await expect(page.locator('#card-cardholder-name')).toBeDisabled();
    await page.locator('#card-form-cancel-btn').click();
    page.once('dialog', dialog => dialog.accept());
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/credit-cards/') && r.request().method() === 'DELETE' && r.status() === 403, { timeout: 20000 }),
      protectedCard.locator('.delete-card-btn').click()
    ]);
    const warning = page.locator('#global-message-container .global-message.warning-message').filter({ hasText: 'protected' }).first();
    await expect(warning).toBeVisible({ timeout: 15000 });
    await expect(protectedCard).toBeVisible();
  });

  test('should block editing own protected email', async ({ page }) => {
    const oldEmail = await page.locator('#current-email-display').textContent();
    const newEmail = `alice${Date.now()}@example.com`;
    await page.locator('#toggle-edit-email-form-btn').click();
    await page.fill('#new-email-input', newEmail);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${alice.id}`) && r.request().method() === 'PUT' && r.status() === 403, { timeout: 20000 }),
      page.locator('#edit-email-form button[type="submit"]').click()
    ]);
    const warning = page.locator('#global-message-container .global-message.warning-message').filter({ hasText: "Action Blocked: User 'AliceSmith'" });
    await expect(warning).toBeVisible({ timeout: 15000 });
    await expect(page.locator('#current-email-display')).toHaveText(oldEmail || '', { timeout: 5000 });
  });

  test('should block editing own protected username via BOLA demo form', async ({ page }) => {
    const currentName = await page.locator('#dynamic-nav-links a[href="/profile"]').textContent();
    const newName = `Alice${Date.now()}`;
    await page.fill('#update-username-input', newName);
    await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${alice.id}`) && r.request().method() === 'PUT' && r.status() === 403, { timeout: 20000 }),
      page.locator('#update-profile-form button[type="submit"]').click()
    ]);
    const warning = page.locator('#global-message-container .global-message.warning-message').filter({ hasText: "Action Blocked: User 'AliceSmith'" });
    await expect(warning).toBeVisible({ timeout: 15000 });
    await expect(page.locator('#dynamic-nav-links a[href="/profile"]')).toHaveText(currentName || '', { timeout: 5000 });
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
    await expect(page.locator('.address-card', { hasText: street })).toHaveCount(0);
  });
});

