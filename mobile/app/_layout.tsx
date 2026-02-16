import { Stack } from "expo-router";
import AppContext from "./context/AppContext";
import React from "react";

export default function RootLayout() {
  const [jwt, setJwt] = React.useState("not-set-yet");
  return (
    <AppContext.Provider value={{ jwt, setJwt }}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </AppContext.Provider>
  );
}
