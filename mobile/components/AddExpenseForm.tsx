import AppContext from "@/app/context/AppContext";
import AlertMessage from "@/components/utility/AlertMessage";
import sharedStyles from "@/styles/shared";
import getErrorMessage from "@/utilities/getErrorMessage";
import { useIsFocused } from "@react-navigation/native";
import { Redirect, useRouter } from "expo-router";
import { useCallback, useContext, useEffect, useState } from "react";
import { Button, Text, TextInput } from "react-native-paper";
export function AddExpenseForm() {
    const jwt = useContext(AppContext).jwt;
    const router = useRouter();
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const [category, setCategory] = useState("");
    const [amount, setAmount] = useState("");
    const [note, setNote] = useState("");
    const [hasBudget, setHasBudget] = useState<boolean | null>(null);
    const isFocused = useIsFocused();

    const checkBudgetExists = useCallback(async () => {
        try {
            const url = "http://localhost:8000/api/v1/budgets/current-month";
            const options = {
                method: "GET",
                headers: {
                    "content-type": "application/json",
                    "Authorization": `Bearer ${jwt}`,
                }
            };
            const response = await fetch(url, options);
            const data = await response.json();
            
            const budgetExists = response.ok && data && typeof data === "object" && "totalAmount" in data;
            setHasBudget(budgetExists);
        } catch (error) {
            console.error("Error checking budget:", error);
            setHasBudget(false);
        }
    }, [jwt]);

    useEffect(() => {
        if (jwt) {
            checkBudgetExists();
        }
    }, [jwt, checkBudgetExists, isFocused]);

    const handleFormSubmit = async () => {
        console.log("Form Submitted!");
        const url = "http://localhost:8000/api/v1/expenses";
        const options = {
            method: "POST",
            headers: {
                "content-type": "application/json",
                "authorization": `Bearer ${jwt}`,
            },
            body: JSON.stringify({
                amount: parseFloat(amount),
                category: category,
                note: note,
                date: new Date().toISOString().split("T")[0], // Get current date in YYYY-MM-DD format
            }),
        };
        try {
            const response = await fetch(url, options);
            const data: unknown = await response.json();
            console.log(data);
            if (response.ok) {
                console.log("Expense Created");
                setErrorMessage("");
                setSuccessMessage("Expense added successfully");
                setCategory("");
                setAmount("");
                setNote("");
                setTimeout(() => {
                    setSuccessMessage("");
                }, 2000);
            } else {
                // Handle login failure (e.g., display error message)
                console.error("Expense creation failed:", data);
                const message = getErrorMessage(data, "Expense creation failed");
                setSuccessMessage("");
                setErrorMessage(message);
                throw new Error(message);
            }
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => {
        console.log("AddExpenseForm focus changed. Is focused:", isFocused);
        console.log("Resetting form state and error message.");
        setErrorMessage("");
        setSuccessMessage("");
        setAmount("");
        setCategory("");
        setNote("");
    }, [isFocused]);

    if (!jwt) {
        return <Redirect href="/login" />;
    }

    if (hasBudget === null) {
        return (
            <Text variant="bodyLarge" style={sharedStyles.centeredText.text} theme={{ colors: { onSurface: "black" } }}>
                Loading...
            </Text>
        );
    }

    if (hasBudget === false) {
        return (
            <>
                <Text variant="displayMedium" style={sharedStyles.centeredText.text} theme={{ colors: { onSurface: "black" } }}>
                    Set up your budget first
                </Text>
                <Text variant="bodyLarge" style={{ ...sharedStyles.centeredText.text, marginTop: 16 }} theme={{ colors: { onSurface: "black" } }}>
                    You need to set a monthly budget before you can add expenses.
                </Text>
                <Button 
                    mode="contained" 
                    theme={sharedStyles.greenButton}
                    onPress={() => router.push("/(tabs)")} 
                    style={{ marginTop: 20 }}
                >
                    Go to Current Month
                </Button>
            </>
        );
    }
    
    return (
        <>
            {errorMessage ? <AlertMessage message={errorMessage} isError={true} /> : null}
            {successMessage ? <AlertMessage message={successMessage} isError={false} /> : null}
            <Text variant="displayLarge" style={sharedStyles.centeredText.text} theme={{ colors: { onSurface: "black" } }}>
                Enter a new expense.
            </Text>
            <TextInput
                label="Category"
                value={category}
                onChangeText={text => setCategory(text)}
                style={{ marginBottom: 8 }}

            />
            <TextInput
                label="Amount ($)"
                value={amount}
                onChangeText={text => setAmount(text)}
                style={{ marginBottom: 8 }}

            />
            <TextInput
                label="Note"
                value={note}
                onChangeText={text => setNote(text)}
                style={{ marginBottom: 16 }}
            />
            <Button theme={sharedStyles.greenButton}
                mode="contained" onPress={handleFormSubmit}>Submit</Button>
        </>
    );
}
export default AddExpenseForm;