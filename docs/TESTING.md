# Testing Guide

This document describes the testing strategy and how to run tests for the Keiko platform.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Unit Tests](#unit-tests)
3. [Integration Tests](#integration-tests)
4. [E2E Tests](#e2e-tests)
5. [Running Tests](#running-tests)
6. [Writing Tests](#writing-tests)
7. [CI/CD Integration](#cicd-integration)

## Testing Strategy

The Keiko platform uses a comprehensive testing strategy with three layers:

```
┌─────────────────────────────────────┐
│         E2E Tests (Playwright)      │  ← User flows, critical paths
├─────────────────────────────────────┤
│    Integration Tests (pytest)       │  ← Service-to-service, API contracts
├─────────────────────────────────────┤
│      Unit Tests (pytest/vitest)     │  ← Functions, components, logic
└─────────────────────────────────────┘
```

### Test Coverage Goals

- **Unit Tests:** 80%+ code coverage
- **Integration Tests:** All API endpoints
- **E2E Tests:** Critical user flows

## Unit Tests

### Python Services

**Framework:** pytest with AsyncMock

**Location:**
- `services/*/tests/unit/`
- `services/*/tests/conftest.py`

**Example:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.method = AsyncMock(return_value="result")
    return client

async def test_function(mock_client):
    result = await function_under_test(mock_client)
    assert result == "expected"
```

**Running:**
```bash
cd services/auth-service
pytest tests/unit/ -v
pytest tests/unit/ --cov=app --cov-report=html
```

### Frontend (React/Next.js)

**Framework:** Vitest with @testing-library/react

**Location:**
- `apps/frontend/src/**/__tests__/`
- `apps/frontend/src/test/setup.ts`

**Example:**
```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Button } from '../button'

describe('Button', () => {
  it('should render button with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })
})
```

**Running:**
```bash
cd apps/frontend
pnpm test              # Run tests
pnpm test:ui           # Run with UI
pnpm test:coverage     # Run with coverage
```

### Rust Services

**Framework:** Built-in Rust testing

**Location:**
- `services/ingestion-service/tests/`

**Running:**
```bash
cd services/ingestion-service
cargo test
cargo test --test integration_test
```

## Integration Tests

Integration tests verify service-to-service communication and API contracts.

**Framework:** pytest with TestClient (FastAPI)

**Location:**
- `services/*/tests/integration/`

**Example:**
```python
from fastapi.testclient import TestClient
from app.main import app

def test_endpoint():
    client = TestClient(app)
    response = client.post("/api/endpoint", json={"data": "test"})
    assert response.status_code == 200
```

**Running:**
```bash
cd services/chat-service
pytest tests/integration/ -v
```

## E2E Tests

End-to-end tests verify complete user flows using Playwright.

**Framework:** Playwright

**Location:**
- `apps/frontend/e2e/`
- `apps/frontend/playwright.config.ts`

**Example:**
```typescript
import { test, expect } from '@playwright/test'

test('should send a message', async ({ page }) => {
  await page.goto('/')
  await page.locator('[data-testid="chat-input"]').fill('Hello')
  await page.locator('[data-testid="send-button"]').click()
  await expect(page.locator('[data-testid="chat-message"]')).toBeVisible()
})
```

**Running:**
```bash
cd apps/frontend

# Install browsers (first time only)
npx playwright install

# Run tests
pnpm test:e2e

# Run with UI
pnpm test:e2e:ui

# Run in debug mode
pnpm test:e2e:debug

# Run specific test
npx playwright test e2e/chat.spec.ts
```

## Running Tests

### All Tests

```bash
# From root directory
make test

# Or manually
cd services/auth-service && pytest
cd services/search-service && pytest
cd services/document-service && pytest
cd apps/frontend && pnpm test && pnpm test:e2e
```

### Specific Service

```bash
# Python service
cd services/<service-name>
pytest tests/unit/
pytest tests/integration/
pytest --cov=app --cov-report=html

# Frontend
cd apps/frontend
pnpm test
pnpm test:e2e
```

### Watch Mode

```bash
# Python (with pytest-watch)
cd services/auth-service
ptw tests/

# Frontend
cd apps/frontend
pnpm test --watch
```

## Writing Tests

### Best Practices

1. **Follow AAA Pattern:**
   - Arrange: Set up test data
   - Act: Execute the function
   - Assert: Verify the result

2. **Use Descriptive Names:**
   ```python
   def test_should_return_error_when_token_expired():
       # Test implementation
   ```

3. **Mock External Dependencies:**
   - Azure services (Blob Storage, AI Search)
   - OpenAI API
   - Redis cache
   - HTTP clients

4. **Test Edge Cases:**
   - Empty inputs
   - Invalid data
   - Error conditions
   - Boundary values

5. **Keep Tests Independent:**
   - Each test should run in isolation
   - Use fixtures for setup/teardown
   - Don't rely on test execution order

### Python Test Template

```python
"""Tests for <module_name>."""

import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_dependency():
    """Mock external dependency."""
    mock = MagicMock()
    mock.method = AsyncMock(return_value="result")
    return mock

class TestClassName:
    """Tests for ClassName."""

    async def test_method_success(self, mock_dependency):
        """Test successful execution."""
        # Arrange
        input_data = {"key": "value"}
        
        # Act
        result = await function_under_test(input_data, mock_dependency)
        
        # Assert
        assert result == "expected"
        mock_dependency.method.assert_called_once()

    async def test_method_error(self, mock_dependency):
        """Test error handling."""
        # Arrange
        mock_dependency.method.side_effect = Exception("Error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await function_under_test({}, mock_dependency)
```

### Frontend Test Template

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('ComponentName', () => {
  it('should render correctly', () => {
    render(<ComponentName />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('should handle user interaction', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<ComponentName onClick={handleClick} />)
    await user.click(screen.getByRole('button'))
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

## CI/CD Integration

Tests are automatically run in CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Python tests
        run: |
          cd services/auth-service
          pytest --cov=app --cov-report=xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Frontend tests
        run: |
          cd apps/frontend
          pnpm install
          pnpm test
          pnpm test:e2e
```

## Troubleshooting

### Common Issues

**Issue:** Tests fail with "Module not found"
**Solution:** Install dependencies: `pip install -r requirements.txt` or `pnpm install`

**Issue:** E2E tests timeout
**Solution:** Increase timeout in `playwright.config.ts` or check if dev server is running

**Issue:** Mock not working
**Solution:** Ensure mock is created before importing the module under test

**Issue:** Async tests hanging
**Solution:** Use `pytest-asyncio` and mark tests with `@pytest.mark.asyncio`

## Related Documentation

- [Rollback Procedures](./ROLLBACK_PROCEDURES.md)
- [Monitoring Guide](./MONITORING.md)
- [Deployment Guide](./DEPLOYMENT.md)

