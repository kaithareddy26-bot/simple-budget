import { useContext, useEffect, useState } from "react";
import { Button, Text, TextInput } from "react-native-paper";
import AlertMessage from "@/components/utility/AlertMessage";
import sharedStyles from "@/styles/shared";
import AppContext from "@/app/context/AppContext";

export default function RegistrationPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
	const setJwt = useContext(AppContext).setJwt;
useEffect(() => {
	console.log("Registration Mounted");
	setJwt("test-jwt-value");
}, []);
  const handleRegistrationSubmit = async () => {
    console.log("Form Submitted!");
    const url = "http://localhost:8000/api/v1/auth/register";
    const options = {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        full_name: fullName,
        password: password,
      }),
    };

    try {
      const response = await fetch(url, options);
      const data = await response.json();
      console.log(data);
      if (response.ok) {
        // Registration successful, handle accordingly (e.g., navigate to login page)
        console.log("Registration successful!");
      } else {
        // Handle registration failure (e.g., display error message)
        console.error("Registration failed:", data);
        setErrorMessage(data.error?.message || "Registration failed");
        throw new Error(data.error?.message || "Registration failed");
      }
    } catch (error) {
      console.error(error);
    }
  };
  return (
    <>
      <Text variant="displayLarge" style={sharedStyles.centeredText.text} theme={{ colors: { onSurface: "black" } }}>
        Register for SimpleBudgetApp
      </Text>
      {errorMessage && <AlertMessage message={errorMessage} />}
      <TextInput
        mode="outlined"
        style={sharedStyles.lightMargin.textInput}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        mode="outlined"
        style={sharedStyles.lightMargin.textInput}
        placeholder="Full Name"
        value={fullName}
        onChangeText={setFullName}
      />
      <TextInput
        mode="outlined"
        style={sharedStyles.lightMargin.textInput}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry={true}
      />
      <Button
        theme={sharedStyles.greenButton}
        mode="contained"
        onPress={handleRegistrationSubmit}
      >
        Register
      </Button>
    </>
  );
}
