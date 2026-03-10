import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Image } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { me } from '../api';
import theme from '../theme';

const logoSource = require('../../assets/daar-logo.png');

export default function SplashScreen({ navigation }) {
  const scaleAnim = useRef(new Animated.Value(0.6)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(scaleAnim, { toValue: 1, duration: 520, useNativeDriver: true }),
      Animated.timing(fadeAnim, { toValue: 1, duration: 520, useNativeDriver: true }),
    ]).start();

    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.05, duration: 700, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 700, useNativeDriver: true }),
      ])
    );
    loop.start();

    (async () => {
      try {
        await Promise.all([me(), new Promise((r) => setTimeout(r, 900))]);
        navigation.replace('Root');
      } catch {
        await new Promise((r) => setTimeout(r, 900));
        navigation.replace('Root');
      }
    })();
    return () => {
      loop.stop();
    };
  }, [fadeAnim, navigation, pulseAnim, scaleAnim]);
  return (
    <LinearGradient colors={[theme.colors.accent, theme.colors.accentAlt]} style={styles.container}>
      <Animated.View style={[styles.logoWrap, { transform: [{ scale: scaleAnim }, { scale: pulseAnim }], opacity: fadeAnim }]}>
        <View style={styles.logoCircle}>
          <Image source={logoSource} style={styles.logoImage} />
        </View>
        <Text style={styles.logoTitle}>دار</Text>
        <Text style={styles.logoSubtitle}>DAAR</Text>
      </Animated.View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoWrap: {
    alignItems: 'center',
    gap: 10,
  },
  logoCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoImage: {
    width: 78,
    height: 78,
    borderRadius: 39,
    resizeMode: 'contain',
  },
  logoTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: 28,
  },
  logoSubtitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    fontSize: 16,
    letterSpacing: 4,
  },
});
