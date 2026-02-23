import AppContext from "@/app/context/AppContext";
import sharedStyles from "@/styles/shared";
import getErrorMessage from "@/utilities/getErrorMessage";
import { useIsFocused } from "@react-navigation/native";
import { Redirect } from "expo-router";
import { useContext, useEffect, useState } from "react";
import { Button, Text, TextInput } from "react-native-paper";
export function AddExpenseForm() {
    const jwt = useContext(AppContext).jwt;
    const [errorMessage, setErrorMessage] = useState("");
    const [category, setCategory] = useState("");
    const [amount, setAmount] = useState("");
    const [note, setNote] = useState("");
    const isFocused = useIsFocused();

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
                // Registration successful, handle accordingly (e.g., navigate to login page)
                console.log("Expense Created");
            } else {
                // Handle login failure (e.g., display error message)
                console.error("Expense creation failed:", data);
                const message = getErrorMessage(data, "Expense creation failed");
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
        setAmount("");
        setCategory("");
        setNote("");
    }, [isFocused]);

    if (!jwt) {
        return <Redirect href="/login" />;
    }
    
    return (
        <>
            {errorMessage ? <Text style={{ color: "red" }}>{errorMessage}</Text> : null}
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
                label="Amount"
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