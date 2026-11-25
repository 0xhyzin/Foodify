# أدوات التوثيق — استخدمنا إيه فعلًا في Sprint 3؟

استخدمنا منظومة توثيق عملية حقيقية متكاملة مع الكود والاختبارات: **MkDocs (`--strict`)** لبناء دليل الفرق HTML، و**FastAPI OpenAPI + Swagger UI** لتوليد عقود الـ `64` مسارًا مباشرة من الكود، و**مولد تقارير JUnit XML** لفهرسة الـ `285` حالة اختبار تلقائيًا، و**Postman Collections** المفحوصة بعقود Node، و**WeasyPrint** لإنتاج حزمة الـ PDF العربية RTL، و**Graphify** لبناء خريطة علاقات الكود AST.

الشرح المعماري وتحليل قرارات التصميم مكتوبان بناءً على مراجعة المصدر. الأدوات تنظم أو تستخرج العقود والنتائج، لكنها لا تستنتج وحده لماذا اخترنا سلة لكل متجر أو كيف نعالج تعارض DMARC في البريد. الفصل بين الدورين يخلّي الفريق يشرح كل أداة بدقة وأمانة.

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

Postman collections طلبات HTTP يدوية جاهزة، وليست أداة كتابة شرح المعمارية. توجد الآن 3 مجموعات تغطي المشروع كاملًا: الحسابات (`Foodify.postman_collection.json`)، المتاجر والدفع (`Foodify.Sprint2.postman_collection.json`)، و**Sprint 3 للبوابات الخمس والأدمن والمندوب والمطبخ والإشعارات (`Foodify.Sprint3.postman_collection.json`)**، ومعها قوالب `development/test/production`.

ظبطنا `base_url` ليكون أصل الباك فقط دون `/api/v1` في المجموعات الثلاث، وفُحصت آليًا عبر `tests/postman.test.mjs` (**7** اختبارات عقود) للتأكد من عدم تكرار `/api/v1/api/v1/` وتغطية مسارات البوابات الجديدة.

المجموعات نفسها يدوية لا تحتوي assertion scripts؛ الاختبارات الآلية موجودة في `back/tests` و`front/tests` و`tests/`.

## 5. فهرس الاختبارات اتعمل بإيه؟

pytest وNode test runner يخرجان تقارير بصيغة JUnit XML تحت `output/verification/`. بعدها `scripts/generate_test_catalog.py` يقرأ التقارير الستة ويكتب:

- `docs/teams/test-catalog.md`: أسماء كل الـ **285** حالة ونتيجتها وعددها حسب المجموعة.
- `docs/teams/assets/test-results.json`: نفس النتائج بصيغة JSON منظمة.

راجع [الفهرس](test-catalog.md) أو [البيانات المنظمة](assets/test-results.json) و[فصل الاختبارات](testing.md).

## 6. WeasyPrint وGraphify (حزمة PDF وخريطة الكود)

- **WeasyPrint + Noto Sans Arabic + DejaVu Sans Mono:** يحوّل HTML/CSS مصمّمًا باتجاه `dir="rtl"` وعزل المصطلحات الإنجليزية `<bdi dir="ltr">` إلى **6** ملفات PDF احترافية في `output/pdf/foodify-sprint-3-*-ar.pdf`، مع معاينة بصرية عبر `pdftoppm`.
- **Graphify (تحليل شجرة AST في `graphify-out/`):** يبني رسمًا بيانيًا للعلاقات والـ imports داخل `back/app` و`front/src` (`graphify extract --code-only`) ليساعد الفريق في استكشاف تبعيات الوحدات بسرعة.

## 7. صياغة الفريق أثناء العرض

صياغة دقيقة ممكن الفريق يستخدمها:

> استخدمنا **MkDocs (`--strict`)** لبناء دليل الفرق، و**FastAPI OpenAPI + Swagger UI** لتوليد عقود الـ64 endpoint مباشرة من DTOs (`export_openapi.py`)، و**مولد JUnit XML** (`generate_test_catalog.py`) لتوثيق 285 اختبارًا بنتائجها الفعلية، وعقود **Postman** للـSprint 1–3، و**WeasyPrint** لإنتاج أدلة PDF العربية، و**Graphify** لرسم خريطة الكود.

ده يوضح الأدوات اللي اشتغلت فعليًا، وما ينسبش كتابة قرارات الهندسة أو تنفيذ الاختبارات إلى Swagger أو Postman.
