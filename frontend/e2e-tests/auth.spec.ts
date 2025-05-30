import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {
  test('should allow registration and login', async ({ page }) => {
    const uniqueSuffix = Date.now();
    const username = `testuser${uniqueSuffix}`;
    const email = `${username}@example.com`;
    const password = 'securePassword123';

    await page.goto('/register');
    await expect(page).toHaveURL(/\/register/);

    await page.fill('#username', username);
    await page.fill('#email', email);
    await page.fill('#password', password);
    await page.fill('#confirm-password', password);
    await page.locator('#register-form button[type="submit"]').click();

    await expect(page).toHaveURL(/\/login/, { timeout: 15000 });

    await page.fill('#username', username);
    await page.fill('#password', password);
    await page.locator('#login-form button[type="submit"]').click();

    await expect(page).toHaveURL(/\/$/, { timeout: 15000 });

    await expect(
      page.locator(`#dynamic-nav-links a[href="/profile"]:has-text("${username}")`)
    ).toBeVisible();
    await expect(page.locator('#logout-link')).toBeVisible();
    await expect(page.locator('#dynamic-nav-links a[href="/login"]')).not.toBeVisible();
  });
  
  test('should show error for incorrect login', async ({ page }) => {
    await page.goto('/login');

    await page.fill('#username', 'nonexistentuser');
    await page.fill('#password', 'wrongpassword');
    await page.locator('#login-form button[type="submit"]').click();

    await expect(page).toHaveURL(/\/login/);
    await expect(
      page.locator('#global-message-container .global-message.error-message')
    ).toContainText('Error: Login failed: Incorrect username or password');
  });
  
  test('should allow logout', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/login');

    await page.fill('#username', 'AliceSmith');
    await page.fill('#password', 'AlicePass1!');
    await page.locator('#login-form button[type="submit"]').click();

    await expect(page).toHaveURL(/\/$/, { timeout: 15000 });
    await expect(page.locator('#logout-link')).toBeVisible();

    await page.locator('#logout-link').click();

    await expect(page).toHaveURL(/\/login|\//, { timeout: 15000 });
    await expect(page.locator('#dynamic-nav-links a[href="/login"]')).toBeVisible();
    await expect(page.locator('#dynamic-nav-links a[href="/register"]')).toBeVisible();
    await expect(page.locator('#logout-link')).not.toBeVisible();
    await expect(page.locator('#dynamic-nav-links a[href="/profile"]')).not.toBeVisible();
  });
});
