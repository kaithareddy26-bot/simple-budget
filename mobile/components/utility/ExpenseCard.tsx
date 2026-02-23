import * as React from 'react';
import { Card, Text } from 'react-native-paper';
export default function ExpenseCard({ header, amount, note }: { header: string; amount: number; note: string }) {
    const cardTheme = {
        colors: {
            surfaceVariant: "black"
        }
    }
    return (
        <Card mode="contained" theme={cardTheme} style={{ marginBottom: 10 }}>
            <Card.Title title={header} subtitle={`$${amount}`}/>
            <Card.Content>
                <Text variant="bodyMedium">{note}</Text>
            </Card.Content>
        </Card>)
}