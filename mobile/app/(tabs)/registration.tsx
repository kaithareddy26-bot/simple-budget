import * as React from "react";
import RegistrationPage from "@/components/RegistrationPage";
import { AppRegistry, View } from "react-native";
import { PaperProvider } from "react-native-paper";
const appName = "Simple Budgeting App";

export default function Registration() {
  return (
    <PaperProvider>
      <View style={{ alignSelf: "center", width: "90%" }}>
        <RegistrationPage />
      </View>
    </PaperProvider>
  );
}

AppRegistry.registerComponent(appName, () => Registration);
