-- جامع الوقوف — مخطَّط Postgres
--
-- مبنيٌّ على قانون المشروع في CLAUDE.md، وأهمُّه ههنا ثلاثة:
--   • مصطلحُ المصدر (raw) لا يُستبدَل، والفئةُ العامّة (category) للّون فقط.
--   • ما لم يُفهَم يُحفَظ ويُعلَّم، ولا يُخمَّن ولا يُحذَف — ولذلك category
--     و term و symbol تقبل NULL، وفي القاعدة ثلاثةُ مواضعَ كذلك بالفعل،
--     عليها review = 'قيمة غير مفهومة، تحتاج مراجعة الأصل'.
--   • confidence نصٌّ حرٌّ لا قائمةٌ مغلقة: فيه «عالية» و«متوسطة» و«تحتاج
--     مراجعة»، وفيه أيضاً «يقين — علامة مضمَّنة في المصحف» لعلامات المصاحف.
--     فمن قيَّده بقائمةٍ أسقط ٩٩٨٠ موضعاً من الهبطي.

BEGIN;

DROP TABLE IF EXISTS riwaya_words, riwayat, rulings, terms, words, sources, categories CASCADE;

-- الفئاتُ العامّة: للعرض واللون، لا للمقارنة بين الكتب
CREATE TABLE categories (
  id        text PRIMARY KEY,
  label     text        NOT NULL,
  symbol    text        NOT NULL,
  color     text        NOT NULL,
  ord       smallint    NOT NULL
);

COMMENT ON TABLE categories IS
  'فئاتٌ عامّةٌ للّون في الواجهة. لا يُحسَب منها اتفاقٌ ولا اختلاف: «صالح» عند العماني و«جائز» عند السجاوندي كلاهما jaiz وليسا قولاً واحداً.';

CREATE TABLE sources (
  id                  text PRIMARY KEY,
  name                text        NOT NULL,
  author              text,
  died                text,
  kind                text        NOT NULL DEFAULT 'book'
                        CHECK (kind IN ('book', 'mushaf')),
  edition             text,
  has_text            boolean     NOT NULL DEFAULT false,
  verified            boolean     NOT NULL DEFAULT false,
  -- حدودُ النسخة المعتمدة: ما وقع خارجها خطأُ مطابقةٍ لا حكمٌ للمؤلف
  sura_lo             smallint,
  sura_hi             smallint,
  owner_unattributed  boolean     NOT NULL DEFAULT false,
  owner               text[]      NOT NULL DEFAULT '{}',
  -- تنبيهاتُ books.json بمفاتيحها: الحدود، النواقص، التبعيّة بين الكتب
  caveats             jsonb       NOT NULL DEFAULT '{}'
);

COMMENT ON COLUMN sources.caveats IS
  'تنبيهاتُ المصدر كما في books.json: _حدود و_نقصٌ في المصدر و_تنبيه. وهي شرطُ الأمانة في العرض، فلا تُطرَح عند النقل.';
COMMENT ON COLUMN sources.owner_unattributed IS
  'صحيحٌ في الكتب التي يَسوق فيها المؤلفُ حكمَه مجرَّداً ثم يَعزو ما خالفه. فالمجرَّدُ من العزو قولُه هو.';

-- كلماتُ المصحف برواية حفص — الفهرسُ المرجعيُّ والمدقِّق
CREATE TABLE words (
  seq        integer  PRIMARY KEY,
  sura       smallint NOT NULL CHECK (sura BETWEEN 1 AND 114),
  sura_name  text     NOT NULL,
  ayah       smallint NOT NULL CHECK (ayah > 0),
  wpos       smallint,            -- NULL في الكلمات المفصولة رسماً (مَا لِ هَٰذَا)
  text       text     NOT NULL
);

CREATE INDEX words_sura_ayah_idx ON words (sura, ayah, seq);

CREATE TABLE rulings (
  seq         integer  NOT NULL REFERENCES words (seq)   ON DELETE CASCADE,
  source      text     NOT NULL REFERENCES sources (id)  ON DELETE CASCADE,
  raw         text     NOT NULL,          -- لفظُ الكتاب بعينه — لا يُستبدَل أبداً
  symbol      text,
  term        text,                       -- المصطلحُ المعياريُّ لهذا اللفظ
  category    text              REFERENCES categories (id),
  approx      boolean  NOT NULL DEFAULT false,   -- تُعرَض ≈ إذا كانت المقابلةُ تقريبية
  alt_symbol  text,
  alt_term    text,                       -- قولٌ آخرُ في الموضع نفسِه
  note        text,                       -- العلّةُ بلفظ المؤلف، ثم العزو، ثم ص/آية
  review      text,                       -- سببُ الإحالة على المراجعة إن وُجد
  status      text     NOT NULL DEFAULT 'proposed'
                CHECK (status IN ('imported', 'proposed', 'verified')),
  confidence  text,                       -- نصٌّ حرٌّ عمداً — انظر صدر الملف
  context     text,
  PRIMARY KEY (seq, source)
);

CREATE INDEX rulings_source_idx   ON rulings (source);
CREATE INDEX rulings_review_idx   ON rulings (source) WHERE review IS NOT NULL;
CREATE INDEX rulings_category_idx ON rulings (category);

COMMENT ON COLUMN rulings.raw IS
  'لفظُ المصدر كما هو. الطبقةُ الأولى من طبقتين، والثانيةُ category وهي للّون فقط.';
COMMENT ON COLUMN rulings.note IS
  'العلّةُ بلفظ المؤلف أولاً، ثم أقوالُ القائلين، ثم ص{الصفحة}/آية {الرقم}. والعلّةُ لا تُلخَّص.';

-- جدولُ المصطلحات: مصطلحُ كلِّ كتابٍ ومقابلُه العامّ، وعَلَمُ المراجعة
CREATE TABLE terms (
  source     text     NOT NULL REFERENCES sources (id) ON DELETE CASCADE,
  symbol     text     NOT NULL,
  term       text     NOT NULL,
  category   text              REFERENCES categories (id),
  approx     boolean  NOT NULL DEFAULT false,
  reviewed   boolean  NOT NULL DEFAULT false,   -- ينتظر نظرَ متخصّص
  PRIMARY KEY (source, symbol)
);

COMMENT ON TABLE terms IS
  'المقابلةُ بين مصطلح كلِّ مصدرٍ والفئة العامّة. كلُّ مدخلٍ reviewed=false حتى يُراجِعه متخصّص، وهو أوّلُ سطحٍ للمراجعة في التطبيق.';

-- الروايات: المصحفُ نفسُه يختلف رسمُه، فالموضعُ الواحدُ قد لا يكون واحداً
CREATE TABLE riwayat (
  id          text PRIMARY KEY,
  name        text,
  line        text,
  region      text,
  script      text,
  word_count  integer NOT NULL DEFAULT 0,
  has_text    boolean NOT NULL DEFAULT false
);

CREATE TABLE riwaya_words (
  riwaya    text     NOT NULL REFERENCES riwayat (id) ON DELETE CASCADE,
  pos       integer  NOT NULL,
  text      text     NOT NULL,
  hafs_seq  integer           REFERENCES words (seq) ON DELETE SET NULL,
  align     text              CHECK (align IN ('exact', 'variant', 'unmatched')),
  PRIMARY KEY (riwaya, pos)
);

CREATE INDEX riwaya_words_hafs_idx ON riwaya_words (hafs_seq);

COMMIT;
