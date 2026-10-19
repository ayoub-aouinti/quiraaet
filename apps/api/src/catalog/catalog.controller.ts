import { Controller, Get, Header } from '@nestjs/common';
import { CatalogService } from './catalog.service.js';

@Controller()
export class CatalogController {
  constructor(private readonly catalog: CatalogService) {}

  @Get('categories')
  @Header('Cache-Control', 'public, max-age=3600')
  categories() {
    return this.catalog.categories();
  }

  @Get('sources')
  @Header('Cache-Control', 'no-cache')
  sources() {
    return this.catalog.sources();
  }

  @Get('suras')
  @Header('Cache-Control', 'public, max-age=86400')
  suras() {
    return this.catalog.suras();
  }

  @Get('riwayat')
  @Header('Cache-Control', 'public, max-age=3600')
  riwayat() {
    return this.catalog.riwayat();
  }

  @Get('stats')
  @Header('Cache-Control', 'no-cache')
  stats() {
    return this.catalog.stats();
  }

  @Get('health')
  health() {
    return { ok: true };
  }
}
