// رموزُ التصميم، منقولةٌ من gen/tokens.py — مصدرُها واحدٌ فلا تتفرّق.
// ألوانٌ مستمدّةٌ من تقليد الزخرفة المغربية: اللازورد والمُغرة والقرمز.

export const color = {
  ink: '#1C1815',
  leaf: '#E9E6DC',
  paper: '#F6F4EE',
  rule: '#CFC9BA',
  lapis: '#1E3A5F',
  lapisLight: '#2E5584',
  ochre: '#A8762C',
  carmine: '#8C2F39',
  sage: '#5A6B5D',
  muted: '#8A857B',
  faint: '#A49E92',
  highlight: '#F2E8D2',
  highlightOn: '#EADFC2',
} as const;

export const fonts = {
  display: "'Reem Kufi', sans-serif",
  body: "'Readex Pro', sans-serif",
  quran: "'Amiri Quran', serif",
} as const;

/** لونُ كلِّ مصدرٍ واسمُه القصير. واسمُه الكامل وبياناتُه تأتي من القاعدة. */
export const sourceStyle: Record<string, { short: string; color: string }> = {
  ashmuni: { short: 'الأشموني', color: '#6B5436' },
  akhshid: { short: 'ابن الإخشيذ', color: '#2E5E7A' },
  hubti: { short: 'الوقف الهبطي', color: '#2F6B5E' },
  ansari: { short: 'الأنصاري', color: '#5A4A7A' },
  amani: { short: 'العُماني', color: '#9A5B2E' },
  saj: { short: 'السجاوندي', color: '#8C2F39' },
  nahhas: { short: 'النحاس', color: '#7A3E8C' },
  dani: { short: 'الداني', color: '#1E3A5F' },
  ghazzal: { short: 'ابن الغزّال', color: '#3C6E8F' },
  anbari: { short: 'ابن الأنباري', color: '#B05A28' },
  ibn_sadan: { short: 'ابن سعدان', color: '#4A6B33' },
};

export const riwayaColor: Record<string, string> = {
  hafs: '#1E3A5F',
  warsh: '#2F6B5E',
  qalun: '#A8762C',
  duri: '#8C2F39',
};

export function sourceColor(id: string): string {
  return sourceStyle[id]?.color ?? color.sage;
}

export function sourceShort(id: string, fallback?: string): string {
  return sourceStyle[id]?.short ?? fallback ?? id;
}
