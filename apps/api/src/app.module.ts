import { Module } from '@nestjs/common';
import { CatalogController } from './catalog/catalog.controller.js';
import { CatalogService } from './catalog/catalog.service.js';
import { AdminGuard } from './common/admin.guard.js';
import { DatabaseService } from './db/database.service.js';
import { MushafController } from './mushaf/mushaf.controller.js';
import { MushafService } from './mushaf/mushaf.service.js';
import { ReviewController } from './review/review.controller.js';
import { ReviewLogService } from './review/review-log.service.js';
import { ReviewService } from './review/review.service.js';
import { TermsController } from './terms/terms.controller.js';
import { TermsService } from './terms/terms.service.js';

@Module({
  controllers: [CatalogController, MushafController, ReviewController, TermsController],
  providers: [DatabaseService, ReviewLogService, CatalogService, MushafService, ReviewService, TermsService, AdminGuard],
})
export class AppModule {}
