# دليل نشر Foodify

يوضح هذا الدليل طريقة نشر المشروع وإعداد الخدمات المرتبطة به. الواجهة والـ API وقاعدة البيانات وخدمة التخزين المؤقت والبريد خدمات مستقلة، ولكل منها إعداداتها.

## النشر الحالي

| الجزء | الخدمة | الرابط أو الوظيفة |
|---|---|---|
| واجهة React | Vercel | [foodify-flax.vercel.app](https://foodify-flax.vercel.app) |
| واجهة API باستخدام FastAPI | FastAPI Cloud Hobby | [foodify-api.fastapicloud.dev](https://foodify-api.fastapicloud.dev) |
| قاعدة بيانات MySQL | Aiven | الحسابات والعناوين والكتالوج والسلال والطلبات والدفع |
| التخزين المؤقت Valkey | Aiven | حفظ عدادات تحديد معدل الطلبات |
| إرسال البريد | Mailjet SMTP | رسائل تأكيد البريد واستعادة كلمة المرور |
| مستودع الكود | GitHub | [0xhyzin/Foodify](https://github.com/0xhyzin/Foodify) |

في مراجعة الإصلاح بتاريخ 2026-10-31 نجح اتصال MySQL، واتضح أن قاعدة الإنتاج بقيت على migration `20261020_0001` رغم نشر كود Sprint 2. أُخذت نسخة محلية مشفرة قبل تطبيق migrations حتى `20261031_0005`، ثم زُرعت 8 متاجر و24 منتجًا و16 تصنيفًا مع الحفاظ على الحسابات القائمة. رجع `/health/ready` بحالة `200` و`{"status":"ready"}`، ورجعت بيانات المطاعم والتصنيفات عبر وسيط Vercel بحالة `200`. فحص الجاهزية يتحقق من MySQL وValkey وإصدار migrations، ولا يثبت إتمام تسجيل OAuth أو تسليم البريد أو الدفع.

```text
المتصفح
  → واجهة React على Vercel
  → طلب من نفس الموقع إلى /api/v1/*
  → api/proxy.mjs (تمرير الطلبات والكوكيز وتوقيع عنوان العميل)
  → API على FastAPI Cloud
      → MySQL على Aiven عبر TLS (الحسابات وصندوق البريد المشفر)
      → Valkey على Aiven عبر TLS (تحديد معدل الطلبات)
      → عامل صندوق البريد داخل التطبيق → Mailjet SMTP عبر STARTTLS

Google / Facebook → callback على الـ API → callback على الواجهة
```

Vercel تستضيف الواجهة ووسيط تمرير طلبات الـ API فقط. منطق التطبيق وتسجيل الدخول موجودان في FastAPI. الوسيط يمرر المسارات `/api/v1/*`؛ أما فحوص الصحة فتكون مباشرة على نطاق الـ API مثل `/health/ready`، وليس تحت `/api/v1`.

## قبل النشر

1. تأكد من إمكانية الدخول إلى لوحات تحكم Vercel وFastAPI Cloud وAiven وMailjet.
2. غيّر بيانات الاعتماد التي أُرسلت في المحادثة أو كُشفت بأي طريقة، ثم حدّث القيم الجديدة في الخدمات وإعدادات النشر. لا تضعها في هذا الملف أو Git أو ملفات Postman أو متغيرات الواجهة التي تبدأ بـ `VITE_`.
3. احتفظ ببيانات MySQL الجديدة وشهادة Aiven العامة في مكان آمن. الشهادة ليست كلمة مرور، لكن التطبيق يحتاجها للتحقق من اتصال MySQL المشفر.
4. تأكد من أن إعدادات Aiven تسمح باتصال خدمة الـ API، وأن عنوان المرسل أو نطاق البريد موثّق في Mailjet.

لا تغيّر `JWT_SECRET` من دون تخطيط؛ تغييره سيخرج المستخدمين من الجلسات الحالية. عند تغيير `FRONTEND_PROXY_SECRET`، حدّث القيمة نفسها في Vercel وFastAPI Cloud ثم أعد نشر الخدمتين. ولا تغيّر `EMAIL_ENCRYPTION_KEY` إلا باتباع إجراء مدروس لتدوير المفاتيح، لأن رسائل صندوق البريد غير المرسلة مشفرة بها.

## 1. تجهيز MySQL وValkey على Aiven

الخدمتان موجودتان في الإعداد الحالي. إذا كنت تعيد إنشاؤهما، أنشئ خدمة MySQL وخدمة Valkey في Aiven، واحفظ بيانات الدخول ومعلومات TLS في مدير كلمات مرور.

### إعداد MySQL

- استخدم المضيف والمنفذ واسم قاعدة البيانات واسم المستخدم وكلمة المرور الظاهرة في صفحة خدمة Aiven. اسم قاعدة البيانات الحالية هو `defaultdb`.
- أنشئ مستخدمًا مخصصًا للـ API بصلاحيات محدودة تكفي للطلبات العادية، ومستخدمًا منفصلًا لتطبيق تغييرات الـ schema. لا تشغّل الـ API بحساب `avnadmin`.
- أنشئ `DATABASE_URL` بصيغة SQLAlchemy وPyMySQL التالية، مع ترميز أي رموز خاصة داخل اسم المستخدم أو كلمة المرور بصيغة URL:

  ```text
  mysql+pymysql://USER:URL_ENCODED_PASSWORD@HOST:PORT/DATABASE?charset=utf8mb4
  ```

- اضبط `DATABASE_TLS_REQUIRED=true` وضع الشهادة كاملة في `DATABASE_SSL_CA_PEM`. التطبيق يتحقق من شهادة الخادم ويشترط TLS 1.2 أو أحدث.
- ابدأ بالقيمتين `DATABASE_POOL_SIZE=2` و`DATABASE_MAX_OVERFLOW=1` لتقليل الاتصالات مع الخطة الصغيرة، ولا ترفعها إلا عند زيادة موارد الخطة أو الحاجة.

### إعداد Valkey

استخدم رابط الخدمة المشفر الذي يبدأ بـ `rediss://` في `REDIS_URL`. انقل اسم المستخدم وكلمة المرور والمضيف والمنفذ ورقم قاعدة البيانات كما توفرها Aiven. التطبيق يتحقق من شهادة TLS ويستخدم Valkey لتحديد معدل الطلبات. عند تعذر الاتصال به، يوقف التطبيق العمليات المحمية بدل تعطيل الحماية.

لا ترسل رابط الخدمة كاملًا في رسائل الدعم؛ فهو يحتوي على بيانات الدخول.

## 2. إعداد ونشر FastAPI Cloud

اسم تطبيق الـ API الحالي هو `foodify-api`. نقطة الدخول هي `app.hosted:app` والمحددة في `back/pyproject.toml`. المجلد `back/.fastapicloud/` يربط نسخة المشروع المحلية بالتطبيق المنشور، وهو مستثنى من Git عمدًا.

من مجلد الباك إند:

```bash
cd /home/hyzin/Projects/Foodify/back
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
fastapi login
```

إذا كان هذا المجلد مربوطًا بالتطبيق بالفعل، انتقل لإعداد المتغيرات. عند العمل على نسخة جديدة من GitHub لا تحتوي على `.fastapicloud/`، نفّذ `fastapi cloud link` واختر التطبيق الحالي `foodify-api`. لا تنشئ تطبيقًا ثانيًا إلا إذا كنت تريد بيئة نشر منفصلة.

أضف المتغيرات الموجودة في `back/.env.free.example` إلى صفحة **Environment Variables** في FastAPI Cloud. اجعل بيانات الاعتماد أسرارًا. يمكنك استخدام سطر الأوامر أيضًا؛ عند عدم كتابة قيمة السر، سيطلبها البرنامج دون إظهارها:

```bash
fastapi cloud env set --secret JWT_SECRET
```

اضبط القيم العامة التالية للإنتاج:

| المتغير | قيمة الإنتاج أو الغرض |
|---|---|
| `APP_ENV` | `production` |
| `DEBUG`, `DOCS_ENABLED` | كلاهما `false` |
| `PUBLIC_BASE_URL` | `https://foodify-api.fastapicloud.dev` |
| `FRONTEND_URL` | `https://foodify-flax.vercel.app` |
| `CORS_ORIGINS` | `["https://foodify-flax.vercel.app"]` |
| `TRUSTED_HOSTS` | `["foodify-api.fastapicloud.dev"]` |
| `DATABASE_TLS_REQUIRED` | `true` |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW` | `2` و`1` |
| `BROWSER_COOKIE_SAME_SITE` | `lax`؛ طلبات المتصفح تمر عبر وسيط Vercel من نفس النطاق |
| `EMAIL_PROVIDER` | `smtp` |
| `SMTP_HOST`, `SMTP_PORT` | `in-v3.mailjet.com` و`587` |
| `SMTP_USE_TLS`, `SMTP_USE_SSL` | `true` و`false`؛ أي STARTTLS |
| `SMTP_FROM_EMAIL` | عنوان المرسل الموثّق في Mailjet |
| `EMBEDDED_EMAIL_WORKER` | `true` |

اجعل المتغيرات التالية أسرارًا: `DATABASE_URL`، و`MIGRATION_DATABASE_URL` (تحتاجه أثناء تطبيق migrations فقط)، و`DATABASE_SSL_CA_PEM`، و`REDIS_URL`، و`JWT_SECRET`، و`EMAIL_ENCRYPTION_KEY`، و`FRONTEND_PROXY_SECRET`، و`SMTP_USERNAME`، و`SMTP_PASSWORD`، وأسرار OAuth التي ستستخدمها. في إعداد SMTP الخاص بـ Mailjet، ضع **API Key** في `SMTP_USERNAME` و**Secret Key** في `SMTP_PASSWORD`. لا تستخدم SMTP key بدل زوج API Key وSecret Key.

أنشئ أسرار التطبيق محليًا في طرفية خاصة، ولا تضع الناتج في Git أو المحادثة:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

استخدم قيمة عشوائية مختلفة لكل من `JWT_SECRET` و`FRONTEND_PROXY_SECRET`، واستخدم ناتج أمر Fernet في `EMAIL_ENCRYPTION_KEY`. احتفظ بها في مدير كلمات مرور وأدخلها مباشرة في إعداد السر لدى مزود الخدمة. لا تستخدم قيم الأمثلة أو قيم التطوير.

### تطبيق تغييرات قاعدة البيانات

قاعدة Aiven الحالية محدثة حتى `20261031_0005`. عند إضافة migration أو تعديل الـ schema مستقبلًا، طبّق التغيير قبل نشر نسخة الكود التي تعتمد عليه. سكربت الإصدار يستخدم `MIGRATION_DATABASE_URL` لتطبيق Alembic، ثم يضيف الأدوار والصلاحيات بحساب التطبيق العادي، ويحافظ على بيانات المستخدمين.

نفّذ `python -m scripts.release` من مجلد `back/` على جهاز آمن يحتوي ملف `.env.production` بإعدادات الإنتاج، بما فيها روابط حساب التهيئة وحساب التطبيق. هذا الملف محلي ومستثنى من Git. بعد اكتمال migration، أزل `MIGRATION_DATABASE_URL` من إعدادات الـ API المنشورة إذا لم تعد تحتاجه. لا تشغّل migrations تلقائيًا عند كل تشغيل للـ API.

### نشر الـ API أو تحديثها

بعد حفظ متغيرات البيئة وتطبيق أي migrations مطلوبة، انشر من مجلد `back/`:

```bash
fastapi deploy
```

يرفع FastAPI Cloud ملفات الباك، ويثبت الاعتماديات، وينشر التطبيق المختار، وينتظر نتيجة النشر افتراضيًا. تغييرات المتغيرات التي تُحفظ من CLI تدخل حيز الاستخدام عند النشر التالي؛ وقد تتيح لوحة التحكم إعادة النشر مباشرة بعد تعديل القيم.

تحقق من التطبيق مباشرة:

```bash
curl 'https://foodify-api.fastapicloud.dev/health/live'
curl 'https://foodify-api.fastapicloud.dev/health/ready'
```

`/health/live` يؤكد أن عملية الـ API تستجيب. أما `/health/ready` فيفترض أن يرجع `200` و`{"status":"ready"}` عند جاهزية MySQL وValkey وتوافق إصدار الـ migrations. توثيق Swagger معطل في الإنتاج عمدًا.

### تحميل بيانات المتاجر والمنتجات في MySQL

قبل نشر واجهة Sprint 2، تأكد أن إعدادات الإنتاج تشير إلى قاعدة MySQL الصحيحة، ثم طبّق migration `20261031_0005_catalog_image_urls` على القاعدة. بعد ذلك شغّل مزامنة الكتالوج من نسخة المشروع الموثوقة، مع توفير إعدادات الاتصال في متغيرات البيئة محليًا:

```bash
cd back
APP_ENV=production python -m scripts.release
APP_ENV=production FOODIFY_ALLOW_DEMO_CATALOG_SEED=true \
  python -m scripts.seed_catalog --allow-production
```

الملف `back/app/ordering/data/demo-catalog.json` مدخل للـseeder في الباك إند فقط. يكتب 8 متاجر و24 منتجًا والفئات وروابط الصور إلى MySQL بمعرّفات ثابتة. الواجهة لا تستورد هذا الملف؛ تقرأ كل هذه البيانات من مسارات FastAPI. مزامنة الكتالوج لا تحذف حسابات أو سلالًا أو طلبات. راجع [شرح بيانات الكتالوج](../back/docs/DEMO_CATALOG.md) قبل تنفيذها.

ملفات العينة جزء من حزمة `app.ordering`، وتدخل ضمن صورة Docker وملفات الباك
المرفوعة إلى FastAPI Cloud. يقرأها السكربت عبر موارد الحزمة، فلا يعتمد على
وجود مجلد خارج `back/`. يتأكد السكربت من مطابقة إصدار قاعدة البيانات قبل
أي كتابة، ويطلب تطبيق migrations أولًا إذا كانت القاعدة قديمة.

بعد نجاح migration والمزامنة، انشر نسخة الباك المتوافقة من مجلد `back/` باستخدام `fastapi deploy`، ثم تحقق من `/health/ready`، وبعدها انشر الفرونت. لا تنشر الواجهة الجديدة قبل وجود مسارات API والكتالوج في قاعدة البيانات.

## 3. إعداد ونشر Vercel

مشروع Vercel الحالي متصل بمستودع GitHub. يقرأ إعدادات `vercel.json` من جذر المستودع؛ وهي تحدد أوامر التثبيت والبناء ومجلد النشر ووسيط الـ API ومسارات تطبيق الصفحة الواحدة.

إعدادات البناء الحالية هي تثبيت الحزم عبر `npm --prefix front ci`، والبناء عبر `npm run build`، ونشر الملفات من `front/dist`. أبقِ جذر مشروع Vercel عند جذر المستودع حتى يستطيع قراءة `vercel.json` وملف الوسيط الموجود في `api/`.

من **Vercel → Project → Settings → Environment Variables**، أضف القيم التالية لبيئة Production. أضفها إلى Preview أيضًا إذا كانت معاينات الفروع ستستخدم الـ API نفسها:

| المتغير | القيمة |
|---|---|
| `FOODIFY_API_ORIGIN` | `https://foodify-api.fastapicloud.dev`؛ النطاق فقط، من دون `/api/v1` |
| `FRONTEND_PROXY_SECRET` | نفس القيمة الموجودة في FastAPI Cloud حرفيًا |
| `VITE_DATA_SOURCE` | `api` |
| `VITE_API_BASE_URL` | `/api/v1` |
| `VITE_APP_ENV` | `production` |

المتغيران الوحيدان اللذان يحتاجهما وسيط Vercel وقت التشغيل هما `FOODIFY_API_ORIGIN` و`FRONTEND_PROXY_SECRET`. متغيرات `VITE_*` عامة وتُضمّن في ملفات المتصفح؛ لا تضع فيها أسرار قاعدة البيانات أو البريد أو OAuth أو JWT أو سر الوسيط. إعداد الإنتاج الافتراضي يستخدم أصلًا `/api/v1`، لكن إضافة القيم العامة صراحةً تجعل إعدادات النشر أسهل في المراجعة.

احفظ المتغيرات ثم أعد نشر آخر نسخة Production. لنشر تغيير في الكود، احفظ التغيير في commit وارفعه إلى فرع الإنتاج المحدد في Vercel؛ بعدها يبني Vercel هذه النسخة وينشرها. تستدعي React المسارات `/api/v1/*` من نطاق الواجهة، ثم يمررها `api/proxy.mjs` إلى FastAPI مع ترويسات التفويض وكوكيز تجديد الجلسة.

افتح [foodify-flax.vercel.app](https://foodify-flax.vercel.app) وتأكد أن الواجهة تعمل. ومن تبويب Network في المتصفح، راجع أن طلب الـ API يذهب إلى `https://foodify-flax.vercel.app/api/v1/...` ويحصل على استجابة. لا تشارك كوكيز تجديد الجلسة أو access tokens في صور الشاشة أو السجلات.

## 4. إعداد تسجيل الدخول عبر Google وFacebook (اختياري)

يحتاج كل مزود إلى ثلاثة إعدادات في الباك: Client ID وClient Secret وRedirect URI. لن يُفعّل المزود إذا كان أحدها ناقصًا. خزّن أسرار العملاء كأسرار في FastAPI Cloud.

في إعداد Foodify الحالي، أُضيفت قيم Google إلى FastAPI Cloud بعنوان العودة الخاص بالإنتاج. فحص بدء OAuth ينجح ويوصل إلى Google؛ إكمال تسجيل الدخول نفسه يحتاج تجربة الزر من المتصفح والموافقة بحساب مسموح له في مشروع Google.

سجّل روابط callback التالية حرفيًا في لوحة المطور الخاصة بكل مزود:

```text
https://foodify-api.fastapicloud.dev/api/v1/auth/oauth/google/callback
https://foodify-api.fastapicloud.dev/api/v1/auth/oauth/facebook/callback
```

أضف `OAUTH_GOOGLE_CLIENT_ID` و`OAUTH_GOOGLE_CLIENT_SECRET` و`OAUTH_GOOGLE_REDIRECT_URI` لتفعيل Google. ولتفعيل Facebook أضف `OAUTH_FACEBOOK_CLIENT_ID` و`OAUTH_FACEBOOK_CLIENT_SECRET` و`OAUTH_FACEBOOK_REDIRECT_URI`؛ يوجد أيضًا `OAUTH_FACEBOOK_GRAPH_VERSION`. احفظ إعدادات المزود وأعد نشر الباك. أضف نطاق الواجهة إلى النطاقات المسموح بها في مزود OAuth حسب متطلباته.

يستقبل الـ API عودة OAuth، ثم تكمل الواجهة عملية تسجيل الدخول باستخدام callback ticket قصير الصلاحية. لا تضع token أو client secret في رابط callback.

## 5. إرسال البريد وروابط التأكيد

يضع الـ API رسائل تأكيد البريد واستعادة كلمة المرور في صندوق بريد مشفر داخل MySQL. عند ضبط `EMBEDDED_EMAIL_WORKER=true`، يقرأ عامل يعمل مع التطبيق الرسائل ويرسلها عبر Mailjet SMTP باتصال TLS. قبول الـ API للطلب لا يعني وحده أن الرسالة وصلت إلى المستخدم.

لمراجعة رسالة، افتح حالتها وسجل أحداثها في Mailjet. حدث `sent` يعني أن خادم بريد المستلم قبل الرسالة، لكنه لا يضمن ظهورها في Inbox بدلًا من Spam أو Promotions. حالة `hardbounce` أو `user unknown` تعني أن خادم المستلم رفض العنوان، غالبًا بسبب خطأ إملائي أو عدم وجود صندوق البريد. راجع بريد الحساب والتحقق من عنوان المرسل في Mailjet قبل تغيير إعدادات SMTP.

تشير روابط البريد إلى مساري الواجهة `/verify-email` و`/reset-password`. يعيد `vercel.json` توجيه المسارين إلى React SPA؛ لذلك يجب ألا تستخدم روابط الإنتاج منفذ تطوير مثل `3000` أو `5173`.

## 6. التحقق اليدوي بعد النشر

هذه خطوات تحقق يدوي وليست مجموعة اختبارات آلية:

1. تأكد من استجابة `GET https://foodify-api.fastapicloud.dev/health/live`.
2. تأكد من أن `GET https://foodify-api.fastapicloud.dev/health/ready` يرجع حالة الجاهزية.
3. افتح الصفحة الرئيسية على Vercel، وتأكد من أن طلبات `/api/v1` تصل إلى الـ API عبر الوسيط.
4. أنشئ حسابًا مخصصًا للتجربة باستخدام بريد تستطيع فتحه. راجع أن الرسالة تظهر في Mailjet بلا ارتداد، ثم افتح رابط التأكيد على نطاق Vercel.
5. جرّب تسجيل الدخول والخروج واستعادة كلمة المرور بهذا الحساب. راجع حدث الإرسال في Mailjet ومجلدي Spam وPromotions عند الحاجة.
6. إذا كان OAuth مفعّلًا، جرّب تسجيل الدخول بكل مزود وتأكد من callback والعودة إلى الواجهة. وإذا كنت تستخدم الملف الشخصي والعناوين، راجع أن الطلبات تظل موثقة بعد إعادة تحميل الصفحة.

نجح فحص جاهزية الـ API وقُبلت رسالة تأكيد من خادم البريد في 2026-10-21. هذه نتيجة تاريخية ولا تثبت حالة الخدمات الحالية؛ تحقق من `/health/ready` ومن وصول رسالة جديدة بعد كل تغيير في إعدادات الخدمات.

## تحديث النشر وتشخيص الأعطال

| المشكلة | أول ما يجب مراجعته |
|---|---|
| Vercel يعرض “API deployment is not configured yet” | أضف `FOODIFY_API_ORIGIN` إلى بيئة Vercel الصحيحة ثم أعد النشر. |
| طلبات الـ API عبر Vercel ترجع `503` | راجع حالة النشر وسجلات FastAPI Cloud؛ قد يحتاج التطبيق المجاني وقتًا للاستيقاظ. تأكد أن سر الوسيط متطابق في الخدمتين. |
| `/health/ready` ترجع `503` | راجع رابط MySQL وترميز كلمة المرور وشهادة TLS والسماح باتصال Aiven ورابط Valkey بصيغة `rediss://` وتوافق Alembic مع الكود المنشور. |
| رسائل outbox تتراكم أو لا تظهر في Mailjet | راجع `EMBEDDED_EMAIL_WORKER=true` وبيانات SMTP وSTARTTLS على المنفذ 587 والتحقق من المرسل وسجلات العامل في FastAPI Cloud. |
| Mailjet يعرض `hardbounced` | صحح بريد المستلم المسجل في الحساب؛ بيانات SMTP لا تعالج عنوانًا غير موجود. |
| حالة البريد `sent` لكن المستخدم لا يجد الرسالة | راجع Spam وPromotions وتأكد من عنوان المستلم. `sent` يؤكد قبول خادم المستلم للرسالة، لا ظهورها في Inbox. |
| Google أو Facebook يعرض `redirect_uri_mismatch` | قارن رابط callback المسجل في لوحة المزود مع الرابط المضبوط للباك حرفًا بحرف. |
| كوكي تجديد الجلسة لا تُحفظ | اجعل طلبات الإنتاج تمر عبر وسيط Vercel من نفس النطاق، وتأكد من تمرير `Set-Cookie` وصحة إعدادات الوسيط. |

لنشر تغييرات الباك، نفّذ `fastapi deploy` من `back/`. لنشر تغييرات الواجهة، ارفع commit إلى فرع الإنتاج المتصل بـ Vercel ثم تابع حالة البناء والنشر. إذا احتاج التغيير إلى migration، طبّقها قبل نشر الكود الذي يعتمد عليها. قد يتطلب تغيير متغير بيئة إعادة نشر الخدمة التي تستخدمه.

## ملفات الإعداد والأسرار

- الملفات `back/.env.free.example` و`back/.env.production.example` و`front/.env.production.example` قوالب فقط. لا تضع بياناتك الحقيقية فيها ثم ترفعها إلى Git.
- الملفات `.env.deploy.local` و`.env.production` ومجلد ربط FastAPI Cloud إعدادات محلية، ويجب أن تظل مستثناة من Git.
- متغيرات الواجهة التي تبدأ بـ `VITE_` تظهر في ملفات المتصفح، لذا لا تعتبرها أسرارًا.
- إذا كُشفت بيانات اعتماد، ألغِها لدى مزودها وأنشئ بديلًا وحدّث كل خدمة تستخدمها. نسّق تغيير كلمات مرور MySQL وValkey مع إعدادات الـ API. يجب تحديث سر الوسيط في Vercel وFastAPI Cloud معًا. تغيير JWT Secret ينهي الجلسات الحالية.
- راجع حدود الخطة والفواتير في لوحة كل مزود؛ الخطط المجانية وحدودها قد تتغير.

## مراجع رسمية

- [أمر النشر في FastAPI Cloud](https://fastapicloud.com/docs/fastapi-cloud-cli/deploy/)
- [متغيرات البيئة في FastAPI Cloud](https://fastapicloud.com/docs/builds-and-deployments/environment-variables/)
- [ربط المشروع بتطبيق FastAPI Cloud](https://fastapicloud.com/docs/fastapi-cloud-cli/link/)
- [إعداد مشروع Vercel](https://vercel.com/docs/projects/project-configuration)
- [اتصال MySQL على Aiven باستخدام TLS](https://docs.aiven.io/docs/products/mysql/howto/connect-mysql)
- [إعداد SMTP في Mailjet](https://documentation.mailjet.com/hc/en-us/articles/360043227473-How-to-configure-my-SMTP-settings)
- [سجل الرسائل في Mailjet](https://dev.mailjet.com/docs/email-api/getting-started/view-message-history)
- [معاني أحداث Mailjet](https://dev.mailjet.com/email/guides/webhooks/)
