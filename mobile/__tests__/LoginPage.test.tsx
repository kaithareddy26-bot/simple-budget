import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import LoginPage from "@/components/LoginPage";

// Mock AppContext as a real context we can provide values to
jest.mock("@/app/context/AppContext", () => {
  const React = require("react");
  return { __esModule: true, default: React.createContext({ jwt: null, setJwt: () => {} }) };
});

jest.mock("@react-navigation/native", () => ({ useIsFocused: () => true }));

const mockReplace = jest.fn();
jest.mock("expo-router", () => ({
  router: { replace: (...args: any[]) => mockReplace(...args) },
}));

jest.mock("@/utilities/getErrorMessage", () => ({
  __esModule: true,
  default: (_data: any, fallback: string) => fallback,
}));

// Make AlertMessage render plain text so we can assert it easily
jest.mock("@/components/utility/AlertMessage", () => ({
  __esModule: true,
  default: ({ message }: { message: string }) => {
    const React = require("react");
    const { Text } = require("react-native");
    return <Text>{message}</Text>;
  },
}));

describe("LoginPage", () => {
  let consoleErrorSpy: jest.SpyInstance;
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.useFakeTimers();
    mockReplace.mockClear();
    (global as any).fetch = jest.fn();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  test("successful login shows success, sets jwt, and navigates to /(tabs)", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");
    const setJwt = jest.fn();

    (global as any).fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "token123" }),
    });

    const screen = render(
      <AppContext.Provider value={{ jwt: "", setJwt }}>
        <LoginPage />
      </AppContext.Provider>
    );

    fireEvent.changeText(screen.getByPlaceholderText("Email"), "a@b.com");
    fireEvent.changeText(screen.getByPlaceholderText("Password"), "pw");
    fireEvent.press(screen.getAllByText("Login")[1]);

    await waitFor(() => {
      expect(screen.getByText("Login successful")).toBeTruthy();
    });

    // LoginPage waits 900ms before setting jwt + navigating
    jest.advanceTimersByTime(900);

    expect(setJwt).toHaveBeenCalledWith("token123");
    expect(mockReplace).toHaveBeenCalledWith("/(tabs)");
  });

  test("failed login shows error message", async () => {
    const { default: AppContext } = require("@/app/context/AppContext");
    const setJwt = jest.fn();

    (global as any).fetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "bad creds" }),
    });

    const screen = render(
      <AppContext.Provider value={{ jwt: "", setJwt }}>
        <LoginPage />
      </AppContext.Provider>
    );

    fireEvent.press(screen.getAllByText("Login")[1]);

    await waitFor(() => {
      expect(screen.getByText("Login failed")).toBeTruthy();
    });

    expect(mockReplace).not.toHaveBeenCalled();
  });
});