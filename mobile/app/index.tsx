import RegistrationPage from "@/components/RegistrationPage";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";

export default function Index() {
  return (
    <SafeAreaProvider>
      <SafeAreaView>
        {/* <WelcomePage /> */}
        <RegistrationPage />
      </SafeAreaView>
  </SafeAreaProvider>
  );
}
