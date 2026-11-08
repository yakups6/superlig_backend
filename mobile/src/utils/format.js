export const DEFAULT_PLAYER_IMG =
  'https://img.a.transfermarkt.technology/portrait/header/default.jpg';

export const DEFAULT_TEAM_LOGO =
  'https://tmssl.akamaized.net/images/wappen/head/default.png';

export function formatMarketValue(val, isLegend = false, isHistorical = false) {
  const num = Number(val) || 0;
  if (num >= 1000000) {
    const inM = num / 1000000;
    return inM % 1 === 0 ? `${inM}M €` : `${inM.toFixed(1)}M €`;
  }
  if (num >= 1000) {
    return `${Math.round(num / 1000)}B €`;
  }
  if (isLegend) return 'Efsane';
  if (isHistorical) return 'Dönem Yıldızı';
  return '-';
}

export function cleanPlayerDisplayName(name = '') {
  return String(name)
    .replace(/\s*\(Devre Aras[ıi]\s+(Geldi|Gitti)\)/gi, '')
    .trim();
}

export function extractApiError(err, fallback = 'İşlem sırasında bir hata oluştu.') {
  const data = err?.response?.data;
  if (!data) {
    if (err?.message?.includes('Network Error') || err?.code === 'ECONNABORTED') {
      return 'Sunucuya bağlanılamadı. Telefonunuzun bilgisayar ile aynı Wi-Fi ağında olduğundan ve Django sunucusunun çalıştığından emin olun.';
    }
    return fallback;
  }
  if (typeof data === 'string') return data;
  const details = data.details || data;
  if (details && typeof details === 'object') {
    if (typeof details.error === 'string') return details.error;
    if (typeof details.detail === 'string') return details.detail;
    const labels = {
      username: 'Kullanıcı Adı',
      email: 'E-posta',
      password: 'Şifre',
      password2: 'Şifre Tekrar',
      old_password: 'Mevcut Şifre',
      new_password: 'Yeni Şifre',
    };
    const parts = [];
    for (const [k, v] of Object.entries(details)) {
      if (['success', 'status_code'].includes(k)) continue;
      const lbl = labels[k] || k;
      const txt = Array.isArray(v) ? v.join(' ') : String(v);
      parts.push(`${lbl}: ${txt}`);
    }
    if (parts.length > 0) return parts.join('\n');
  }
  return data.error || fallback;
}

