import React from 'react';
import { Appbar } from 'react-native-paper';
import { COLORS } from '../theme/colors';

export default function Header({ title, onBack }) {
  return (
    <Appbar.Header style={{ backgroundColor: COLORS.surface }}>
      {onBack ? <Appbar.BackAction onPress={onBack} color={COLORS.text} /> : null}
      <Appbar.Content title={title} titleStyle={{ color: COLORS.text }} />
    </Appbar.Header>
  );
}
