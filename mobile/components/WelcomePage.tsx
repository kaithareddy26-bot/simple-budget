import AppContext from "@/app/context/AppContext";
import { useIsFocused } from "@react-navigation/native";
import { Redirect } from "expo-router";
import { useContext, useEffect, useState } from "react";
import { ScrollView } from "react-native";
import { Text } from "react-native-paper";
import ExpenseCard from "./utility/ExpenseCard";
export function WelcomePage() {
  const { jwt, setJwt } = useContext(AppContext);
  const [errorMessage, setErrorMessage] = useState("");
  const [budgetData, setBudgetData] = useState({});
  const [expensesData, setExpensesData] = useState([]);
  const isFocused = useIsFocused();

  const fetchBudget = async () => {
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
      if (response.ok) {
        // Successfully retrieved budget, handle accordingly (e.g., display budget information)
        console.log("Budget retrieved successfully!");
        setErrorMessage("");
        setBudgetData(data);
      } else {
        // Handle login failure (e.g., display error message)
        console.error("Unable to retrieve budget:", data);
        setErrorMessage(data.error?.message || "Unable to retrieve budget");
        throw new Error(data.error?.message || "Unable to retrieve budget");
      }
    } catch (error) {
      console.error(error);
    }
  };
  const fetchExpenses = async () => {
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
        setErrorMessage(data.error?.message || "Unable to retrieve expenses");
      }
    } catch (error) {
      console.error(error);
    }
  }
  useEffect(() => {
    fetchBudget();
    fetchExpenses();
  }, []);

  useEffect(() => {
    console.log("HomePage focus state changed. Is focused:", isFocused);
    setErrorMessage("");
    console.log("HomePage is focused, refetching budget and expenses");
    fetchBudget();
    fetchExpenses();
  }, [isFocused]);

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
        {budgetData && <Text theme={blackTextTheme} variant="headlineLarge">Current month's budget: {budgetData.totalAmount}</Text>}
        {expensesData && expensesData.map((expense: any) => (
          <ExpenseCard key={expense.id} header={expense.category} amount={expense.amount} note={expense.note} />
        ))}
      </ScrollView>
    </>
  );
}