import { useState } from "react";
import { Button, Text, TextInput } from "react-native-paper";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const handleLoginSubmit = () => {
        console.log("Login handling goes here")
    }

    return (
        <>
            <Text>Welcome Back!</Text>
            <h1>Registration Page</h1>
            <Text>{email}</Text>
            <Text>{password}</Text>
            <TextInput
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
            />
            <TextInput
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={true}
            />
            <Button mode="elevated" onPress={handleLoginSubmit}>Login</Button>
        </>
    );
}