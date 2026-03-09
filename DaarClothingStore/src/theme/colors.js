import { MD3DarkTheme } from 'react-native-paper';

export const COLORS = {
  primary: '#e94560',
  secondary: '#8b2f97',
  background: '#0f0f23',
  surface: '#1a1a2e',
  text: '#ffffff',
  textSecondary: '#a0a0a0',
  error: '#e74c3c',
  success: '#27ae60',
};

export const theme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: COLORS.primary,
    secondary: COLORS.secondary,
    background: COLORS.background,
    surface: COLORS.surface,
    onSurface: COLORS.text,
    onBackground: COLORS.text,
  },
};
