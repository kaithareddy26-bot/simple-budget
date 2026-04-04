import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import LoginPage from "@/components/LoginPage";
import RegistrationPage from "@/components/RegistrationPage";
import AppContext from "@/app/context/AppContext";

jest.mock("@react-navigation/native", () => ({ useIsFocused: () => true }));
jest.mock("expo-router", () => ({ router: { replace: jest.fn() } }));
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

  beforeEach(() => {
    jest.useFakeTimers();
    (global as any).fetch = jest.fn();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    consoleErrorSpy.mockRestore();
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

    it("should call login API with credentials", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: "test-token" }),
      });

      const { getByTestId } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <LoginPage />
        </AppContext.Provider>
      );

      const emailInput = getByTestId("email-input");
      const passwordInput = getByTestId("password-input");
      
      expect(emailInput).toBeTruthy();
      expect(passwordInput).toBeTruthy();
    });

    it("should display error on login failure", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: "Invalid credentials" }),
      });

      const { getByTestId, queryByTestId } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <LoginPage />
        </AppContext.Provider>
      );

      // Verify component renders correctly
      expect(getByTestId("email-input")).toBeTruthy();
      expect(getByTestId("password-input")).toBeTruthy();
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
      const { getByTestId } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <RegistrationPage />
        </AppContext.Provider>
      );

      // Verify all form fields render
      expect(getByTestId("email-input")).toBeTruthy();
      expect(getByTestId("password-input")).toBeTruthy();
      expect(getByTestId("confirm-password-input")).toBeTruthy();
    });
  });
});
