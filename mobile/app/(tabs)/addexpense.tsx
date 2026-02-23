import AddExpenseFormPage from '@/components/AddExpenseForm';
import * as React from 'react';
import { AppRegistry, View } from 'react-native';
import { PaperProvider } from 'react-native-paper';

const appName = "Simple Budgeting App";
export default function Index() {
  return (
    <PaperProvider>
      <View style={{ alignSelf: "center", width: "90%"}}>
        <AddExpenseFormPage />
      </View>
    </PaperProvider>
  );
}


AppRegistry.registerComponent(appName, () => Index);