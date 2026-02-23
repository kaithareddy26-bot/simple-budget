import AppContext from "@/app/context/AppContext";
import AlertMessage from "@/components/utility/AlertMessage";
import getErrorMessage from "@/utilities/getErrorMessage";
import { useIsFocused } from "@react-navigation/native";
import { router } from "expo-router";
import { useContext, useEffect, useState } from "react";
import { Button, Text, TextInput } from "react-native-paper";

export default function LoginPage() {
    const { setJwt } = useContext(AppContext);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const isFocused = useIsFocused();

    useEffect(() => {
        if (isFocused) {
            setEmail("");
            setPassword("");
            setErrorMessage("");
            setSuccessMessage("");
        }
    }, [isFocused]);

    const clearMessage = () => {
        if (errorMessage || successMessage) {
            setErrorMessage("");
            setSuccessMessage("");
        }
    };

    const handleLoginSubmit = async () => {
        console.log("Form Submitted!");
        const url = "http://localhost:8000/api/v1/auth/login";
        const options = {
            method: "POST",
            headers: {
                "content-type": "application/json",
            },
            body: JSON.stringify({
                email: email,
                password: password,
            }),
        };
        try {
            const response = await fetch(url, options);
            const data: unknown = await response.json();
            console.log(data);
            if (response.ok) {
                console.log("User has been logged in");
                setErrorMessage("");
                setSuccessMessage("Login successful");
                setTimeout(() => {
                    setSuccessMessage("");
                    setJwt((data as { access_token: string }).access_token);
                    router.replace("/(tabs)");
                }, 900);
            } else {
                // Handle login failure (e.g., display error message)
                console.error("Login failed:", data);
                const message = getErrorMessage(data, "Login failed");
                setSuccessMessage("");
                setErrorMessage(message);
                throw new Error(message);
            }
        } catch (error) {
            console.error(error);
        }
    };
    const blackTextTheme = {
        colors: {
            onSurface: "black"
        }
    };

    return (
        <>
            <Text variant="displayLarge" style={{ textAlign: "center" }} theme={blackTextTheme}>Welcome Back!</Text>
            <Text variant="headlineSmall" theme={blackTextTheme}>Login</Text>
            {errorMessage ? <AlertMessage message={errorMessage} isError={true} /> : null}
            {successMessage ? <AlertMessage message={successMessage} isError={false} /> : null}
            <TextInput
                placeholder="Email"
                value={email}
                onChangeText={(value) => {
                    clearMessage();
                    setEmail(value);
                }}
            />
            <TextInput
                placeholder="Password"
                value={password}
                onChangeText={(value) => {
                    clearMessage();
                    setPassword(value);
                }}
                secureTextEntry={true}
            />
            <Button mode="elevated" onPress={handleLoginSubmit}>Login</Button>
        </>
    );
}
