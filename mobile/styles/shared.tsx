import { StyleSheet } from 'react-native';

const lightMargin = StyleSheet.create({
    text: {
        margin: 8
    },
    textInput: {
        margin: 8
    }
})

const mainText = {colors: { onSurface:  "black"} }
const greenButton = {
    margin: 8,
    colors: {
        primary: "green",
        onPrimary: "black"
    }
}
const centeredText = StyleSheet.create({
    text: {
        textAlign: "center"
    }
})
const sharedStyles = {
    lightMargin: lightMargin,
    mainText: mainText,
    greenButton: greenButton,
    centeredText: centeredText
}

export default sharedStyles