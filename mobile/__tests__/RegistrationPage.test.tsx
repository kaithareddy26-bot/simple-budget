import React from "react";
import { render, fireEvent, waitFor, act } from "@testing-library/react-native";
import RegistrationPage from "@/components/RegistrationPage";

jest.mock("@react-navigation/native", () => ({ useIsFocused: () => true }));

const mockReplace = jest.fn();
jest.mock("expo-router", () => ({
  router: { replace: (...args: any[]) => mockReplace(...args) },
}));

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

describe("RegistrationPage", () => {
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

  test("successful registration navigates to /(tabs)/login after 1200ms", async () => {
    (global as any).fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ id: "new-user" }),
    });

    const screen = render(<RegistrationPage />);

    fireEvent.changeText(screen.getByPlaceholderText("Email"), "a@b.com");
    fireEvent.changeText(screen.getByPlaceholderText("Full Name"), "A B");
    fireEvent.changeText(screen.getByPlaceholderText("Password"), "pw");
    fireEvent.press(screen.getByText("Register"));

    await waitFor(() => {
      expect(screen.getByText("Registration successful")).toBeTruthy();
    });

    act(() => {
      jest.advanceTimersByTime(1200);
    });
    expect(mockReplace).toHaveBeenCalledWith("/(tabs)/login");
  });

  test("failed registration shows error message", async () => {
    (global as any).fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ error: "bad" }),
    });

    const screen = render(<RegistrationPage />);
    fireEvent.press(screen.getByText("Register"));

    await waitFor(() => {
      expect(screen.getByText("Registration failed")).toBeTruthy();
    });

    expect(mockReplace).not.toHaveBeenCalled();
  });
});