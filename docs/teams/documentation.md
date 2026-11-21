# أدوات التوثيق — استخدمنا إيه فعلًا؟

استخدمنا **MkDocs** لبناء دليل الفرق من ملفات Markdown إلى صفحات HTML، و**FastAPI OpenAPI + Swagger UI** لتوثيق عقود الـAPI من الكود. واستخدمنا **تقارير JUnit** لبناء فهرس حالات الاختبار ونتائجها تلقائيًا.

الشرح المعماري وتحليل قرارات التصميم مكتوبان بناءً على مراجعة المصدر. MkDocs ينظم ويحوّل المحتوى، لكنه لا يستنتج وحده لماذا اخترنا سلة لكل متجر أو كيف نمنع تكرار الدفع. الفصل بين الدورين يخلّي الفريق يشرح الأداة بدقة.

## 1. MkDocs بيعمل إيه؟

MkDocs هو Static Documentation Generator: يقرأ ملفات Markdown وقائمة الصفحات والإعدادات ثم ينتج موقع توثيق ثابتًا. داخل المشروع:

| الملف أو المجلد | الوظيفة |
|---|---|
| `mkdocs.yml` | اسم الدليل، مصدر الصفحات، ترتيب التنقل، القالب، وفحص الروابط. |
| `docs/teams/*.md` | الشرح القابل للتحرير لكل تيم وللاختبارات والأدوات. |
| `docs/teams/assets/handbook.css` | اتجاه عربي مناسب للنص والكود. |
| `docs/teams/assets/language.js` | إبقاء فصل Backend إنجليزيًا باتجاه LTR وباقي الفصول عربيًا. |
| `requirements-docs.txt` | نسخة MkDocs المحددة لبناء الدليل. |
| `site/` | ناتج HTML؛ يتولد من المصدر ومستبعد من Git. |

الخطوات الفعلية: قسمنا المحتوى إلى فصول، ضبطنا `docs_dir` و`nav`، ربطنا الملفات، ثم شغّلنا build بالوضع الصارم. `--strict` يفشل عند تحذيرات مثل روابط داخلية ناقصة؛ ده يساعد على اكتشاف توثيق غير قابل للتصفح قبل تسليمه.

راجع [التعريف الرسمي](https://www.mkdocs.org/getting-started/) و[إعدادات MkDocs](https://www.mkdocs.org/user-guide/configuration/).

## 2. تشغيل وبناء الدليل

من جذر المشروع:

```bash
python -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.txt
.venv-docs/bin/python -m mkdocs build --strict
```

للمعاينة في المتصفح:

```bash
.venv-docs/bin/python -m mkdocs serve --dev-addr 127.0.0.1:8030
```

المعاينة على `http://127.0.0.1:8030`. أمر serve مخصص لقراءة الدليل محليًا، ولا ينشر المشروع أو يرفع بياناته إلى خدمة خارجية.

## 3. FastAPI OpenAPI بيتولد إزاي؟

FastAPI يقرأ الـrouters وتعريف المدخلات والمخرجات في Pydantic DTOs، ويستخرج schema بصيغة OpenAPI. العقود دي تشمل paths وHTTP methods وparameters وresponse schemas وأجزاء الأمان المعرفة في الكود.

```text
Router + Request DTO + Response DTO + Security Dependencies
  → FastAPI .openapi()
  → JSON Schema / OpenAPI document
  → Swagger UI يعرض العقد ويسمح بتجربته عند تفعيل docs
```

لذلك تعديل DTO أو route ثم إعادة التوليد يغيّر المرجع، بدل كتابة جدول endpoints يدوي ينسى الفريق تحديثه. الشرح البشري عن ownership أو قرارات business يظل مطلوبًا بجانب العقد.

في التطبيق، `/docs` و`/openapi.json` متاحان حسب `DOCS_ENABLED`؛ إعداد الإنتاج يقفلهما افتراضيًا. Swagger يحتاج access token للعمليات المحمية، لكنه لا يخلقه من نفسه ولا يتجاوز صلاحيات الباك.

أضفنا سكربت توليد نسخة ثابتة للدليل:

```bash
back/.venv/bin/python scripts/export_openapi.py
```

السكربت يستخرج العقود من التطبيق الفعلي بإعدادات معزولة، دون قراءة `.env`، ودون تشغيل lifespan أو قواعد البيانات أو إرسال رسائل. الاتصالات الخارجية محظورة أثناء التصدير. الناتج قابل للتنزيل: [OpenAPI JSON](assets/openapi.json).

## 4. Postman دوره إيه؟

Postman collections طلبات HTTP يدوية جاهزة، وليست أداة كتابة شرح المعمارية. توجد مجموعة للحسابات وأخرى لـSprint 2، ومعهما قوالب development/test/production.

ظبطنا `base_url` ليكون أصل الباك فقط دون `/api/v1` في المجموعتين، وأضفنا مراجع طلبات browser verification وlogin وrefresh وlogout وOAuth completion. كده الفريق يقدر يشرح request وheaders وbody ويجرب endpoint بدون تخمين الصيغة.

المجموعات الحالية لا تحتوي assertion scripts؛ الاختبارات الآلية في ملفات pytest وNode مستقلة. استيراد collection أو إرسال طلب ناجح لا يعني إننا شغّلنا Integration Test suite.

## 5. فهرس الاختبارات اتعمل بإيه؟

pytest وNode test runner يخرجان تقارير بصيغة JUnit XML. بعد التشغيل، `scripts/generate_test_catalog.py` يقرأ reports تحت `output/verification/` ويكتب:

- `docs/teams/test-catalog.md`: أسماء كل الحالات ونتيجتها وعددها حسب المجموعة.
- `docs/teams/assets/test-results.json`: نفس النتائج بصيغة قابلة للقراءة برمجيًا.

يمكن تحديث المصدر بإعادة تشغيل `python scripts/generate_test_catalog.py` بعد توليد التقارير الست. فحص CI يبني MkDocs ويعيد تصدير OpenAPI من الكود، أما فهرس آخر تشغيل فيُحدّث من تقارير الاختبارات كما هو موضح في فصل الاختبارات.

السكربت لا يفترض أن الحالة نجحت لمجرد وجود دالة اختبار؛ يقرأ `failure` و`error` و`skipped` من التقرير الفعلي. القيم Parameterized تظهر كحالات منفصلة. [شاهد الفهرس](test-catalog.md) أو [البيانات المنظمة](assets/test-results.json).

عند تغيير الاختبارات: شغّل الأوامر الموثقة في [فصل الاختبارات](testing.md)، ثم شغّل مولد الفهرس، وبعدها MkDocs build. ملفات نتائج آخر تشغيل لا تثبت حالة أي تعديلات لاحقة لم تختبر.

## 6. صياغة الفريق أثناء العرض

صياغة دقيقة ممكن الفريق يستخدمها:

> استخدمنا MkDocs لبناء دليل الفرق من Markdown، وFastAPI ولّد عقود OpenAPI من الـDTOs والـroutes وعرضها في Swagger UI. وثّقنا قرارات المعمارية وتدفق المستخدم من مراجعة الكود، وربطنا النتائج بتقارير JUnit مولّدة من تشغيل pytest وNode test runner. كده التوثيق فيه شرح قابل للقراءة، ومرجع API، ودليل على نتائج الاختبارات.

ده يوضح الأدوات اللي اشتغلت فعليًا، وما ينسبش كتابة كل الشرح أو تنفيذ الاختبارات إلى Swagger أو Postman.
