import { Platform, Vibration } from 'react-native';
import Constants from 'expo-constants';
import { superligApi } from './api';

let Notifications = null;
try {
  Notifications = require('expo-notifications');
} catch (e) {
  console.log('[Notifications] expo-notifications yüklenemedi:', e?.message);
}

// Uygulama açıkken veya arka plandayken bildirimlerin nasıl davranacağını belirle
if (Notifications && Notifications.setNotificationHandler) {
  try {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowBanner: true,
        shouldShowList: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
  } catch (e) {
    console.log('[Notifications] setNotificationHandler error:', e);
  }
}

/**
 * Cihazın Expo Push Token'ını alır ve Django backend'e kaydeder.
 */
export async function registerForPushNotificationsAsync() {
  if (!Notifications) return null;
  let token = null;

  try {
    if (Platform.OS === 'android' && Notifications.setNotificationChannelAsync) {
      try {
        await Notifications.setNotificationChannelAsync('superlig-match-alerts', {
          name: 'Süper Lig Canlı Maç & Gol Bildirimleri',
          importance: Notifications.AndroidImportance ? Notifications.AndroidImportance.MAX : 5,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#10b981',
          sound: 'default',
          enableVibrate: true,
        });
      } catch (_) {}
    }

    if (Notifications.getPermissionsAsync) {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted' && Notifications.requestPermissionsAsync) {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        console.log('[Notifications] Bildirim izni verilmedi.');
        return null;
      }
    }

    const projectId =
      Constants?.expoConfig?.extra?.eas?.projectId ??
      Constants?.easConfig?.projectId ??
      undefined;

    if (Notifications.getExpoPushTokenAsync) {
      const tokenData = await Notifications.getExpoPushTokenAsync(
        projectId ? { projectId } : undefined
      );
      token = tokenData?.data;

      if (token) {
        console.log('[Notifications] Push Token alındı:', token);
        await superligApi.registerDeviceToken(
          token,
          Platform.OS,
          `${Platform.OS.toUpperCase()} Cihazı`
        );
      }
    }
  } catch (error) {
    console.log('[Notifications] Token alma veya kayıt hatası:', error?.message);
  }

  return token;
}

/**
 * Anında yerel sistem bildirimi fırlatır (Expo Go veya bağımsız modda doğrudan çalışır)
 */
export async function showLocalMatchNotification(title, body, data = {}) {
  try {
    // Titreşim efekti (Gol için çift vuruş)
    try {
      Vibration.vibrate([0, 180, 80, 240]);
    } catch (_) {}

    if (Notifications && Notifications.scheduleNotificationAsync) {
      await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data,
          sound: true,
          priority: Notifications.AndroidNotificationPriority ? Notifications.AndroidNotificationPriority.MAX : undefined,
        },
        trigger: null, // Anında fırlat
      });
    }
  } catch (err) {
    console.log('[Notifications] Local bildirim hatası:', err?.message);
  }
}
