# Unit Tests وIntegration Tests — إيه اللي اختبرناه؟

في المراجعة الحالية استبدلنا اختبارات Flask القديمة باختبارات للتطبيق الحالي FastAPI، وأضفنا اختبارات Sprint 3 للفرونت والباك والـproxy والعقود وإرسال البريد وبوابة `/admin`. النتائج الفعلية لكل مجموعة ولكل حالة موجودة في [الفهرس المولّد](test-catalog.md)، ومصدره تقارير JUnit من تشغيل الاختبارات.

نتيجة مراجعة **Sprint 3 (2026-11-25): 285 حالة ناجحة، صفر فشل وصفر تجاهل**. الباك **207** حالة: **55 Unit** و**152 Integration**. الفرونت **59** حالة: **49 Unit/Regression** و**10 Integration**. الوسيط **12** وعقود Postman **7** (إجمالي `npm test` = **78** حالة JS). تغطية كود الباك المقاسة **`91%`** (`5,263 / 5,754` سطرًا تنفيذيًا عبر `pytest --cov=app`)؛ هذه النسبة لا تعني اكتمال فحص الخدمات الحية.

## 1. الفرق ببساطة

**Unit Test** يختبر مسؤولية صغيرة وحدها مع بدائل للاعتماديات. مثلًا: رابط Paymob الخبيث لازم يُرفض، أو توقيع HMAC خاطئ لازم يفشل، أو حساب Decimal لازم يرجع النتيجة المحددة. الاختبار لا يحتاج تطبيق HTTP كاملًا ولا قاعدة بيانات فعلية.

**Integration Test** يختبر أجزاء حقيقية متصلة ببعض. في الباك مثلًا نرسل request إلى FastAPI، فيمر على router وDTO وservice وSQLAlchemy repository ثم قاعدة SQLite معزولة، ونراجع الاستجابة والبيانات المحفوظة. الهدف اكتشاف أخطاء حدود المعاملات والصلاحيات والـmapping التي لا تظهر باختبار دالة وحدها.

**End-to-End Test** يختبر رحلة من المتصفح عبر الخدمات المطلوبة. المجموعة الحالية لا تدّعي وجود رحلة آلية عبر Google الحقيقي أو Paymob الحقيقي أو قواعد الإنتاج. محاكاة حد HTTP في الفرونت واختبارات SQLite ليست E2E مع المزودين.

## 2. ليه نحتاج النوعين؟

مثال InstaPay يوضح الفرق: Unit Test ممكن يثبت أن قرار المراجعة اسمه `approve` أو `reject`. لكنه لن يكتشف وحده أن تحديث reference مكرر يتسبب في autoflush أثناء قراءة أخرى داخل SQLAlchemy. Integration Test يمر على الخدمة وقيد uniqueness الحقيقي، فيكشف هل الرد409 وهل المعاملة ترجع كما كانت.

ومثال الدفع: Unit Test يرفض دومين مشابه لـPaymob. Integration Test يثبت أن HTTP repository يقرأ `checkout_url` من envelope الصحيحة ويمرره لنفس validator، بدل أن يصلح validator وتظل الصفحة تستخدم مسارًا آخر.

## 3. الأدوات المستعملة

| الأداة | استخدامها الفعلي |
|---|---|
| pytest | تشغيل اختبارات Python، fixtures، markers وParameterized cases. |
| FastAPI TestClient | إرسال HTTP داخل العملية إلى التطبيق الحقيقي دون منفذ خارجي. |
| SQLite in-memory | قاعدة جديدة معزولة لكل حالة لتجربة المستودعات والقيود والمعاملات. |
| unittest.mock / monkeypatch | استبدال حد المزود أو الاعتماد والتحكم في الفشل والوقت والـresponses. |
| pytest-cov | قياس تنفيذ أسطر كود الباك أثناء المجموعة، وليس إثبات الصحة بمفرده. |
| Node test runner + assert | اختبارات JavaScript دون إضافة test framework خارجي. |
| Vite ssrLoadModule | تحميل ملفات TypeScript والـaliases نفسها المستخدمة في الفرونت للاختبار. |
| JUnit XML | صيغة تقرير يستخدمها مولد فهرس النتائج. |
| GitHub Actions | تشغيل الاختبارات والبناء وفحص Python عند push/PR إلى main. |

## 4. Unit Tests للباك بتعمل إيه؟

أمثلة من `back/tests/test_domain_units.py` وأجزاء `test_security.py` و`test_payments.py` الموسومة `unit`:

- **Money boundaries:** تجربة كسور وحدود التقريب باستخدام Decimal، حتى نثبت أن المال لا يعالج بحساب floating point.
- **Cart mapping:** سلة فارغة لا تُحصّل رسوم توصيل، وتوفر المتجر والمنتج ينعكس على العرض.
- **Confirmation transaction:** باستخدام UnitOfWork وsession issuer بديلين، نثبت أن commit لا يحصل إلا بعد نجاح إصدار الجلسة؛ الفشل يعمل rollback.
- **HMAC integrity:** تعديل amount بعد توقيع payload يجعل التحقق يفشل، والأنواع غير الصحيحة لا تتحول لنجاح مزيف.
- **Payment status parsing:** paid/refunded/pending/failure تستخرج بالقواعد المتوقعة، والمحاكاة محظورة في production.
- **Rate limiter adapter:** البديل يعيد تجاوز الحد، فينتج Retry-After الصحيح؛ فشل Redis يفشل بشكل مغلق ولا يحوّل الخدمة إلى مسار بلا حماية.

في الباك كل test لها marker واحدة فقط: `unit` أو `integration`. توجد حماية وقت collection ترفض الحالة غير المصنفة أو المصنفة بالنوعين؛ لذلك الفصل قابل للتشغيل وليس مجرد عنوان في README.

## 5. Integration Tests للباك بتعمل إيه؟

| المجموعة | السلوك الذي تتحقق منه |
|---|---|
| الحسابات | التسجيل برسالة عامة، منع التكرار، التطبيع، تأكيد البريد واستخدام الرمز مرة واحدة، إصدار جلسة browser، reset/revocation وrefresh/logout. |
| الملف والعناوين | تعديل البيانات، ملكية العنوان، الافتراضي وحدود القائمة، وعدم وصول مستخدم إلى عنوان غيره. |
| الكتالوج والمفضلة | قراءة عامة، فلاتر وpagination، وتغيير المفضلة دون تكرار bridge row. |
| السلال | استقلال متجرين لنفس الحساب، دمج إضافة نفس الصنف، صحة الكميات، منع صنف متجر آخر وعزل المستخدمين. |
| Checkout | عدم الثقة في مبلغ العميل، رفض revision/price قديمين، idempotency، نسخة تاريخية من المنتجات والعنوان، ومسح السلة المناسبة فقط. |
| الطلبات والعمليات | تاريخ طلبات مملوك، رفض الوصول غير المصرح، تسلسل المراحل، ومنع تحضير طلب إلكتروني غير مدفوع. |
| Paymob callback | توقيع ومطابقة المبلغ/العملة/Integration ID، منع replay، حماية paid من رد فشل متأخر، ورفض عملية واحدة لتسوية طلبين. |
| تجهيز الدفع | بنود تساوي الإجمالي، تشفير checkout token، إعادة استخدام جلسة قائمة، وتمييز رفض صريح عن حالة غير محسومة. |
| InstaPay | claim لا يساوي paid، مراجعة مخولة، ومنع استخدام نفس reference لدفع طلبين مع rollback واضح. |
| OAuth | رحلة provider بديل تنشئ عميلًا يحتاج استكمال بيانات، verifier مطلوب، state لا يعاد استخدامه، ولا ربط صامتًا لبريد حساب قائم. |
| حدود الأمان | JWT غير صحيح/منتهي/بسياق خاطئ، CORS وOrigin وHost، HTTP headers، وenvelope أخطاء لا يكشف مدخلات حساسة. |
| التوصيل والمندوب (`test_sprint3_delivery.py`) | تعيين وإعادة تعيين المندوب، عرض عنوان العميل الكامل وهاتفه للمندوب المعيّن فقط، انتقال `ready_for_pickup -> picked_up -> delivered`، ومنع اختطاف الطلب من مندوب آخر (`403`). |
| المطبخ والمطاعم (`test_sprint3_kitchen_and_restaurants.py`) | عزل بوابة المطبخ `/kitchen/orders`، إتمام التحضير، إضافة مطعم وأصناف منيو، وتعيين المحضّر والموظفين بنطاق `restaurant_staff`. |
| الإشعارات والاتساق (`test_sprint3_notifications_and_consistency.py`) | توليد الـ12 حدثًا بعد commit بأمان (دون تعطيل الطلب لو فشل الإشعار)، عزل `/notifications` لكل مستخدم، والإلغاء من العميل أو المدير. |
| الأدمن والهجرة (`test_sprint3_admin.py`) | إنشاء موظف مفعّل عبر `/admin/staff`، قراءة وتعديل الأدوار، إيقاف الجلسات، منع إسقاط الأدمن لنفسه (`409 cannot_demote_self`)، وتوافق `alembic head = 20261121_0006` + `seed_reference_data`. |
| تسليم البريد (`test_email_delivery.py`) | وحدة: توليد HTML Multipart وترويسات RFC 5322، تنظيف مسافات Gmail App Password، اكتشاف رفض المستلمين، تحذير DMARC عند استخدام `@gmail.com` مع Mailjet/Brevo، ومرسل `Resend` و`Brevo`. |

هذه الاختبارات تستخدم الراوترات والخدمات والمستودعات الفعلية. مزود OAuth والبريد وPaymob وrate limiter الخارجي لهم بدائل؛ لم يحدث تحصيل أو إرسال بريد إلى مستخدم أثناء المجموعة.

## 6. Unit Tests للفرونت بتعمل إيه؟

الملف `front/tests/frontend-regressions.test.mjs` يحتوي **49** حالة Regression/Unit. يختبر وحدات التطبيق مع بدائل للاعتماديات:

- قبول Paymob domains ومساراتها المحددة، ورفض HTTP والدومين المشابه وcredentials وfragment والمفاتيح المكررة/الفارغة والرابط المنتهي.
- حفظ المسار والـfragment عند تحويل localhost إلى 127، وتطبيع روابط البريد وOAuth إلى HashRouter.
- تجميع refresh المتزامن، ومنع response متأخر من مسح جلسة جديدة أو استعادة جلسة بعد clear/logout.
- منع إعادة request من حساب A تحت حساب B، وإعادة استخدام token مجدد للحساب نفسه.
- اعتماد جلسة تأكيد البريد والانتقال للموبايل ثم العنوان حسب البيانات الناقصة، وتوجيه الأدوار عند الدخول في `loginDestination`.
- verifier في OAuth، تنظيفه بعد الاستهلاك، ورفض وجهات authorization الخبيثة.
- رفض `quantity` غير صحيحة وتمرير `cart revision` و`idempotency key`.
- عدم عرض مرحلة تجهيز لطلب `cancelled` أو `awaiting_payment` أو حالة غير معروفة، وفصل انتقالات المدير والمحضّر والمندوب في `role stage helpers`.

الاختبارات تحمل TypeScript عبر Vite، لكنها لا ترسم React DOM ولا تضغط أزرارًا في متصفح. اختبار helper مرحلة الطلب يثبت قراره البرمجي؛ لا يثبت وحده تنسيق الزر على شاشة موبايل.

## 7. Integration Tests للفرونت بتعمل إيه؟

الملف `front/tests/frontend-integration.test.mjs` يركّب وحدات حقيقية مع بعض (**10** حالات)، وحد HTTP فقط له بديل:

| الحالة | الأجزاء المتصلة | النتيجة المطلوبة |
|---|---|---|
| تأكيد البريد | Auth repository + HTTP client + session manager + mapper + accountDestination. | POST للمسار الجديد، جلسة مقبولة، واستكمال الملف دون login جديد. |
| Access token انتهى | HTTP client + session manager الحقيقيان. | 401 ثم refresh واحد ثم retry بالـtoken الجديد. |
| سلتان لمتجرين | Cart repository + HTTP client + mapper. | IDs الصحيحة في الطلبات والنماذج، والمبالغ strings بلا تقريب. |
| Checkout | Use Case + order repository + HTTP client + mapper. | headers وsnake_case body وrevision صحيحة، وorder domain صحيح. |
| بدء Paymob | Payment repository + HTTP client + destination validator. | رابط وصلاحية صحيحتان، دون اتصال فعلي بـPaymob. |
| تعارض سعر | Order repository + HTTP error reader. | الاحتفاظ بكود الخطأ وrequest ID، وعدم عرض نص تشخيص خام. |
| الإلغاء وبيانات Sprint 3 | Order mapper + HTTP client. | قراءة العنوان المنظم ومعرفات المحضّر والمندوب ومعرف المعاملة وحالة الإلغاء. |
| بوابة المندوب (`DeliveryRepository`) | Delivery repository + HTTP client + mapper. | قراءة `/delivery/couriers` و`/delivery/my-orders` وتعيين/إعادة تعيين المندوب وتحديث `picked_up`/`delivered`. |
| الإشعارات والمطبخ والمنيو | Notification + Operations repositories + HTTP client. | قراءة صندوق `/notifications` وتحديد المقروء، وإنشاء مطعم وصنف، وتعيين المحضّر وتحديث `/kitchen/orders`. |
| بوابة الأدمن (`/admin`) | Operations repository + Admin DTOs + HTTP client. | تغطية `GET /admin/users` و`POST /admin/staff` و`PATCH /admin/users/{id}/roles`. |

## 8. الـproxy وPostman

**12 اختبارًا للـproxy:** نقل الفلاتر وheaders والكوكيز المتعددة، توقيع IP، رفض origins غير آمنة وطرق ومسارات غير صالحة، حد body، رفض redirect غير متوقع، وتوحيد خطأ انقطاع الباك. الـfetch الخارجي مستبدل؛ هذه فحوص معزولة لوظيفة الوسيط.

**7 اختبارات عقود Postman:** بادئة `/api/v1` مرة واحدة عبر مجموعات Sprint 1 وSprint 2 وSprint 3 (`Foodify.Sprint3.postman_collection.json`)، `base_url` موحدة كأصل، browser verification بالـheaders الصحيحة، متغيرات credentials، والتحقق من تغطية مسارات `/admin/staff` و`/kitchen/orders` و`/delivery/my-orders` و`/notifications`. هذه فحوص لصحة ملفات العقد؛ لا ترسل طلبات حقيقية من Postman.

## 9. تشغيل المجموعات

من جذر المشروع، بعد تثبيت Node dependencies بـ`npm --prefix front ci`:

```bash
npm test
```

الأمر يشغّل proxy والعقود وجميع اختبارات الفرونت. **لا يشغّل Python**؛ الباك له أمره المستقل:

```bash
cd back
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q -m unit
.venv/bin/python -m pytest -q -m integration
```

من جذر المشروع، لتشغيل كل طبقة فرونت منفردة:

```bash
npm --prefix front run test:unit
npm --prefix front run test:integration
npm run test:proxy
npm run test:contracts
```

أوامر `build:test` و`dev:test` تختار بيئة Vite، وليست أوامر تشغيل اختبارات. Typecheck والبناء فحوص إضافية:

```bash
npm run typecheck
npm --prefix front run build:test
npm run build
```

## 10. تقارير قابلة لإعادة التوليد

من جذر المشروع، جهز `output/verification` ثم شغّل:

```bash
mkdir -p output/verification
cd back
.venv/bin/python -m pytest -q -m unit --junitxml=../output/verification/backend-unit.xml
.venv/bin/python -m pytest -q -m integration --junitxml=../output/verification/backend-integration.xml
cd ../front
node --test --test-reporter=junit --test-reporter-destination=../output/verification/frontend-unit.xml tests/frontend-regressions.test.mjs
node --test --test-reporter=junit --test-reporter-destination=../output/verification/frontend-integration.xml tests/frontend-integration.test.mjs
cd ..
node --test --test-reporter=junit --test-reporter-destination=output/verification/proxy.xml tests/proxy.test.mjs
node --test --test-reporter=junit --test-reporter-destination=output/verification/contracts.xml tests/postman.test.mjs
python scripts/generate_test_catalog.py
.venv-docs/bin/python -m mkdocs build --strict
```

ضع options الخاصة بـNode قبل أسماء ملفات الاختبارات، حتى تُقرأ كخيارات للـrunner. المولد يحتاج تقارير المجموعات الست كلها، ولا يحوّل غياب تقرير إلى نجاح.

## 11. العزل وحدود النتيجة

الاختبارات الآلية لا تقرأ `.env` ولا تتصل بقاعدة التطوير أو الإنتاج. كل حالة باك تبدأ بـSQLite داخل الذاكرة، مع foreign keys مفعلة وبيانات مخصصة؛ اتصالات socket الخارجية محظورة. ده يحمي البيانات ويجعل الحالات قابلة للتكرار.

لكن SQLite لا تطابق MySQL في row locking وcollation وDDL وسلوك الحمل المتزامن. ولم تُشغَّل رحلة بطاقة أو Google/Facebook أو SMTP حقيقية ضمن هذه المجموعة. هذه حدود معلنة، وليست نتائج ناجحة مستنتجة من Build أو coverage.

رقم coverage يوضح الأسطر التي نُفّذت، وليس نسبة الأمان أو ضمان عدم وجود أخطاء. لا توجد قاعدة أن100% coverage تعني100% صحة. عند تغير الكود يجب إعادة الاختبارات؛ [الفهرس](test-catalog.md) يصف التشغيل الذي ولّد التقرير فقط.
