import AppContext from "@/app/context/AppContext";
import sharedStyles from "@/styles/shared";
import { Redirect } from "expo-router";
import { useContext } from "react";
import { Text } from "react-native-paper";
export function HomePage() {
  const { jwt } = useContext(AppContext);

  if (!jwt) {
    return <Redirect href="/login" />;
  }

  return (
      <>
      <Text testID="home-page" variant="displayLarge" style={sharedStyles.centeredText.text} theme={{ colors: { onSurface: "black" } }}>
        Your JWT is: {jwt}
      </Text>
      </>
        );
}
export default HomePage;
export default HomePage;