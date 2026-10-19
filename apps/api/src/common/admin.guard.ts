import { CanActivate, ExecutionContext, ForbiddenException, Injectable, UnauthorizedException } from '@nestjs/common';
import { createHash, timingSafeEqual } from 'node:crypto';
import type { Request } from 'express';

/**
 * حارسُ طلبات الكتابة. المراجِعون يحملون رموزاً في ADMIN_TOKENS بصيغة
 * «اسم:رمز» مفصولةً بفواصل، فيُقيَّد اسمُ صاحب كلِّ قرارٍ في review_log.
 * فإن لم يُعرَّف رمزٌ أُغلقت الكتابةُ كلُّها، ولا تُفتَح بلا رمز.
 */
@Injectable()
export class AdminGuard implements CanActivate {
  private readonly tokens: { actor: string; digest: Buffer }[];

  constructor() {
    this.tokens = (process.env.ADMIN_TOKENS ?? '')
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
      .map((pair) => {
        const i = pair.indexOf(':');
        const actor = i > 0 ? pair.slice(0, i) : 'admin';
        const token = i > 0 ? pair.slice(i + 1) : pair;
        return { actor, digest: digest(token) };
      });
  }

  canActivate(ctx: ExecutionContext): boolean {
    const req = ctx.switchToHttp().getRequest<Request & { actor?: string }>();
    if (!this.tokens.length) {
      throw new ForbiddenException('الكتابةُ مغلقة: لم يُعرَّف ADMIN_TOKENS على الخادم.');
    }
    const header = req.headers.authorization ?? '';
    const m = /^Bearer\s+(.+)$/i.exec(header);
    if (!m) throw new UnauthorizedException('رمزُ المراجِع مطلوب.');
    const d = digest(m[1].trim());
    const hit = this.tokens.find((t) => timingSafeEqual(t.digest, d));
    if (!hit) throw new UnauthorizedException('رمزُ المراجِع غيرُ صحيح.');
    req.actor = hit.actor;
    return true;
  }
}

function digest(s: string): Buffer {
  return createHash('sha256').update(s, 'utf8').digest();
}
