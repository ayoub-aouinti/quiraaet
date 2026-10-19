import sys, json
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
PAGE=json.load(open('out/page_sample.json',encoding='utf-8'))['text']
frag=' '.join(PAGE.split()[:34])


riw_cards=""
import sqlite3 as _s
_c=_s.connect('out/waqf.db'); _c.row_factory=_s.Row
for r in _c.execute('SELECT id,name,line,region,script,word_count,has_text FROM riwayat'):
    has=bool(r['has_text'])
    col = '#2F6B5E' if r['id']=='warsh' else ('#1E3A5F' if r['id']=='hafs' else RULE)
    state = (f"{r['word_count']:,}".replace(',', chr(0x066C)) + ' كلمة') if has else 'قيد الإعداد'
    fg = INK if has else '#A49E92'
    riw_cards += f"""
<div style="background: {PAPER}; padding: 22px 22px 20px; border-top: 3px solid {col}">
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 19px; margin-bottom: 5px; color: {fg}">{r['name']}</div>
<div style="font-size: 13px; line-height: 1.85; color: {SAGE}">{r['line']}<br>{r['region']} — رسم {r['script']}</div>
<div style="margin-top: 13px; padding-top: 11px; border-top: 1px solid {RULE}; font-family: 'Reem Kufi', sans-serif; font-size: 15px; color: {fg}">{state}</div>
</div>"""

src_rows=''.join(f'''
<a href="Reader.dc.html" style="display: flex; align-items: baseline; gap: 16px; padding: 15px 0; border-bottom: 1px solid {RULE}">
<span style="flex: 0 0 10px; height: 10px; border-radius: 5px; background: {c}; align-self: center"></span>
<span style="flex: 0 0 132px; font-size: 17px; font-weight: 500; color: {INK}">{n}</span>
<span style="flex: 1; font-size: 14.5px; color: {SAGE}">{sub}</span>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 19px; color: {c}">{cnt:,}</span>
</a>'''.replace(',','٬') for k,(n,c,sub,cnt) in SRC.items())

body = f'''
<div dir="rtl" style="background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; min-height: 100vh">

<header style="display: flex; align-items: center; justify-content: space-between; gap: 24px; max-width: 1180px; margin: 0 auto; padding: 26px 40px">
<a href="Landing.dc.html" style="display: flex; align-items: center; gap: 12px">
{logo_mark(30)}
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 23px; font-weight: 600; letter-spacing: 0.5px">جامع الوقوف</span>
</a>
<nav style="display: flex; align-items: center; gap: 30px; font-size: 15px">
<a href="Reader.dc.html" style="color: {SAGE}">المصحف</a>
<a href="Reader.dc.html" style="color: {SAGE}">المصادر</a>
<a href="Admin.dc.html" style="color: {SAGE}">المنهج</a>
<a href="Reader.dc.html" style="display: inline-flex; align-items: center; height: 44px; padding: 0 22px; border-radius: 3px; background: {LAPIS}; color: {PAPER}; font-size: 15px; font-weight: 500">افتح المصحف</a>
</nav>
</header>

<section style="max-width: 1180px; margin: 0 auto; padding: 42px 40px 0; display: grid; grid-template-columns: minmax(0, 420px) minmax(0, 1fr); gap: 64px; align-items: start">
<div style="padding-top: 26px">
<h1 style="margin: 0 0 22px; font-family: 'Reem Kufi', sans-serif; font-size: 50px; line-height: 1.32; font-weight: 500">أين يقف القارئ،<br>وبِمَ احتجّ العلماء</h1>
<p style="margin: 0 0 18px; font-size: 17.5px; line-height: 1.95; color: #42403B; max-width: 46ch">ستة مصادر في الوقف والابتداء، مقابَلة على المصحف كلمةً كلمة: كتب الأئمة من الداني إلى الأشموني، ورموز الرسم العثماني، ووقف الهبطي في المصحف المغربي.</p>
<p style="margin: 0 0 30px; font-size: 15px; line-height: 1.9; color: {SAGE}; max-width: 46ch">يُعرض لك مصطلح كل عالم بلفظه الذي استعمله، لا مردوداً إلى اصطلاح غيره.</p>
<div style="display: flex; gap: 12px; flex-wrap: wrap">
<a href="Reader.dc.html" style="display: inline-flex; align-items: center; height: 50px; padding: 0 26px; border-radius: 3px; background: {LAPIS}; color: {PAPER}; font-size: 16px; font-weight: 500">ابدأ من الفاتحة</a>
<a href="Compare.dc.html" style="display: inline-flex; align-items: center; height: 50px; padding: 0 26px; border-radius: 3px; border: 1px solid {LAPIS}; color: {LAPIS}; font-size: 16px">قارن المصادر</a>
</div>
</div>

<figure style="margin: 0; position: relative">
<div style="border: 1.5px solid {LAPIS}; padding: 7px; background: {PAPER}">
<div style="border: 0.8px solid {OCHRE}; padding: 34px 30px 30px">
<div style="font-family: 'Maghribi', serif; font-size: 27px; line-height: 2.5; text-align: justify; color: {INK}; direction: rtl">{frag}</div>
</div>
</div>
<figcaption style="margin-top: 14px; font-size: 13.5px; color: {SAGE}; text-align: center; line-height: 1.8">المصحف المحمدي برواية ورش — وقف الهبطي مضمَّن في النصّ كما طُبع</figcaption>
<div style="position: absolute; top: 112px; left: -22px; width: 190px; padding: 13px 15px; background: {PAPER}; border-inline-start: 3px solid {CARMINE}; box-shadow: 0 1px 0 {RULE}">
<div style="font-size: 12.5px; color: {SAGE}; margin-bottom: 4px">السجاوندي</div>
<div style="font-size: 15px; font-weight: 500">لا يوقف عليه</div>
</div>
</figure>
</section>

<section style="max-width: 1180px; margin: 92px auto 0; padding: 0 40px">
<div style="display: grid; grid-template-columns: minmax(0, 300px) minmax(0, 1fr); gap: 64px; align-items: start">
<div>
<h2 style="margin: 0 0 14px; font-family: 'Reem Kufi', sans-serif; font-size: 29px; font-weight: 500">ما في الجامع</h2>
<p style="margin: 0; font-size: 15.5px; line-height: 1.95; color: {SAGE}">٣١٬١٢٩ حكماً على ٧٧٬٤٣٦ كلمة. كل حكم موصول بمصدره وموضعه من المصحف.</p>
</div>
<div>{src_rows}</div>
</div>
</section>

<section style="max-width: 1180px; margin: 92px auto 0; padding: 0 40px">
<h2 style="margin: 0 0 8px; font-family: 'Reem Kufi', sans-serif; font-size: 29px; font-weight: 500">الصفحة كما طُبعت</h2>
<p style="margin: 0 0 30px; font-size: 15.5px; line-height: 1.9; color: #5A6B5D; max-width: 62ch">لا نعيد صفّ المصحف ولا نغيّر رسمه. تُعرض الصفحة بنصّها وخطّها كما في مصحفها، وعلامات الوقف فيها من أصل النصّ لا مضافة فوقه.</p>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 26px">
<figure style="margin: 0">
<div style="border: 1.3px solid #2F6B5E; padding: 5px; background: #F6F4EE">
<div style="border: 0.7px solid #A8762C; padding: 14px 13px; height: 258px; overflow: hidden">
<p style="margin: 0; font-family: 'Maghribi', serif; font-size: 17px; line-height: 2.3; text-align: justify; color: #1C1815">يَظُنُّونَ أَنَّهُم مُّچَقُواْ رَبِّهِمْ وَأَنَّهُمُ; إِلَيْهِ رَ؛جِعُونَؐ (45) يَـٰبَنِىٓ إِسْرَآءِيلَ ۸ذْكُرُواْ نِعْمَتِيَ ۰لتِىٓ أَنْعَمْــتُ عَلَيْكُمْ وَأَنِّـى فَضَّلْتُكُمْ عَلَي ۰لْعَــٰلَمِينَؐ (46) وَاتَّقُواْ يَوْماً لاَّ تَجْزۣى نَفْس٘ عَن نَّفْسٍ شَيْــٔاً وَلاَ يُقْبَلُ مِنْهَا شَفَــٰعَةٌ وَلاَ يُوخَذُ مِنْهَا عَدْلٌ وَلاَ هُمْ يُنصَرُونَؐ (47) وَإِذْ نَجَّيْنَـٰكُم مِّـنَ —الِ فِرْعَوْنَ يَسُومُونَكُمْ سُوٓءَ ۰لْعَذَابببِ يُذَبِّحُونَ أَبْنَآءَكُمْ وَيَسْتَحْيُونَ نِسَآءَكُمْؐ وَفِى ذَ؛لِكُم بَلٓاَءٌ مِّن رَّبِّكُمْ عَظِيمٌؐ (48) وَإِذْ فَرَقْنَا بِكُمُ ۴ڤْبَحْرَ فَأَنجَيْنَـٰ</p>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #1C1815">الفاتحة وأول البقرة
<span style="display: block; font-size: 11.5px; color: #5A6B5D; margin-top: 2px">ورش عن نافع — خطّ مغربي</span></figcaption>
</figure>
<figure style="margin: 0">
<div style="border: 1.3px solid #2F6B5E; padding: 5px; background: #F6F4EE">
<div style="border: 0.7px solid #A8762C; padding: 14px 13px; height: 258px; overflow: hidden">
<p style="margin: 0; font-family: 'Maghribi', serif; font-size: 17px; line-height: 2.3; text-align: justify; color: #1C1815">وَڤِيُمَحِّصَ ۰للَّهُ ۴لذِينَ ءَامَنُواْ وَيَمْحَقَ ۰لْكۭـٰفِـرۣينَؐ (141) أَمْ حَسِبْتُمُ; أَن تَدْخُلُواْ ۴لْجَنَّةَ وَلَمَّا يَعْلَمِ ۱للَّهُ ۴لذِينَ جَــٰهَدُواْ مِنكُمْ وَيَعْلَمَ ۰لصَّــٰبِرۣينَؐ (142) وَلَقَدْ كُنتُمْ تَمَنَّوْنَ ۰لْمَوْتتتَ مِن قَبْلِ أَن تَلْقَوْهُ فَقَدْ رَأَيْتُمُوهُ وَأَنتُمْ تَنظُرُونَؐ (143) ® وَمَا مُحَمَّد٘ اِلاَّ رَسُولٌ قَدْ خَلَــتْ مِن قَبْلِهِ ۱لرُّسُلُؐ أَفَإِيْن مَّاتتتَ أَوْ قُتِلَ "نقَلَبْتُمْ عَلَيٰٓ أَعْقَــٰبِكُمْؐ وَمَنْ يَّنقَلِبْ عَلَيٰ عَقِبَيْهِ فَلَنْ يَّضُرَّ۰للَّهَ شَيْـــٔـاًؐ وَسَيَجْزۣى ۱للَّهُ ۴لشَّـٰكِرۣينَؐ (144) وَمَا كَانَ لِنَفْس؉ ا</p>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #1C1815">من سورة البقرة
<span style="display: block; font-size: 11.5px; color: #5A6B5D; margin-top: 2px">ورش عن نافع — خطّ مغربي</span></figcaption>
</figure>
<figure style="margin: 0">
<div style="border: 1.3px solid #2F6B5E; padding: 5px; background: #F6F4EE">
<div style="border: 0.7px solid #A8762C; padding: 14px 13px; height: 258px; overflow: hidden">
<p style="margin: 0; font-family: 'Maghribi', serif; font-size: 17px; line-height: 2.3; text-align: justify; color: #1C1815">عُذْراًؐ (75) فَانطَلَقَا حَتَّيٰٓ إِذَآ أَتَيَآ أَهْلَ قَرْيَةٖ 'سْتَطْعَمَآ أَهْلَهَا فَأَبَوَاْ اَنْ يُّضَيِّفُوهُمَا فَوَجَدَا فِيهَا جِدَاراً يُرۣيدُ أَنْ يَّنقَضَّ فَأَقَامَهُؐ, قَالَ لَوْ شِيؔــتَ ڤَتَّخَذتَّ عَلَيْهِ أَجْراًؐ (76) قَالَ هَـٰذَا فِرَاقُ بَيْنِى وَبَيْنِــكَؐ سَٱُنَبِّيؖــكَ بِتَاوۣيلِ مَا لَمْ تَسْتَطِع عَّلَيْهِ صَبْراٗؐ (77) اَمَّا ۰لسَّفِينَةُ فَكَانَــتْ لِمَسَـٰكِينَ يَعْمَلُونَ فِى ۱ڤْبَحْرۣ فَأَرَدتُّ أَنَ اَعِيبَهَا وَكَانَ وَرَآءَهُم مَّلِكٌ يَاخُذُ كُلَّ سَفِينَةٖ غَصْباًؐ (78) وَأَمَّا ۰لْغُچَمُ فَكَانَ أَبَوَ؛هُ مُومِنَيْنِ فَخَشِينَآ أَنْ يُّرْهِقَهُمَا طُغ</p>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #1C1815">من وسط المصحف
<span style="display: block; font-size: 11.5px; color: #5A6B5D; margin-top: 2px">ورش عن نافع — خطّ مغربي</span></figcaption>
</figure></div>
</section>

<section style="max-width: 1180px; margin: 84px auto 0; padding: 0 40px">
<h2 style="margin: 0 0 8px; font-family: 'Reem Kufi', sans-serif; font-size: 29px; font-weight: 500">الموضع نفسه في الروايات الأربع</h2>
<p style="margin: 0 0 30px; font-size: 15.5px; line-height: 1.9; color: #5A6B5D; max-width: 62ch">الرواية تغيّر الرسم والخطّ معاً، لا الخطّ وحده. هذه أربع صور لموضع واحد، كلٌّ بما طُبع به في مصحفه.</p>
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 22px">
<figure style="margin: 0">
<div style="border: 1.3px solid #2F6B5E; padding: 5px; background: #F6F4EE">
<div style="border: 0.7px solid #A8762C; padding: 14px 13px; height: 236px; overflow: hidden">
<p style="margin: 0; font-family: 'Maghribi', serif; font-size: 17px; line-height: 2.3; text-align: justify; color: #1C1815">وَڤِيُمَحِّصَ ۰للَّهُ ۴لذِينَ ءَامَنُواْ وَيَمْحَقَ ۰لْكۭـٰفِـرۣينَؐ (141) أَمْ حَسِبْتُمُ; أَن تَدْخُلُواْ ۴لْجَنَّةَ وَلَمَّا يَعْلَمِ ۱للَّهُ ۴لذِينَ جَــٰهَدُواْ مِنكُمْ وَيَعْلَمَ ۰لصَّــٰبِرۣينَؐ (142) وَلَقَدْ كُنتُمْ تَمَنَّوْنَ ۰لْمَوْتتتَ مِن قَبْلِ أَن تَلْقَوْهُ فَقَدْ رَأَيْتُمُوهُ وَأَنتُمْ تَنظُرُونَؐ (143) ® وَمَا مُحَمَّد٘ اِلاَّ رَسُولٌ قَدْ خَلَــتْ مِن قَبْلِهِ ۱لرُّسُلُؐ أَفَإِيْن مَّاتتتَ أَوْ قُتِلَ "نقَلَبْتُمْ عَلَيٰٓ أَعْقَــٰبِكُمْؐ وَمَنْ يَّنقَلِبْ عَلَيٰ عَقِبَيْهِ فَلَنْ يَّضُرَّ۰للَّ</p>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #1C1815">ورش عن نافع
<span style="display: block; font-size: 11.5px; color: #5A6B5D; margin-top: 2px">المصحف المحمدي — خطّ مغربي</span></figcaption>
</figure>
<figure style="margin: 0">
<div style="border: 1.3px solid #1E3A5F; padding: 5px; background: #F6F4EE">
<div style="border: 0.7px solid #A8762C; padding: 14px 13px; height: 236px; overflow: hidden">
<p style="margin: 0; font-family: 'UthHafs', serif; font-size: 17px; line-height: 2.3; text-align: justify; color: #1C1815">وَلِيُمَحِّصَ ٱللَّهُ ٱلَّذِينَ ءَامَنُواْ وَيَمۡحَقَ ٱلۡكَـٰفِرِينَ أَمۡ حَسِبۡتُمۡ أَن تَدۡخُلُواْ ٱلۡجَنَّةَ وَلَمَّا يَعۡلَمِ ٱللَّهُ ٱلَّذِينَ جَـٰهَدُواْ مِنكُمۡ وَيَعۡلَمَ ٱلصَّـٰبِرِينَ وَلَقَدۡ كُنتُمۡ تَمَنَّوۡنَ ٱلۡمَوۡتَ مِن قَبۡلِ أَن تَلۡقَوۡهُ فَقَدۡ رَأَيۡتُمُوهُ وَأَنتُمۡ تَنظُرُونَ وَمَا مُحَمَّدٌ إِلَّا رَسُولٞ قَدۡ خَلَتۡ مِن قَبۡلِهِ ٱلرُّسُلُ أَفَإِيْن مَّاتَ أَوۡ قُتِلَ ٱنقَلَبۡتُمۡ عَلَىٰٓ أَعۡقَـٰبِكُمۡ وَمَن يَنقَلِبۡ عَلَىٰ عَقِبَيۡهِ فَلَن يَضُرَّ ٱللَّهَ شَيۡـٔٗا وَسَيَجۡزِى ٱللَّهُ ٱلش</p>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #1C1815">حفص عن عاصم
<span style="display: block; font-size: 11.5px; color: #5A6B5D; margin-top: 2px">خطّ المجمع — رسم عثماني</span></figcaption>
</figure>
<figure style="margin: 0">
<div style="border: 1.3px solid #A8762C; padding: 5px; background: #F6F4EE">
<div style="border: 0.7px solid #A8762C; padding: 14px 13px; height: 236px; overflow: hidden">
<p style="margin: 0; font-family: 'UthQalun', serif; font-size: 17px; line-height: 2.3; text-align: justify; color: #1C1815">وَلِيُمَحِّصَ اَ۬للَّهُ اُ۬لذِينَ ءَامَنُواْ وَيَمْحَقَ اَ۬لْكَٰفِرِينَۖ أَمْ حَسِبْتُمْ أَن تَدْخُلُواْ اُ۬لْجَنَّةَ وَلَمَّا يَعْلَمِ اِ۬للَّهُ اُ۬لذِينَ جَٰهَدُواْ مِنكُمْ وَيَعْلَمَ اَ۬لصَّٰبِرِينَۖ وَلَقَدْ كُنتُمْ تَمَنَّوْنَ اَ۬لْمَوْتَ مِن قَبْلِ أَن تَلْقَوْهُ فَقَدْ رَأَيْتُمُوهُ وَأَنتُمْ تَنظُرُونَۖ ۞وَمَا مُحَمَّدٌ إِلَّا رَسُولٞ قَدْ خَلَتْ مِن قَبْلِهِ اِ۬لرُّسُلُۖ أَفَإِيْن مَّاتَ أَوْ قُتِلَ اَ۪نقَلَبْتُمْ عَلَيٰ أَعْقَٰبِكُمْۖ وَمَنْ يَّنقَلِبْ عَلَيٰ عَقِبَيْهِ فَلَنْ يَّضُرَّ اَ۬للَّهَ شَئْاٗۖ </p>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #1C1815">قالون عن نافع
<span style="display: block; font-size: 11.5px; color: #5A6B5D; margin-top: 2px">خطّ المجمع — علامة الوقف المغربية</span></figcaption>
</figure>
<figure style="margin: 0">
<div style="border: 1.3px solid #8C2F39; padding: 5px; background: #F6F4EE">
<div style="border: 0.7px solid #A8762C; padding: 14px 13px; height: 236px; overflow: hidden">
<p style="margin: 0; font-family: 'UthDuri', serif; font-size: 17px; line-height: 2.3; text-align: justify; color: #1C1815">وَلِيُمَحِّصَ اَ۬للَّهُ اُ۬لَّذِينَ ءَامَنُواْ وَيَمۡحَقَ اَ۬لۡكٰ۪فِرِينَ أَمۡ حَسِبۡتُمۡ أَن تَدۡخُلُواْ اُ۬لۡجَنَّةَ وَلَمَّا يَعۡلَمِ اِ۬للَّهُ اُ۬لَّذِينَ جَٰهَدُواْ مِنكُمۡ وَيَعۡلَمَ اَ۬لصَّٰبِرِينَ وَلَقَدۡ كُنتُمۡ تَمَنَّوۡنَ اَ۬لۡمَوۡتَ مِن قَبۡلِ أَن تَلۡقَوۡهُ فَقَدۡ رَأَيۡتُمُوهُ وَأَنتُمۡ تَنظُرُونَ ۞وَمَا مُحَمَّدٌ إِلَّا رَسُولٞ قَدۡ خَلَتۡ مِن قَبۡلِهِ اِ۬لرُّسُلُۚ أَفَإِيْن مَّاتَ أَوۡ قُتِلَ اَ۪نقَلَبۡتُمۡ عَلَىٰٓ أَعۡقَٰبِكُمۡۚ وَمَن يَنقَلِبۡ عَلَىٰ عَقِبَيۡهِ فَلَن يَضُرَّ اَ۬للَّهَ شَيۡـٔٗاۗ و</p>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #1C1815">الدوري عن أبي عمرو
<span style="display: block; font-size: 11.5px; color: #5A6B5D; margin-top: 2px">خطّ المجمع — رموز الوقف المشرقية</span></figcaption>
</figure></div>
</section>

<section style="max-width: 1180px; margin: 92px auto 0; padding: 0 40px">
<h2 style="margin: 0 0 8px; font-family: 'Reem Kufi', sans-serif; font-size: 29px; font-weight: 500">أربع روايات</h2>
<p style="margin: 0 0 30px; font-size: 15.5px; line-height: 1.9; color: {SAGE}; max-width: 62ch">الرواية تغيّر النصّ نفسه لا طريقة عرضه: رسمَه وعدَّ آيه ومواضع وقفه. فلكل رواية مصحفها، وأحكام الوقف تُعرض عليها بمحاذاة الكلمات.</p>
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; background: {RULE}; border: 1px solid {RULE}">{riw_cards}</div>
</section>

<section style="max-width: 1180px; margin: 92px auto 0; padding: 0 40px">
<h2 style="margin: 0 0 8px; font-family: 'Reem Kufi', sans-serif; font-size: 29px; font-weight: 500">كيف نعرض الخلاف</h2>
<p style="margin: 0 0 34px; font-size: 15.5px; line-height: 1.9; color: {SAGE}; max-width: 62ch">مراتب المدارس لا يقابل بعضها بعضاً: «المطلق» عند السجاوندي ليس «الكافي» عند الداني. فلا نردّ مصطلحاً إلى مصطلح، ولا نحسب اتفاقاً ولا خلافاً من تلقاء أنفسنا.</p>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: {RULE}; border: 1px solid {RULE}">
<div style="background: {PAPER}; padding: 26px 24px">
<h3 style="margin: 0 0 10px; font-size: 17px; font-weight: 600">اللفظ كما قاله صاحبه</h3>
<p style="margin: 0; font-size: 14.5px; line-height: 1.9; color: {SAGE}">يُنقل مصطلح المصدر بحروفه، ومعه نصّ كلامه في الموضع، ولا يُستبدل.</p>
</div>
<div style="background: {PAPER}; padding: 26px 24px">
<h3 style="margin: 0 0 10px; font-size: 17px; font-weight: 600">الفئة للّون وحده</h3>
<p style="margin: 0; font-size: 14.5px; line-height: 1.9; color: {SAGE}">الفئة العامة تلوّن العلامة لتقرأ الصفحة بسرعة. وعلامة ≈ تقول لك إن المطابقة تقريبية.</p>
</div>
<div style="background: {PAPER}; padding: 26px 24px">
<h3 style="margin: 0 0 10px; font-size: 17px; font-weight: 600">المقترح يُسمّى مقترحاً</h3>
<p style="margin: 0; font-size: 14.5px; line-height: 1.9; color: {SAGE}">٥٬٦٩٧ موضعاً مستخرجة آلياً من الكتب، موسومة بذلك حتى يعتمدها متخصص.</p>
</div>
</div>
</section>

<footer style="margin-top: 96px; border-top: 1px solid {RULE}">
<div style="max-width: 1180px; margin: 0 auto; padding: 30px 40px; display: flex; justify-content: space-between; align-items: center; gap: 24px; font-size: 14px; color: {SAGE}">
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 17px; color: {INK}">جامع الوقوف</span>
<span>نصّ المصحف من المصحف المحمدي برواية ورش · الأحكام من مصادرها المذكورة</span>
</div>
</footer>

</div>'''

script = '''class Component extends DCLogic {
  renderVals() { return {}; }
}'''
open(ROOT+'Landing.dc.html','w',encoding='utf-8').write(doc('جامع الوقوف', body, script, 1440, 2320, fill=True))
print('Landing written')
