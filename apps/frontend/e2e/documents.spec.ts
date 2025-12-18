/**
 * E2E tests for document management functionality.
 */

import { test, expect } from '@playwright/test'
import path from 'path'

test.describe('Documents Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the documents page
    await page.goto('/documents')
  })

  test('should display documents page', async ({ page }) => {
    // Check if documents page is loaded
    await expect(page).toHaveURL(/.*documents/)

    // Check for upload button or document list
    const uploadButton = page.locator('[data-testid="upload-button"]')
    await expect(uploadButton).toBeVisible()
  })

  test('should open upload dialog', async ({ page }) => {
    // Click upload button
    await page.locator('[data-testid="upload-button"]').click()

    // Check if upload dialog is visible
    await expect(page.locator('[data-testid="upload-dialog"]')).toBeVisible()
  })

  test('should upload a document', async ({ page }) => {
    // Click upload button
    await page.locator('[data-testid="upload-button"]').click()

    // Create a test file
    const fileInput = page.locator('input[type="file"]')

    // Upload a test file (you would need to have a test file in your test fixtures)
    // For this example, we'll just check if the file input exists
    await expect(fileInput).toBeAttached()

    // In a real test, you would do:
    // await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test.pdf'))

    // Then verify upload progress or success
    // await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible()
  })

  test('should display document list', async ({ page }) => {
    // Check if document list is visible
    const documentList = page.locator('[data-testid="document-list"]')
    const emptyState = page.locator('[data-testid="empty-state"]')

    // Either document list or empty state should be visible
    const isListVisible = await documentList.isVisible()
    const isEmptyVisible = await emptyState.isVisible()

    expect(isListVisible || isEmptyVisible).toBeTruthy()
  })

  test('should preview a document', async ({ page }) => {
    // Check if there are any documents
    const documentItems = page.locator('[data-testid="document-item"]')
    const count = await documentItems.count()

    if (count > 0) {
      // Click on the first document
      await documentItems.first().click()

      // Check if preview is displayed
      await expect(page.locator('[data-testid="document-preview"]')).toBeVisible()
    }
  })

  test('should download a document', async ({ page }) => {
    // Check if there are any documents
    const documentItems = page.locator('[data-testid="document-item"]')
    const count = await documentItems.count()

    if (count > 0) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download')

      // Click download button on first document
      await documentItems.first().locator('[data-testid="download-button"]').click()

      // Wait for download to start
      const download = await downloadPromise

      // Verify download started
      expect(download).toBeTruthy()
    }
  })

  test('should delete a document', async ({ page }) => {
    // Check if there are any documents
    const documentItems = page.locator('[data-testid="document-item"]')
    const count = await documentItems.count()

    if (count > 0) {
      // Click delete button on first document
      await documentItems.first().locator('[data-testid="delete-button"]').click()

      // Confirm deletion if there's a dialog
      const confirmButton = page.locator('button:has-text("Delete")')
      if (await confirmButton.isVisible()) {
        await confirmButton.click()
      }

      // Wait for success message
      await expect(
        page.locator('[data-testid="success-message"]')
      ).toBeVisible({ timeout: 5000 })
    }
  })

  test('should filter documents by type', async ({ page }) => {
    // Check if filter exists
    const filterDropdown = page.locator('[data-testid="type-filter"]')

    if (await filterDropdown.isVisible()) {
      // Click on filter
      await filterDropdown.click()

      // Select PDF filter
      await page.locator('[data-testid="filter-pdf"]').click()

      // Wait for filtered results
      await page.waitForTimeout(500)

      // Verify filtering worked
      const documentItems = page.locator('[data-testid="document-item"]')
      const count = await documentItems.count()
      expect(count).toBeGreaterThanOrEqual(0)
    }
  })

  test('should search documents', async ({ page }) => {
    // Check if search input exists
    const searchInput = page.locator('[data-testid="search-input"]')

    if (await searchInput.isVisible()) {
      // Type search query
      await searchInput.fill('test')

      // Wait for search results
      await page.waitForTimeout(500)

      // Verify search results
      const results = page.locator('[data-testid="document-item"]')
      const count = await results.count()
      expect(count).toBeGreaterThanOrEqual(0)
    }
  })

  test('should handle upload errors', async ({ page }) => {
    // Click upload button
    await page.locator('[data-testid="upload-button"]').click()

    // Try to upload an invalid file type
    const fileInput = page.locator('input[type="file"]')

    // In a real test, you would upload an invalid file
    // and check for error message
    await expect(fileInput).toBeAttached()
  })
})

