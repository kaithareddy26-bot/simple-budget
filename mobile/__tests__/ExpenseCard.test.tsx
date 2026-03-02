import React from "react";
import { render } from "@testing-library/react-native";
import ExpenseCard from "@/components/utility/ExpenseCard";

describe("ExpenseCard", () => {
  test("renders header, amount, and note", () => {
    const screen = render(
      <ExpenseCard header="Groceries" amount={42.5} note="Weekly shopping" />
    );

    expect(screen.getByText("Groceries")).toBeTruthy();
    expect(screen.getByText("$42.5")).toBeTruthy();
    expect(screen.getByText("Weekly shopping")).toBeTruthy();
  });

  test("formats zero amount with dollar prefix", () => {
    const screen = render(
      <ExpenseCard header="Transport" amount={0} note="Bus pass" />
    );

    expect(screen.getByText("$0")).toBeTruthy();
  });
});
