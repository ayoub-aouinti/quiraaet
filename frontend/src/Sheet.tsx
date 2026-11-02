import { useEffect, useRef } from 'react';
import { fontStyle, paint } from './paint';
import type { Meta, ReadEntry, RiwayaMeta } from './types';
import { condText, nameOf, type Colors, type Cover, type Target } from './view';

const KIND: Record<number, string> = {
  1: 'ضبط مخالف (حركات أو همزات) — مرشَّح للمراجعة', 2: 'رسم مخالف', 3: 'كلمة لا مقابل لها في قالون',
};

interface Ctx { meta: Meta; colors: Colors; sel: Set<string>; qtext: Map<number, string> }

function Tags({ r }: { r: ReadEntry['r'][number] }) {
  const tags: string[] = [];
  if (r.cond) tags.push(condText(r));
  if (r.khulf) tags.push('بخلافٍ عنه');
  return tags.length ? <span className="tags">{tags.map(t => <span key={t} className="tag">{t}</span>)}</span> : null;
}

/** عنصرُ خلافٍ: رواةٌ بكلماتهم وحروفهم المخالفة، ثم البيان بلفظ المصدر */
function Entry({ e, only, hl, ctx }: { e: ReadEntry; only?: string; hl?: string; ctx: Ctx }) {
  const { meta, colors, sel, qtext } = ctx;
  const rs = only ? e.r.filter(r => r.id === only) : e.r;
  const rank = (r: { id: string }) => (r.id === 'qalun' ? 2 : sel.has(r.id) ? 1 : 0);
  const order = rs.filter(r => only || r.id === 'qalun' || sel.has(r.id)).sort((a, b) => rank(b) - rank(a));   // من أُلغي تحديدُه لا يظهر خلافُه
  return (
    <div className={'ent' + (rs.some(r => sel.has(r.id)) ? '' : ' off')}>
      <h4>
        <span>{e.e > e.s ? 'خلاف في عبارة' : 'خلاف'}</span>
        {e.t === 'rasm' && <span className="tag warn">≈ مطابقة بالرسم</span>}
        {e.t === 'm' && <span className="tag">فرق في المصحف</span>}
        {(e.t === 'u' || e.t === 'w') && <span className="tag">أصلٌ عامّ معمَّم على مواضعه</span>}
        {e.u && <span className="tag warn">مشكوك فيه</span>}
        <span className="tag">غير مُتحقَّق</span>
      </h4>
      {e.e > e.s && (
        <div className="same" style={{ ...fontStyle('qalun'), fontSize: '1.4rem' }}>
          {[...Array(e.e - e.s + 1).keys()].map(i => qtext.get(e.s + i)).join(' ')}
        </div>
      )}
      {order.map(r => {
        const on = sel.has(r.id) || r.id === 'qalun';
        const col = colors.color[r.id];
        return (
          <div key={r.id} className={'rr' + (hl === r.id ? ' hl' : '') + (on ? '' : ' dim')}>
            <span className="nm">
              <span className="chip" style={{ background: col || 'var(--muted)' }} />
              <span>{nameOf(meta, r.id)}</span>
            </span>
            {r.same ? <span className="same">كقالون</span>
              : r.x ? (
                <>
                  <span className="tx" style={fontStyle(r.f || 'hafs')}>
                    {paint(r.x, new Map((r.dx || []).map(i => [i, col])), new Map((r.dxa || []).map(i => [i, col])))}
                  </span>
                  {(r.n || r.cond || r.khulf) && (
                    <span className="tags">
                      {r.n && <span className="tag">{r.n}</span>}
                      {r.cond ? <span className="tag">{condText(r)}</span> : null}
                      {r.khulf && <span className="tag">بخلافٍ عنه</span>}
                    </span>
                  )}
                </>
              ) : (
                <>
                  <span className="same">
                    {r.n ? 'يخالف قالون: ' + r.n : 'يخالف قالون (لم يُبيَّن وجهه في المصادر المتاحة)'}
                  </span>
                  <Tags r={r} />
                </>
              )}
          </div>
        );
      })}
    </div>
  );
}

interface Props extends Ctx {
  target: Target; hl?: string; cover: Cover; riw: RiwayaMeta; onClose: () => void;
}

export default function Sheet({ target, hl, cover, riw, onClose, ...ctx }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const prev = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    return () => { if (prev?.isConnected) prev.focus(); };
  }, []);

  let title: string, font: string, body: React.ReactNode;
  if (target.mode === 'q') {
    const ents = (cover.get(target.seq) || []).map(c => c.e);
    const score = (e: ReadEntry) => e.r.filter(r => ctx.sel.has(r.id)).length;
    const shown = ents.filter(e => score(e) > 0).sort((a, b) => score(b) - score(a));
    title = ctx.qtext.get(target.seq) || ''; font = 'qalun';
    body = shown.length
      ? shown.map((e, i) => <Entry key={i} e={e} hl={hl} ctx={ctx} />)
      : <p className="empty">{ents.length
        ? 'لا خلاف في هذه الكلمة للرواة المحدَّدين.'
        : 'لا خلاف مسجَّل لهذه الكلمة في المصادر المتوفرة. وخلوّ الموضع من خلافٍ ليس نفياً له؛ قد يكون نقصاً في المصدر.'}</p>;
  } else {
    const { k, q, text } = target;
    title = text; font = target.font || riw.mush || 'qalun';
    body = (
      <>
        <div className="ent">
          <h4>{k ? KIND[k] || 'يخالف قالون' : 'مطابقة لقالون'}</h4>
          {q && ctx.qtext.has(q)
            ? <div className="rr"><span className="nm">قالون</span><span className="tx" style={fontStyle('qalun')}>{ctx.qtext.get(q)}</span></div>
            : q ? <p className="same">مقابل قالون في سورةٍ أخرى (رقم الكلمة {q}).</p> : null}
          <p className="same">{riw.mush
            ? 'هذا فرقُ نصّين بين مصحفين، لا حكمُ قراءة؛ ولا يُنسَب إلى قارئ إلا من البيان أدناه إن وُجد.'
            : 'مصحفُ قالون وقد استُبدلت الكلمةُ بكلمة قراءته من المصدر.'}</p>
        </div>
        {q ? (cover.get(q) || []).filter(({ e }) => e.r.some(r => r.id === riw.reader))
          .map(({ e }, i) => <Entry key={i} e={e} only={riw.reader} hl={riw.reader} ctx={ctx} />) : null}
      </>
    );
  }

  return (
    <div id="sheet" className="sheet" role="dialog" aria-modal="false" aria-labelledby="sheet-title">
      <div className="sheet-head">
        <h2 id="sheet-title" style={fontStyle(font)}>{title}</h2>
        <button ref={closeRef} type="button" id="sheet-close" aria-label="إغلاق" onClick={onClose}>×</button>
      </div>
      <div id="sheet-body" className="sheet-body">{body}</div>
    </div>
  );
}
