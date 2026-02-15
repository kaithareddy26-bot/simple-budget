import * as React from 'react';
import { AppRegistry, View } from 'react-native';
import { PaperProvider } from 'react-native-paper';
import LoginPage from '@/components/LoginPage';

const appName = "Simple Budgeting App";
export default function Login() {
  return (
    <PaperProvider>
      <View style={{ alignSelf: "center", width: "90%"}}>
        <LoginPage />
      </View>
    </PaperProvider>
  );
}


AppRegistry.registerComponent(appName, () => Login);