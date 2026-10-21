# Foodify API

باك إند FastAPI لتطبيق توصيل الطعام والبقالة. المرحلة الحالية تنفذ حساب العميل فقط: التسجيل والدخول، تأكيد البريد، استرجاع كلمة المرور، جلسات JWT، تسجيل Google وFacebook، رقم الهاتف وعناوين التوصيل.

المشروع مقسم حسب الكيان ثم العملية: كل وظيفة مثل تسجيل الدخول لها فولدر مستقل داخل `app/users/` يحتوي `dto.py` و`interfaces.py` و`service.py` و`dependencies.py` و`router.py`. داخله معمارية ثلاث طبقات مبسطة: `router → service → repository`، مع واجهات تفصل الاعتمادات وDependency Injection لكل عملية. الـ repositories وأجزاء الجلسات والبريد المشتركة لها ملفات مستقلة داخل `app/users/shared/`، وصيغة الأخطاء موحدة. قاعدة البيانات MySQL، ومحددات المحاولات مشتركة عبر Redis، والبريد يرسل من worker مستقل عبر transactional outbox مشفر.

إعداد Render للـ API والـ worker وMySQL وربط Vercel موضح بالكامل في [دليل النشر](../docs/DEPLOYMENT.md). ملفات البيئة المحلية الحالية لم تتغير. `python -m scripts.release` ينفذ migrations بحساب مخصص ثم يعمل seed للأدوار بحساب التطبيق المحدود عند النشر.

## نقطة البداية والنسخة القديمة

كان المشروع Flask + SQLite، وفيه حسابات ومطاعم ومنيو ومستخدم بدور واحد. التنفيذ الحالي يفصل حساب العميل في FastAPI ويؤسس علاقات أدوار وصلاحيات قابلة للتوسع. ملفات Flask محفوظة في `legacy/`، وملف `foodify.db` الأصلي محفوظ ولم يستخدم كقاعدة للتنفيذ الجديد. لم ننفذ نقل بيانات قديمة تلقائيًا.

ملفات `tests/` القديمة محفوظة بدون تعديل وتعتمد على Flask؛ ليست متوافقة مع FastAPI الجديد. لم تنشأ أو تشغل اختبارات ضمن هذا العمل، وفق نطاق المهمة. بيئة `test` متاحة للفريق المختص لتجهيز اختباراتهم.

## الوثائق

| الملف | المحتوى |
| --- | --- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | تقسيم الملفات، حدود الطبقات، ERD، الـ bridges وقواعد منع التكرار. |
| [FUNCTIONS.md](docs/FUNCTIONS.md) | كل endpoint، الدالة التي يناديها، الجداول المتأثرة ومسار التنفيذ. |
| [SECURITY.md](docs/SECURITY.md) | ضوابط الأمان وربطها بـ OWASP Top 10:2025 ومسؤوليات النشر. |
| [OAUTH.md](docs/OAUTH.md) | إعداد Google/Meta والتحقق من provider identity وتفاصيل flow الربط. |
| [Postman](postman/README.md) | استيراد الـ collection والبيئات وتشغيل كل flow يدويًا. |

## أين أعدل كل وظيفة؟

ابدأ بفولدر العملية نفسها؛ مثلًا تسجيل الدخول كله في `app/users/login/`:

```text
app/users/
  login/
    dto.py           LoginRequest وLoginResponse
    interfaces.py    عقد خدمة تسجيل الدخول
    service.py       LoginService.execute فقط لحالة تسجيل الدخول
    dependencies.py  تركيب اعتمادات تسجيل الدخول
    router.py        POST /auth/login
  register/          التسجيل، بنفس تقسيم الملفات
  update_profile/    تعديل الاسم والهاتف، بنفس التقسيم
  addresses/
    add_address/     إضافة عنوان، بنفس التقسيم
  oauth/
    start/           بدء الدخول الاجتماعي، بنفس التقسيم
  shared/            أدوات وعقود وrepositories مشتركة بين العمليات
  router.py          يجمع routers العمليات، بلا منطق أعمال
```

الدخول والتسجيل والتأكيد والاسترجاع وكل عملية عناوين/OAuth مستقلة عن بعضها. خدمة العملية تنفذ حالة استخدام واحدة عن طريق `execute()`؛ الـrouter يستقبل HTTP، والـrepository ينفذ استعلامات التخزين. `dto.py` المحلي يحدد مدخلات ومخرجات العملية، ويستخدم الأنواع المشتركة بدل نسخ نفس قيود البريد والهاتف أو بيانات الاستجابة. راجع [شجرة المشروع وحدود الطبقات](docs/ARCHITECTURE.md) و[مسار كل دالة](docs/FUNCTIONS.md) للوصول للملف المطلوب.

## المتطلبات

يوصى بـ Python 3.14 لمطابقة Docker ونسخ الاعتمادات المثبتة في `requirements.lock.txt`، مع MySQL 8.4 وRedis وSMTP. تعريف الحزمة يسمح بـ Python 3.12 أو أحدث، لكن الفحص المحلي تم على 3.14. إعداد Docker Compose المرفق مخصص للتطوير ويشغل MySQL وRedis وMailpit والـ API والـ email worker. يمكن تشغيل Python محليًا مع نفس خدمات التطوير.

## إعداد development

أنشئ البيئة الافتراضية وثبت الاعتمادات ثم انسخ template الإعدادات:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
cp .env.development.example .env.development
```

ولد قيمًا جديدة محليًا وضعها في `.env.development` بدل كل `REPLACE_...`. الأوامر التالية تطبع مفاتيح على جهازك؛ لا ترسل قيمها إلى Git أو README أو Postman المشترك:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
python -c 'import secrets; print(secrets.token_hex(32))'
python -c 'import secrets; print(secrets.token_hex(32))'
```

القيم بالترتيب: `JWT_SECRET`، `EMAIL_ENCRYPTION_KEY`، `MYSQL_PASSWORD`، ثم `MYSQL_ROOT_PASSWORD`. قيمة كلمة المرور داخل `DATABASE_URL` يجب أن تطابق `MYSQL_PASSWORD`. استخدم القيمتين المختلفتين لحساب MySQL الخاص بالتطبيق وحساب root. لا تستخدم أمثلة placeholders كأسرار فعلية. ملفات `.env` الحقيقية مستبعدة من Git.

شغل خدمات البيانات ثم نفذ migration والـ seed صراحة:

```bash
docker compose --env-file .env.development up -d mysql redis mailpit
docker compose --env-file .env.development run --build --rm api alembic upgrade head
docker compose --env-file .env.development run --rm api python -m scripts.seed
docker compose --env-file .env.development up -d --build api email-worker
```

لا ينشئ `run.py` الجداول ولا ينفذ migrations أو seed تلقائيًا. الـ seed يجهز الأدوار والصلاحيات وأنواع التوكنات فقط؛ لا ينشئ حساب أدمن أو كلمة مرور افتراضية. الاحتفاظ بالـ named volumes يحفظ بيانات MySQL وRedis عند إيقاف Compose.

عند تعديل `.env.development` أو كود التطبيق، أعد إنشاء API وعامل البريد معًا بينما خدمات البيانات قيد التشغيل:

```bash
docker compose --env-file .env.development up -d --build --force-recreate --no-deps api email-worker
```

`email-worker` يبني روابط تأكيد البريد واسترجاع كلمة المرور وقت الإرسال باستخدام `FRONTEND_URL`. إعادة تشغيل API وحده لا تحدث إعدادات عامل البريد. كذلك `docker compose restart` لا يطبق متغيرات البيئة الجديدة. لفحص العنوان الفعلي داخل عامل البريد دون عرض أسرار:

```bash
docker compose --env-file .env.development exec email-worker python -c 'from app.core.config import get_settings; print(get_settings().frontend_url)'
```

القيمة المحلية الحالية `http://127.0.0.1:5173`. بعد تحديث الخدمات اطلب رسالة جديدة؛ الرسائل القديمة تحتفظ بروابطها الأصلية. أضف `sudo` أمام أوامر Docker إذا كانت صلاحيات الجهاز تتطلب ذلك.

| الخدمة | العنوان المحلي |
| --- | --- |
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| OpenAPI | `http://localhost:8000/openapi.json` |
| Mailpit: قراءة رسائل التأكيد والاسترجاع | `http://localhost:8025` |
| MySQL / Redis | `127.0.0.1:3306` / `127.0.0.1:6379` |

للتطوير مع Python على الجهاز، شغل خدمات البيانات فقط ثم نفذ:

```bash
APP_ENV=development alembic upgrade head
APP_ENV=development python -m scripts.seed
python run.py --env development --reload
```

وفي terminal آخر، بعد تفعيل نفس virtualenv:

```bash
APP_ENV=development python -m app.worker
```

وجود الـ worker ضروري لوصول رسائل التسجيل والاسترجاع. الـ API يسجل الرسالة مشفرة في MySQL داخل نفس transaction؛ نجاح `202` يعني قبول الطلب، وليس تأكيد أن SMTP سلم الرسالة. Mailpit خدمة تطوير تجمع الرسائل محليًا.

## development / test / production

| المرحلة | ملف الإعدادات | الاستخدام |
| --- | --- | --- |
| development | `.env.development` | API 8000، frontend 5173، docs مفعلة، reload اختياري. |
| test | `.env.test` | قاعدة مستقلة `foodify_test`، Redis DB 1، API 8001 وfrontend 5173 عند تشغيله بوضع test؛ التشغيل وحده لا يشغل اختبارات. |
| production | `.env.production` | إعدادات مستقلة، docs/debug معطلان، HTTPS وSMTP TLS مع authentication، Redis بكلمة مرور، MySQL user غير root. |

انسخ template المرحلة المطلوبة وولد أسرارًا مختلفة لكل بيئة. جهز قاعدة MySQL ومستخدمها وصلاحياتها خارج التطبيق. متغيرات النظام تتقدم على القيم الموجودة في ملف dotenv، و`APP_ENV` يحدد الملف المستخدم للأوامر المساعدة.

```bash
cp .env.test.example .env.test
APP_ENV=test alembic upgrade head
APP_ENV=test python -m scripts.seed
python run.py --env test
APP_ENV=test python -m app.worker
```

السطران الأخيران عمليتان مستقلتان؛ شغل worker في terminal أو process منفصل. في الإنتاج نفذ migrations مرة واحدة أثناء النشر، ثم شغل API والـ worker كخدمتين منفصلتين:

```bash
APP_ENV=production alembic upgrade head
APP_ENV=production python -m scripts.seed
python run.py --env production
APP_ENV=production python -m app.worker
```

إعداد Compose المرفق للتطوير فقط. نشر الإنتاج يحتاج TLS reverse proxy يحافظ على `Host` الصحيح، أسرار من secret manager، قواعد وRedis خاصة بالإنتاج، نسخًا احتياطية ومراقبة. runner يعطل access logs حتى لا تسجل OAuth authorization codes، ولا يثق تلقائيًا في forwarded headers. اضبط `TRUSTED_PROXY_IPS` على IP أو نطاق الـproxy الفعلي فقط حتى تعمل حدود IP على العميل الصحيح؛ wildcard ونطاق `/0` مرفوضان. `--reload` مسموح في development فقط، و`--host/--port/--workers` overrides واضحة عند الحاجة.

`requirements.txt` يحدد الاعتمادات المباشرة ونطاقات التحديث؛ `requirements.lock.txt` يثبت النسخ التي جرى فحص تركيبها. عند ترقية الاعتمادات حدّث ملف التثبيت بعد مراجعة التغييرات بواسطة الفريق المختص.

## API وflow الاستخدام

كل مسارات التطبيق تحت `/api/v1`، ما عدا health endpoints. الطلبات JSON. ضع `Authorization: Bearer <access_token>` لمسارات العميل وتسجيل الخروج. لا تضع التوكن في query string.

في Swagger، أمر curl للمسار المحمي يعرض `Authorization: Bearer ACCESS_TOKEN_HERE`؛ وبعد إدخال `access_token` في **Authorize** يعرض التوكن الحقيقي. القيمة التوضيحية تظهر في المثال فقط.

| الوظيفة | المسار | النجاح |
| --- | --- | --- |
| تسجيل عميل | `POST /api/v1/auth/register` | `202` رسالة عامة |
| إعادة إرسال التأكيد | `POST /api/v1/auth/resend-verification` | `202` رسالة عامة |
| تأكيد البريد | `POST /api/v1/auth/verify-email` | `200` |
| الدخول للواجهة | `POST /api/v1/auth/browser/login` | `200` access + user؛ refresh في HttpOnly cookie |
| تجديد جلسة الواجهة | `POST /api/v1/auth/browser/refresh` | `200` access جديد + user؛ cookie تلقائيًا |
| طلب استرجاع كلمة المرور | `POST /api/v1/auth/forgot-password` | `202` رسالة عامة |
| تعيين كلمة مرور جديدة | `POST /api/v1/auth/reset-password` | `200` |
| إنهاء جلسة الواجهة | `POST /api/v1/auth/browser/logout` | `204` |
| بدء Google/Facebook | `POST /api/v1/auth/oauth/{provider}/start` | `200` authorization_url |
| رد مقدم OAuth | `GET /api/v1/auth/oauth/{provider}/callback` | redirect للـ frontend |
| استبدال OAuth ticket للواجهة | `POST /api/v1/auth/browser/oauth/complete` | `200` access + user؛ refresh في cookie |
| قراءة / تعديل الملف | `GET /api/v1/users/me` / `PATCH /api/v1/users/me` | `200` |
| عرض / إضافة عنوان | `GET /api/v1/users/me/addresses` / `POST` لنفس المسار | `200` / `201` |
| استبدال / حذف عنوان | `PUT /api/v1/users/me/addresses/{id}` / `DELETE` | `200` / `204` |
| اختيار العنوان الافتراضي | `PUT /api/v1/users/me/default-address/{id}` | `200` ملف العميل |
| حياة العملية / جاهزية الاعتمادات | `GET /health/live` / `GET /health/ready` | `200` أو `503` للجاهزية |

### البريد وكلمة المرور

1. أرسل `name/email/password` إلى register. كلمة المرور الجديدة من 15 إلى 128 حرفًا، والـ DTO يرفض أي حقول إضافية مثل الدور. البريد يطبع إلى صيغة lowercase للمقارنة.
2. افتح رسالة Mailpit؛ الرابط يتجه إلى frontend `/verify-email#token=...`. الواجهة الحالية تحول الرابط لمسار HashRouter وتستدعي `verify-email` ثم تمسح الرمز من العنوان.
3. نفذ login باستخدام `email/password`. البريد يجب أن يكون مؤكدًا. استجابة الدخول تحتوي `access_token` و`refresh_token` و`expires_in` بالثواني و`user`.
4. عند انتهاء الـ access token أرسل refresh token في body إلى refresh. استبدل التوكنين بالقيم الجديدة؛ إعادة استخدام القديم تعامل كاشتباه وتلغي الجلسة التابعة له.
5. forgot-password يستقبل email. رابط الرسالة `/reset-password#token=...`؛ reset-password يستقبل `token/password`. نجاح التغيير يلغي الجلسات القديمة ويطلب دخولًا جديدًا.

register وresend-verification وforgot-password يعيدون رسائل عامة لمنع كشف الحسابات المسجلة. لن يرجع token تأكيد البريد أو استرجاع كلمة المرور في استجابة الـ API أو في logs.

### استكمال الحساب والعناوين

`PATCH /users/me` يسمح بـ `name` و`phone` فقط. الرقم بصيغة E.164 مثل `+201012345678`. لا يوجد SMS verification في هذه المرحلة؛ تأكيد البريد مستقل عن التحقق من صحة صيغة الرقم.

```json
{
  "label": "البيت",
  "recipient_name": "عميل Foodify",
  "phone": "+201012345678",
  "country_code": "EG",
  "city": "القاهرة",
  "area": "مدينة نصر",
  "street": "شارع مثال",
  "building": "12",
  "floor": "3",
  "apartment": "7",
  "delivery_notes": "اتصل عند الوصول",
  "latitude": 30.05,
  "longitude": 31.35
}
```

أول عنوان يصبح افتراضيًا تلقائيًا. `profile_complete=true` عندما يوجد هاتف للحساب وعنوان افتراضي، بنفس القاعدة للحساب المحلي وOAuth. العنوان له رقم المستلم بصورة مستقلة. الإحداثيات اختيارية لكن يجب إرسال القيمتين معًا. `PUT` يستبدل العنوان كاملًا؛ حذف الافتراضي يختار أقدم عنوان متبقٍ، والحد 20 عنوانًا. كل address ID تابع لصاحبه؛ ID غير موجود أو تابع لشخص آخر يرجع `404`.

### Google وFacebook

فعّل provider بإعداد `CLIENT_ID` و`CLIENT_SECRET` و`REDIRECT_URI` الخاصة به معًا في ملف البيئة، وسجل نفس callback URI حرفيًا لدى مقدم الخدمة. عند تركها جميعًا غير مضبوطة يبقى provider غير مفعل. استخدم تطبيق OAuth وcredentials مختلفين لكل مرحلة.

العميل ينشئ `binding_verifier` عشوائيًا ويحتفظ به مؤقتًا أثناء flow، ويرسل `binding_challenge=SHA256(verifier)` بصيغة hex lowercase إلى `/auth/oauth/{provider}/start`. يفتح `authorization_url` في المتصفح. بعد callback يرجع الخادم إلى `/oauth/callback#ticket=...`، ثم ترسل الواجهة `ticket/binding_verifier` إلى `/auth/browser/oauth/complete`. هذا يربط ticket بالعميل الذي بدأ العملية؛ التوكنات لا توضع في redirect URL.

Google يتحقق من ID token وissuer/audience/nonce، وFacebook يتحقق من access token عبر مقدم الخدمة. لا ندمج حسابًا محليًا قائمًا تلقائيًا بسبب تطابق البريد وحده. عندما لا توجد قرينة بريد موثق كافية، ينشأ الحساب غير مؤكد ويرسل تأكيد محلي وتظهر `#error=email_verification_required`؛ أكمل تأكيد البريد ثم ابدأ OAuth مرة أخرى. تفاصيل التنفيذ وحدود الثقة في [SECURITY.md](docs/SECURITY.md).

## الأدوار والتوسع

الأدوار الحالية `customer`، `courier`، `order_preparer`، `operations_manager`، `admin`. الاسم المقترح للدور الأقل من الأدمن هو **مدير العمليات**. المستخدم قد يمتلك عدة أدوار عبر bridge، والدور عدة صلاحيات عبر bridge آخر. لا توجد public endpoints لإنشاء موظفين أو تغيير أدوار في المرحلة الحالية؛ تسجيل العميل لا يقبل دورًا من العميل.

عند إضافة الطلبات أو إدارة الموظفين، أضف feature مستقلة وطبق فحص permission في dependencies لكل endpoint. امتلاك JWT يثبت هوية مستخدم وجلسة؛ تنفيذ صلاحية الموظف يحتاج فحصًا صريحًا من قاعدة البيانات.

## الأخطاء والتشغيل

صيغة الخطأ موحدة:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [{"field": "body.phone", "type": "string_pattern_mismatch"}],
    "request_id": "..."
  }
}
```

`401` مصادقة غير صالحة، `403` عدم سماح أو بريد غير مؤكد، `404` مورد غير موجود، `409` تعارض، `422` payload غير صالح، `429` تجاوز محاولات مع `Retry-After`، `503` خدمة مطلوبة غير متاحة. أخطاء validation لا تعيد كلمة المرور أو التوكن المدخل. `X-Request-ID` يربط الطلب بالـ logs من غير كتابة بيانات حساسة.

الـ worker يعيد محاولة رسائل البريد الفاشلة حتى 10 محاولات مع تأخير؛ الرسائل التي تستنفد المحاولات تتطلب تدخل التشغيل ومراجعة SMTP ثم إعادة جدولتها بقرار إداري. راقب pending/dead-letter outbox وRedis وSMTP. تدوير مفتاح تشفير البريد يحتاج خطة للاحتفاظ بإمكانية فك الرسائل المعلقة؛ لا تغيره عشوائيًا أثناء وجودها.

الأمان هنا مجموعة ضوابط موثقة مسترشدة بـ [OWASP Top 10:2025](https://top10.owasp.org/2025/)، وليس شهادة تدقيق أو بديلًا عن مراجعة فريق الجودة والأمان قبل الإنتاج.

## واجهة React

واجهة حساب العميل موجودة في [`../front/`](../front/README.md)، منظمة حسب الـ feature بطبقات domain/application/infrastructure/presentation. وضع التطوير يربط API على 8000 عبر HTTP repositories، مع وضع `demo` اختياري للمعاينة.

```bash
cd ../front
npm ci
npm run dev
```

تفاصيل الطبقات في [معمارية الواجهة](../front/docs/ARCHITECTURE.md)، وعقود الربط في [دليل integration](../front/docs/INTEGRATION.md).
