export function computeClientLiveClock(match, nowMs = Date.now()) {
  if (!match) return { type: 'NS', shortLabel: '', heroLabel: '' };

  if (!match.is_live) {
    if (match.status === 'FT') {
      return { type: 'FT', shortLabel: 'MS', heroLabel: 'MAÇ SONUCU (MS)' };
    }
    const nsTxt = match.status_display || 'Başlamadı';
    return { type: 'NS', shortLabel: nsTxt, heroLabel: nsTxt };
  }

  const clk = match.live_clock || {};
  const rawDisp = String(clk.display_clock || match.status_display || '').trim();

  // İlk Yarı Sonu / Devre Arası (Maçkolik: İY)
  if (
    match.status === 'HT' ||
    clk.phase === 'HT' ||
    rawDisp.toUpperCase() === 'İY' ||
    rawDisp.toUpperCase() === 'HT'
  ) {
    return {
      type: 'HT',
      shortLabel: 'İY',
      heroLabel: 'İY • DEVRE ARASI',
    };
  }

  const recvMs = match._clientReceivedMs || nowMs;
  const elapsedSinceRecv = Math.min(30, Math.max(0, Math.floor((nowMs - recvMs) / 1000)));
  const baseSec = Number(clk.clock_seconds || 0);
  const totalSec = Math.max(0, baseSec + elapsedSinceRecv);
  const pad2 = (n) => String(Math.max(0, Math.floor(n))).padStart(2, '0');

  // 1. Yarı
  if (match.status === '1H' || clk.period === 1) {
    if (clk.phase === '1H_STOPPAGE' || totalSec >= 2700 || rawDisp.includes('+')) {
      const stopLbl = rawDisp.includes('+') ? rawDisp : "45+1'";
      return {
        type: 'LIVE',
        shortLabel: stopLbl,
        heroLabel: `1. YARI UZATMA • ${stopLbl}`,
      };
    }
    const curMin = Math.max(1, Math.min(45, Math.floor(totalSec / 60) + 1));
    const mm = Math.floor(totalSec / 60);
    const ss = totalSec % 60;
    return {
      type: 'LIVE',
      shortLabel: `${curMin}'`,
      heroLabel: `1. YARI • ${curMin}' (${pad2(mm)}:${pad2(ss)})`,
    };
  }

  // 2. Yarı (veya uzatma)
  const sec2H = totalSec < 2700 ? totalSec + 2700 : totalSec;
  if (clk.phase === '2H_STOPPAGE' || sec2H >= 5400 || rawDisp.includes('+')) {
    const stopLbl = rawDisp.includes('+') ? rawDisp : "90+1'";
    return {
      type: 'LIVE',
      shortLabel: stopLbl,
      heroLabel: `2. YARI UZATMA • ${stopLbl}`,
    };
  }
  const curMin2 = Math.max(46, Math.min(90, Math.floor(sec2H / 60) + 1));
  const mm2 = Math.floor(sec2H / 60);
  const ss2 = sec2H % 60;
  return {
    type: 'LIVE',
    shortLabel: `${curMin2}'`,
    heroLabel: `2. YARI • ${curMin2}' (${pad2(mm2)}:${pad2(ss2)})`,
  };
}

