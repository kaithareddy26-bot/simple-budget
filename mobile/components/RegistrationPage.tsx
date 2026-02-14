import { useState } from "react";
import { Text, TextInput } from "react-native";

export default function RegistrationPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
  return (
    <>
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
    </>
  );
}