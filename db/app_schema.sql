-- جامع الوقوف — جداولُ التطبيق فوق المخطَّط الأصلي
--
-- إضافةٌ لا تمسّ db/schema.sql ولا تُسقِط شيئاً منه، فتُطبَّق مرّةً بعد
-- الهجرة، وتُعاد بلا ضرر (IF NOT EXISTS).
--
--   npm run db:app          (يقرأ DATABASE_URL من apps/api/.env)
--
-- سجلُّ المراجعة: كلُّ قرارٍ من مراجِعٍ يُقيَّد بقيمته قبلُ وبعدُ. فاعتمادُ حكمٍ
-- مقترَحٍ أو ردُّه أو ضبطُ مصطلحٍ لا يقع إلا ومعه أثرُه، ويمكن الرجوعُ عنه.
-- والردُّ لا يحذف الحكم: يُبقيه مقترَحاً ويُثبِت سببَه في rulings.review.

BEGIN;

CREATE TABLE IF NOT EXISTS review_log (
  id          bigserial    PRIMARY KEY,
  at          timestamptz  NOT NULL DEFAULT now(),
  actor       text         NOT NULL,
  entity      text         NOT NULL CHECK (entity IN ('ruling', 'term')),
  key         jsonb        NOT NULL,     -- {"seq":…,"source":…} أو {"source":…,"symbol":…}
  action      text         NOT NULL,     -- verify | reject | patch
  before      jsonb        NOT NULL,
  after       jsonb        NOT NULL,
  reason      text
);

CREATE INDEX IF NOT EXISTS review_log_key_idx ON review_log USING gin (key);
CREATE INDEX IF NOT EXISTS review_log_at_idx  ON review_log (at DESC);

COMMENT ON TABLE review_log IS
  'سجلُّ قرارات المراجعة. لا يُحذَف منه شيء؛ والرجوعُ عن قرارٍ قرارٌ جديدٌ يُقيَّد.';

COMMIT;
