import React from "react";
import { Text as RNText, TextInput as RNTextInput, TouchableOpacity, View } from "react-native";

export const Text = (props: any) => <RNText {...props} />;
export const TextInput = (props: any) => <RNTextInput {...props} />;

// Minimal Button that supports press + shows children text
export const Button = ({ onPress, children, disabled }: any) => (
  <TouchableOpacity onPress={onPress} disabled={disabled}>
    <RNText>{children}</RNText>
  </TouchableOpacity>
);

export const Card = ({ children }: any) => <View>{children}</View>;
Card.Title = ({ title, subtitle }: any) => (
  <>
    <RNText>{title}</RNText>
    <RNText>{subtitle}</RNText>
  </>
);
Card.Content = ({ children }: any) => <View>{children}</View>;