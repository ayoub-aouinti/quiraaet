import { BadRequestException, Body, Controller, Get, Param, Patch, Query, Req, UseGuards } from '@nestjs/common';
import { AdminGuard } from '../common/admin.guard.js';
import { idParam } from '../common/params.js';
import { TermsService, type TermPatch } from './terms.service.js';

@Controller('terms')
export class TermsController {
  constructor(private readonly terms: TermsService) {}

  @Get()
  list(@Query('source') source?: string) {
    return this.terms.list(source ? idParam(source, 'source') : undefined);
  }

  @Patch(':source/:symbol')
  @UseGuards(AdminGuard)
  patch(
    @Param('source') source: string,
    @Param('symbol') symbol: string,
    @Body() body: Record<string, unknown> | undefined,
    @Req() req: { actor: string },
  ) {
    const patch: TermPatch = {};
    const b = body ?? {};
    for (const k of Object.keys(b)) {
      if (!['reviewed', 'approx', 'category'].includes(k)) throw new BadRequestException(`حقلٌ غيرُ معروف: ${k}.`);
    }
    if (b.reviewed !== undefined) {
      if (typeof b.reviewed !== 'boolean') throw new BadRequestException('reviewed منطقيّ.');
      patch.reviewed = b.reviewed;
    }
    if (b.approx !== undefined) {
      if (typeof b.approx !== 'boolean') throw new BadRequestException('approx منطقيّ.');
      patch.approx = b.approx;
    }
    if (b.category !== undefined) {
      if (b.category !== null && typeof b.category !== 'string') throw new BadRequestException('category نصٌّ أو null.');
      patch.category = b.category as string | null;
    }
    if (!symbol || symbol.length > 40) throw new BadRequestException('الرمزُ غيرُ صالح.');
    return this.terms.patch(idParam(source, 'source'), symbol, patch, req.actor);
  }
}
