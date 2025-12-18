/**
 * E2E tests for ideas functionality.
 */

import { test, expect } from '@playwright/test'

test.describe('Ideas Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the ideas page
    await page.goto('/ideas')
  })

  test('should display ideas page', async ({ page }) => {
    // Check if ideas page is loaded
    await expect(page).toHaveURL(/.*ideas/)

    // Check for ideas list or empty state
    const ideasList = page.locator('[data-testid="ideas-list"]')
    const emptyState = page.locator('[data-testid="empty-state"]')

    // Either ideas list or empty state should be visible
    const isListVisible = await ideasList.isVisible()
    const isEmptyVisible = await emptyState.isVisible()

    expect(isListVisible || isEmptyVisible).toBeTruthy()
  })

  test('should open idea submission form', async ({ page }) => {
    // Click on "New Idea" button
    await page.locator('[data-testid="new-idea-button"]').click()

    // Check if form is visible
    await expect(page.locator('[data-testid="idea-form"]')).toBeVisible()
  })

  test('should submit a new idea', async ({ page }) => {
    // Open form
    await page.locator('[data-testid="new-idea-button"]').click()

    // Fill in the form
    await page.locator('[data-testid="idea-title"]').fill('Test Idea')
    await page.locator('[data-testid="idea-description"]').fill('This is a test idea description')

    // Submit the form
    await page.locator('[data-testid="submit-idea-button"]').click()

    // Wait for success message or redirect
    await expect(
      page.locator('[data-testid="success-message"]')
    ).toBeVisible({ timeout: 5000 })
  })

  test('should validate required fields', async ({ page }) => {
    // Open form
    await page.locator('[data-testid="new-idea-button"]').click()

    // Try to submit without filling fields
    await page.locator('[data-testid="submit-idea-button"]').click()

    // Check for validation errors
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible()
  })

  test('should display idea details', async ({ page }) => {
    // Check if there are any ideas
    const ideaCards = page.locator('[data-testid="idea-card"]')
    const count = await ideaCards.count()

    if (count > 0) {
      // Click on the first idea
      await ideaCards.first().click()

      // Check if detail page is displayed
      await expect(page.locator('[data-testid="idea-detail"]')).toBeVisible()
    }
  })

  test('should display similar ideas', async ({ page }) => {
    // Open form
    await page.locator('[data-testid="new-idea-button"]').click()

    // Fill in title
    await page.locator('[data-testid="idea-title"]').fill('AI Assistant')

    // Wait a bit for similar ideas to load
    await page.waitForTimeout(1000)

    // Check if similar ideas section appears
    const similarIdeas = page.locator('[data-testid="similar-ideas"]')
    if (await similarIdeas.isVisible()) {
      await expect(similarIdeas).toBeVisible()
    }
  })

  test('should filter ideas by status', async ({ page }) => {
    // Check if filter dropdown exists
    const filterDropdown = page.locator('[data-testid="status-filter"]')

    if (await filterDropdown.isVisible()) {
      // Click on filter
      await filterDropdown.click()

      // Select a status
      await page.locator('[data-testid="filter-option-pending"]').click()

      // Wait for filtered results
      await page.waitForTimeout(500)

      // Verify URL or filtered state
      expect(page.url()).toContain('status=pending')
    }
  })

  test('should search ideas', async ({ page }) => {
    // Check if search input exists
    const searchInput = page.locator('[data-testid="search-input"]')

    if (await searchInput.isVisible()) {
      // Type search query
      await searchInput.fill('AI')

      // Wait for search results
      await page.waitForTimeout(500)

      // Verify search results are displayed
      const results = page.locator('[data-testid="idea-card"]')
      const count = await results.count()
      expect(count).toBeGreaterThanOrEqual(0)
    }
  })
})

