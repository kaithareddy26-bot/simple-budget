import toTitleCase from "@/utilities/toTitleCase";
import { Banner, Text } from "react-native-paper";
export default function AlertMessage({
  message,
  isError,
}: {
  message: string;
  isError?: boolean;
}) {
	const textTheme = {
    colors: { onSurface: "white" }
	};

	const bannerTheme = {
    backgroundColor: isError ? "red" : "green"
	}
  return (
    <Banner style={bannerTheme} visible={true}>
      <Text theme={textTheme} variant="headlineMedium">{toTitleCase(message)}</Text>
    </Banner>
  );
}
