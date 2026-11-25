# فريق Deployment: شرح Sprint 3

هذا الشرح يوضح مسؤولية فريق النشر في **Sprint 3**: تحويل نسخة الكود إلى خدمات تعمل معًا، وضبط البيئات والأسرار، وتنظيم الـ Pull Requests على GitHub، وتشخيص وإصلاح مشكلة وصول البريد الإلكتروني، ثم تطبيق migration الجديدة ورفع الإصدار بأمان.

يمكن قراءة [شرح Integration](integration.md) لفهم تفاصيل التبادل بين الواجهة والباك، و[شرح الاختبارات](testing.md) لمعرفة ما تثبته الفحوص الآلية. شرح [Backend](backend.md) بالإنجليزية، وشرح [Frontend](frontend.md) بالعربية.

## 1. ماذا قدّم فريق Deployment حتى Sprint 3؟

الفريق جهز مسار تشغيل محلي باستخدام Docker Compose، ومسار نشر مستقل للواجهة (Vercel) والباك (FastAPI Cloud) وقاعدة البيانات (Aiven MySQL + Valkey). في Sprint 3 أضفنا:
1. تشخيص وعلاج مشكلة عدم وصول إيميلات التحقق واستعادة كلمة المرور من جذورها (تعارض DMARC بين `@gmail.com` ومزود `Mailjet`).
2. دعم 3 مزودي إرسال للبريد (`smtp` مع Gmail App Password مباشر، أو `brevo`، أو `resend`) مع محتوى `HTML Multipart` وترويسات RFC 5322 وأداة تشخيص `python -m scripts.check_email`.
3. تنظيم الريبو على GitHub عبر **Feature Pull Requests** مفصولة (`PR #1` إلى `PR #5`) تمر كلها بفحص GitHub Actions قبل الدمج في `main`.
4. migration `20261121_0006_sprint3_delivery_notifications.py` وسكربت `back/scripts/deploy_sprint3.sh` للتحديث الذري الآمن دون تعطل `/health/ready`.

في Sprint 2 أصبح النشر يحتاج تنسيقًا أكبر: الواجهة تعتمد على كتالوج من MySQL، والطلب يعتمد على عنوان وسلة وأسعار فعلية، والدفع يحتاج مزودًا خارجيًا وcallback عامًا. لذلك نشر React وحدها لا يكفي لتشغيل الرحلة كاملة.

| الخدمة | أين تعمل؟ | دورها |
|---|---|---|
| React + TypeScript + Vite | Vercel | تقديم ملفات الواجهة للمستخدم. |
| `api/proxy.mjs` | Vercel Function | تمرير طلبات `/api/v1/*` إلى الباك. |
| FastAPI | FastAPI Cloud | تنفيذ قواعد الحسابات والسلال والطلبات والدفع. |
| MySQL | Aiven | تخزين البيانات الدائمة والعلاقات والطلبات. |
| Valkey | Aiven | عدادات Rate Limiting المشتركة. |
| Mailjet SMTP | مزود بريد خارجي | إرسال الرسائل التي ينتجها Email Outbox. |
| Paymob | Hosted Checkout | استقبال بيانات البطاقة أو المحفظة وإرسال نتيجة موثقة. |

هذا هو توزيع الاستضافة المعتمد في إعدادات المشروع. وجود أسماء الخدمات أو عناوينها هنا لا يثبت حالة حساباتها أو حدود خططها أو أن أحدث commit منشور عليها.

## 2. كيف تنتقل العملية بين الخدمات؟

المتصفح يفتح الواجهة على Vercel. عندما تطلب React المطاعم مثلًا، تستدعي `/api/v1/restaurants` من نطاق الواجهة؛ فيستقبل Vercel Proxy الطلب ويمرره إلى FastAPI Cloud. الباك يقرأ MySQL، ثم ترجع البيانات عبر المسار نفسه إلى الشاشة.

في الدفع، الباك ينشئ Paymob Intention ويعيد رابط Checkout. المتصفح ينتقل إلى Paymob لإدخال بيانات الدفع، بينما Paymob يرسل نتيجة العملية إلى callback في الباك. صفحة الطلب تقرأ الحالة المحفوظة من API بعد العودة.

| المسار | مصدر الحقيقة |
|---|---|
| الكتالوج والسعر | MySQL عبر FastAPI. |
| إجمالي الطلب | حساب الباك من السلة والمنتجات ورسوم التوصيل. |
| حالة الدفع | نتيجة يتحقق منها الباك، ثم يخزنها. |
| صلاحيات المستخدم | جلسة وهوية وصلاحيات يتحقق منها الباك. |

الواجهة لا تحمل بيانات اتصال MySQL، ولا تتصل مباشرة بـ Mailjet أو Paymob Secret API. لا ينبغي أن توجد أسرار هذه الخدمات في ملفات React التي تصل إلى المتصفح.

## 3. الأدوات ولماذا استخدمناها

استخدمنا Docker لتثبيت بيئة تشغيل الباك واعتمادياته، وCompose لتشغيل الخدمات المحلية معًا. استخدمنا Alembic لتغييرات schema القابلة للتتبع، وGit لتحديد نسخة الكود، وGitHub Actions لتشغيل الفحوص عند تحديث المستودع.

Vercel يبني ملفات React ويشغّل وسيط API. FastAPI Cloud يشغّل تطبيق Python المستقل من `app.hosted:app`. Aiven يوفر MySQL وValkey خارج حاوية الباك، حتى لا تعتمد البيانات الدائمة على ملفات حاوية مؤقتة.

| الملف | لماذا يحتاجه فريق النشر؟ |
|---|---|
| `vercel.json` | أوامر البناء، مجلد الناتج، rewrite للـ API، وترويسات الحماية. |
| `back/Dockerfile` | صورة Python وصلاحيات مستخدم الحاوية وطريقة التشغيل. |
| `back/compose.yaml` | API والعامل وMySQL وRedis وMailpit محليًا. |
| `back/pyproject.toml` | نقطة دخول FastAPI Cloud وتعريف حزمة الباك. |
| `back/requirements.lock.txt` | إصدارات Python المثبتة للتشغيل. |
| `front/package-lock.json` | شجرة حزم JavaScript التي يثبتها `npm ci`. |
| `.github/workflows/build.yml` | الفحوص الآلية على GitHub. |
| `back/scripts/release.py` | انتظار القاعدة ثم migrations والبيانات المرجعية. |

`pyproject.toml` يقرأ الآن الاعتماديات الديناميكية من `requirements.lock.txt`، مثل Docker. هذا يصحح اختلافًا سابقًا كان يجعل مسار حزمة الباك يعتمد على ملف بإصدارات مرنة. مراجعة سجل بناء السحابة تظل ضرورية للتأكد من النسخة المنشورة فعليًا.

## 4. فصل Development وTest وProduction

| المرحلة | الإعدادات | الاستخدام |
|---|---|---|
| Development | `.env.development` و`.env.payments.development` | تطوير محلي وMailpit ومفاتيح Paymob Test عند إعدادها. |
| Test runtime | `.env.test` و`.env.payments.test` | تشغيل تطبيق تجريبي بقاعدة MySQL مستقلة وحسابات منفصلة. |
| Production | أسرار FastAPI Cloud وVercel | المستخدمون الفعليون وروابط HTTPS والخدمات الخارجية. |

يختار `APP_ENV` ملفات الباك. متغيرات العملية تتقدم على الملفات، لذلك تغيير ملف محلي لا يغير قيمة سبق ضبطها في منصة الاستضافة. بعد تعديل إعدادات خدمة منشورة يجب إعادة تشغيلها أو إعادة نشرها بالطريقة التي تطبق الإعدادات الجديدة.

تشغيل التطبيق بوضع `APP_ENV=test` يظل تشغيلًا يعتمد على MySQL. أما مجموعة `pytest` فتستخدم إعدادات معزولة وSQLite في الذاكرة، ولا تقرأ ملفات `.env` ولا تتصل بالخدمات الخارجية. هذان مساران مختلفان؛ نجاح المجموعة لا يثبت سلوك أقفال MySQL أو migration على MySQL حقيقية.

يجب فصل اسم القاعدة والمستخدم وكلمات المرور ومفاتيح الدفع وروابط callback بين البيئات. لا تغيّر `APP_ENV` إلى `test` وتترك `DATABASE_URL` يشير إلى قاعدة الإنتاج.

## 5. التشغيل المحلي باستخدام Docker

من مجلد `back/` تُنسخ قوالب الإعداد مرة واحدة عند غياب الملفات الفعلية. لا تنسخ القالب فوق ملف يحتوي إعداداتك. تُضبط كلمات مرور MySQL ومفتاح JWT ومفتاح Fernet محليًا؛ لا تُرفع إلى Git.

```bash
cd /home/hyzin/Projects/Foodify/back
docker compose --env-file .env.development up -d mysql redis mailpit
docker compose --env-file .env.development run --build --rm api python -m scripts.release
docker compose --env-file .env.development run --rm api python -m scripts.seed_catalog
docker compose --env-file .env.development up -d --build api email-worker
```

الأمر الأول يشغّل الخدمات المساندة. `scripts.release` ينتظر اتصال MySQL، ويطبق `alembic upgrade head`، ثم يجهز الأدوار والصلاحيات وأنواع التوكنات. `seed_catalog` خطوة مستقلة لإدخال بيانات العينة المعتمدة في قاعدة البيانات.

صورة Docker تستخدم Python 3.14 ومستخدم تشغيل غير root. Compose يسقط capabilities ويمنع اكتساب صلاحيات إضافية ويجعل نظام ملفات التطبيق للقراءة فقط، مع مساحة مؤقتة في `/tmp`. منافذ التطوير منشورة على `127.0.0.1`.

خدمة API تقرأ مفاتيح الدفع عند وجود ملفها، بينما عامل البريد لا يحتاج مفاتيح Paymob. إعداد Compose يوجه SMTP إلى Mailpit على المنفذ 1025؛ الرسائل المحلية تظهر في `http://127.0.0.1:8025` بدل إرسالها إلى بريد حقيقي.

```bash
cd /home/hyzin/Projects/Foodify
npm --prefix front ci
npm run dev
```

تعمل الواجهة على `http://127.0.0.1:5173` والباك على `http://127.0.0.1:8000`. يتطلب المشروع Node.js `>=22.12`، بينما CI يستخدم Node 24. Vite يطبق تعديلات الواجهة أثناء التطوير، لكن تغيير ملف `.env` يحتاج إعادة تشغيله.

تعديل كود الباك يحتاج إعادة بناء الصورة وتشغيل API الجديدة. تعديل schema يحتاج `scripts.release` أولًا. `docker compose down` يحتفظ بالـ named volumes؛ حذف volumes يحذف البيانات، وليس خطوة مطلوبة لتحديث الكود.

## 6. تجهيز الأسرار والعناوين

| الإعداد | مكانه الصحيح | ملاحظته |
|---|---|---|
| `DATABASE_URL` وشهادة CA | الباك | اتصال `mysql+pymysql` مع TLS موثّق في الإنتاج. |
| `MIGRATION_DATABASE_URL` | خطوة الإصدار | حساب يملك صلاحية تعديل schema. |
| `REDIS_URL` | الباك | اتصال Aiven Valkey بصيغة `rediss://` ومصادقة. |
| `JWT_SECRET` | الباك | توقيع Access Tokens. |
| `EMAIL_ENCRYPTION_KEY` | الباك | تشفير بيانات حساسة محفوظة مثل outbox. |
| OAuth وSMTP وPaymob secrets | الباك | لا تدخل حزمة المتصفح. |
| `FRONTEND_PROXY_SECRET` | Vercel والباك | قيمة واحدة لتوقيع بيانات عنوان العميل التي يرسلها الوسيط. |
| `VITE_API_BASE_URL` | بناء React | إعداد عام يظهر في ملفات المتصفح. |

تُحفظ ملفات القيم الفعلية خارج Git، وتبقى ملفات `.example` قوالب بلا أسرار. لا تستخدم متغيرًا يبدأ بـ `VITE_` لحفظ Secret Key؛ Vite يضم هذه القيم إلى ناتج المتصفح.

يحتاج الإنتاج `APP_ENV=production` و`DEBUG=false` و`DOCS_ENABLED=false`. وتُضبط `PUBLIC_BASE_URL` للباك، و`FRONTEND_URL` للواجهة، و`CORS_ORIGINS` و`TRUSTED_HOSTS` بأسماء صريحة. تتحقق Settings من شروط أساسية مثل HTTPS وأطوال الأسرار وصيغة الاتصالات وتوافق مفاتيح Paymob مع Test/Live.

حساب تشغيل MySQL يملك صلاحيات البيانات المطلوبة، وحساب migration يملك صلاحيات schema. يجب أن يشيرا إلى القاعدة المقصودة نفسها. لا تستخدم حساب root لتشغيل التطبيق، ولا تعطل فحص شهادة TLS لحل خطأ اتصال.

## 7. ماذا تفعل GitHub Actions؟

عند push أو pull request إلى `main` يشغّل Workflow المسمى `Checks` وظائف منفصلة:

| الوظيفة | الأوامر الأساسية | ما تكشفه |
|---|---|---|
| Frontend | `npm test` ثم `npm run build` | اختبارات JavaScript والوسيط والعقد، ثم أخطاء الأنواع والبناء. |
| Backend tests | تثبيت `requirements-test.txt` ثم `python -m pytest -q` | اختبارات Python المعزولة وحالات HTTP والخدمات. |
| Python syntax | `python -m compileall -q back/app back/scripts back/migrations` | أخطاء صياغة Python في كود التشغيل والسكربتات وmigrations. |

`requirements-test.txt` يستورد lockfile ويضيف أدوات pytest. وظيفة syntax لا تشغّل التطبيق، ونجاح TypeScript لا يثبت عمل Paymob. كل فحص يثبت جانبًا محددًا؛ شرح الحالات وحدودها موجود في [شرح الاختبارات](testing.md).

هذا Workflow للفحص فقط: لا ينفذ `fastapi deploy` ولا migrations ولا seed. نشر Vercel من Git تكامل منفصل؛ وجود Checks وحده لا يجعله شرطًا مانعًا للنشر إلا عند ضبط قواعد الفرع أو إعدادات الربط المناسبة في الحساب.

## 8. ترتيب الإصدار إلى الإنتاج

أولًا نحدد commit المرشح، ونشغّل الفحوص، ونحتفظ بمعرّف النسخة السابقة ونسخة احتياطية قابلة للاستعادة. ثم نراجع إعدادات البيئة والمزودين، ونطبق migrations، ونجهز البيانات المطلوبة، وننشر الباك، وبعد جاهزيته ننشر الواجهة المتوافقة.

السبب في هذا الترتيب أن React الجديدة قد تطلب endpoint أو عمودًا غير موجود في الإصدار القديم. كما أن نشر الباك لا ينشئ schema تلقائيًا، ونجاح migration لا يضمن أن بيانات الكتالوج موجودة.

من بيئة Python معزولة داخل `back/`، وبعد إعداد قيم البيئة الصحيحة، تكون أوامر الإصدار المقصودة:

```bash
pip install -r requirements.lock.txt
APP_ENV=production alembic heads
APP_ENV=production alembic current
APP_ENV=production python -m scripts.release
```

هذه الأوامر تكتب في قاعدة البيئة المحددة عند تنفيذها؛ ليست أوامر فحص للقراءة فقط. الرقم الموجود في نسخة Sprint 2 هو `20261031_0005`، لكن المرجع عند نشر تغيير لاحق هو `alembic heads` للنسخة الجديدة.

الكتالوج التجريبي في MySQL يحتوي 8 متاجر و24 منتجًا و16 تصنيفًا من ملفات العينة المرفقة بحزمة `app.ordering`. يحتفظ seeder بمعرّفات ثابتة ويحدث صفوف العينة التي يديرها، ويعطل الأصناف القديمة التابعة لها دون مسح حسابات المستخدمين أو الطلبات.

```bash
APP_ENV=production FOODIFY_ALLOW_DEMO_CATALOG_SEED=true \
  python -m scripts.seed_catalog --allow-production
```

الشرطان يحميان الإنتاج من زرع العينة بالخطأ. لا يُشغّل seeder في كل startup، ولا يعتبر بديلًا عن شاشة إدارة كتالوج حقيقي. بيانات العلامات والأسعار المعتمدة هنا بيانات عرض تجريبية، ولا تثبت شراكة مع أي متجر.

## 9. نشر الباك والواجهة

```bash
cd /home/hyzin/Projects/Foodify/back
fastapi login
fastapi cloud link
fastapi deploy
```

هذه خطوات النشر عند تنفيذ إصدار مصرح به؛ `link` مطلوب عند غياب الربط المحلي، مع اختيار تطبيق `foodify-api` الموجود. `fastapi deploy` يعمل من `back/` لأن هذا مجلد حزمة الباك. نقطة الدخول هي `app.hosted:app`، وليست `scripts/hosted_start.py`.

في FastAPI Cloud تضبط الأسرار ثم تعيد النشر لتطبيق القيم. `EMBEDDED_EMAIL_WORKER=true` يسمح للتطبيق بتشغيل عامل معالجة outbox في هذا المسار المستضاف. هذا لا ينفذ migration أو catalog seed أثناء بدء الخدمة.

| إعداد Vercel | القيمة الحالية |
|---|---|
| Root Directory | جذر المستودع، لأن `api/proxy.mjs` خارج `front/`. |
| Install Command | `npm --prefix front ci`. |
| Build Command | `npm run build`. |
| Output Directory | `front/dist`. |
| `FOODIFY_API_ORIGIN` | `https://foodify-api.fastapicloud.dev` بدون `/api/v1`. |
| `VITE_API_BASE_URL` | `/api/v1`. |
| `VITE_DATA_SOURCE` و`VITE_APP_ENV` | `api` و`production`. |

نشر الفرونت من الفرع المتصل بـ Vercel يبني commit المرفوع. يجب متابعة حالة النشر ومعرّف النسخة؛ نجاح push لا يثبت نجاح Build. تغيير إعداد عام لـ Vite يحتاج بناء جديد، لأنه أصبح جزءًا من ملفات JavaScript.

الوسيط يقبل مسارات API محدودة ويحدد وجهة HTTPS من إعداد خادم ثابت، ويمرر Authorization وCookie و`Idempotency-Key`. يرجع `Set-Cookie` من الباك ويمنع تخزين استجابات API في cache، ولا يعمل كوكيل مفتوح إلى عنوان يختاره المستخدم.

## 10. ضبط الجلسة وOAuth والبريد

في الإنتاج تستخدم React نطاق Vercel نفسه لاستدعاءات `/api/v1`، ويحفظ المتصفح Refresh Token داخل HttpOnly Cookie. أصل الواجهة المسموح، وHTTPS، وSameSite، وتمرير الكوكيز عوامل متصلة؛ توسيع CORS إلى `*` لا يصلح إعداد جلسة خاطئًا.

روابط التأكيد واستعادة كلمة المرور تُبنى من `FRONTEND_URL`. يعيد `vercel.json` المسارات `/verify-email` و`/reset-password` و`/oauth/callback` إلى SPA. الواجهة تحوّل الروابط إلى HashRouter، والتأكيد يستخدم browser endpoint الذي ينشئ جلسة لاستكمال الهاتف والعنوان.

العنوانان المسجلان لدى مزودي OAuth يجب أن يطابقا إعداد الباك حرفيًا:

```text
https://foodify-api.fastapicloud.dev/api/v1/auth/oauth/google/callback
https://foodify-api.fastapicloud.dev/api/v1/auth/oauth/facebook/callback
```

محليًا يستخدم القالب callback على `http://localhost:8000`، بينما أصل الواجهة المعتمد `http://127.0.0.1:5173`. الواجهة توحد اسم المضيف قبل بدء الجلسة في Development، لأن PKCE verifier محفوظ في `sessionStorage` الخاص بالأصل الذي بدأ OAuth.

البريد في الإنتاج يمر من `email_outbox` في MySQL إلى `EmbeddedEmailWorker`. **مشكلة Sprint 2 وتشخيصها في Sprint 3:** السجلات الحية في قاعدة Aiven أثبتت أن الرسائل الـ15 في `email_outbox` تم تسليمها إلى Mailjet SMTP (`in-v3.mailjet.com:587`) خلال 2–3 ثوانٍ وحصلت على `250 OK` (لذلك سجل العامل `sent_at` بدون أخطاء)، لكن العنوان المرسل `SMTP_FROM_EMAIL` كان على نطاق `@gmail.com` — وبسبب سياسة DMARC/SPF لحسابات البريد المجانية يرفض مزودو الاستقبال أي رسالة بـ `From: @gmail.com` صادرة من خادم Mailjet/Brevo طرف ثالث!

**إصلاح Sprint 3 الكامل للبريد (`PR #1`):**
- إضافة محتوى `HTML` متجاوب مع RTL بجانب النص العادي (`ActionEmailContent.html` في `app/infrastructure/email_content.py`) وترويسات RFC 5322 (`Date`، `Message-ID`، `Reply-To`، `formataddr` مع `SMTP_FROM_NAME`).
- دعم اختيار مزود البريد عبر `EMAIL_PROVIDER`: إما `smtp` (مع تنظيف مسافات 16 حرفًا في **Google App Password** تلقائيًا لـ `smtp.gmail.com:587` لكي تطابق SPF/DKIM الخاصة بجوجل مباشرة!)، أو `brevo` (`xkeysib`), أو `resend` (`EMAIL_PROVIDER=resend` + `RESEND_API_KEY`).
- تحذير تلقائي عند بدء التشغيل إذا كان `SMTP_FROM_EMAIL` نطاقًا عامًا مجانيًا عبر Relay خارجي، وسكربت فحص حي `back/.venv/bin/python -m scripts.check_email --to test@example.com`، وتنبيه عند انتهاء صلاحية رسالة في outbox.

## 11. تنظيم GitHub بـ Feature Pull Requests وهجرة Sprint 3

تم تقسيم إضافات Sprint 3 على المستودع `0xhyzin/Foodify` إلى **5 Pull Requests** منفصلة تمر كلها أولًا بفحص GitHub Actions (`Checks`: Frontend tests/build + Backend pytest/OpenAPI/MkDocs strict + Python syntax):
1. **PR #1 (`fix/email-deliverability-and-providers`):** إصلاح تسليم البريد وتعدد المزودين وتشخيص `scripts.check_email`.
2. **PR #2 (`feat/admin-portal-and-role-routing`):** فصل بوابة `/admin` وAPIs إدارة الموظفين والأدوار وتوجيه الدخول `loginDestination`.
3. **PR #3 (`feat/sprint3-postman-and-junit-catalog`):** مجموعة `Foodify.Sprint3.postman_collection.json` وتوليد فهرس JUnit (`285` حالة، تغطية `91%`).
4. **PR #4 (`docs/sprint3-mkdocs-handbook-and-openapi`):** تحديث عقود OpenAPI (`64` مسارًا) ودليل الفرق `MkDocs --strict`.
5. **PR #5 (`docs/sprint3-complete-pdf-pack`):** حزمة ملفات PDF العربية الستة الكاملة لـ Sprint 3.

**أهمية التسلسل الذري مع `20261121_0006`:** الهجرة `20261121_0006_sprint3_delivery_notifications.py` تضيف جداول `restaurant_staff` و`delivery_assignments` و`notifications` والعمود `assigned_preparer_id` وتحوّل الحالات القديمة (`placed -> pending`، `ready -> ready_for_pickup`، `out_for_delivery -> picked_up`). ولأن `/health/ready` في الباك يتحقق أن `applied == get_expected_revision_heads()`، يجب تشغيل `scripts.release` و`fastapi deploy` معًا عبر `back/scripts/deploy_sprint3.sh` بعد `fastapi login` حتى لا يرفض كود Sprint 2 قاعدة Sprint 3 أثناء الفاصل بينهما.

## 11. ضبط الدفع دون خلط Test وLive

يحتاج Paymob Secret Key وPublic Key وHMAC Secret وIntegration ID للبطاقة أو المحفظة. يجب أن تنتمي القيم إلى الحساب نفسه والوضع نفسه، مع `PAYMOB_LIVE=false` للتجربة. التطبيق يستخدم Intention API ثم يرسل المستخدم إلى `https://eg.checkout.paymob.com/`.

Processed Callback هو `https://foodify-api.fastapicloud.dev/api/v1/payments/paymob/callback`. أما مسار العودة فهو `/api/v1/payments/return/{order_id}`، ويضع الكود Order ID الفعلي لكل Intention؛ لا تُنسخ الأقواس الحرفية إلى لوحة المزود.

محليًا قد يفتح نموذج البطاقة بمفاتيح Test، لكن Paymob لا يستطيع الاتصال بـ localhost على جهازك. تجربة callback كاملة تحتاج باك متاحًا عبر HTTPS وإعدادات أصول وجلسة متوافقة، أو بيئة Test مستقلة متاحة للمزود.

الرجوع بمعامل `success=true` لا يثبت التحصيل؛ الباك يتحقق من HMAC والمبلغ والعملة والتكامل وربط العملية. لا تعاد تهيئة `initialization_unknown` تلقائيًا قبل مراجعة المزود. InstaPay في هذا الإصدار تحويل يدوي يراجعه موظف مصرح له، وليس تكامل API مؤكدًا آليًا.

## 12. كيف نراجع الإصدار والتراجع؟

`/health/live` يثبت أن عملية API تستجيب. `/health/ready` يراجع اتصال MySQL وValkey وتوافق revision. لا يفحص أي منهما إكمال Google أو وصول رسالة إلى المستلم أو نجاح Paymob الحقيقي.

نراجع بعدها عبور الكتالوج من API عبر وسيط Vercel، وجلسة حساب تجربة، واستقلال سلتين، وإنشاء طلب وإعادة قراءته. ويُفحص OAuth والبريد وPaymob Sandbox كرحلات مستقلة مع مزوديها عند توفر بيئة الفحص المناسبة، دون اعتبار بيانات الاختبار المعزولة دليلًا على الخدمات الحية.

نتائج النشر المشار إليها في مستندات 2026-10-31 نتائج تاريخية لتلك النسخة وذلك الوقت. لم يُنفذ نشر أو استعلام إلى قاعدة الإنتاج أو المزودين أثناء إعداد هذا الشرح في 2026-11-03. أحدث نتائج التشغيل الآلي وحدودها تُراجع في [شرح الاختبارات](testing.md) وتقرير التحقق داخل المستودع.

عند العطل نحدد الخدمة من Network وrequest ID والسجلات المنقحة. غياب المطاعم قد يعني API خاطئة أو migration ناقصة أو كتالوجًا غير مزروع؛ فشل OAuth قد يعني callback مختلفًا؛ انتظار الدفع قد يعني callback لم يصل. التشخيص يحدد السبب قبل إعادة نشر الخدمات عشوائيًا.

التراجع يبدأ بنشر نسخة كود سابقة متوافقة مع schema الحالية. لا ننفذ `alembic downgrade` تلقائيًا؛ تغيير schema قد يحذف بيانات، واستعادة backup قد تفقد طلبات ومدفوعات حدثت بعدها. العمليات غير المؤكدة تحتاج مطابقة لدى Paymob قبل إعادة المحاولة.

تغيير JWT Secret ينهي صلاحية التوكنات الحالية، وتغيير سر الوسيط يحتاج تنسيق Vercel والباك. تغيير مفتاح Fernet عشوائيًا قد يمنع فك بيانات قديمة؛ لذلك إدارة الأسرار تشمل التدوير المنظم، وحفظ المفاتيح اللازمة للبيانات القائمة، ومراجعة ما تأثر بالتغيير.

لشرح دور الفريق شفهيًا: جهزنا البيئات والخدمات، وثبتنا الاعتماديات، وفصلنا الأسرار، ورتبنا migrations والبيانات والنشر، وأضفنا فحوص CI، وحددنا كيف نعرف أن الإصدار يعمل وما الذي ما زال يحتاج فحصًا مع المزودين. ارجع إلى [فهرس الشرح](index.md) لبقية أدوار الفريق و[شرح إعداد Documentation](documentation.md) لطريقة إنتاج هذه الصفحات.
