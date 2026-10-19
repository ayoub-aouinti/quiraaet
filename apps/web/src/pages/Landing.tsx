import { Link } from 'react-router-dom';
import { arNum, sourceColor, sourceShort } from '@jamei/shared';
import { useMeta } from '../lib/meta';

export function Landing() {
  const meta = useMeta();
  const total = meta.sources.reduce((n, s) => n + s.counts.total, 0);
  const words = meta.suras.reduce((n, s) => n + s.words, 0);
  return (
    <div className="landing">
      <section className="hero">
        <h1>
          أين يقف القارئ،
          <br />
          وبِمَ احتجّ العلماء
        </h1>
        <p className="lead">
          جامعٌ لأقوال كتب الوقف والابتداء ورموز المصاحف، كلمةً كلمةً على كلمات المصحف كلِّها. كلُّ حكمٍ بلفظ كتابه، ومعه علّتُه
          كما قالها صاحبُها.
        </p>
        <div className="hero-actions">
          <Link className="btn primary" to="/read/1">
            ابدأ من الفاتحة
          </Link>
          <Link className="btn" to="/sources">
            المصادر وحالُها
          </Link>
        </div>
        <dl className="hero-stats">
          <div>
            <dt>كلمةً في الفهرس</dt>
            <dd>{arNum(words)}</dd>
          </div>
          <div>
            <dt>حكماً</dt>
            <dd>{arNum(total)}</dd>
          </div>
          <div>
            <dt>مصدراً</dt>
            <dd>{arNum(meta.sources.length)}</dd>
          </div>
          <div>
            <dt>روايات</dt>
            <dd>{arNum(meta.riwayat.length)}</dd>
          </div>
        </dl>
      </section>

      <section className="principles">
        <h2>كيف نعرض الخلاف</h2>
        <div className="grid3">
          <article>
            <h3>اللفظُ كما قاله صاحبُه</h3>
            <p>
              لكلِّ حكمٍ لفظُ كتابه بعينه، لا يُستبدَل. «صالح» عند العماني يبقى «صالحاً»، و«مرخَّصٌ لضرورة» عند السجاوندي يبقى كذلك.
            </p>
          </article>
          <article>
            <h3>الفئةُ للّون وحده</h3>
            <p>
              تُردّ المصطلحاتُ إلى فئاتٍ عامّةٍ لتلوين الصفحة فقط، وعليها ≈ إن كانت المقابلةُ تقريبية. ولا يُحسَب منها اتفاقٌ ولا اختلاف.
            </p>
          </article>
          <article>
            <h3>المقترَحُ يُسمّى مقترَحاً</h3>
            <p>
              ما استُخرج آلياً ولم يُراجَع يُعلَّم «مقترَحاً» حيث عُرض. وخلوُّ موضعٍ من حكمٍ ليس نفياً للوقف: قد يكون نقصَ مصدر.
            </p>
          </article>
        </div>
      </section>

      <section className="src-strip">
        <h2>ما في الجامع</h2>
        <ul>
          {meta.sources.map((s) => (
            <li key={s.id} style={{ borderInlineStartColor: sourceColor(s.id) }}>
              <b>{sourceShort(s.id, s.name)}</b>
              <span>{s.name}</span>
              <span className="muted small">{arNum(s.counts.total)} موضعاً</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="desk-note">
        <h2>على سطح المكتب</h2>
        <p className="muted">
          ليس للجامع تطبيقُ سطح مكتبٍ منفصل: هذه الواجهةُ نفسُها تُثبَّت من المتصفّح (Chrome أو Edge: «تثبيت جامع الوقوف» في شريط
          العنوان) فتعمل في نافذتها مربوطةً بالخادم.
        </p>
      </section>
    </div>
  );
}
