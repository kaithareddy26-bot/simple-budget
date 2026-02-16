import * as React from 'react';
import { AppRegistry, View } from 'react-native';
import { PaperProvider } from 'react-native-paper';
import { WelcomePage } from '@/components/WelcomePage';

const appName = "Simple Budgeting App";
export default function Index() {
  return (
    <PaperProvider>
      <View style={{ alignSelf: "center", width: "90%"}}>
        <WelcomePage />
      </View>
    </PaperProvider>
  );
}


AppRegistry.registerComponent(appName, () => Index);