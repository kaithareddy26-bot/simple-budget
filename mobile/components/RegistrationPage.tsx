import AlertMessage from "@/components/utility/AlertMessage";
import sharedStyles from "@/styles/shared";
import getErrorMessage from "@/utilities/getErrorMessage";
import { useIsFocused } from "@react-navigation/native";
import { useEffect, useState } from "react";
import { router } from "expo-router";
import { Button, Text, TextInput } from "react-native-paper";

export default function RegistrationPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const isFocused = useIsFocused();

  const clearMessages = () => {
    if (errorMessage || successMessage) {
      setErrorMessage("");
      setSuccessMessage("");
    }
  };

  useEffect(() => {
    console.log("Registration Mounted");
  }, []);

  useEffect(() => {
    if (isFocused) {
      setEmail("");
      setFullName("");
      setPassword("");
      setErrorMessage("");
      setSuccessMessage("");
    }
  }, [isFocused]);
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
        console.log("Registration successful!");
        setErrorMessage("");
        setSuccessMessage("Registration successful");
        setEmail("");
        setFullName("");
        setPassword("");
        setTimeout(() => {
          setSuccessMessage("");
          setErrorMessage("");
          router.replace("/(tabs)/login");
        }, 1200);
      } else {
        // Handle registration failure (e.g., display error message)
        console.error("Registration failed:", data);
        const message = getErrorMessage(data, "Registration failed");
        setSuccessMessage("");
        setErrorMessage(message);
        throw new Error(message);
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
      {errorMessage && <AlertMessage message={errorMessage} isError={true} />}
      {successMessage && <AlertMessage message={successMessage} isError={false} />}
      <TextInput
        mode="outlined"
        style={sharedStyles.lightMargin.textInput}
        placeholder="Email"
        value={email}
        onChangeText={(value) => {
          clearMessages();
          setEmail(value);
        }}
      />
      <TextInput
        mode="outlined"
        style={sharedStyles.lightMargin.textInput}
        placeholder="Full Name"
        value={fullName}
        onChangeText={(value) => {
          clearMessages();
          setFullName(value);
        }}
      />
      <TextInput
        mode="outlined"
        style={sharedStyles.lightMargin.textInput}
        placeholder="Password"
        value={password}
        onChangeText={(value) => {
          clearMessages();
          setPassword(value);
        }}
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
