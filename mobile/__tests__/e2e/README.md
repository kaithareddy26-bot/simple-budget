# E2E Tests for Mobile App

This directory contains component-level integration tests for the Simple Budget mobile application. These tests verify key user flows and route guards by rendering screens with mocked network and navigation dependencies.

## Overview

The E2E test suite is organized into three main test files:

### 1. **auth.e2e.test.tsx** - Authentication Flows
Tests complete authentication workflows including:
- User login with valid credentials
- Failed login attempts with error handling
- User registration with validation
- Password mismatch prevention
- Session management and logout

**Key Scenarios:**
- Successful login redirects to home tab
- Error messages display on authentication failure
- Form validation prevents incomplete submissions
- JWT tokens are properly stored and cleared

### 2. **expense.e2e.test.tsx** - Expense Management
Tests the complete expense creation workflow including:
- Budget availability checking
- Expense submission with validation
- Budget limit enforcement
- Error handling and network resilience
- Form state management after submission

**Key Scenarios:**
- Budget is checked on component load
- Expenses are created with complete data
- Expenses exceeding budget trigger errors
- Required fields are validated
- Forms clear after successful submission
- Network errors are handled gracefully

### 3. **navigation.e2e.test.tsx** - Route Guards & Screen Rendering
Tests authenticated and unauthenticated rendering behavior:
- Redirect logic based on authentication status
- Welcome page rendering with budget and expenses data
- Home page visibility with authenticated JWT

**Key Scenarios:**
- Unauthenticated users are redirected to login
- Welcome page renders current month budget and expenses for authenticated users
- Home page loads with authenticated JWT

## Running Tests

### Run all E2E tests:
```bash
npm test -- __tests__/e2e
```

### Run specific E2E test file:
```bash
npm test -- __tests__/e2e/auth.e2e.test.tsx
npm test -- __tests__/e2e/expense.e2e.test.tsx
npm test -- __tests__/e2e/navigation.e2e.test.tsx
```

### Run tests in watch mode:
```bash
npm test -- __tests__/e2e --watch
```

### Run tests with coverage:
```bash
npm test -- __tests__/e2e --coverage
```

## Test Structure

Each test file follows this pattern:

```typescript
describe("Feature E2E Tests", () => {
  beforeEach(() => {
    // Setup: Mock timers, fetch, spies
  });

  afterEach(() => {
    // Cleanup: Restore mocks
  });

  describe("User Flow Name", () => {
    it("should accomplish specific goal", async () => {
      // 1. Setup: Mock API responses
      // 2. Act: Render component and trigger actions
      // 3. Assert: Verify behavior and side effects
    });
  });
});
```

## Mocking Strategy

The E2E tests use the following mocking approach:

### API Calls (Fetch)
```typescript
(global.fetch as jest.Mock).mockResolvedValueOnce({
  ok: true,
  json: async () => ({ access_token: "jwt-token" })
});
```

### Navigation
```typescript
jest.mock("expo-router", () => ({
  router: { replace: (...args) => mockReplace(...args) }
}));
```

### React Navigation
```typescript
jest.mock("@react-navigation/native", () => ({
  useIsFocused: () => true
}));
```

### Context & Utilities
- `AppContext` is provided by test with test values
- `getErrorMessage` utility is mocked
- `AlertMessage` component renders as simple Text for assertions

## Writing New E2E Tests

When adding new E2E tests:

1. **Identify the user flow** - What actions does the user take?
2. **Setup mocks** - Mock all external dependencies (API, navigation)
3. **Render the component** - Provide AppContext with necessary values
4. **Trigger actions** - Use `fireEvent` to simulate user interactions
5. **Assert outcomes** - Verify component behavior and side effects

Example:
```typescript
it("should complete the feature", async () => {
  // Mock the API
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: true,
    json: async () => ({ result: "success" })
  });

  // Render with context
  const { getByTestId, getByText } = render(
    <AppContext.Provider value={{ jwt: "token", setJwt: jest.fn() }}>
      <MyComponent />
    </AppContext.Provider>
  );

  // Trigger user action
  fireEvent.press(getByText("Submit"));

  // Assert expectations
  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalledWith(...);
  });
});
```

## Best Practices

### ✅ Do:
- Test complete user flows, not isolated actions
- Mock API responses to test various scenarios (success, error, timeout)
- Use `waitFor` for async operations
- Clear test IDs in components for reliable selection
- Test error states and edge cases
- Use descriptive test names that explain the scenario

### ❌ Don't:
- Test implementation details
- Mock more than necessary
- Use fixed delays instead of `waitFor`
- Create interdependent tests
- Test third-party libraries

## Common Testing Patterns

### Testing Async Operations
```typescript
await waitFor(() => {
  expect(global.fetch).toHaveBeenCalled();
});
```

### Testing Form Submission
```typescript
const input = getByTestId("email-input");
fireEvent.changeText(input, "test@example.com");
fireEvent.press(getByText("Submit"));
```

### Testing Error Messages
```typescript
(global.fetch as jest.Mock).mockResolvedValueOnce({
  ok: false,
  json: async () => ({ detail: "Error message" })
});

// After triggering action
expect(screen.getByTestID("alert-message")).toBeTruthy();
```

## Test Helpers & Utilities

### Testing Library Methods
- `render()` - Mount component with providers
- `fireEvent` - Simulate user interactions
- `waitFor()` - Wait for async updates
- `screen.getByTestID()` - Find elements by testID
- `getByText()` - Find elements by text content
- `getByTestId()` - Render-specific element finder

## Debugging Tests

### View rendered output:
```typescript
const { debug } = render(<Component />);
debug(); // Prints component tree
```

### Check mock calls:
```typescript
console.log((global.fetch as jest.Mock).mock.calls);
```

### Use real timers for debugging:
```typescript
// In beforeEach, comment out:
// jest.useFakeTimers();
```

## Continuous Integration

These tests are automatically run in CI/CD pipelines. To ensure tests pass:

1. All API endpoints should be mocked
2. Timer operations use fake timers
3. No console errors are expected
4. All async operations complete within timeouts

## Related Documentation

- [Testing Library React Native](https://testing-library.com/docs/react-native-testing-library/intro)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Expo Testing Guide](https://docs.expo.dev/guides/testing/)

## Troubleshooting

### Tests timeout
- Ensure `jest.runAllTimers()` is called for synchronous timer operations
- Check that `waitFor` has appropriate timeout (default 1000ms)

### Mock not working
- Verify mock is setup before component render
- Check mock reset/clear in `afterEach`

### Component not rendering
- Verify AppContext is provided
- Check that all required props are passed
- Review console errors from mocks

### Assertions fail
- Use `debug()` to see actual rendered output
- Verify test IDs exist in actual components
- Check timing issues with `waitFor`
