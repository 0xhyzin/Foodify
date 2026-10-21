# نشر Foodify

الكود موجود في ريبو خاصة على حساب صاحب المشروع: [0xhyzin/Foodify](https://github.com/0xhyzin/Foodify). الريبو القديمة لم تتغير.

## التقسيم النهائي

| الجزء | التقنية | الاستضافة |
|---|---|---|
| الواجهة | React + TypeScript + Vite | Vercel |
| API | Python + FastAPI | Render web service |
| إرسال البريد | Python transactional outbox worker | Render background worker |
| قاعدة البيانات | MySQL 8.4 | Render private service + persistent disk |
| تحديد محاولات الطلبات | Redis 7.4 | Render private service بكلمة مرور |

قاعدة البيانات تظل MySQL. لا توجد migrations إلى PostgreSQL ولا اعتماد على Supabase في هذا الإعداد. Supabase ليس استضافة MySQL أو سيرفر FastAPI.

## حالة النشر

وجود الملفات والـ build لا يعني أن الباك منشور. إنشاء موارد Render يحتاج الموافقة على تكلفتها وتوفير إعداد SMTP الفعلي. إلى أن يكتمل ذلك، الواجهة تفتح وتعرض الصفحات، وطلبات الحساب ترجع `503 service_unavailable` بشكل واضح بدل بيانات تجريبية.

لا توجد اختبارات جديدة في هذا التغيير ولا pipeline يشغل الاختبارات. خطوات التحقق هي build للفرونت وPython syntax compilation فقط.

## ما الذي تغير

- `vercel.json`: بناء الواجهة من `front/`، وإتاحة المسارات الفعلية لروابط تأكيد البريد وإعادة كلمة المرور وOAuth.
- `api/proxy.mjs`: طبقة نقل صغيرة من Vercel إلى عنوان FastAPI المحدد في إعدادات الخادم. لا تحتوي منطق تسجيل أو قاعدة بيانات.
- `front/src/app/config.ts`: وضع الإنتاج الافتراضي `api`، والعنوان `/api/v1`. وضع التصميم `demo` يظل اختيارًا صريحًا.
- `front/vite.config.ts`: CSP يسمح بطلبات نفس الأصل عند استخدام `/api/v1`.
- `render.yaml`: أربع خدمات مستقلة؛ لا ينشر الواجهة على Render.
- `deploy/mysql/`: MySQL بقرص دائم، وحساب تطبيق محدود وlogin آخر للمigrations.
- `deploy/redis/`: Redis خاص بكلمة مرور، ولا يضع كلمة المرور في command-line arguments.
- `back/app/core/config.py`: يبني روابط MySQL وRedis بأمان من مكونات الخدمات، مع URL encoding لكلمات المرور. روابط `DATABASE_URL` و`REDIS_URL` الصريحة ما زالت تعمل وتتقدم على المكونات.
- `back/migrations/env.py`: يستخدم `MIGRATION_DATABASE_URL` عند وجوده بدل حساب التطبيق.
- `back/scripts/release.py`: ينتظر اتصال MySQL، يطبق Alembic، ثم ينشئ تعريفات الأدوار والصلاحيات وأنواع التوكنات. لا يحذف حسابات ولا ينشئ حساب أدمن افتراضيًا.
- `back/app/core/client_ip.py`: يقبل IP المستخدم من proxy الواجهة فقط عند وجود توقيع HMAC صحيح وحديث؛ غير ذلك يستخدم عنوان الاتصال المعتاد.

## نشر الواجهة على Vercel

اربط مشروع Vercel بالريبو الجديدة، واجعل Root Directory هو جذر الريبو `.`. الإعدادات موجودة في `vercel.json`:

```text
Framework: Vite
Install: npm --prefix front ci
Build: npm run build
Output: front/dist
```

متغيرات الخادم المطلوبة بعد نشر FastAPI:

| المتغير | القيمة |
|---|---|
| `FOODIFY_API_ORIGIN` | عنوان Render الفعلي، مثل `https://foodify-api-xxxx.onrender.com`، بدون `/api/v1` |
| `FRONTEND_PROXY_SECRET` | نفس السر العشوائي الموجود على خدمة FastAPI |

يمكن ترك متغيرات Vite غير مضبوطة، فالإنتاج يستخدم `/api/v1` افتراضيًا. إذا كانت موجودة من نشر سابق، اجعل `VITE_DATA_SOURCE=api` و`VITE_API_BASE_URL=/api/v1`. لا تضع بيانات MySQL أو SMTP أو OAuth في أي متغير يبدأ بـ `VITE_`.

الـ proxy لا يقبل upstream من المستخدم؛ العنوان من إعداد الخادم فقط، ويتطلب HTTPS. ينقل فقط headers اللازمة، ولا يتبع redirects، ويقيد حجم الطلب ومهلة الاتصال. ينقل `Set-Cookie` حتى تبقى refresh cookie على أصل الواجهة؛ هذا يتجنب الاعتماد على third-party cookies بين Vercel وRender.

## نشر الباك وMySQL على Render

1. افتح **New → Blueprint**، واربط الريبو `0xhyzin/Foodify` وفرع `main`.
2. يستخدم Blueprint ملف `render.yaml`. راجع أسعار **أربع خدمات Starter** والقرص **10 GB** قبل الموافقة. هذه الموارد ليست خطة مجانية.
3. اختر نفس workspace/region للخدمات؛ الملف يستخدم Frankfurt. MySQL وRedis من نوع private service ولا يحصلان على endpoint عام.
4. أدخل القيم المطلوبة أدناه. Render ينشئ كلمات مرور قواعد البيانات وJWT ومفتاح تشفير outbox عشوائيًا، ويشارك فقط القيم المطلوبة بين الخدمات.
5. عند أول نشر، تهيئة MySQL تنشئ حساب التطبيق `foodify` بصلاحيات `SELECT/INSERT/UPDATE/DELETE`، وحساب `foodify_migrator` بصلاحيات schema على قاعدة `foodify` فقط. كلمة root تبقى داخل خدمة MySQL.
6. pre-deploy الخاص بخدمة API ينفذ `python -m scripts.release`. العامل لا يحصل على كلمة مرور migrator، ولا يشغل migrations.
7. اضبط عنوان API النهائي في `PUBLIC_BASE_URL` و`TRUSTED_HOSTS`، ثم أعد نشر API والعامل إذا تغير العنوان. اضبط `FOODIFY_API_ORIGIN` في Vercel وأعد نشر الواجهة.

لا تضف `DATABASE_URL` أو `REDIS_URL` من إعداد جهازك إلى Blueprint؛ الملف يبنيهما من عناوين الخدمات الخاصة وكلمات المرور المشتركة. حساب MySQL واسم القاعدة في هذا القالب هما `foodify`. برامج تهيئة MySQL تعمل مرة واحدة عند إنشاء قرص فارغ، ولا تعيد تعيين كلمات المرور عند إعادة تشغيل قرص موجود.

### القيم التي تحتاج بياناتك

| متغير Render | القيمة المطلوبة |
|---|---|
| `PUBLIC_BASE_URL` | عنوان FastAPI المنشور HTTPS |
| `FRONTEND_URL` | أصل الواجهة المنشور HTTPS بدون `/#/login` |
| `CORS_ORIGINS` | JSON مثل `["https://YOUR_FRONTEND.vercel.app"]` |
| `TRUSTED_HOSTS` | JSON فيه hostname الخاص بـ API فقط، بدون scheme أو path |
| `FRONTEND_PROXY_SECRET` | سر جديد بطول 32 bytes على الأقل، نفس القيمة على Vercel |
| `SMTP_HOST` | خادم SMTP الحقيقي |
| `SMTP_USERNAME` | مستخدم SMTP |
| `SMTP_PASSWORD` | كلمة مرور SMTP أو App Password المناسبة للمزود |
| `SMTP_FROM_EMAIL` | بريد إرسال فعلي تسمح به خدمة SMTP |

القالب يستخدم STARTTLS على `587`. لو المزود يحتاج SSL على `465`، عدّل API والعامل معًا إلى `SMTP_PORT=465` و`SMTP_USE_SSL=true` و`SMTP_USE_TLS=false`.

لا تستخدم Mailpit أو localhost في الإنتاج. خدمة البريد تحتاج تشغيلًا مستمرًا؛ نجاح register أو forgot-password بـ `202` يعني أن الرسالة دخلت outbox، وليس أنها وصلت بالفعل. خطة Render المجانية تقيد منافذ SMTP المعتادة، لذلك القالب يستخدم خدمات مدفوعة.

يمكن توليد سر الـ proxy محليًا، ثم إدخاله في لوحتي الخدمات بدون وضعه في Git:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

### Google وFacebook

لكل مزود تضيف القيم الثلاث معًا على خدمة API:

```text
OAUTH_GOOGLE_CLIENT_ID
OAUTH_GOOGLE_CLIENT_SECRET
OAUTH_GOOGLE_REDIRECT_URI=https://YOUR_API.onrender.com/api/v1/auth/oauth/google/callback

OAUTH_FACEBOOK_CLIENT_ID
OAUTH_FACEBOOK_CLIENT_SECRET
OAUTH_FACEBOOK_REDIRECT_URI=https://YOUR_API.onrender.com/api/v1/auth/oauth/facebook/callback
```

سجل عنوان callback نفسه حرفيًا في Google Cloud أو Meta. أسرار OAuth لا تدخل في build الواجهة. لا يحتاج عامل البريد مفاتيح Google أو Facebook.

روابط الإيميل تستخدم `FRONTEND_URL/verify-email#token=...` و`FRONTEND_URL/reset-password#token=...`. قيمة `FRONTEND_URL` مشتركة مع العامل، لذلك عند تغييرها تأكد من نشر العامل أيضًا.

## البيانات وإعادة النشر

- التشغيل المحلي وملفات `.env.development` يظلان كما هما؛ رفع الكود لا ينقل حسابات MySQL المحلية تلقائيًا.
- قرص MySQL على `/var/lib/mysql` يحتفظ بالبيانات عند إعادة نشر الصورة. لا تحذف القرص لإعادة نشر التطبيق.
- خذ نسخًا منطقية باستخدام `mysqldump` قبل migrations مهمة؛ snapshots للقرص ليست بديلًا عن backup متسق لقاعدة البيانات.
- auto-deploy مفعّل لـ API والعامل، ومغلق لخدمات MySQL وRedis حتى لا يعاد تشغيلهما عند كل تعديل للواجهة.
- endpoint `/health/ready` يفحص اكتمال migrations واتصال Redis، و`/health/live` يفحص وصول التطبيق فقط.

## الملفات الحساسة

ملفات `.env` الحقيقية و`.venv` و`node_modules` وbuild outputs مستبعدة من Git. Vercel يستبعد مجلد `back/` و`deploy/` من رفع CLI. لا ترفع dumps لقاعدة البيانات أو روابط reset فعلية أو ملفات Postman تحتوي توكنات مستخدمين.

## مراجع الاستضافة

- [Render: MySQL](https://render.com/docs/deploy-mysql)
- [Render: Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render: SMTP limits on free services](https://render.com/docs/free)
- [Vercel: Vite](https://vercel.com/docs/frameworks/frontend/vite)
- [Supabase: PostgreSQL database](https://supabase.com/docs/guides/database/overview)
