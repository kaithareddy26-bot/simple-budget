import AppContext from "@/app/context/AppContext";
import sharedStyles from "@/styles/shared";
import { useContext } from "react";
import { Text } from "react-native-paper";
export function  HomePage() {
  const jwt = useContext(AppContext).jwt;
  return (
      <Text variant="displayLarge" style={sharedStyles.centeredText.text} theme={{ colors: { onSurface: "black" } }}>
        "Your JWT is: {jwt}"
      </Text>
        );
}
export default HomePage;