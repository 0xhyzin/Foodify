# Sprint 2 — المراجعة النهائية والاختبارات

تاريخ النتائج: **2026-11-03**. هذا التقرير يصف تشغيل الاختبارات والبناء على التغييرات المحلية الحالية. نتائج النشر القديمة في 2026-10-31 سجل تاريخي مستقل، ولا تثبت أن إصلاحات هذه المراجعة منشورة.

## 1. نتيجة الاختبارات الفعلية

| المجموعة | الحالات الناجحة | فاشل | متجاهل |
|---|---:|---:|---:|
| Backend Unit | 37 | 0 | 0 |
| Backend Integration | 135 | 0 | 0 |
| Frontend Unit / Regression | 48 | 0 | 0 |
| Frontend Integration | 6 | 0 | 0 |
| Vercel proxy handler | 12 | 0 | 0 |
| Postman contract checks | 5 | 0 | 0 |
| **الإجمالي** | **243** | **0** | **0** |

اختبارات الباك الكاملة: **172 passed** في نحو47 ثانية. التغطية المقاسة لكل `back/app` هي **89.41%**: نُفّذت4003 أسطر تنفيذية من4477. النسبة لا تمثل فحص اختراق أو شهادة أمان أو نجاح الخدمات الخارجية.

نتائج `deselected` عند اختيار marker واحدة تعني استبعاد المجموعة الأخرى من هذا الأمر فقط؛ بعد تشغيل المجموعتين لم تبق حالة غير منفذة أو skipped.

- [شرح وظيفة كل مجموعة والفرق بين Unit وIntegration](teams/testing.md).
- [فهرس كل حالة ونتيجتها المولّد من تقارير JUnit](teams/test-catalog.md).
- [نتائج منظمة JSON](teams/assets/test-results.json).

## 2. ماذا حدث للاختبارات القديمة؟

كانت ملفات `back/tests` تستورد Flask و`create_app, db` بعقد قديم، وبالتالي لم تكن تختبر FastAPI الحالي. استُبدلت بحالات على HTTP contracts والخدمات والمستودعات الحالية، مع fixtures مستقلة وبيانات صناعية وmarkers صريحة ومتبادلة الاستبعاد.

التجهيز يحظر اتصالات socket، ولا يقرأ `.env`، وينشئ SQLite داخل الذاكرة مع foreign keys لكل حالة. لا يتصل بقاعدة التطوير أو الإنتاج، ولا ينفذ إرسال بريد أو تحصيلًا ماليًا. Unit Tests تختبر وحدات ببدائل، وIntegration Tests تربط أجزاء حقيقية من التطبيق مع حدود خارجية مستبدلة.

الفرونت يستخدم Node test runner وVite loader الموجود بالفعل؛ لا توجد حاجة إلى Jest/Vitest أو اعتماديات إضافية للتشغيل الحالي. أضيفت6 حالات ربط للـHTTP client والمستودعات والـmappers والجلسة بجانب48 حالة Regression/Unit.

## 3. الأعطال التي اكتُشفت وأُصلحت

| العطل | الإصلاح والدليل |
|---|---|
| واجهة العمليات تعرض بدء تجهيز لحالة ملغاة/غير مدفوعة | `nextOrderStage` يرجع نتيجة فقط للمراحل النشطة، مع regression للحالات الملغاة وغير المعروفة. |
| رد Paymob يبدو ناجحًا لكن intention ID فارغة أو provider order ID غير موجب | رفض الرد كـ`payment_initialization_unknown` دون حفظ جلسة غير صالحة أو تكرار إنشائها. |
| مراجعة InstaPay بنفس مرجع بنك مستعمل ترجع503 بسبب autoflush | فحص قيد uniqueness بواسطة `UnitOfWork.flush` قبل استعلام التسوية؛ الرد409 وrollback يبقي الطلب الثاني غير مدفوع. |
| Postman Sprint2 يرجع404 مع environment الحسابات | توحيد `base_url` إلى الأصل فقط وإضافة `/api/v1` داخل كل طلب؛5 اختبارات للعقود. |
| مصدر Python dependencies يختلف بين Docker وCloud packaging | `pyproject.toml` يقرأ `requirements.lock.txt` نفسها المستخدمة في Docker؛ ملف الاختبارات يعيد استخدامها. |

المراجعة تشمل أيضًا إصلاحات الدفع والجلسة السابقة: browser email confirmation تصدر جلسة وتفتح استكمال البيانات، أصل التطوير موحّد حتى لا يضيع OAuth verifier، refresh متأخر لا يكتب فوق جلسة أحدث، وفشل إنشاء دفع غير محسوم لا يؤدي إلى إنشاء عملية أخرى تلقائيًا. اختبارات هذه المسارات موجودة ضمن النتائج أعلاه.

## 4. فحوص البناء والتوثيق

| الفحص | النتيجة |
|---|---|
| TypeScript typecheck | ناجح. |
| Vite build:test | ناجح؛ هذا بناء لبيئة test، وليس تشغيل اختبار. |
| Vite build:production | ناجح. |
| Python compileall للتطبيق والسكربتات والمigrations | ناجح. |
| Offline backend wheel | Swagger JavaScript وملفا الكتالوج موجودة، ولا توجد ملفات `.env`؛71 اعتمادًا مثبت الإصدار في metadata. |
| OpenAPI export من التطبيق |44 path مولّدة إلى ملف JSON دون تشغيل DB أو شبكة. |
| MkDocs build --strict | ناجح، دون روابط داخلية ناقصة في دليل التيمات. |
| git diff --check | ناجح. |

أضيف تشغيل اختبارات JavaScript وPython وبناء التوثيق إلى GitHub Actions. هذا يصف ملف CI المجهز محليًا؛ تشغيل GitHub نفسه يحتاج دفع التغييرات، ولم تُفترض له نتيجة ناجحة لم تحصل.

## 5. أوامر إعادة التشغيل

من جذر المشروع:

```bash
npm --prefix front ci
npm test
npm run typecheck
npm --prefix front run build:test
npm run build
cd back
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q -m unit
.venv/bin/python -m pytest -q -m integration
```

لقياس التغطية من `back`:

```bash
.venv/bin/python -m pytest -q --cov=app --cov-report=term:skip-covered
```

للبناء من جذر المشروع:

```bash
back/.venv/bin/python scripts/export_openapi.py
.venv-docs/bin/python -m mkdocs build --strict
```

تجهيز بيئة MkDocs موثق في [أدوات التوثيق](teams/documentation.md)، وتوليد تقارير JUnit الست والفهرس في [شرح الاختبارات](teams/testing.md).

## 6. حدود المراجعة الحالية

- SQLite لا تثبت row locking أو MySQL migration DDL أو concurrency تحت حمل فعلي؛ `Base.metadata.create_all` في fixtures ليست `alembic upgrade` على MySQL.
- Redis بديل داخل HTTP tests، ووحدات rate limiter تستخدم Fake Redis؛ لم ينفذ هذا الاختبار Lua الحقيقي داخل Valkey.
- OAuth ومزود الدفع والبريد لها بدائل؛ لا تدعي النتائج تسجيل Google/Facebook بحساب حقيقي أو تسليم Mailjet أو دورة Paymob Sandbox خارجية.
- اختبارات الفرونت الحالية لا ترسم React DOM في متصفح. فحوص الواجهة اليدوية السابقة مسجلة كتاريخ، وليست نتيجة تشغيل E2E جديد هنا.
- السيرفر المحلي لم يكن يستمع على8000 عند فحص هذه الجولة، وصلاحية Docker socket غير متاحة؛ لم نعد بناء الحاويات، ولم نعتبر اختبار TestClient تشغيلًا للنسخة المنشورة أو Docker.
- لم تُطبّق migrations على قاعدة بعيدة ولم تُنشر إصلاحات هذه المراجعة ضمن إعداد التوثيق والاختبارات.

## 7. ملفات الشرح المطلوبة

- [دليل التيمات الشامل](teams/index.md).
- [Frontend بالعربي](teams/frontend.md).
- [Backend in English](teams/backend.md) و[مرجع التنفيذ بالإنجليزي](../back/README_SPRINT_2.md).
- [Integration بالعربي](teams/integration.md) و[مرجع الربط التفصيلي](SPRINT_2_INTEGRATION.md).
- [Deployment بالعربي](teams/deployment.md) و[خطوات النشر التفصيلية](SPRINT_2_DEPLOYMENT.md).
- [الاختبارات بالعربي](teams/testing.md).
- [أدوات التوثيق واستخدامها الفعلي](teams/documentation.md).
