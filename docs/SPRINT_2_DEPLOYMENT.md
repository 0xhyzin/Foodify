# شرح Deployment لسبرينت 2

هذا الملف يشرح تشغيل ونشر Sprint 2 من نسخة المشروع الموجودة في المستودع: الكتالوج، سلة مستقلة لكل مطعم أو متجر، العناوين، الطلبات، متابعة الطلب، قائمة طلبات المطعم، والدفع. أسماء الخدمات أدناه هي توزيع الاستضافة الذي يعتمد عليه المشروع؛ وجود الرابط في هذا الملف لا يثبت أن آخر تعديل محلي نُشر عليه.

لشرح الربط بين الواجهة والباك راجع [Sprint 2 Integration](SPRINT_2_INTEGRATION.md)، ولشرح الباك بالإنجليزية راجع [Backend Sprint 2](../back/README_SPRINT_2.md)، ولشرح الواجهة بالعربية راجع [Frontend Sprint 2](../front/README_SPRINT_2.md). الدليل العام للإعدادات موجود في [DEPLOYMENT.md](DEPLOYMENT.md).

## 1. كل جزء يُنشر أين، ولماذا؟

| الجزء | مكان التشغيل | وظيفته في Sprint 2 |
|---|---|---|
| React + TypeScript + Vite | Vercel | عرض بيانات المتاجر والسلال والطلبات، وجمع اختيارات المستخدم. |
| `api/proxy.mjs` | Vercel Function | تمرير `/api/v1/*` إلى الباك مع Authorization والكوكيز و`Idempotency-Key`. |
| FastAPI | FastAPI Cloud | التحقق من المستخدم والصلاحيات، حساب المبالغ، حفظ الطلب، والتعامل مع Paymob. |
| MySQL | Aiven | المصدر الفعلي للحسابات والعناوين والمتاجر والمنتجات والسلال والطلبات والمدفوعات. |
| Valkey | Aiven | عدادات Rate Limiting المشتركة بين عمليات الباك. |
| Mailjet SMTP | خدمة بريد خارجية | إرسال التأكيد واستعادة كلمة المرور من Email Outbox. |
| Paymob | Hosted Checkout خارج الموقع | إدخال بيانات البطاقة أو استكمال عملية المحفظة، ثم إرسال نتيجة موثقة للباك. |

```text
المتصفح → Vercel React → /api/v1/* → Vercel Proxy → FastAPI Cloud
                                                       ├─ MySQL / Aiven
                                                       ├─ Valkey / Aiven
                                                       ├─ Outbox Worker → Mailjet
                                                       └─ Paymob Intention API
المتصفح ← رابط Checkout من الباك → صفحة Paymob
Paymob → POST callback موقّعة → الباك → تحديث الدفع والطلب في MySQL
المتصفح ← صفحة الطلب ← يقرأ حالة الطلب من الباك
```

الواجهة لا تتصل بـ MySQL، ولا تحفظ كتالوج المطاعم باعتباره المصدر الأساسي. ملف `back/app/ordering/data/demo-catalog.json` مدخل لسكربت يكتب البيانات في MySQL. بعد ذلك تقرأ React الكتالوج عبر API.

## 2. البيئات الثلاث

| البيئة | إعداد الباك | إعداد الواجهة | الاستخدام |
|---|---|---|---|
| Development | `back/.env.development` | `front/.env.development` | Docker محلي وMailpit وPaymob Test عند إعداد مفاتيحه. |
| Test runtime | `back/.env.test` | `front/.env.test` | تشغيل تطبيق مستقل على MySQL منفصلة، ببيانات وأسرار مخصصة للتجربة. |
| Production | متغيرات FastAPI Cloud، وملف محلي خاص عند إدارة migration | متغيرات Vercel | HTTPS والخدمات الخارجية وقاعدة الإنتاج. |

يقرأ الباك `APP_ENV`، ثم `.env.<environment>` و`.env.payments.<environment>` إن وُجدا. متغيرات العملية تتقدم على ملفات الإعداد. لا تبدّل `APP_ENV` فقط مع الإبقاء على روابط قاعدة الإنتاج أثناء الاختبار. منفذ بيئة Test في القالب هو `8001`؛ راجع رابط API في ملف الواجهة الخاص بها.

تشغيل Test runtime يختلف عن مجموعة `pytest` الآلية: الاختبارات تنشئ إعدادات معزولة دون قراءة `.env`، وتستخدم SQLite في الذاكرة مع بدائل للخدمات الخارجية ومنع اتصالات الشبكة. هذه المجموعة لا تتصل بـ MySQL الخاصة ببيئة Test ولا بقاعدة الإنتاج؛ لذلك لا تثبت وحدها سلوك أقفال MySQL أو migrations عليها أو إكمال Paymob وOAuth والبريد لدى المزود الحقيقي.

## 3. التشغيل المحلي من البداية

الأوامر التالية من مجلد المشروع الفعلي `/home/hyzin/Projects/Foodify`. إذا كان المشروع عندك في مسار آخر، استخدم مساره. لا تنسخ القوالب فوق ملفات إعداد موجودة تحتوي قيمك.

### تجهيز الملفات

انسخ مرة واحدة، فقط إذا كانت الملفات غير موجودة:

```bash
cd /home/hyzin/Projects/Foodify/back
cp .env.development.example .env.development
cp .env.payments.example .env.payments.development
```

عدّل `.env.development` محليًا: أنشئ قيمًا مستقلة لـ `MYSQL_PASSWORD` و`MYSQL_ROOT_PASSWORD` و`JWT_SECRET` و`EMAIL_ENCRYPTION_KEY`. اجعل كلمة مرور `DATABASE_URL` مساوية لكلمة مرور مستخدم التطبيق `MYSQL_PASSWORD` عند تشغيل Python خارج Docker. داخل Compose يُبنى رابط قاعدة البيانات تلقائيًا باسم الخدمة `mysql`.

انسخ `front/.env.development.example` إلى `front/.env.development` إن لم يكن موجودًا. القيم المناسبة للواجهة المحلية هي:

```dotenv
VITE_APP_ENV=development
VITE_DATA_SOURCE=api
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

يكون `FRONTEND_URL=http://127.0.0.1:5173` في الباك. افتح الواجهة بهذا العنوان نفسه؛ الواجهة تحوّل `localhost:5173` إلى `127.0.0.1:5173` في Development قبل بدء الجلسة، حتى يبقى OAuth verifier في أصل المتصفح نفسه.

### تشغيل البيانات ثم migrations والكتالوج

```bash
cd /home/hyzin/Projects/Foodify/back
docker compose --env-file .env.development up -d mysql redis mailpit
docker compose --env-file .env.development run --build --rm api python -m scripts.release
docker compose --env-file .env.development run --rm api python -m scripts.seed_catalog
docker compose --env-file .env.development up -d --build api email-worker
```

`release` ينتظر اتصال MySQL ثم ينفذ `alembic upgrade head` ويجهز الأدوار والصلاحيات وأنواع التوكنات. `seed_catalog` يزامن البيانات التجريبية المعتمدة بمعرّفات ثابتة: 8 متاجر و24 منتجًا و16 تصنيفًا. السكربت يوقف الكتابة إذا كانت migrations غير متوافقة، ويحدّث بيانات المتاجر التجريبية التي يديرها فقط.

Compose يستخدم MySQL وRedis وMailpit محليًا. خدمة `email-worker` ترسل إلى Mailpit، الذي يعرض البريد على `http://127.0.0.1:8025`. لا تضف Mailjet إلى تجربة Docker العادية؛ إعداد Compose يوجه البريد إلى Mailpit عمدًا.

### تشغيل الواجهة

المشروع يشترط Node.js `>=22.12` في `package.json`.

```bash
cd /home/hyzin/Projects/Foodify
npm --prefix front ci
npm run dev
```

افتح [الواجهة المحلية](http://127.0.0.1:5173)، و[Swagger المحلي](http://127.0.0.1:8000/docs)، و[Mailpit](http://127.0.0.1:8025). Swagger مخصص للتطوير؛ قد يكون معطلًا في الإنتاج.

### تطبيق تعديل لاحق

عند تعديل الباك، ابنِ صورة API الجديدة وشغّلها. إذا تغيّر كود عامل البريد، أعد بناءه أيضًا. عند إضافة migration، نفذ `scripts.release` قبل تشغيل النسخة التي تعتمد عليها:

```bash
cd /home/hyzin/Projects/Foodify/back
docker compose --env-file .env.development run --build --rm api python -m scripts.release
docker compose --env-file .env.development up -d --build api email-worker
```

Vite يعرض تعديلات الواجهة أثناء `npm run dev`. عند تغيير `.env` الخاص بالواجهة أوقف Vite وشغله مجددًا. `docker compose down` يوقف الحاويات مع الاحتفاظ بالـ named volumes؛ حذف volumes يحذف البيانات، ولذلك لا يدخل ضمن تحديث التطبيق.

## 4. تجهيز الإنتاج قبل رفع الكود

قالب الخدمة الحالية هو `back/.env.free.example`. الاسم لا يضمن بقاء أي خطة مجانية؛ راجع حدود حسابك لدى كل مزود. `back/.env.production.example` قالب إنتاج عام أيضًا، لكنه ليس ملفًا جاهزًا للرفع بقيم الأمثلة.

| مجموعة الإعداد | أهم المتغيرات | مكانها |
|---|---|---|
| البيئة | `APP_ENV=production`, `DEBUG=false`, `DOCS_ENABLED=false` | FastAPI Cloud |
| العناوين | `PUBLIC_BASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS`, `TRUSTED_HOSTS` | FastAPI Cloud |
| MySQL | `DATABASE_URL`, `DATABASE_TLS_REQUIRED=true`, `DATABASE_SSL_CA_PEM` | أسرار الباك |
| migration | `MIGRATION_DATABASE_URL` | جهاز أو مهمة الإصدار فقط، بحساب schema منفصل |
| Valkey | `REDIS_URL=rediss://...` | أسرار الباك |
| الجلسات | `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`, `BROWSER_COOKIE_SAME_SITE=lax` | الباك؛ JWT Secret سر |
| التشفير | `EMAIL_ENCRYPTION_KEY` | أسرار الباك |
| الوسيط | `FRONTEND_PROXY_SECRET` | السر نفسه في Vercel وFastAPI Cloud |
| البريد | `EMAIL_PROVIDER=smtp`, إعدادات Mailjet، `EMBEDDED_EMAIL_WORKER=true` | FastAPI Cloud |
| OAuth | Client ID وSecret وRedirect URI لكل مزود مفعّل | الباك ولوحة مزود OAuth |
| الدفع | مفاتيح Paymob وIntegration IDs ووضع التشغيل | الباك فقط |

صيغة رابط MySQL التي يقبلها الكود هي `mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE?charset=utf8mb4`؛ رمّز الرموز الخاصة في كلمة المرور داخل URL. رابط Aiven الذي يبدأ بـ `mysql://` لا يُنسخ كما هو إلى `DATABASE_URL`. الخادم يتحقق من شهادة CA، فلا تستبدل التحقق من TLS بتعطيله. `DATABASE_POOL_SIZE=2` و`DATABASE_MAX_OVERFLOW=1` نقطتا بداية موجودتان في قالب Aiven؛ عدّلهما وفق حدود قاعدة بياناتك.

اجعل مستخدم التشغيل محدود الصلاحيات، ومستخدم migration قادرًا على تغييرات schema. يجب أن يشيرا إلى قاعدة البيانات نفسها؛ حساب `avnadmin` ليس حساب التشغيل المقترح. لا تعرض URI يحتوي كلمة مرور في السجلات أو لقطات الشاشة.

في Mailjet: المضيف `in-v3.mailjet.com` والمنفذ `587`، و`SMTP_USE_TLS=true` و`SMTP_USE_SSL=false`. ضع API Key في `SMTP_USERNAME` وSecret Key في `SMTP_PASSWORD`، وعنوان مرسل موثّق في `SMTP_FROM_EMAIL`. في الإنتاج العامل المدمج يعالج Email Outbox؛ قبول طلب التسجيل لا يثبت وصول البريد إلى Inbox. راجع أحداث البريد عند الحاجة. [إعداد SMTP الرسمي في Mailjet](https://documentation.mailjet.com/hc/en-us/articles/360043227473-How-to-configure-my-SMTP-settings).

## 5. ترتيب إصدار Sprint 2

نفّذ الترتيب التالي عند نشر التغيير، بعد مراجعة الكود وتشغيل الفحوص:

1. احتفظ بمعرّف commit السابق، ونسخة قاعدة بيانات قابلة للاستعادة، وإعدادات البيئة في مكان آمن.
2. جهز أسرار MySQL وValkey والبريد وPaymob وعناوين callback.
3. طبّق migrations على قاعدة البيئة المقصودة باستخدام نسخة الباك التي ستنشرها.
4. زامن الكتالوج عند الحاجة، ثم تحقق من البيانات.
5. انشر الباك وتحقق من جاهزية schema والخدمات.
6. انشر الفرونت المتوافق، ثم راجع الرحلة من المتصفح.

### migrations والكتالوج

من مجلد `back/` وفي بيئة Python معزولة ثبّت الاعتماديات المثبتة في lockfile. وجود Python `>=3.12` مطلوب وفق `pyproject.toml`؛ صورة Docker المرفقة تستخدم Python 3.14.

```bash
cd /home/hyzin/Projects/Foodify/back
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
```

جهّز `.env.production` محليًا من قالب الإنتاج المناسب، بالقيم الفعلية وحسابي التشغيل والتهيئة. لا تضف هذا الملف إلى Git. الأوامر التالية تتصل بقاعدة الإنتاج وتكتب فيها، لذلك تُنفذ في خطوة الإصدار المقصودة بعد النسخ الاحتياطي:

```bash
APP_ENV=production alembic heads
APP_ENV=production alembic current
APP_ENV=production python -m scripts.release
```

الرأس الموجود في نسخة Sprint 2 هو `20261031_0005`. المرجع الدائم عند إضافة تغييرات لاحقة هو ناتج `alembic heads` للنسخة التي تُنشر، وليس رقمًا منسوخًا من مستند قديم. `scripts.release` لا يزرع المطاعم تلقائيًا؛ يحتاج الكتالوج الأمر المنفصل التالي عند اعتماد بيانات العينة للإنتاج:

```bash
APP_ENV=production FOODIFY_ALLOW_DEMO_CATALOG_SEED=true \
  python -m scripts.seed_catalog --allow-production
```

الشرطان يمنعان زرع البيانات التجريبية في الإنتاج بالخطأ. راجع [Demo Catalog](../back/docs/DEMO_CATALOG.md). السكربت لا يحذف حسابات أو طلبات، لكنه يعطّل أصناف العينة القديمة والمتاجر التجريبية المتقاعدة التي يديرها ويحدث الأسعار المعتمدة؛ لذلك لا تستخدمه باعتباره أداة إدارة عامة لبيانات عملاء حقيقيين.

### نشر الباك

تعتمد صورة Docker والتجهيز المحلي على `requirements.lock.txt`. عُدّل `pyproject.toml` أيضًا ليقرأ الاعتماديات الديناميكية من الملف نفسه، فأصبح مسار تثبيت حزمة الباك يستخدم الإصدارات المثبتة نفسها. لا يحتاج هذا إلى افتراض اكتشاف FastAPI Cloud لاسم lockfile المخصص؛ المرجع هو إعداد الحزمة. بعد نشر إصدار جديد راجع سجل البناء وآلية التثبيت والإصدارات الفعلية، لأن تغيير الملف محليًا لا يثبت أن إصدار السحابة أُعيد بناؤه. [توثيق تثبيت الاعتماديات](https://fastapicloud.com/docs/builds-and-deployments/install-dependencies/).

من مجلد `back/` سجّل الدخول ثم اربط التطبيق الموجود إذا كانت هذه نسخة clone جديدة لا تحتوي ربطًا محليًا:

```bash
fastapi login
fastapi cloud link
fastapi deploy
```

تختار `foodify-api` عند الربط بدل إنشاء خدمة ثانية. نقطة الدخول الفعلية محددة في `back/pyproject.toml`: `app.hosted:app`. هذا المدخل يشغّل API والعامل المدمج عند تفعيله؛ لا ينفذ migration أو seed تلقائيًا. الملف `scripts/hosted_start.py` مسار تشغيل مختلف موجود في المستودع، وليس نقطة الدخول الحالية لـ FastAPI Cloud.

القيم السرية تُضاف في Environment Variables لدى FastAPI Cloud، ثم تعاد عملية النشر لتستخدم القيم الجديدة. يرفع `fastapi deploy` المجلد الحالي؛ لذلك نفذه من `back/`. يحتفظ `.fastapicloud/` بالربط المحلي وهو مستثنى من Git. [أمر النشر](https://fastapicloud.com/docs/fastapi-cloud-cli/deploy/)، [ربط تطبيق موجود](https://fastapicloud.com/docs/fastapi-cloud-cli/link/)، [متغيرات البيئة وإعادة النشر](https://fastapicloud.com/docs/builds-and-deployments/environment-variables/).

### نشر الفرونت

Vercel يقرأ `vercel.json` من جذر المستودع، لأن `api/proxy.mjs` خارج مجلد `front/`. إعدادات المشروع:

| إعداد Vercel | القيمة |
|---|---|
| Root Directory | جذر المستودع |
| Install Command | `npm --prefix front ci` |
| Build Command | `npm run build` |
| Output Directory | `front/dist` |
| `FOODIFY_API_ORIGIN` | `https://foodify-api.fastapicloud.dev`، دون `/api/v1` |
| `FRONTEND_PROXY_SECRET` | مطابق لسر الباك |
| `VITE_APP_ENV` | `production` |
| `VITE_DATA_SOURCE` | `api` |
| `VITE_API_BASE_URL` | `/api/v1` |

`npm run build` في الجذر يستدعي `build:production` في الفرونت. متغيرات `VITE_*` تصبح جزءًا من ملفات المتصفح؛ لا تحتوي كلمات مرور أو Secret Keys. يحدد وسيط Vercel عنوان الباك من متغير خادم، ولا يأخذ وجهة الاتصال من المستخدم. بعد رفع commit إلى الفرع الموصول بـ Production تابع نتيجة النشر في Vercel، وأعد النشر عند تعديل المتغيرات. [مرجع إعداد Vercel](https://vercel.com/docs/projects/project-configuration).

## 6. الجلسات وروابط البريد وOAuth

طلبات الإنتاج تخرج إلى `/api/v1` على نطاق Vercel، ثم يمرر الوسيط Authorization و`Set-Cookie`. Refresh Token داخل HttpOnly Cookie؛ Access Token تستخدمه الواجهة لطلبات Bearer. `FRONTEND_PROXY_SECRET` يسمح للباك بالتحقق من توقيع عنوان العميل المستخدم في Rate Limiting. لا تعالج خطأ كوكيز بتوسيع CORS إلى `*`؛ راجع الأصل الفعلي و`credentials` وإعداد SameSite وتمرير الكوكيز.

روابط البريد تُبنى من `FRONTEND_URL`، ومنها `/verify-email#token=...` و`/reset-password#token=...`. يعيد Vercel المسارين إلى SPA، ثم تحولهما الواجهة إلى HashRouter. بعد تأكيد البريد يستخدم الفرونت `POST /api/v1/auth/browser/verify-email` لإنشاء الجلسة وتوجيه المستخدم لاستكمال بياناته. لا تتوقع تسجيلًا تلقائيًا إذا استدعيت مسار التأكيد القديم الذي يعيد رسالة فقط.

عناوين OAuth للإنتاج تُسجل حرفيًا لدى Google وFacebook، ويطابق كل منها متغير Redirect URI في الباك:

```text
https://foodify-api.fastapicloud.dev/api/v1/auth/oauth/google/callback
https://foodify-api.fastapicloud.dev/api/v1/auth/oauth/facebook/callback
```

العودة الأولى تكون إلى الباك، ثم إلى `/oauth/callback` في الواجهة مع ticket قصير الصلاحية، ثم تستبدله الواجهة بجلسة عبر مسار browser. على الجهاز المحلي، مثال قالب Google هو `http://localhost:8000/api/v1/auth/oauth/google/callback`، بينما `FRONTEND_URL` للواجهة هو `http://127.0.0.1:5173`. سجل callback المحلي نفسه لدى Google عند استخدامه؛ لا تستبدله بعنوان الواجهة أو رابط سياسة الخصوصية. لا تنتقل بين أصول واجهة مختلفة في منتصف OAuth لأن verifier محفوظ في `sessionStorage` للأصل الذي بدأ الرحلة.

## 7. إعداد Paymob والرجوع إلى الطلب

في `.env.payments.development` محليًا أو أسرار FastAPI Cloud عند النشر، جهز:

| المتغير | المعنى |
|---|---|
| `PAYMOB_SECRET_KEY` | Secret Key لاستدعاء Intention API من الباك. |
| `PAYMOB_PUBLIC_KEY` | Public Key للرابط المستضاف الذي يبنيه الباك. |
| `PAYMOB_HMAC_SECRET` | التحقق من توقيع نتيجة الدفع. |
| `PAYMOB_CARD_INTEGRATION_ID` | تكامل البطاقة الخاص بالحساب والبيئة. |
| `PAYMOB_WALLET_INTEGRATION_ID` | تكامل Mobile Wallets؛ التفعيل الفعلي لدى Paymob يحدد المحافظ المتاحة. |
| `PAYMOB_LIVE` | `false` لمفاتيح Test و`true` لمفاتيح وIDs الـ Live معًا. |

الأماكن تختلف حسب لوحة Paymob، لكن عادة تجد المفاتيح تحت Developers → API Keys، والتكاملات تحت Developers → Payment Integrations. يجب أن ينتمي Integration ID للحساب نفسه ويطابق Test/Live. الكود يستخدم Intention API؛ قيمة API Key القديمة وحدها ليست بديلًا لـ Secret Key. [Create Intention وإعداد التكامل](https://developers.paymob.com/paymob-docs/intention-apis/create-intention).

`GET /api/v1/payments/methods` يعرض المتاح وفق إعدادات الباك، لذلك لا تُفعّل البطاقة شكليًا في React. بعد إنشاء الطلب ترسل الواجهة `POST /api/v1/orders/{order_id}/payment`، فيبني الباك مبالغ القروش من بيانات MySQL، ثم يعيد رابط `https://eg.checkout.paymob.com/` الذي يحتوي رمز checkout الخاص بهذه العملية. صفحة Paymob تستقبل بيانات البطاقة؛ التطبيق لا يجمع PAN أو CVV أو OTP.

| العنوان | وظيفته |
|---|---|
| `https://foodify-api.fastapicloud.dev/api/v1/payments/paymob/callback` | Processed Callback؛ Paymob يرسل إليه POST وتوقيع HMAC. |
| `https://foodify-api.fastapicloud.dev/api/v1/payments/return/{order_id}` | Response/Return URL؛ الباك يضع Order ID الفعلي أثناء إنشاء Intention. |
| `https://foodify-flax.vercel.app/#/orders/{order_id}` | صفحة المستخدم بعد الرجوع؛ تقرأ الحالة من API. |

يضبط الباك `notification_url` و`redirection_url` لكل Intention. إذا طلبت لوحة Paymob قيم callback للتكامل، اجعل Processed Callback مسار POST أعلاه؛ مسار العودة يحتوي Order ID ويولده الكود لكل طلب، فلا تضع قيمة `{order_id}` الحرفية في لوحة الخدمة. لا تضبط Response URL على مسار Processed Callback.

فتح صفحة البطاقة محليًا ممكن باستخدام مفاتيح Test، لكن Paymob لا يستطيع إرسال callback إلى `localhost` أو `127.0.0.1` على جهازك. لإكمال الرحلة محليًا استخدم HTTPS tunnel موثوقًا إلى الباك واضبط `PUBLIC_BASE_URL` على عنوانه وحدث `TRUSTED_HOSTS`. إذا كانت الواجهة HTTP المحلية والـAPI أصبحت HTTPS، فإن Secure/SameSite cookies تحتاج أصل واجهة HTTPS مناسبًا وضبط CORS و`FRONTEND_URL`؛ الأسهل فحص الرحلة الكاملة على بيئة HTTPS مستقلة. لا ترفع أسرار التطوير إلى عنوان tunnel أو خدمة غير موثوقة.

الرجوع من Paymob بمعامل `success=true` لا يؤكد الدفع. الباك يتحقق من HMAC والمبلغ والعملة والتكامل وربط العملية بالطلب، ويمنع تكرار تطبيق الحدث. حالة `initialization_unknown` تعني أن نتيجة إنشاء Intention غير مؤكدة؛ راجع Paymob قبل المحاولة التالية بدل إعادة الإرسال تلقائيًا. `PAYMOB_LIVE=false` عملية Sandbox حتى إذا نجحت.

`ALLOW_SIMULATED_PAYMENTS` مخصص Development/Test، ويُضبط `false` في Production. الدفع النقدي يتحكم فيه `ALLOW_CASH_ON_DELIVERY`. InstaPay في هذا الإصدار تحويل يدوي يحتاج `INSTAPAY_RECIPIENT` و`INSTAPAY_RECIPIENT_NAME` ثم claim من العميل ومراجعة موظف له صلاحية؛ ليس ربط API آليًا مع InstaPay.

## 8. الفحوص قبل النشر وبعده

من الجذر شغّل اختبارات JavaScript ثم افحص البناء والأنواع:

```bash
npm test
npm run typecheck
npm run build
```

ومن `back/` داخل بيئة Python معزولة، ثبّت `requirements-test.txt` ثم شغّل `python -m pytest -q`. ملف الاختبارات يستورد اعتماديات التشغيل المثبتة في lockfile ويضيف أدوات الاختبار؛ لا حاجة لإعداد اتصال قاعدة بيانات حقيقية لهذه المجموعة.

ملف `.github/workflows/build.yml` يشغّل اختبارات الفرونت والوسيط وعقد Postman عبر `npm test`، وبناء الفرونت، واختبارات الباك بـ `pytest`، وفحص Python syntax عند push أو pull request إلى `main`. هذا Workflow للفحص؛ لا ينفذ نشر FastAPI Cloud أو migrations أو seed، ووجوده وحده لا يثبت أن Vercel تنتظر نجاحه دون إعداد قواعد الفرع والنشر. أوامر ونتائج المراجعة وحدودها موثقة في [SPRINT_2_VERIFICATION.md](SPRINT_2_VERIFICATION.md). لا تعتبر نجاح Build أو المجموعة المعزولة دليل نجاح الدفع أو تسليم البريد أو OAuth، ولا تعتبر نتائج 2026-10-31 إثباتًا لحالة الخدمات اليوم.

من الجهاز المحلي، ثم غيّر الأصل إلى API المنشور عند مراجعة النشر:

```bash
curl --fail-with-body 'http://127.0.0.1:8000/health/live'
curl --fail-with-body 'http://127.0.0.1:8000/health/ready'
curl --fail-with-body 'http://127.0.0.1:8000/api/v1/restaurants'
curl --fail-with-body 'http://127.0.0.1:8000/api/v1/payments/methods'
```

`/health/live` يؤكد استجابة العملية. `/health/ready` يفحص MySQL وValkey وتطابق revision مع الكود؛ لا يفحص حساب Paymob أو تسليم Mailjet أو موافقة OAuth. في Vercel راجع `https://foodify-flax.vercel.app/api/v1/restaurants` للتأكد من عبور الوسيط، بينما health تُطلب مباشرة من نطاق الباك.

| الرحلة | النتيجة التي تراجعها يدويًا |
|---|---|
| كتالوج | مطاعم ومنتجات وصور من API، مع حالة واضحة عند تعطل الخدمة. |
| تأكيد بريد | رسالة جديدة تصل للمستلم، ثم تأكيد وجلسة واستكمال هاتف وعنوان دون فقد الحالة. |
| Google/Facebook | بدء المزود ثم callback صحيح، واستكمال بيانات الحساب عند نقصها. |
| سلتان | إضافة أصناف من متجرين، ثم العودة إلى كل متجر والعثور على سلته. |
| Checkout | عنوان يملكه المستخدم، إجمالي من الباك، ومنع تكرار إنشاء الطلب عند تكرار الإرسال. |
| Paymob Test | فتح نموذج الدفع، ثم نتيجة callback موثقة، ثم صفحة الطلب تعرض الحالة الحقيقية. |
| متابعة الطلب | طلب المستخدم يظهر في تاريخه، وقائمة المطعم متاحة للموظف المصرح له فقط. |
| Logout | تعذر الوصول للموارد المحمية بعد الخروج، دون بقاء بيانات مستخدم سابق في العرض. |

استخدم حسابًا مخصصًا للتجربة وPaymob Test فقط للفحص المقصود. لا تعتبر كتابة حالة `paid` يدويًا في MySQL اختبارًا لتكامل الدفع.

## 9. تشخيص أسرع للمشكلات

| المشكلة | ما تراجعه |
|---|---|
| المطاعم غير ظاهرة | أصل API، `/health/ready`، migration، ثم وجود الكتالوج في القاعدة المقصودة. |
| `Resource not found` عند `/` | جذر API ليس شاشة الفرونت؛ راجع مسار `/api/v1/...` الصحيح وhealth المباشر. |
| API قديم رغم تعديل الكود | أعد بناء صورة Docker محليًا؛ في السحابة تحقق من commit/نسخة النشر الفعلية. |
| البريد يفتح `3000` أو نطاقًا قديمًا | صحح `FRONTEND_URL` وأعد تشغيل/نشر الباك، ثم اطلب رسالة جديدة؛ الروابط القديمة لن تتغير. |
| OAuth يرجع للدخول أو يفقد verifier | استخدم أصل الواجهة نفسه من بداية الرحلة، وراجع callback الحرفي والجلسة والكوكيز. |
| Google `redirect_uri_mismatch` | Redirect URI المسجل عند Google يطابق متغير الباك حرفيًا، بما في ذلك hostname والمنفذ والمسار. |
| `payment_method_unavailable` | مفاتيح Paymob الثلاثة وIntegration ID الخاص بالوسيلة ووضع Test/Live. |
| `payment_setup_rejected` | إعداد التكامل أو المفاتيح أو بيانات الطلب؛ راجع الكود الآمن ومعرّف الطلب دون كشف secrets. |
| `payment_initialization_unknown` | لا تعيد التهيئة تلقائيًا؛ تحقق من العملية لدى Paymob أولًا. |
| دفع ناجح والطلب ينتظر | تحقق من وصول POST callback العام وHMAC والمبلغ، وليس رابط العودة فقط. |
| `401` على موارد المستخدم | Bearer Access Token وجلسة refresh، وتمرير Authorization والكوكيز عبر الوسيط. |
| فشل خط عربي أو صور في الإنتاج | راجع CSP ووجهة الصور؛ البناء يخرج الخطوط كملفات مستقلة، فلا توسع السياسة بلا حاجة. |

## 10. الأسرار وخطة التراجع

الأسرار توضع في إعدادات خادم الاستضافة أو ملفات محلية مستثناة من Git، ولا تدخل `VITE_*` أو Postman exports أو README. النسخ الاحتياطية ولقطات المتصفح قد تحتوي بيانات حساسة أيضًا. عند كشف مفتاح، ألغِه وأنشئ بديلًا عند المزود، ثم حدث جميع الخدمات التي تستخدمه.

تدوير `FRONTEND_PROXY_SECRET` يحتاج تنسيقًا بين Vercel والباك. تغيير `JWT_SECRET` ينهي صلاحية التوكنات الحالية. `EMAIL_ENCRYPTION_KEY` يشفّر Email Outbox ورمز Paymob المحفوظ؛ تغييره عشوائيًا قد يمنع فك بيانات العمليات السابقة، لذلك يحتاج خطة تدوير واضحة.

إذا ظهر عطل بعد النشر: أوقف إصدار تغييرات إضافية، وحدد الخدمة المتأثرة من Network وrequest ID والسجلات المنقحة، ثم أعد نشر نسخة الكود السابقة المتوافقة مع schema الحالي. لا تنفذ `alembic downgrade` تلقائيًا؛ بعض التراجعات تحذف جداول أو أعمدة. الرجوع إلى قاعدة سابقة يحتاج نسخة احتياطية وإجراء استعادة مقصودًا ومراعاة الطلبات والمدفوعات التي حدثت بعد النسخة. بعد التراجع كرر health وقراءة الكتالوج والجلسة وقراءة الطلب، وراجع أي عملية دفع غير مؤكدة لدى Paymob قبل إعادة المحاولة.
