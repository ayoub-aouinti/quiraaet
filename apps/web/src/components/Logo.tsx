import { color } from '@jamei/shared';

/** علامةُ جامع الوقوف: فجوةٌ في السطر، وفوقها ∴ المعانقة بثلاثة ألوان. */
export function LogoMark({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <circle cx="16" cy="8.5" r="2.55" fill={color.lapis} />
      <circle cx="10.6" cy="15.2" r="2.55" fill={color.ochre} />
      <circle cx="21.4" cy="15.2" r="2.55" fill={color.carmine} />
      <path d="M4 22 H12.5" stroke={color.ink} strokeWidth="1.9" strokeLinecap="round" />
      <path d="M19.5 22 H28" stroke={color.ink} strokeWidth="1.9" strokeLinecap="round" />
    </svg>
  );
}
