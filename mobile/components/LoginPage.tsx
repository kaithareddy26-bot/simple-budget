import AppContext from "@/app/context/AppContext";
import { useContext, useState } from "react";
import { Button, Text, TextInput } from "react-native-paper";

export default function LoginPage() {
  const { jwt, setJwt } = useContext(AppContext);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
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
      const data = await response.json();
      console.log(data);
      if (response.ok) {
        // Registration successful, handle accordingly (e.g., navigate to login page)
        console.log("USer has been logged in");
        setJwt(data.access_token);
      } else {
        // Handle login failure (e.g., display error message)
        console.error("Login failed:", data);
        setErrorMessage(data.error?.message || "Login failed");
        throw new Error(data.error?.message || "Login failed");
      }
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <>
      <Text>Welcome Back!</Text>
      <h1>Login Page</h1>
      <Text>{email}</Text>
      <Text>{password}</Text>
      <TextInput placeholder="Email" value={email} onChangeText={setEmail} />
      <TextInput
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry={true}
      />
      <Button mode="elevated" onPress={handleLoginSubmit}>
        Login
      </Button>
    </>
  );
}
