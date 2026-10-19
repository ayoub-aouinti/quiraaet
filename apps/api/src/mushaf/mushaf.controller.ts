import { BadRequestException, Controller, Get, Header, Param, Query } from '@nestjs/common';
import { idParam, intParam, optionalInt } from '../common/params.js';
import { normalizeArabic } from '../common/arabic.js';
import { MushafService } from './mushaf.service.js';

@Controller()
export class MushafController {
  constructor(private readonly mushaf: MushafService) {}

  @Get('suras/:sura/ayat')
  @Header('Cache-Control', 'no-cache')
  ayat(@Param('sura') sura: string, @Query('from') from?: string, @Query('to') to?: string) {
    return this.mushaf.ayat(
      intParam(sura, 'sura', { min: 1, max: 114 }),
      optionalInt(from, 'from', { min: 1, max: 286 }),
      optionalInt(to, 'to', { min: 1, max: 286 }),
    );
  }

  @Get('words/:seq')
  @Header('Cache-Control', 'no-cache')
  word(@Param('seq') seq: string) {
    return this.mushaf.word(intParam(seq, 'seq', { min: 1 }));
  }

  @Get('riwayat/:id/text')
  @Header('Cache-Control', 'public, max-age=3600')
  riwayaText(
    @Param('id') id: string,
    @Query('sura') sura?: string,
    @Query('from') from?: string,
    @Query('to') to?: string,
  ) {
    const s = intParam(sura, 'sura', { min: 1, max: 114 });
    const f = intParam(from, 'from', { min: 1, max: 286 });
    const t = intParam(to, 'to', { min: f, max: 286 });
    if (t - f > 60) throw new BadRequestException('النطاقُ أوسعُ من ستين آية.');
    return this.mushaf.riwayaText(idParam(id, 'riwaya'), s, f, t);
  }

  @Get('search')
  search(@Query('q') q?: string, @Query('limit') limit?: string) {
    const norm = normalizeArabic(q ?? '');
    if (norm.length < 2) throw new BadRequestException('اكتب حرفين على الأقلّ.');
    if (norm.length > 80) throw new BadRequestException('العبارةُ أطولُ من اللازم.');
    return this.mushaf.search(norm, intParam(limit, 'limit', { min: 1, max: 200, fallback: 50 }));
  }
}
