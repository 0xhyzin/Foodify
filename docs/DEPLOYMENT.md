# نشر Foodify بالخطة المجانية

## الوضع الحالي

- الكود اترفع في ريبو خاصة: [0xhyzin/Foodify](https://github.com/0xhyzin/Foodify).
- الواجهة منشورة على [foodify-flax.vercel.app](https://foodify-flax.vercel.app).
- الباك وقاعدة البيانات لم ينشرا بعد؛ مطلوب إعداد حسابي Aiven وBrevo وبياناتهما. طلبات الحساب ترجع `503` إلى أن يتم ضبط عنوان API الفعلي على Vercel.
- لم تُنشأ أي خدمة Render مدفوعة، ولم تُضاف أو تُشغل اختبارات في هذا التعديل.

## توزيع الخدمات

| الجزء | الاستضافة | الخطة |
|---|---|---|
| React + TypeScript | Vercel | Hobby |
| FastAPI + outbox worker | Render web service واحد | Free |
| MySQL الحقيقي | Aiven for MySQL | Free، مساحة 1 GB |
| محددات المحاولات | Aiven for Valkey، متوافق مع Redis client الحالي | Free |
| رسائل التأكيد واسترجاع كلمة المرور | Brevo API عبر HTTPS | Free، حتى 300 رسالة يوميًا بحسب حدود الحساب |

هذه خطط مجانية للاستخدام المحدود؛ تأكد من اختيار Free عند إنشاء الخدمات، وليس trial لخطة مدفوعة. توجد حدود وحالات خمول موضحة أدناه. قاعدة التطبيق تظل MySQL، ولا يوجد تحويل إلى PostgreSQL أو Supabase.

## ما الذي جهزناه

`render.yaml` الآن ينشئ web service مجانية فقط. إعداد الأربع خدمات المدفوعة محفوظ كخيار منفصل في `deploy/render.paid.yaml`، وشرحه في [الدليل المدفوع](DEPLOYMENT_PAID.md). لا تستخدمه للخطة المجانية.

التشغيل المجاني يمر كالتالي:

```text
Vercel React
  → /api/v1 على نفس أصل الواجهة
  → api/proxy.mjs: نقل HTTP فقط
  → FastAPI على Render
  → MySQL على Aiven باتصال TLS موثق
  → Valkey على Aiven باتصال rediss
  → outbox مشفر في MySQL
  → worker داخل نفس عملية خدمة الويب
  → Brevo HTTPS API
```

منطق التسجيل وJWT وOAuth والعناوين ما زال في FastAPI. الـ proxy على Vercel لا يتصل بقاعدة البيانات ولا يخزن جلسات؛ ينقل `Set-Cookie` حتى تبقى refresh cookie على نفس أصل الواجهة.

عامل البريد يستخدم نفس `deliver_next_email` وlocking وretry وexpiry الموجودين بالفعل. فصلناه عن طريقة التشغيل: يمكن تشغيله مستقلًا بالأمر القديم، أو داخل lifecycle التطبيق عند `EMBEDDED_EMAIL_WORKER=true`. توقف السيرفر يترك الطلبات غير المنتهية في MySQL، لتُستكمل بعد تشغيله.

إرسال البريد يمر من interface `EmailSender`. الـ composition root في `email_sender.py` يختار SMTP أو Brevo؛ نص الرسالة والرابط يأتيان من `email_content.py` لكلا المزودين. التشغيل المحلي يظل SMTP افتراضيًا، ولا يتغير Mailpit أو ملف `.env.development`.

## تجهيز حسابات الخدمات

أنشئ حسابًا مجانيًا في [Aiven](https://console.aiven.io/signup) وحسابًا في [Brevo](https://app.brevo.com/account/register). في Brevo أكمل تفعيل transactional email وإثبات عنوان المرسل المطلوب.

الملف المحلي `.env.deploy.local` مستبعد من Git ومهيأ بصلاحيات ملف خاصة. ضع البيانات فيه محليًا فقط، دون إرسالها في المحادثة:

| المفتاح | المطلوب |
|---|---|
| `AIVEN_API_TOKEN` | Authentication token لإدارة الخدمات في حسابك، يستخدم أثناء الإعداد فقط |
| `AIVEN_PROJECT` | اسم مشروع Aiven، ويمكن تركه فارغًا إلى أن نقرأ المشاريع المتاحة |
| `AIVEN_MYSQL_SERVICE` | الاسم المقترح `foodify-mysql` |
| `AIVEN_VALKEY_SERVICE` | الاسم المقترح `foodify-valkey` |
| `BREVO_API_KEY` | API key من قسم SMTP & API في Brevo، وليس SMTP password |
| `SMTP_FROM_EMAIL` | عنوان المرسل الذي فعلته في Brevo |

المثال الخالي من الأسرار في [`.env.deploy.local.example`](../.env.deploy.local.example) يوضح الأسماء. توكن إدارة Aiven لا يدخل في build الواجهة أو إعداد تشغيل FastAPI؛ بعد الإعداد يمكن إلغاؤه. مفتاح Brevo يكون على الباك فقط.

## إنشاء MySQL وValkey على Aiven

1. أنشئ خدمتي MySQL وValkey باستخدام خطة Free، وليس PostgreSQL. Aiven يسمح بخدمة واحدة من كل نوع في المؤسسة حسب حدود الخطة.
2. من MySQL احصل على host وport واسم القاعدة وشهادة CA العامة. لا تفترض أن المنفذ `3306`؛ استخدم القيمة المعروضة في الحساب.
3. جهز حسابًا منفصلًا للتطبيق بصلاحيات DML على قاعدة التطبيق: `SELECT/INSERT/UPDATE/DELETE`. حساب التهيئة يستخدم migrations، بينما حساب التطبيق يستخدم الطلبات اليومية. الحساب الافتراضي `avnadmin` يحفظ لخطوات التهيئة.
4. عنوان MySQL داخل SQLAlchemy يبدأ بـ `mysql+pymysql://`. يجب URL-encode لكلمة المرور عند وضعها في connection URL.
5. اتصال MySQL في التطبيق يستخدم `DATABASE_SSL_CA_PEM` أو ملف `DATABASE_SSL_CA` مع التحقق من شهادة الخادم واسم المضيف. لا تستخدم `ssl_verify=false`.
6. عنوان Valkey يكون `rediss://...` مع اسم المستخدم وكلمة المرور والمنفذ من Aiven. Redis adapter الحالي يتصل به، ويتحقق من الشهادة واسم المضيف.

## إعداد FastAPI على Render

اربط الريبو `0xhyzin/Foodify` وفرع `main` بخدمة Docker مجانية، أو استخدم `render.yaml` كـ Blueprint. الملفات داخل `back/`، وDockerfile هو `back/Dockerfile` وbuild context هو `back/`.

```text
Plan: Free
Docker command: python -m scripts.hosted_start
Health check: /health/ready
Workers: 1
```

`scripts.hosted_start` يجهز إصدار قاعدة البيانات بـ Alembic وseed للأدوار، ثم يستبدل نفسه بـ Uvicorn. لا يفرغ القاعدة ولا ينشئ مستخدمين تجريبيين. بعد اكتمال التهيئة، يمكن إزالة `MIGRATION_DATABASE_URL` من runtime حتى يحتاج أي تغيير schema لاحق إضافة صلاحية التهيئة مجددًا.

متغيرات التشغيل موضحة في [`.env.free.example`](../back/.env.free.example). أهمها:

| المتغير | القيمة |
|---|---|
| `APP_ENV` | `production` |
| `DEBUG`, `DOCS_ENABLED` | `false` |
| `DATABASE_URL` | رابط MySQL لحساب التطبيق المحدود |
| `MIGRATION_DATABASE_URL` | رابط حساب التهيئة، مطلوب عندما يوجد schema جديد |
| `DATABASE_TLS_REQUIRED` | `true` |
| `DATABASE_SSL_CA_PEM` | شهادة CA العامة من Aiven؛ يقبل `\n` داخل النص |
| `REDIS_URL` | رابط Valkey بصيغة `rediss://` |
| `EMAIL_PROVIDER` | `brevo` |
| `BREVO_API_KEY` | مفتاح Brevo الفعلي |
| `SMTP_FROM_EMAIL` | المرسل المعتمد في Brevo؛ الاسم محفوظ للتوافق مع SMTP |
| `EMBEDDED_EMAIL_WORKER` | `true` |
| `FRONTEND_URL` | `https://foodify-flax.vercel.app` |
| `CORS_ORIGINS` | `["https://foodify-flax.vercel.app"]` |
| `PUBLIC_BASE_URL` | أصل API HTTPS على Render |
| `TRUSTED_HOSTS` | قائمة JSON فيها hostname الخاص بـ API |
| `FRONTEND_PROXY_SECRET` | سر عشوائي جديد، نفس القيمة على Vercel |

`JWT_SECRET` ومفتاح Fernet باسم `EMAIL_ENCRYPTION_KEY` يجب توليدهما للإنتاج، وعدم استخدام أسرار التطوير. Render Blueprint يولد قيمًا عشوائية لهما. يعمل البريد عبر HTTPS على المنفذ `443`، لأن الخطة المجانية تقيد منافذ SMTP الشائعة.

## إكمال الربط على Vercel

إعداد الجذر `vercel.json` يبني `front/` ويفتح `/verify-email` و`/reset-password` و`/oauth/callback`، ثم React يعالج fragment الخاص بالتوكن.

بعد معرفة عنوان API المنشور، اضبط متغيرين على Vercel:

```text
FOODIFY_API_ORIGIN=https://YOUR_API.onrender.com
FRONTEND_PROXY_SECRET=نفس_السر_العشوائي_على_Render
```

لا تضف `/api/v1` إلى `FOODIFY_API_ORIGIN`، ولا تضع هذه الأسرار في متغيرات `VITE_`. الواجهة تستخدم `VITE_DATA_SOURCE=api` و`VITE_API_BASE_URL=/api/v1` افتراضيًا في build الإنتاج. أعد نشر الواجهة بعد ضبط إعدادات الخادم.

## Google وFacebook

مفاتيح OAuth الحالية لا تصبح جاهزة للإنتاج بمجرد رفع الكود. أضف قيم `CLIENT_ID` و`CLIENT_SECRET` و`REDIRECT_URI` لكل مزود على الباك، وسجل callback HTTPS نفسه حرفيًا في Google Cloud وMeta:

```text
https://YOUR_API.onrender.com/api/v1/auth/oauth/google/callback
https://YOUR_API.onrender.com/api/v1/auth/oauth/facebook/callback
```

روابط التأكيد واسترجاع الباسورد تستخدم أصل الواجهة المنشور. تغيير إعداد `FRONTEND_URL` يطبق على عامل البريد المدمج مع إعادة تشغيل API نفسه.

## حدود المجاني

- Render Free ينام بعد الخمول. أول طلب قد ينتظر بدء الخدمة، والـ proxy يسمح بمهلة أطول لاستيعاب ذلك. لا يوجد ضمان أن كل cold start سينتهي قبل مهلة الطلب.
- عامل البريد يعمل عندما تكون خدمة الويب مستيقظة. رسائل retry المنتظرة تستكمل عند عودة السيرفر، وقد تنتهي صلاحية رابط قديم؛ يمكن طلب رسالة جديدة.
- MySQL المجاني على Aiven محدود بـ 1 GB ومسار single node. قد توقف Aiven الخدمات غير النشطة بعد تنبيه؛ هذا ليس ضمان توافر لإنتاج كبير.
- Brevo يطبق الحد اليومي وتفعيل المرسل وقواعد الحساب. القالب يجهز التكامل ولا يتجاوز هذه الحدود.
- الميزانية صفر ضمن الخطط المجانية وحدودها. لا تتم ترقية أي خطة تلقائيًا من الكود.

## التحقق المنفذ

Frontend production build وTypeScript compilation، وPython syntax compilation، وتوليد Alembic SQL بدون اتصال، وفحص JSON/YAML وملفات shell، وفحص استبعاد الأسرار من Git. لا توجد اختبارات auth أو إرسال رسائل فعلية أو حسابات تجريبية. التحقق من حسابات Aiven وBrevo والـ API المنشور يظل مطلوبًا بعد توفر بيانات الخدمات.

## مراجع

- [Aiven MySQL Free](https://aiven.io/docs/products/mysql/concepts/mysql-free-tier)
- [Aiven Valkey Free](https://aiven.io/docs/products/valkey/concepts/valkey-free-tier)
- [Aiven TLS certificates](https://aiven.io/docs/platform/concepts/tls-ssl-certificates)
- [Render Free](https://render.com/docs/free)
- [Brevo Free plan](https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans)
- [Brevo transactional email API](https://developers.brevo.com/docs/send-a-transactional-email)
