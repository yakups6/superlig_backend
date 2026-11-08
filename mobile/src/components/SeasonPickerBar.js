import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  FlatList,
} from 'react-native';
import { COLORS } from '../theme/colors';

const DEFAULT_QUICK_SEASONS = [
  '2026/2027',
  '2025/2026',
  '2024/2025',
  '2023/2024',
  '2020/2021',
  '2015/2016',
  '2010/2011',
  '1999/2000',
  '1988/1989',
  '1959',
];

function shortCodeFromName(name) {
  if (!name) return '26/27';
  if (name === 'ALL') return 'TÜMÜ';
  if (String(name).includes('/')) {
    const parts = String(name).split('/');
    return `${parts[0].slice(-2)}/${parts[1].slice(-2)}`;
  }
  return String(name);
}

export default function SeasonPickerBar({
  seasons = [],
  selectedSeasonName = '2026/2027',
  onSelectSeason,
  subtitle,
  includeAllOption = false,
  allOptionLabel = 'Tüm Sezonlar',
}) {
  const [modalOpen, setModalOpen] = useState(false);

  const isAll = selectedSeasonName === 'ALL';
  const matched = seasons.find(
    (s) => s.name === selectedSeasonName || String(s.id) === String(selectedSeasonName)
  );

  const pillCode = isAll ? 'TÜMÜ' : matched?.short_code || shortCodeFromName(selectedSeasonName);
  const titleText = isAll
    ? allOptionLabel
    : `${matched?.name || selectedSeasonName} Sezonu`;
  const subText =
    subtitle ||
    (isAll
      ? 'Tüm Zamanlar & Sezon Geçmişi'
      : matched?.is_current || selectedSeasonName === '2026/2027'
      ? 'Aktif Sezon (Güncel)'
      : `${matched?.name || selectedSeasonName} Dönemi`);

  const quickChips = includeAllOption
    ? ['ALL', ...DEFAULT_QUICK_SEASONS]
    : DEFAULT_QUICK_SEASONS;

  const modalItems = includeAllOption
    ? [{ id: 'ALL', name: 'ALL', label: allOptionLabel, short_code: 'TÜMÜ' }, ...seasons]
    : seasons;

  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        <View style={styles.leftInfo}>
          <View style={styles.pillBadge}>
            <Text style={styles.pillText}>{pillCode}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.titleText} numberOfLines={1}>
              {titleText}
            </Text>
            <Text style={styles.subText} numberOfLines={1}>
              {subText}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.dropdownBtn}
          activeOpacity={0.75}
          onPress={() => setModalOpen(true)}
        >
          <Text style={styles.dropdownBtnText}>
            {isAll ? 'Tümü' : matched?.name || selectedSeasonName} ▾
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chipsScroll}
      >
        {quickChips.map((sName) => {
          const active = selectedSeasonName === sName;
          const label = sName === 'ALL' ? '🌟 Tümü' : shortCodeFromName(sName);
          return (
            <TouchableOpacity
              key={sName}
              style={[styles.chip, active && styles.chipActive]}
              onPress={() => onSelectSeason && onSelectSeason(sName)}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>
                {label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      <Modal
        visible={modalOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setModalOpen(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setModalOpen(false)}
        >
          <View style={styles.modalCard} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHead}>
              <Text style={styles.modalTitle}>Sezon Seç ({seasons.length || 68} Sezon)</Text>
              <TouchableOpacity onPress={() => setModalOpen(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={modalItems}
              keyExtractor={(item, idx) => String(item.id || item.name || idx)}
              style={{ maxHeight: 380 }}
              renderItem={({ item }) => {
                const val = item.name;
                const active = selectedSeasonName === val;
                return (
                  <TouchableOpacity
                    style={[styles.modalRow, active && styles.modalRowActive]}
                    onPress={() => {
                      setModalOpen(false);
                      onSelectSeason && onSelectSeason(val);
                    }}
                  >
                    <View style={styles.modalCodePill}>
                      <Text style={styles.modalCodeText}>
                        {item.short_code || shortCodeFromName(val)}
                      </Text>
                    </View>
                    <Text style={[styles.modalRowText, active && { color: COLORS.white, fontWeight: '800' }]}>
                      {item.label || `${item.name} Sezonu`}
                    </Text>
                    {(item.is_current || val === '2026/2027') && (
                      <View style={styles.currentBadge}>
                        <Text style={styles.currentBadgeText}>AKTİF</Text>
                      </View>
                    )}
                  </TouchableOpacity>
                );
              }}
            />
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    padding: 10,
    marginBottom: 12,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    marginBottom: 8,
  },
  leftInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 8,
  },
  pillBadge: {
    backgroundColor: COLORS.primarySoft,
    borderWidth: 1,
    borderColor: COLORS.primaryBorder,
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
  },
  pillText: {
    color: COLORS.primaryGlow,
    fontSize: 11,
    fontWeight: '900',
  },
  titleText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '800',
  },
  subText: {
    color: COLORS.textMuted,
    fontSize: 10,
    marginTop: 1,
  },
  dropdownBtn: {
    backgroundColor: '#0a2230',
    borderWidth: 1,
    borderColor: COLORS.cardBorderCyan,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  dropdownBtnText: {
    color: COLORS.white,
    fontSize: 11,
    fontWeight: '800',
  },
  chipsScroll: {
    gap: 6,
    paddingTop: 2,
  },
  chip: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  chipActive: {
    backgroundColor: COLORS.primarySoft,
    borderColor: COLORS.primaryGlow,
  },
  chipText: {
    color: COLORS.textMuted,
    fontSize: 10,
    fontWeight: '700',
  },
  chipTextActive: {
    color: COLORS.primaryGlow,
    fontWeight: '800',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.78)',
    justifyContent: 'center',
    padding: 20,
  },
  modalCard: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    padding: 14,
  },
  modalHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.cardBorder,
  },
  modalTitle: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '800',
  },
  modalClose: {
    color: COLORS.textMuted,
    fontSize: 16,
    fontWeight: '800',
    paddingHorizontal: 6,
  },
  modalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 10,
    gap: 10,
  },
  modalRowActive: {
    backgroundColor: COLORS.primarySoft,
  },
  modalCodePill: {
    backgroundColor: 'rgba(255,255,255,0.07)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    minWidth: 50,
    alignItems: 'center',
  },
  modalCodeText: {
    color: COLORS.accentBlue,
    fontSize: 11,
    fontWeight: '800',
  },
  modalRowText: {
    color: COLORS.textSoft,
    fontSize: 13,
    flex: 1,
  },
  currentBadge: {
    backgroundColor: COLORS.accentGreenSoft,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  currentBadgeText: {
    color: COLORS.accentGreen,
    fontSize: 9,
    fontWeight: '800',
  },
});

