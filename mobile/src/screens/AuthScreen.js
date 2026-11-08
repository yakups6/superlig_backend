import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import { superligApi } from '../services/api';
import { extractApiError } from '../utils/format';

export default function AuthScreen({ navigation }) {
  const {
    user,
    isLoggedIn,
    favorites,
    apiBaseUrl,
    signIn,
    signUp,
    signOut,
    updateUserLocal,
    changeServerUrl,
  } = useAuth();

  const [tab, setTab] = useState('LOGIN');
  const [busy, setBusy] = useState(false);

  // Login fields
  const [loginUser, setLoginUser] = useState('');
  const [loginPass, setLoginPass] = useState('');

  // Register fields
  const [regFirst, setRegFirst] = useState('');
  const [regLast, setRegLast] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPass, setRegPass] = useState('');
  const [regPass2, setRegPass2] = useState('');

  // Profile fields
  const [editFirst, setEditFirst] = useState(user?.first_name || '');
  const [editLast, setEditLast] = useState(user?.last_name || '');
  const [editEmail, setEditEmail] = useState(user?.email || '');

  // Password fields
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [newPw2, setNewPw2] = useState('');

  // Custom server URL
  const [serverUrlInput, setServerUrlInput] = useState(apiBaseUrl || '');

  useEffect(() => {
    setEditFirst(user?.first_name || '');
    setEditLast(user?.last_name || '');
    setEditEmail(user?.email || '');
  }, [user]);

  useEffect(() => {
    if (apiBaseUrl) setServerUrlInput(apiBaseUrl);
  }, [apiBaseUrl]);

  const handleLogin = async () => {
    if (!loginUser.trim() || !loginPass) {
      Alert.alert('Eksik Bilgi', 'Kullanıcı adı ve şifre giriniz.');
      return;
    }
    try {
      setBusy(true);
      const res = await signIn(loginUser.trim(), loginPass);
      setLoginPass('');
      Alert.alert(
        'Giriş Başarılı',
        `Hoş geldin, ${res?.user?.first_name || res?.user?.username}!`
      );
      navigation.goBack();
    } catch (e) {
      Alert.alert('Giriş Hatası', extractApiError(e, 'Kullanıcı adı veya şifre hatalı.'));
    } finally {
      setBusy(false);
    }
  };

  const handleRegister = async () => {
    if (!regUsername.trim() || !regEmail.trim() || !regPass) {
      Alert.alert('Eksik Bilgi', 'Kullanıcı adı, e-posta ve şifre zorunludur.');
      return;
    }
    if (regPass !== regPass2) {
      Alert.alert('Hata', 'Şifreler birbiriyle eşleşmiyor.');
      return;
    }
    try {
      setBusy(true);
      const res = await signUp({
        username: regUsername.trim(),
        email: regEmail.trim(),
        first_name: regFirst.trim(),
        last_name: regLast.trim(),
        password: regPass,
        password2: regPass2,
      });
      Alert.alert(
        'Kayıt Tamamlandı',
        `Hoş geldin @${res?.user?.username}! Oturumun otomatik açıldı.`
      );
      navigation.goBack();
    } catch (e) {
      Alert.alert('Kayıt Hatası', extractApiError(e, 'Kayıt tamamlanamadı.'));
    } finally {
      setBusy(false);
    }
  };

  const handleProfileSave = async () => {
    try {
      setBusy(true);
      const updated = await superligApi.updateProfile({
        first_name: editFirst.trim(),
        last_name: editLast.trim(),
        email: editEmail.trim(),
      });
      await updateUserLocal(updated);
      Alert.alert('Başarılı', 'Profil bilgileriniz güncellendi.');
    } catch (e) {
      Alert.alert('Hata', extractApiError(e, 'Profil güncellenemedi.'));
    } finally {
      setBusy(false);
    }
  };

  const handleChangePw = async () => {
    if (newPw !== newPw2) {
      Alert.alert('Hata', 'Yeni şifreler birbiriyle eşleşmiyor.');
      return;
    }
    try {
      setBusy(true);
      await superligApi.changePassword(oldPw, newPw);
      setOldPw('');
      setNewPw('');
      setNewPw2('');
      Alert.alert('Başarılı', 'Şifreniz güncellendi.');
    } catch (e) {
      Alert.alert('Hata', extractApiError(e, 'Şifre güncellenemedi.'));
    } finally {
      setBusy(false);
    }
  };

  const handleSaveServerUrl = async () => {
    const nextUrl = await changeServerUrl(serverUrlInput);
    setServerUrlInput(nextUrl);
    Alert.alert('Sunucu Adresi Güncellendi', `Aktif API: ${nextUrl}`);
  };

  const initials = (() => {
    if (!user) return 'ÜY';
    const f = (user.first_name || '').trim();
    const l = (user.last_name || '').trim();
    if (f && l) return (f[0] + l[0]).toUpperCase();
    return (user.username || 'ÜY').slice(0, 2).toUpperCase();
  })();

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {isLoggedIn ? 'HESABIM & PROFİL' : 'ÜYELİK & GİRİŞ'}
        </Text>
        <View style={{ width: 32 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {!isLoggedIn ? (
          <>
            <View style={styles.tabsRow}>
              <TouchableOpacity
                style={[styles.tabBtn, tab === 'LOGIN' && styles.tabBtnActive]}
                onPress={() => setTab('LOGIN')}
              >
                <Text style={[styles.tabBtnText, tab === 'LOGIN' && { color: '#060f14', fontWeight: '900' }]}>
                  🔑 Giriş Yap
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tabBtn, tab === 'REGISTER' && styles.tabBtnActive]}
                onPress={() => setTab('REGISTER')}
              >
                <Text style={[styles.tabBtnText, tab === 'REGISTER' && { color: '#060f14', fontWeight: '900' }]}>
                  ✨ Kayıt Ol
                </Text>
              </TouchableOpacity>
            </View>

            {tab === 'LOGIN' ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Hesabınıza Giriş Yapın</Text>
                <Text style={styles.cardSub}>
                  Kullanıcı adınız veya e-posta adresinizle JWT oturumu açın.
                </Text>

                <Text style={styles.label}>Kullanıcı Adı veya E-posta</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Örn: yakups6"
                  placeholderTextColor={COLORS.textDim}
                  autoCapitalize="none"
                  value={loginUser}
                  onChangeText={setLoginUser}
                />

                <Text style={styles.label}>Şifre</Text>
                <TextInput
                  style={styles.input}
                  placeholder="••••••••"
                  placeholderTextColor={COLORS.textDim}
                  secureTextEntry
                  value={loginPass}
                  onChangeText={setLoginPass}
                />

                <TouchableOpacity
                  style={styles.primaryBtn}
                  onPress={handleLogin}
                  disabled={busy}
                >
                  {busy ? (
                    <ActivityIndicator color={COLORS.white} />
                  ) : (
                    <Text style={styles.primaryBtnText}>🔑 Giriş Yap</Text>
                  )}
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Yeni Hesap Oluştur</Text>
                <Text style={styles.cardSub}>
                  Favori oyuncularınız hesabınızla otomatik senkronize edilir.
                </Text>

                <View style={styles.row2}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.label}>Ad</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Adınız"
                      placeholderTextColor={COLORS.textDim}
                      value={regFirst}
                      onChangeText={setRegFirst}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.label}>Soyad</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Soyadınız"
                      placeholderTextColor={COLORS.textDim}
                      value={regLast}
                      onChangeText={setRegLast}
                    />
                  </View>
                </View>

                <Text style={styles.label}>Kullanıcı Adı *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Örn: arda_scout"
                  placeholderTextColor={COLORS.textDim}
                  autoCapitalize="none"
                  value={regUsername}
                  onChangeText={setRegUsername}
                />

                <Text style={styles.label}>E-posta *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="ornek@eposta.com"
                  placeholderTextColor={COLORS.textDim}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  value={regEmail}
                  onChangeText={setRegEmail}
                />

                <Text style={styles.label}>Şifre * (En az 8 karakter)</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Şifreniz"
                  placeholderTextColor={COLORS.textDim}
                  secureTextEntry
                  value={regPass}
                  onChangeText={setRegPass}
                />

                <Text style={styles.label}>Şifre Tekrar *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Şifreyi doğrulayın"
                  placeholderTextColor={COLORS.textDim}
                  secureTextEntry
                  value={regPass2}
                  onChangeText={setRegPass2}
                />

                <TouchableOpacity
                  style={styles.primaryBtn}
                  onPress={handleRegister}
                  disabled={busy}
                >
                  {busy ? (
                    <ActivityIndicator color={COLORS.white} />
                  ) : (
                    <Text style={styles.primaryBtnText}>✨ Kayıt Ol ve Giriş Yap</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}
          </>
        ) : (
          <>
            <View style={styles.profileHero}>
              <View style={styles.heroTopRow}>
                <View style={styles.avatarCircle}>
                  <Text style={styles.avatarText}>{initials}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.profName}>
                    {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.username}
                  </Text>
                  <Text style={styles.profUser}>@{user.username} • JWT Aktif</Text>
                  <Text style={styles.profEmail}>{user.email || 'E-posta belirtilmedi'}</Text>
                </View>
              </View>

              <View style={styles.row2}>
                <TouchableOpacity
                  style={styles.secondaryBtn}
                  onPress={() => navigation.navigate('MainTabs', { screen: 'ScoutTab' })}
                >
                  <Text style={styles.secondaryBtnText}>
                    ❤️ Favorilerim ({favorites.length})
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.logoutBtn}
                  onPress={() => {
                    signOut();
                    Alert.alert('Çıkış Yapıldı', 'Oturumunuz güvenli şekilde kapatıldı.');
                  }}
                >
                  <Text style={styles.logoutBtnText}>🚪 Çıkış Yap</Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.card}>
              <Text style={styles.cardTitle}>📝 Profil Bilgilerini Güncelle</Text>
              <View style={styles.row2}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Ad</Text>
                  <TextInput
                    style={styles.input}
                    value={editFirst}
                    onChangeText={setEditFirst}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Soyad</Text>
                  <TextInput
                    style={styles.input}
                    value={editLast}
                    onChangeText={setEditLast}
                  />
                </View>
              </View>
              <Text style={styles.label}>E-posta</Text>
              <TextInput
                style={styles.input}
                autoCapitalize="none"
                value={editEmail}
                onChangeText={setEditEmail}
              />
              <TouchableOpacity style={styles.secondaryBtn} onPress={handleProfileSave}>
                <Text style={styles.secondaryBtnText}>💾 Değişiklikleri Kaydet</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.card}>
              <Text style={styles.cardTitle}>🔒 Şifre Değiştir</Text>
              <Text style={styles.label}>Mevcut Şifre</Text>
              <TextInput
                style={styles.input}
                secureTextEntry
                value={oldPw}
                onChangeText={setOldPw}
              />
              <Text style={styles.label}>Yeni Şifre</Text>
              <TextInput
                style={styles.input}
                secureTextEntry
                value={newPw}
                onChangeText={setNewPw}
              />
              <Text style={styles.label}>Yeni Şifre Tekrar</Text>
              <TextInput
                style={styles.input}
                secureTextEntry
                value={newPw2}
                onChangeText={setNewPw2}
              />
              <TouchableOpacity style={styles.primaryBtn} onPress={handleChangePw}>
                <Text style={styles.primaryBtnText}>🔒 Şifreyi Güncelle</Text>
              </TouchableOpacity>
            </View>
          </>
        )}

        {/* BACKEND CONNECTION CONFIG (HELPFUL FOR WI-FI / DEPLOY TESTING) */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📡 Backend API Bağlantısı</Text>
          <Text style={styles.cardSub}>
            Otomatik algılanan sunucu adresi. Farklı ağda veya bulut sunucuda test ediyorsanız değiştirebilirsiniz (sıfırlamak için boş bırakıp kaydedin).
          </Text>
          <TextInput
            style={styles.input}
            placeholder="http://192.168.1.97:8000/api"
            placeholderTextColor={COLORS.textDim}
            autoCapitalize="none"
            value={serverUrlInput}
            onChangeText={setServerUrlInput}
          />
          <TouchableOpacity style={styles.secondaryBtn} onPress={handleSaveServerUrl}>
            <Text style={styles.secondaryBtnText}>🔗 Sunucu Adresini Uygula</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 10,
  },
  backBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backText: { color: COLORS.white, fontSize: 16, fontWeight: '700' },
  headerTitle: { color: COLORS.white, fontSize: 14, fontWeight: '800' },
  scrollContent: { padding: 14, paddingBottom: 40 },
  tabsRow: {
    flexDirection: 'row',
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 12,
    padding: 4,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    marginBottom: 12,
    gap: 6,
  },
  tabBtn: { flex: 1, paddingVertical: 10, borderRadius: 9, alignItems: 'center' },
  tabBtnActive: { backgroundColor: COLORS.primary },
  tabBtnText: { color: COLORS.textMuted, fontSize: 12, fontWeight: '800' },
  card: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    padding: 16,
    marginBottom: 12,
  },
  cardTitle: { color: COLORS.white, fontSize: 15, fontWeight: '800', marginBottom: 4 },
  cardSub: { color: COLORS.textMuted, fontSize: 11, marginBottom: 12, lineHeight: 16 },
  label: { color: COLORS.textSoft, fontSize: 11, fontWeight: '700', marginBottom: 4 },
  input: {
    backgroundColor: '#060f14',
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: COLORS.white,
    fontSize: 13,
    marginBottom: 12,
  },
  row2: { flexDirection: 'row', gap: 10 },
  primaryBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  primaryBtnText: { color: '#060f14', fontSize: 13, fontWeight: '900' },
  secondaryBtn: {
    flex: 1,
    backgroundColor: 'rgba(6,182,212,0.16)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.38)',
    borderRadius: 10,
    paddingVertical: 11,
    alignItems: 'center',
  },
  secondaryBtnText: { color: COLORS.secondary, fontSize: 12, fontWeight: '800' },
  logoutBtn: {
    flex: 1,
    backgroundColor: COLORS.accentRedSoft,
    borderWidth: 1,
    borderColor: COLORS.accentRedBorder,
    borderRadius: 10,
    paddingVertical: 11,
    alignItems: 'center',
  },
  logoutBtnText: { color: '#f87171', fontSize: 12, fontWeight: '800' },
  profileHero: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    padding: 16,
    marginBottom: 12,
  },
  heroTopRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 14 },
  avatarCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(16,185,129,0.15)',
    borderWidth: 2,
    borderColor: COLORS.avatarRingEmerald,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: COLORS.primaryGlow, fontSize: 18, fontWeight: '900' },
  profName: { color: COLORS.white, fontSize: 15, fontWeight: '800' },
  profUser: { color: COLORS.primaryGlow, fontSize: 11, fontWeight: '700', marginTop: 2 },
  profEmail: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
});
