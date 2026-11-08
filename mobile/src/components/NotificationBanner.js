import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { COLORS } from '../theme/colors';

const { width } = Dimensions.get('window');

export default function NotificationBanner({ notification, onDismiss, onPress }) {
  const translateY = useRef(new Animated.Value(-120)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (notification) {
      Animated.parallel([
        Animated.spring(translateY, {
          toValue: 0,
          friction: 7,
          tension: 40,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 1,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();

      const timer = setTimeout(() => {
        handleClose();
      }, 6500);

      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleClose = () => {
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: -120,
        duration: 250,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      if (onDismiss) onDismiss();
    });
  };

  if (!notification) return null;

  const isGoal = notification.type === 'GOAL' || notification.notification_type === 'GOAL';
  const isLineup = notification.type === 'LINEUP' || notification.notification_type === 'LINEUP';

  return (
    <Animated.View
      style={[
        styles.wrapper,
        {
          transform: [{ translateY }],
          opacity,
        },
      ]}
    >
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => {
          if (onPress) onPress(notification);
          handleClose();
        }}
        style={[styles.container, isGoal && styles.containerGoal, isLineup && styles.containerLineup]}
      >
        <View style={styles.topRow}>
          <View style={[styles.badge, isGoal && styles.badgeGoal, isLineup && styles.badgeLineup]}>
            <Text style={styles.badgeText}>
              {isGoal ? '⚽ CANLI GOL!' : isLineup ? '📋 İLK 11' : '🔔 BİLDİRİM'}
            </Text>
          </View>
          <Text style={styles.timeText}>Şimdi</Text>
          <TouchableOpacity onPress={handleClose} style={styles.closeBtn} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Text style={styles.closeText}>✕</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.title} numberOfLines={1}>
          {notification.title}
        </Text>
        <Text style={styles.body} numberOfLines={2}>
          {notification.body}
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'absolute',
    top: 45,
    left: 14,
    right: 14,
    zIndex: 9999,
    alignItems: 'center',
  },
  container: {
    width: width - 28,
    backgroundColor: '#0a1720',
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: COLORS.primaryGlow,
    paddingHorizontal: 14,
    paddingVertical: 12,
    shadowColor: '#10b981',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.45,
    shadowRadius: 12,
    elevation: 10,
  },
  containerGoal: {
    borderColor: COLORS.primaryGlow,
    backgroundColor: '#07161b',
  },
  containerLineup: {
    borderColor: COLORS.secondary,
    backgroundColor: '#06131c',
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  badge: {
    backgroundColor: COLORS.primarySoft,
    borderWidth: 1,
    borderColor: COLORS.primaryGlow,
    borderRadius: 6,
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  badgeGoal: {
    backgroundColor: 'rgba(16,185,129,0.22)',
    borderColor: COLORS.primaryGlow,
  },
  badgeLineup: {
    backgroundColor: 'rgba(6,182,212,0.22)',
    borderColor: COLORS.secondary,
  },
  badgeText: {
    color: COLORS.primaryGlow,
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  timeText: {
    color: COLORS.textDim,
    fontSize: 10,
    fontWeight: '600',
    flex: 1,
    marginLeft: 8,
  },
  closeBtn: {
    paddingHorizontal: 4,
  },
  closeText: {
    color: COLORS.textMuted,
    fontSize: 13,
    fontWeight: '800',
  },
  title: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '900',
    letterSpacing: 0.3,
  },
  body: {
    color: COLORS.textSoft,
    fontSize: 12,
    marginTop: 3,
    lineHeight: 17,
  },
});

