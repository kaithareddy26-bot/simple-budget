import { useState } from "react";
import { Button, Text, TextInput } from "react-native-paper";

export default function RegistrationPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");

    const handleRegistrationSubmit = async () => {
        console.log("Form Submitted!")
        const url = 'http://localhost:8000/api/v1/auth/register';
        const options = {
            method: 'POST',
            headers: {
                'content-type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                full_name: fullName,
                password: password
            })
        };

        try {
            const response = await fetch(url, options);
            const data = await response.json();
            console.log(data);
        } catch (error) {
            console.error(error);
        }
    }
    return (
        <>
            <h1>Register for simple-budget-app!</h1>
            <Text>{email}</Text>
            <Text>{password}</Text>
            <TextInput
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
            />
            <TextInput
                placeholder="Full Name"
                value={fullName}
                onChangeText={setFullName}
            />
            <TextInput
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={true}
            />
            <Button mode="elevated" onPress={handleRegistrationSubmit}>Register</Button>
        </>
    );
}