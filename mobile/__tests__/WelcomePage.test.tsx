import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import { WelcomePage } from "@/components/WelcomePage";

jest.mock("@react-navigation/native", () => ({ useIsFocused: () => false }));

jest.mock("@/utilities/getErrorMessage", () => ({
  __esModule: true,
  default: (_data: any, fallback: string) => fallback,
}));

// Mock Redirect so we can assert it
jest.mock("expo-router", () => ({
  Redirect: ({ href }: { href: string }) => {
    const React = require("react");
    const { Text } = require("react-native");
    return <Text testID="redirect">{href}</Text>;
  },
}));

jest.mock("@/app/context/AppContext", () => {
  const React = require("react");
  return { __esModule: true, default: React.createContext({ jwt: null }) };
});

jest.mock("@/components/utility/ExpenseCard", () => ({
  __esModule: true,
  default: ({ header, amount, note }: { header: string; amount: number; note: string }) => {
    const React = require("react");
    const { Text } = require("react-native");
    return (
      <>
        <Text>{header}</Text>
        <Text>{`$${amount}`}</Text>
        <Text>{note}</Text>
      </>
    );
  },
}));

describe("WelcomePage", () => {
  let consoleErrorSpy: jest.SpyInstance;
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    (global as any).fetch = jest.fn();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  test("redirects to /login when jwt is missing", () => {
    const { default: AppContext } = require("@/app/context/AppContext");

    const screen = render(
      <AppContext.Provider value={{ jwt: null }}>
        <WelcomePage />
      </AppContext.Provider>
    );

    expect(screen.getByTestId("redirect")).toHaveTextContent("/login");
  });

  test("shows budget setup UI when current-month budget is missing (404)", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");

    // fetchBudget is called (at least once). Return 404 + any JSON.
    (global as any).fetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ code: "BUD_NOT_FOUND" }),
    });

    const screen = render(
      <AppContext.Provider value={{ jwt: "jwt-token" }}>
        <WelcomePage />
      </AppContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText("Set your monthly budget to get started")).toBeTruthy();
    });
  });

  test("validates budget amount > 0 before POSTing", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");

    // Always 404 so setup UI shows
    (global as any).fetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ code: "BUD_NOT_FOUND" }),
    });

    const screen = render(
      <AppContext.Provider value={{ jwt: "jwt-token" }}>
        <WelcomePage />
      </AppContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText("Set your monthly budget to get started")).toBeTruthy();
    });

    fireEvent.changeText(screen.getByDisplayValue(""), "0");
    fireEvent.press(screen.getByText("Save Budget"));

    await waitFor(() => {
      expect(screen.getByText("Please enter a valid budget amount greater than 0")).toBeTruthy();
    });
  });

  test("shows current budget and expenses when fetches succeed", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");

    (global as any).fetch.mockImplementation(async (url: string) => {
      if (url.includes("/api/v1/budgets/current-month")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ totalAmount: 500 }),
        };
      }

      if (url.includes("/api/v1/expenses/current-month")) {
        return {
          ok: true,
          status: 200,
          json: async () => ([{ id: "exp-1", category: "Food", amount: 25, note: "Lunch" }]),
        };
      }

      return {
        ok: false,
        status: 500,
        json: async () => ({ detail: "unexpected" }),
      };
    });

    const screen = render(
      <AppContext.Provider value={{ jwt: "jwt-token" }}>
        <WelcomePage />
      </AppContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText("Current month budget: $500")).toBeTruthy();
    });

    expect(screen.getByText("Food")).toBeTruthy();
    expect(screen.getByText("$25")).toBeTruthy();
    expect(screen.getByText("Lunch")).toBeTruthy();
  });

  test("creates budget successfully and exits setup flow", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");

    (global as any).fetch.mockImplementation(async (url: string, options?: { method?: string; body?: string }) => {
      if (url.includes("/api/v1/budgets/current-month")) {
        return {
          ok: false,
          status: 404,
          json: async () => ({ code: "BUD_NOT_FOUND" }),
        };
      }

      if (url.endsWith("/api/v1/budgets") && options?.method === "POST") {
        return {
          ok: true,
          status: 200,
          json: async () => ({ totalAmount: 250 }),
        };
      }

      if (url.includes("/api/v1/expenses/current-month")) {
        return {
          ok: true,
          status: 200,
          json: async () => ([]),
        };
      }

      return {
        ok: false,
        status: 500,
        json: async () => ({ detail: "unexpected" }),
      };
    });

    const screen = render(
      <AppContext.Provider value={{ jwt: "jwt-token" }}>
        <WelcomePage />
      </AppContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText("Set your monthly budget to get started")).toBeTruthy();
    });

    fireEvent.changeText(screen.getByDisplayValue(""), "250");
    fireEvent.press(screen.getByText("Save Budget"));

    await waitFor(() => {
      expect(screen.getByText("Current month budget: $250")).toBeTruthy();
    });

    const postBudgetCall = (global as any).fetch.mock.calls.find(
      ([url, options]: [string, { method?: string }]) =>
        url.endsWith("/api/v1/budgets") && options?.method === "POST"
    );
    expect(postBudgetCall).toBeTruthy();
  });
});