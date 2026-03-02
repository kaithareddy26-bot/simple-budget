import React from "react";
import { render, fireEvent, waitFor, act } from "@testing-library/react-native";
import AddExpenseForm from "@/components/AddExpenseForm";

jest.mock("@react-navigation/native", () => ({ useIsFocused: () => false }));

jest.mock("@/utilities/getErrorMessage", () => ({
  __esModule: true,
  default: (_data: any, fallback: string) => fallback,
}));

jest.mock("@/components/utility/AlertMessage", () => ({
  __esModule: true,
  default: ({ message }: { message: string }) => {
    const React = require("react");
    const { Text } = require("react-native");
    return <Text>{message}</Text>;
  },
}));

jest.mock("@/app/context/AppContext", () => {
  const React = require("react");
  return { __esModule: true, default: React.createContext({ jwt: null }) };
});

const mockPush = jest.fn();
jest.mock("expo-router", () => ({
  Redirect: ({ href }: { href: string }) => {
    const React = require("react");
    const { Text } = require("react-native");
    return <Text testID="redirect">{href}</Text>;
  },
  useRouter: () => ({ push: (...args: any[]) => mockPush(...args) }),
}));

describe("AddExpenseForm", () => {
  let consoleErrorSpy: jest.SpyInstance;
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.useFakeTimers();
    mockPush.mockClear();
    (global as any).fetch = jest.fn();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  test("redirects to /login when jwt missing", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");
    const screen = render(
      <AppContext.Provider value={{ jwt: null }}>
        <AddExpenseForm />
      </AppContext.Provider>
    );
    expect(screen.getByTestId("redirect")).toHaveTextContent("/login");
  });

  test("shows 'Set up your budget first' when budget check fails", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");

    // checkBudgetExists fetch => ok but missing totalAmount => hasBudget false
    (global as any).fetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    const screen = render(
      <AppContext.Provider value={{ jwt: "jwt-token" }}>
        <AddExpenseForm />
      </AppContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText("Set up your budget first")).toBeTruthy();
    });

    fireEvent.press(screen.getByText("Go to Current Month"));
    expect(mockPush).toHaveBeenCalledWith("/(tabs)");
  });

  test("submitting an expense shows success and clears inputs", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");

    // First fetch: budget exists
    (global as any).fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ totalAmount: 100 }),
      })
      // Second fetch: expense POST ok
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "exp1" }),
      });

    const screen = render(
      <AppContext.Provider value={{ jwt: "jwt-token" }}>
        <AddExpenseForm />
      </AppContext.Provider>
    );

    // Wait until form renders (budget check complete)
    await waitFor(() => {
      expect(screen.getByText("Enter a new expense.")).toBeTruthy();
    });

    const [categoryInput, amountInput, noteInput] = screen.getAllByDisplayValue("");

    fireEvent.changeText(categoryInput, "Food");
    fireEvent.changeText(amountInput, "12.50");
    fireEvent.changeText(noteInput, "Lunch");
    fireEvent.press(screen.getByText("Submit"));

    await waitFor(() => {
      expect(screen.getByText("Expense added successfully")).toBeTruthy();
    });

    // Inputs cleared immediately on success
    expect(categoryInput.props.value).toBe("");
    expect(amountInput.props.value).toBe("");
    expect(noteInput.props.value).toBe("");

    // Success message auto-clears after 2000ms
    act(() => {
      jest.advanceTimersByTime(2000);
    });
  });
});