import React from "react";
import { render, waitFor } from "@testing-library/react-native";
import AppContext from "@/app/context/AppContext";
import WelcomePage from "@/components/WelcomePage";
import HomePage from "@/components/HomePage";

jest.mock("expo-router", () => ({
  Redirect: ({ href }: { href: string }) => {
    const { Text } = require("react-native");
    return <Text>Redirecting to {href}</Text>;
  },
  useRouter: () => ({
    replace: jest.fn(),
    push: jest.fn(),
  }),
}));

jest.mock("@react-navigation/native", () => ({
  useIsFocused: () => true,
}));

jest.mock("@/utilities/getErrorMessage", () => ({
  __esModule: true,
  default: (_: any, fallback: string) => fallback,
}));

jest.mock("@/components/utility/AlertMessage", () => ({
  __esModule: true,
  default: () => null,
}));

describe("Navigation E2E Tests", () => {
  let consoleErrorSpy: jest.SpyInstance;
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.useFakeTimers();
    (global as any).fetch = jest.fn();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  describe("Route Guards and Rendering", () => {
    it("should redirect welcome page to login when unauthenticated", () => {
      const { getByText } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <WelcomePage />
        </AppContext.Provider>
      );

      expect(getByText("Redirecting to /login")).toBeTruthy();
    });

    it("should render welcome page content when authenticated", async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ totalAmount: 1200 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ totalAmount: 1200 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ([{ id: "1", category: "Food", amount: 20, note: "Lunch" }]),
        });

      const { getByTestId, getByText } = render(
        <AppContext.Provider value={{ jwt: "jwt-token", setJwt: jest.fn() }}>
          <WelcomePage />
        </AppContext.Provider>
      );

      expect(getByTestId("welcome-page")).toBeTruthy();

      await waitFor(() => {
        expect(getByText("Current month budget: $1200")).toBeTruthy();
      });
      expect(getByText("Lunch")).toBeTruthy();
    });

    it("should redirect home page to login when unauthenticated", () => {
      const { getByText } = render(
        <AppContext.Provider value={{ jwt: "", setJwt: jest.fn() }}>
          <HomePage />
        </AppContext.Provider>
      );

      expect(getByText("Redirecting to /login")).toBeTruthy();
    });

    it("should render home page jwt text when authenticated", () => {
      const { getByTestId, getByText } = render(
        <AppContext.Provider value={{ jwt: "jwt-token", setJwt: jest.fn() }}>
          <HomePage />
        </AppContext.Provider>
      );

      expect(getByTestId("home-page")).toBeTruthy();
      expect(getByText("Your JWT is: jwt-token")).toBeTruthy();
    });
  });
});

