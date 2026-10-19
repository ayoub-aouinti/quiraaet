import { BadRequestException } from '@nestjs/common';

/** يقرأ عدداً صحيحاً من معامِل الطلب ويتحقَّق من حدَّيه. */
export function intParam(
  value: string | undefined,
  name: string,
  opts: { min?: number; max?: number; fallback?: number } = {},
): number {
  if (value === undefined || value === '') {
    if (opts.fallback !== undefined) return opts.fallback;
    throw new BadRequestException(`${name} مطلوب.`);
  }
  if (!/^-?\d+$/.test(value)) throw new BadRequestException(`${name} يجب أن يكون عدداً صحيحاً.`);
  const n = Number(value);
  if (opts.min !== undefined && n < opts.min) throw new BadRequestException(`${name} أقلُّ من ${opts.min}.`);
  if (opts.max !== undefined && n > opts.max) throw new BadRequestException(`${name} أكثرُ من ${opts.max}.`);
  return n;
}

export function optionalInt(value: string | undefined, name: string, opts: { min?: number; max?: number } = {}) {
  return value === undefined || value === '' ? undefined : intParam(value, name, opts);
}

/** معرِّفٌ نصّيٌّ قصيرٌ آمن: معرّفُ مصدرٍ أو رواية. */
export function idParam(value: string | undefined, name: string): string {
  if (!value || !/^[a-z_][a-z0-9_]{0,40}$/.test(value)) {
    throw new BadRequestException(`${name} غيرُ صالح.`);
  }
  return value;
}
