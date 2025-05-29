import { test, expect, Page } from '@playwright/test';

// --- User Constants ---
const alice = { // Attacker
  username: 'AliceSmith',
  password: 'AlicePass1!',
  id: '00000002-0000-0000-0000-000000000002'
};
const bob = { // Protected Victim
  username: 'BobJohnson',
  password: 'BobPass2@', // Not used for login by Alice
  id: '00000003-0000-0000-0000-000000000003'
};
const grace = { // Non-Protected Victim
  username: 'GraceWilson',
  password: 'GracePass7&', // Not used for login by Alice
  id: '00000008-0000-0000-0000-000000000008'
};

// --- Helper Functions ---
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
  // No page.reload() here, as beforeEach will handle fresh page state
}

async function viewVictimProfile(page: Page, victimId: string, victimUsername: string) {
  await page.goto('/profile'); // Start from Alice's profile
  await page.locator('#discover-users-btn').click();
  const victimButton = page.locator(`.select-victim-btn[data-victim-id="${victimId}"]`);
  await victimButton.waitFor({ state: 'visible', timeout: 15000 });
  const cardsResponsePromise = page.waitForResponse(response =>
    response.url().includes(`/api/users/${victimId}/credit-cards`) && response.status() === 200
  , { timeout: 20000 });
  await victimButton.click();
  await expect(page.locator('#bola-demo-active-banner')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('#current-viewing-username-span')).toContainText(victimUsername, { timeout: 10000 });
  // Wait for victim's data to load (e.g., credit card section)
  await expect(page.locator('#card-list-container')).toBeVisible({ timeout: 15000 });
  // Ensure credit cards have been loaded
  await cardsResponsePromise;
}

// --- Test Suite ---
test.describe('Profile Page - BOLA Vulnerabilities', () => {
  test.describe.configure({ mode: 'serial' }); // Run tests in this suite serially

  let newlyCreatedCardIdForGrace = '';

  test.beforeEach(async ({ page }) => {
    await page.goto('/'); // Go to a neutral page first
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
    await enableUiDemos(page); // Enable UI demos via localStorage
    await login(page, alice.username, alice.password); // Login as Alice (attacker)
  });

  test('BOLA - Attacker views victim\'s credit card list on victim\'s profile page', async ({ page }) => {
    // View Bob's (protected) profile and cards
    await viewVictimProfile(page, bob.id, bob.username);
    await expect(page.locator('#card-list-container .credit-card-card', { hasText: 'Bob Johnson' })).toBeVisible(); // Check for one of Bob's known cards
    await expect(page.locator('#card-list-container .credit-card-card', { hasText: 'Robert Johnson' })).toBeVisible();

    // Return to own profile briefly to reset context for next victim
    await page.locator('#return-to-my-profile-btn').click();
    await page.waitForResponse(r => r.url().includes(`/api/users/${alice.id}`) && r.status() === 200);

    // View Grace's (non-protected) profile and cards
    await viewVictimProfile(page, grace.id, grace.username);
    await expect(page.locator('#card-list-container .credit-card-card', { hasText: 'Grace Wilson' })).toBeVisible();
  });

  test('BOLA - Attacker adds new credit card FOR a non-protected victim (GraceWilson)', async ({ page }) => {
    await viewVictimProfile(page, grace.id, grace.username);

    const cardholderName = `Grace-Attacked ${Date.now()}`;
    await page.locator('#toggle-card-form-btn').click();
    await expect(page.locator('#card-form-container')).toBeVisible();

    await page.fill('#card-cardholder-name', cardholderName);
    await page.fill('#card-number-input', '4999888877776666'); // Test card number
    await page.fill('#card-expiry-month', '11');
    await page.fill('#card-expiry-year', '2028');
    await page.fill('#card-cvv-input', '789');

    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${grace.id}/credit-cards`) &&
        r.request().method() === 'POST' &&
        r.status() === 201
      , { timeout: 20000 }),
      page.locator('#card-form-submit-btn').click()
    ]);

    const successMsg = page.locator('#global-message-container .global-message.success-message');
    await expect(successMsg.filter({ hasText: `Credit card for ${grace.username} added successfully!` })).toBeVisible({ timeout: 15000 });

    const newCardInList = page.locator('#card-list-container .credit-card-card', { hasText: cardholderName });
    await expect(newCardInList).toBeVisible();
    const cardIdAttribute = await newCardInList.locator('.edit-card-btn').getAttribute('data-card-id');
    expect(cardIdAttribute).toBeTruthy();
    if (cardIdAttribute) newlyCreatedCardIdForGrace = cardIdAttribute;
  });

  test('BOLA - Attacker edits non-protected victim\'s (GraceWilson) newly added card', async ({ page }) => {
    expect(newlyCreatedCardIdForGrace, 'Test depends on card created in previous step').toBeTruthy();
    await viewVictimProfile(page, grace.id, grace.username); // Ensure correct profile context

    const cardToEdit = page.locator(`#card-list-container .item-card:has(.edit-card-btn[data-card-id="${newlyCreatedCardIdForGrace}"])`);
    await expect(cardToEdit).toBeVisible();
    await cardToEdit.locator('.edit-card-btn').click();

    await expect(page.locator('#card-form-container')).toBeVisible();
    const updatedCardholderName = `Grace-Updated ${Date.now()}`;
    await page.fill('#card-cardholder-name', updatedCardholderName);
    // Expiry can also be updated as per backend logic
    await page.fill('#card-expiry-year', '2032');


    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${grace.id}/credit-cards/${newlyCreatedCardIdForGrace}`) &&
        r.request().method() === 'PUT' &&
        r.status() === 200
      , { timeout: 20000 }),
      page.locator('#card-form-submit-btn').click()
    ]);

    const successMsg = page.locator('#global-message-container .global-message.success-message');
    await expect(successMsg.filter({ hasText: `Credit card for ${grace.username} updated successfully!` })).toBeVisible({ timeout: 15000 });
    await expect(page.locator('#card-list-container .credit-card-card', { hasText: updatedCardholderName })).toBeVisible();
    await expect(page.locator('#card-list-container .credit-card-card', { hasText: 'Expires: 11/32' })).toBeVisible();
  });

  test('BOLA - Attacker deletes non-protected victim\'s (GraceWilson) newly added card', async ({ page }) => {
    expect(newlyCreatedCardIdForGrace, 'Test depends on card created and edited in previous steps').toBeTruthy();
    await viewVictimProfile(page, grace.id, grace.username);

    const cardToDelete = page.locator(`#card-list-container .item-card:has(.delete-card-btn[data-card-id="${newlyCreatedCardIdForGrace}"])`);
    await expect(cardToDelete).toBeVisible();

    page.once('dialog', d => d.accept());
    const [delResp] = await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${grace.id}/credit-cards/${newlyCreatedCardIdForGrace}`) &&
        r.request().method() === 'DELETE' &&
        r.status() === 200
      , { timeout: 20000 }),
      cardToDelete.locator('.delete-card-btn').click()
    ]);
    const delBody = await delResp.json();
    expect(delBody.message).toMatch(/credit card deleted/i);

    const successMsg = page.locator('#global-message-container .global-message.success-message');
    await expect(successMsg.filter({ hasText: `Credit card deleted successfully for ${grace.username}!` })).toBeVisible({ timeout: 15000 });
    await expect(cardToDelete).toHaveCount(0);
  });

  test('BOLA - Attacker attempts to delete a protected victim\'s (BobJohnson) protected card', async ({ page }) => {
    await viewVictimProfile(page, bob.id, bob.username);

    // Bob's first card from prepopulated_data.json is protected
    const protectedCardId = 'cc000003-0001-0000-0000-000000000001';
    const bobProtectedCard = page.locator(`#card-list-container .item-card:has(.delete-card-btn[data-card-id="${protectedCardId}"])`);
    await expect(bobProtectedCard.filter({hasText: 'Bob Johnson'})).toBeVisible();

    page.once('dialog', d => d.accept());
    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${bob.id}/credit-cards/${protectedCardId}`) &&
        r.request().method() === 'DELETE' &&
        r.status() === 403
      , { timeout: 20000 }),
      bobProtectedCard.locator('.delete-card-btn').click()
    ]);

    const warningMsg = page.locator('#global-message-container .global-message.warning-message');
    await expect(warningMsg.filter({ hasText: 'Action Blocked: Credit Card ID' }).first()).toBeVisible({ timeout: 15000 });
    await expect(warningMsg.filter({ hasText: 'is protected and cannot be deleted' }).first()).toBeVisible({ timeout: 15000 });
    await expect(bobProtectedCard).toBeVisible(); // Card should still be there
  });

  test('BOLA - Attacker attempts to update another user\'s (non-protected GraceWilson) username', async ({ page }) => {
    await viewVictimProfile(page, grace.id, grace.username);
    const originalUsername = grace.username; // From const definition
    const newGraceUsername = `GraceAltered${Date.now()}`;

    await page.fill('#update-username-input', newGraceUsername); // This input is part of the "BOLA Demo: Update Profile" form

    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${grace.id}`) &&
        r.request().method() === 'PUT' &&
        r.url().includes(`username=${encodeURIComponent(newGraceUsername)}`) && // Ensure username param is present
        r.status() === 200
      , { timeout: 20000 }),
      page.locator('#update-profile-form button[type="submit"]').click()
    ]);

    const successMsg = page.locator('#global-message-container .global-message.success-message');
    await expect(successMsg.filter({ hasText: `Profile for ${originalUsername} updated.` }).first()).toBeVisible({ timeout: 15000 });

    // Verify the displayed profile info for Grace has updated
    await expect(page.locator('#profile-info-content p', { hasText: `Username: ${newGraceUsername}` })).toBeVisible({ timeout: 5000 });
    // Also check the "Currently viewing" indicator
    await expect(page.locator('#current-viewing-username-span')).toContainText(newGraceUsername, { timeout: 5000 });

    // Revert for test hygiene (optional, but good practice if possible)
    await page.fill('#update-username-input', originalUsername);
     await Promise.all([
      page.waitForResponse(r => r.url().includes(`/api/users/${grace.id}`) && r.status() === 200, { timeout: 20000 }),
      page.locator('#update-profile-form button[type="submit"]').click()
    ]);
  });

  test('BOLA - Attacker attempts to update protected user\'s (BobJohnson) username - EXPECT FAILURE', async ({ page }) => {
    await viewVictimProfile(page, bob.id, bob.username);
    const originalBobUsername = bob.username;
    const newBobUsernameAttempt = `BobAltered${Date.now()}`;

    await page.fill('#update-username-input', newBobUsernameAttempt);

    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes(`/api/users/${bob.id}`) &&
        r.request().method() === 'PUT' &&
        r.status() === 403 // Expecting 403 because Bob's username is protected
      , { timeout: 20000 }),
      page.locator('#update-profile-form button[type="submit"]').click()
    ]);

    const warningMsg = page.locator('#global-message-container .global-message.warning-message');
    await expect(warningMsg.filter({ hasText: `Action Blocked: User '${originalBobUsername}' is protected. Username and email cannot be changed.` })).toBeVisible({ timeout: 15000 });

    // Verify Bob's username in the UI has NOT changed
    await expect(page.locator('#profile-info-content p', { hasText: `Username: ${originalBobUsername}` })).toBeVisible({ timeout: 5000 });
    await expect(page.locator('#current-viewing-username-span')).toContainText(originalBobUsername, { timeout: 5000 });
  });
});
