import { Tabs } from "expo-router";

export default function TabLayout() {
  return (
    <Tabs>
      <Tabs.Screen name="index" options={{ title: "Index" }} />
      <Tabs.Screen name="registration" options={{ title: "Register" }} />
      <Tabs.Screen name="home" options={{ title: "Home" }} />
      <Tabs.Screen name="login" options={{ title: "Login" }} />
    </Tabs>
  );
}
