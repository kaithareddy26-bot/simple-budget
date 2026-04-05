import React from "react";
import { render, fireEvent, waitFor, act } from "@testing-library/react-native";
import LoginPage from "@/components/LoginPage";
import RegistrationPage from "@/components/RegistrationPage";
import AppContext from "@/app/context/AppContext";

const mockReplace = jest.fn();

jest.mock("@react-navigation/native", () => ({ useIsFocused: () => true }));
jest.mock("expo-router", () => ({
  router: { replace: (...args: unknown[]) => mockReplace(...args) },
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

describe("Authentication E2E Tests", () => {
  let consoleErrorSpy: jest.SpyInstance;
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.useFakeTimers();
    (global as any).fetch = jest.fn();
    mockReplace.mockReset();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  describe("Login", () => {
    it("should render login form with email and password inputs", () => {
      const { getByTestId } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <LoginPage />
        </AppContext.Provider>
      );

      expect(getByTestId("email-input")).toBeTruthy();
      expect(getByTestId("password-input")).toBeTruthy();
    });

    it("should call login API, set jwt, and redirect on success", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: "test-token" }),
      });

      const setJwt = jest.fn();
      const { getByTestId, getAllByText } = render(
        <AppContext.Provider value={{ jwt: "", setJwt }}>
          <LoginPage />
        </AppContext.Provider>
      );

      fireEvent.changeText(getByTestId("email-input"), "user@example.com");
      fireEvent.changeText(getByTestId("password-input"), "password123");
      fireEvent.press(getAllByText("Login")[1]);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://localhost:8000/api/v1/auth/login",
          expect.objectContaining({ method: "POST" })
        );
      });

      const [, requestOptions] = (global.fetch as jest.Mock).mock.calls[0];
      expect(JSON.parse(requestOptions.body)).toEqual({
        email: "user@example.com",
        password: "password123",
      });

      act(() => {
        jest.advanceTimersByTime(900);
      });

      expect(setJwt).toHaveBeenCalledWith("test-token");
      expect(mockReplace).toHaveBeenCalledWith("/(tabs)");
    });

    it("should display error on login failure", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: "Invalid credentials" }),
      });

      const { getByTestId, getByText, getAllByText } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <LoginPage />
        </AppContext.Provider>
      );

      fireEvent.changeText(getByTestId("email-input"), "bad@example.com");
      fireEvent.changeText(getByTestId("password-input"), "wrong-password");
      fireEvent.press(getAllByText("Login")[1]);

      await waitFor(() => {
        expect(getByText("Login failed")).toBeTruthy();
      });
    });
  });

  describe("Registration", () => {
    it("should render registration form with all required fields", () => {
      const { getByTestId } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <RegistrationPage />
        </AppContext.Provider>
      );

      expect(getByTestId("email-input")).toBeTruthy();
      expect(getByTestId("password-input")).toBeTruthy();
      expect(getByTestId("confirm-password-input")).toBeTruthy();
    });

    it("should call registration API with form data", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "user-123" }),
      });

      const { getByTestId, getByText } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <RegistrationPage />
        </AppContext.Provider>
      );

      fireEvent.changeText(getByTestId("email-input"), "new@example.com");
      fireEvent.changeText(getByTestId("password-input"), "password123");
      fireEvent.changeText(getByTestId("confirm-password-input"), "password123");
      fireEvent.press(getByText("Register"));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://localhost:8000/api/v1/auth/register",
          expect.any(Object)
        );
      });
    });

    it("should show error when passwords don't match", async () => {
      const { getByTestId, getByText } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <RegistrationPage />
        </AppContext.Provider>
      );

      fireEvent.changeText(getByTestId("email-input"), "new@example.com");
      fireEvent.changeText(getByTestId("password-input"), "password123");
      fireEvent.changeText(getByTestId("confirm-password-input"), "different-password");
      fireEvent.press(getByText("Register"));

      await waitFor(() => {
        expect(getByText("Passwords do not match")).toBeTruthy();
      });
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });
});
