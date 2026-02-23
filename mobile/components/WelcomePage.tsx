import AppContext from "@/app/context/AppContext";
import { useIsFocused } from "@react-navigation/native";
import { Redirect } from "expo-router";
import { useCallback, useContext, useEffect, useState } from "react";
import { ScrollView } from "react-native";
import { Button, Text, TextInput } from "react-native-paper";
import getErrorMessage from "@/utilities/getErrorMessage";
import ExpenseCard from "./utility/ExpenseCard";

interface BudgetData {
  totalAmount: number;
}

interface ExpenseData {
  id: string;
  category: string;
  amount: number;
  note?: string;
}

export function WelcomePage() {
  const { jwt } = useContext(AppContext);
  const [errorMessage, setErrorMessage] = useState("");
  const [budgetData, setBudgetData] = useState<BudgetData | null>(null);
  const [expensesData, setExpensesData] = useState<ExpenseData[]>([]);
  const [requiresBudgetSetup, setRequiresBudgetSetup] = useState(false);
  const [budgetAmount, setBudgetAmount] = useState("");
  const [isSubmittingBudget, setIsSubmittingBudget] = useState(false);
  const isFocused = useIsFocused();

  const fetchBudget = useCallback(async () => {
    try {
      const url = "http://localhost:8000/api/v1/budgets/current-month";
      const options = {
        method: "GET",
        headers: {
          "content-type": "application/json",
          "Authorization": `Bearer ${jwt}`,
        }
      }
      const response = await fetch(url, options);
      const data = await response.json();
      console.log(data);
      const hasBudgetPayload = Boolean(
        data &&
        typeof data === "object" &&
        "totalAmount" in (data as Record<string, unknown>)
      );

      if (response.ok && hasBudgetPayload) {
        console.log("Budget retrieved successfully!");
        setErrorMessage("");
        setRequiresBudgetSetup(false);
        setBudgetData(data as BudgetData);
      } else if (response.status === 404 || (response.ok && !hasBudgetPayload)) {
        setRequiresBudgetSetup(true);
        setBudgetData(null);
        setErrorMessage("");
      } else {
        console.error("Unable to retrieve budget:", data);
        const message = getErrorMessage(data, "Unable to retrieve budget");
        setErrorMessage(message);
        throw new Error(message);
      }
    } catch (error) {
      console.error(error);
    }
  }, [jwt]);

  const createBudget = async () => {
    const amountAsNumber = parseFloat(budgetAmount);
    if (Number.isNaN(amountAsNumber) || amountAsNumber <= 0) {
      setErrorMessage("Please enter a valid budget amount greater than 0");
      return;
    }

    const currentMonth = new Date().toISOString().slice(0, 7);
    const url = "http://localhost:8000/api/v1/budgets";
    const options = {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "Authorization": `Bearer ${jwt}`,
      },
      body: JSON.stringify({
        month: currentMonth,
        amount: amountAsNumber,
      }),
    };

    try {
      setIsSubmittingBudget(true);
      const response = await fetch(url, options);
      const data = await response.json();

      if (response.ok) {
        setErrorMessage("");
        setBudgetAmount("");
        setRequiresBudgetSetup(false);
        setBudgetData(data);
        await fetchExpenses();
      } else {
        const message = getErrorMessage(data, "Unable to create budget");
        setErrorMessage(message);
      }
    } catch (error) {
      console.error(error);
      setErrorMessage("Unable to create budget");
    } finally {
      setIsSubmittingBudget(false);
    }
  };

  const fetchExpenses = useCallback(async () => {
    const url = "http://localhost:8000/api/v1/expenses/current-month";
    const options = {
      method: "GET",
      headers: {
        "content-type": "application/json",
        "Authorization": `Bearer ${jwt}`,
      },
    };
    try {
      const response = await fetch(url, options);
      const data = await response.json();
      console.log(data);
      if (response.ok) {
        setExpensesData(data);
      } else {
        setErrorMessage(getErrorMessage(data, "Unable to retrieve expenses"));
      }
    } catch (error) {
      console.error(error);
    }
  }, [jwt]);
  useEffect(() => {
    fetchBudget();
    setExpensesData([]);
  }, [fetchBudget]);

  useEffect(() => {
    console.log("HomePage focus state changed. Is focused:", isFocused);
    setErrorMessage("");
    setBudgetAmount("");
    console.log("HomePage is focused, refetching budget and expenses");
    fetchBudget();
    setExpensesData([]);
  }, [fetchBudget, isFocused]);

  useEffect(() => {
    if (budgetData) {
      fetchExpenses();
    }
  }, [budgetData, fetchExpenses]);

  const blackTextTheme = {
    colors: {
      onSurface: "black"
    }
  };
  if (!jwt) {
    return <Redirect href="/login" />;
  }
  return (
    <>
      <ScrollView>
        <Text theme={blackTextTheme} variant="headlineLarge">{errorMessage}</Text>
        {requiresBudgetSetup ? (
          <>
            <Text theme={blackTextTheme} variant="headlineLarge">Set your monthly budget to get started</Text>
            <TextInput
              label="Monthly budget ($)"
              value={budgetAmount}
              onChangeText={setBudgetAmount}
              keyboardType="decimal-pad"
            />
            <Button mode="contained" onPress={createBudget} loading={isSubmittingBudget} disabled={isSubmittingBudget}>
              Save Budget
            </Button>
          </>
        ) : null}
        {budgetData && <Text theme={blackTextTheme} variant="headlineLarge">Current month budget: ${budgetData.totalAmount}</Text>}
        {budgetData && expensesData && expensesData.map((expense: ExpenseData) => (
          <ExpenseCard key={expense.id} header={expense.category} amount={expense.amount} note={expense.note || ""} />
        ))}
      </ScrollView>
    </>
  );
}