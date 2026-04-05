import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import { AddExpenseForm } from "@/components/AddExpenseForm";
import AppContext from "@/app/context/AppContext";

const mockPush = jest.fn();

jest.mock("@react-navigation/native", () => ({ useIsFocused: () => true }));
jest.mock("expo-router", () => ({
  useRouter: () => ({ push: (...args: unknown[]) => mockPush(...args) }),
  Redirect: ({ href }: { href: string }) => {
    const React = require("react");
    const { Text } = require("react-native");
    return <Text testID="redirect-message">Redirecting to {href}</Text>;
  },
}));
jest.mock("@/utilities/getErrorMessage", () => ({ __esModule: true, default: (_: any, fallback: string) => fallback }));
jest.mock("@/components/utility/AlertMessage", () => ({
  __esModule: true,
  default: ({ message }: { message: string }) => {
    const React = require("react");
    const { Text } = require("react-native");
    return <Text testID="alert-message">{message}</Text>;
  },
}));

describe("Expense Management E2E Tests", () => {
  const mockJwt = "valid-jwt-token";
  let consoleErrorSpy: jest.SpyInstance;
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.useFakeTimers();
    (global as any).fetch = jest.fn();
    mockPush.mockReset();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  describe("Add Expense Form", () => {
    it("should check budget on component mount", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ totalAmount: 1000, spent: 200 }),
      });

      render(
        <AppContext.Provider value={{ jwt: mockJwt, setJwt: jest.fn() }}>
          <AddExpenseForm />
        </AppContext.Provider>
      );

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("budgets/current-month"),
          expect.any(Object)
        );
      });
    });

    it("should render form inputs when budget exists", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ totalAmount: 1000 }),
      });

      const { getByTestId } = render(
        <AppContext.Provider value={{ jwt: mockJwt, setJwt: jest.fn() }}>
          <AddExpenseForm />
        </AppContext.Provider>
      );

      await waitFor(() => {
        expect(getByTestId("category-input")).toBeTruthy();
        expect(getByTestId("amount-input")).toBeTruthy();
        expect(getByTestId("note-input")).toBeTruthy();
      });
    });

    it("should submit expense with valid data", async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ totalAmount: 1000 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: "expense-123" }),
        });

      const { getByTestId, getByText } = render(
        <AppContext.Provider value={{ jwt: mockJwt, setJwt: jest.fn() }}>
          <AddExpenseForm />
        </AppContext.Provider>
      );

      await waitFor(() => {
        expect(getByTestId("category-input")).toBeTruthy();
      });

      fireEvent.changeText(getByTestId("category-input"), "Food");
      fireEvent.changeText(getByTestId("amount-input"), "25.50");
      fireEvent.changeText(getByTestId("note-input"), "Lunch");
      fireEvent.press(getByText("Submit"));

      await waitFor(() => {
        expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThanOrEqual(2);
      });

      const expenseCall = (global.fetch as jest.Mock).mock.calls[1];
      expect(expenseCall[0]).toContain("/expenses");
      expect(expenseCall[1]).toEqual(expect.objectContaining({ method: "POST" }));
      expect(JSON.parse(expenseCall[1].body)).toEqual(
        expect.objectContaining({
          category: "Food",
          amount: 25.5,
          note: "Lunch",
        })
      );

      await waitFor(() => {
        expect(getByTestId("category-input").props.value).toBe("");
        expect(getByTestId("amount-input").props.value).toBe("");
        expect(getByTestId("note-input").props.value).toBe("");
      });
    });

    it("should show error when budget check fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: "No budget found" }),
      });

      const { getByText } = render(
        <AppContext.Provider value={{ jwt: mockJwt, setJwt: jest.fn() }}>
          <AddExpenseForm />
        </AppContext.Provider>
      );

      await waitFor(() => {
        expect(getByText("Set up your budget first")).toBeTruthy();
      });
    });

    it("should handle network errors gracefully", async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network failed"));

      const { getByText } = render(
        <AppContext.Provider value={{ jwt: mockJwt, setJwt: jest.fn() }}>
          <AddExpenseForm />
        </AppContext.Provider>
      );

      await waitFor(() => {
        expect(getByText("Set up your budget first")).toBeTruthy();
      });
    });

    it("should require authentication token", () => {
      const { getByTestId } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <AddExpenseForm />
        </AppContext.Provider>
      );

      expect(getByTestId("redirect-message")).toBeTruthy();
    });
  });
});
