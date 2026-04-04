import { Tabs } from "expo-router";
import { useContext } from "react";
import { Pressable, Text } from "react-native";
import sharedStyles from "@/styles/shared";
import AppContext from "../context/AppContext";

export default function TabLayout() {
  const { jwt, setJwt } = useContext(AppContext);
  const userIsLoggedIn = jwt !== "";
  return (
    <Tabs screenOptions={{
      headerRight: () => userIsLoggedIn ? (
        <Pressable testID="logout-button" onPress={() => setJwt("")} style={{ marginRight: 12 }}>
          <Text style={{ color: sharedStyles.greenButton.colors.primary }}>Logout</Text>
        </Pressable>
      ) : null
    }}>
      <Tabs.Screen testID="home-tab" name="index" options={{ title: "Current Month", href: userIsLoggedIn ? "/(tabs)" : null }} />
      <Tabs.Screen testID="register-button" name="registration" options={{ title: "Register", href: userIsLoggedIn ? null : "/registration" }} />
      <Tabs.Screen name="home" options={{ title: "Home", href: null}} /> 
      <Tabs.Screen testID="add-expense-tab" name="addexpense" options={{ title: "Add Expense", href: userIsLoggedIn ? "/(tabs)/addexpense" : null }} />
      <Tabs.Screen testID="login-button" name="login" options={{ title: "Login", href: userIsLoggedIn ? null : "/login" }} />
    </Tabs>
  );
}
