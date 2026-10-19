import { BadRequestException, Body, Controller, Get, HttpCode, Param, Patch, Post, Query, Req, UseGuards } from '@nestjs/common';
import { AdminGuard } from '../common/admin.guard.js';
import { idParam, intParam } from '../common/params.js';
import { ReviewService, type Decision, type RulingPatch } from './review.service.js';

@Controller()
export class ReviewController {
  constructor(private readonly review: ReviewService) {}

  /** الطابورُ قراءةٌ، فلا يُشترَط له رمز. */
  @Get('review/queue')
  queue(@Query('source') source?: string, @Query('limit') limit?: string, @Query('after') after?: string) {
    let cursor: { seq: number; source: string } | undefined;
    if (after) {
      const [seq, src] = after.split(':');
      cursor = { seq: intParam(seq, 'after.seq', { min: 0 }), source: idParam(src, 'after.source') };
    }
    return this.review.queue(
      source ? idParam(source, 'source') : undefined,
      intParam(limit, 'limit', { min: 1, max: 100, fallback: 20 }),
      cursor,
    );
  }

  @Post('review/:seq/:source')
  @HttpCode(200)
  @UseGuards(AdminGuard)
  decide(
    @Param('seq') seq: string,
    @Param('source') source: string,
    @Body() body: { decision?: string; reason?: string } | undefined,
    @Req() req: { actor: string },
  ) {
    const decision = body?.decision;
    if (decision !== 'verify' && decision !== 'reject') {
      throw new BadRequestException('decision إمّا verify وإمّا reject.');
    }
    if (body?.reason !== undefined && typeof body.reason !== 'string') {
      throw new BadRequestException('reason نصّ.');
    }
    if (body?.reason && body.reason.length > 2000) throw new BadRequestException('السببُ أطولُ من اللازم.');
    return this.review.decide(
      intParam(seq, 'seq', { min: 1 }),
      idParam(source, 'source'),
      decision as Decision,
      body?.reason,
      req.actor,
    );
  }

  /** تعديلُ حكمٍ قائم: لفظُ المصدر والرمز والمصطلح والفئة والعلّة. */
  @Patch('rulings/:seq/:source')
  @UseGuards(AdminGuard)
  patchRuling(
    @Param('seq') seq: string,
    @Param('source') source: string,
    @Body() body: Record<string, unknown> | undefined,
    @Req() req: { actor: string },
  ) {
    return this.review.patchRuling(
      intParam(seq, 'seq', { min: 1 }),
      idParam(source, 'source'),
      parseRulingFields(body ?? {}, ['raw', 'symbol', 'term', 'category', 'approx', 'note', 'reason']),
      req.actor,
    );
  }

  /** إدخالُ حكمٍ جديدٍ على كلمة، من مصدرٍ ليس له فيها حكم. */
  @Post('rulings/:seq')
  @UseGuards(AdminGuard)
  createRuling(
    @Param('seq') seq: string,
    @Body() body: Record<string, unknown> | undefined,
    @Req() req: { actor: string },
  ) {
    const b = body ?? {};
    const fields = parseRulingFields(b, ['source', 'raw', 'symbol', 'term', 'category', 'approx', 'note', 'reason']);
    if (typeof b.source !== 'string') throw new BadRequestException('source مطلوب.');
    if (!fields.raw) throw new BadRequestException('لفظُ المصدر (raw) مطلوب.');
    return this.review.createRuling(
      intParam(seq, 'seq', { min: 1 }),
      idParam(b.source, 'source'),
      { ...fields, raw: fields.raw },
      req.actor,
    );
  }

  /** يتحقَّق من رمز المراجِع دون أن يكتب شيئاً. */
  @Post('auth/check')
  @HttpCode(200)
  @UseGuards(AdminGuard)
  check(@Req() req: { actor: string }) {
    return { ok: true, actor: req.actor };
  }
}

const MAX_TEXT = 20000;

/**
 * يقرأ حقولَ الحكم من الجسم ويُطبِّعها: النصُّ الفارغُ في غير raw يصير null،
 * وما لم يُذكَر يبقى غائباً فلا يُمسّ. وأيُّ حقلٍ خارجَ القائمة يُرفَض.
 */
function parseRulingFields(b: Record<string, unknown>, allowed: string[]): RulingPatch {
  for (const k of Object.keys(b)) {
    if (!allowed.includes(k)) throw new BadRequestException(`حقلٌ غيرُ معروف: ${k}.`);
  }
  const out: RulingPatch = {};
  for (const k of ['raw', 'symbol', 'term', 'category', 'note', 'reason'] as const) {
    const v = b[k];
    if (v === undefined) continue;
    if (v !== null && typeof v !== 'string') throw new BadRequestException(`${k} نصٌّ.`);
    const t = typeof v === 'string' ? v.trim() : null;
    if (t && t.length > MAX_TEXT) throw new BadRequestException(`${k} أطولُ من اللازم.`);
    if (k === 'raw') {
      if (!t) throw new BadRequestException('لفظُ المصدر (raw) لا يُفرَغ.');
      out.raw = t;
    } else if (k === 'reason') {
      out.reason = t ?? undefined;
    } else {
      out[k] = t || null;
    }
  }
  if (b.approx !== undefined) {
    if (typeof b.approx !== 'boolean') throw new BadRequestException('approx منطقيّ.');
    out.approx = b.approx;
  }
  return out;
}
