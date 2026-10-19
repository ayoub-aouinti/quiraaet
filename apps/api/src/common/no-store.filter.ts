import { ArgumentsHost, Catch } from '@nestjs/common';
import { BaseExceptionFilter } from '@nestjs/core';
import type { Response } from 'express';

/**
 * الأخطاءُ لا تُخزَّن. طرقُ القراءة تحمل Cache-Control: public لتُخزَّن
 * أجوبتُها، وNest يضع هذا الترويسةَ قبل تنفيذ الطريق، فيرثها الخطأُ أيضاً.
 * فإن تعطّلت القاعدةُ ساعةً حفظ المتصفّحُ الخطأَ ساعةً وأعاده ولو عادت.
 */
@Catch()
export class NoStoreOnErrorFilter extends BaseExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const res = host.switchToHttp().getResponse<Response>();
    if (!res.headersSent) res.setHeader('Cache-Control', 'no-store');
    super.catch(exception, host);
  }
}
