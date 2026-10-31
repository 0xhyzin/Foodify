# Foodify

Foodify هو نظام توصيل أكل. المشروع متقسم إلى واجهة React مستقلة وباك إند FastAPI مستقل، بحيث كل جزء يقدر يتطور ويتنشر بشكل منفصل.

الواجهة تعرض Marketplace عربيًا للمطاعم والحلويات والقهوة والبقالة، ببحث وفئات وفلاتر ومفضلة. مصدر بيانات المتاجر والمنتجات هو MySQL عبر FastAPI؛ والواجهة لا تحتوي كتالوجًا محليًا بديلًا. ملف seed الخاص بالباك يجهز عينة من 8 متاجر و24 منتجًا، لكن لم تتم مزامنتها مع قاعدة الاستضافة بعد بسبب تعذر حل عنوان MySQL الحالي. تفاصيل التنفيذ في [شرح الواجهة للسبرنت الثاني](front/README_SPRINT_2.md) و[شرح الباك والربط للسبرنت الثاني](back/README_SPRINT_2.md).

الواجهة منشورة على [Vercel](https://foodify-flax.vercel.app)، والباك على [FastAPI Cloud](https://foodify-api.fastapicloud.dev)، وقاعدة MySQL وValkey على Aiven، ورسائل التأكيد واسترجاع كلمة المرور عبر Mailjet SMTP. حالة الاتصال الحالية وقائمة خطوات النشر والتحقق موجودة في [دليل النشر](docs/DEPLOYMENT.md). قاعدة البيانات MySQL.

## شكل المشروع

~~~text
Foodify/
├── back/                         # FastAPI + SQLAlchemy + Redis + email worker
│   ├── app/
│   │   ├── users/                # كل عملية: DTO / interface / service / router
│   │   ├── roles/                # role and permission definitions
│   │   ├── core/                 # settings and request security
│   │   ├── infrastructure/       # database, email and external adapters
│   │   └── main.py
│   ├── migrations/
│   ├── postman/
│   ├── compose.yaml
│   └── .env.development.example
└── front/                        # React + TypeScript + Vite
    ├── src/
    │   ├── app/                  # composition root, routing, shared UI
    │   ├── shared/               # common components and domain errors
    │   ├── features/
    │   │   ├── auth/             # login, register, email, password, OAuth
    │   │   ├── account/          # profile and addresses
    │   │   └── marketplace/      # catalog, carts, checkout, payments, orders
    │   └── infrastructure/       # HTTP client and browser session
    └── .env.development.example
~~~

## المعمارية المستخدمة

الفرونت مبني على Clean Architecture مبسطة مع Component-Based Architecture. كل feature متقسمة إلى:

~~~text
feature/
├── domain/                       # types و repository interface
├── application/                  # use cases
├── infrastructure/               # HTTP implementation و DTO mapping
└── presentation/                # pages, components, hooks
~~~

الاتجاه المسموح للاعتماديات هو:

~~~text
Presentation
    ↓
Application use case
    ↓
Domain repository interface
    ↓
Infrastructure HTTP repository
    ↓
Shared FetchHttpClient
    ↓
FastAPI API
~~~

الـ domain لا يعرف React أو fetch أو FastAPI. الـ application يعرف المطلوب من خلال interface فقط، أما التنفيذ الحقيقي فيكون داخل infrastructure. هذا يمنع وضع كل الوظائف في ملف واحد ويجعل تغيير API أو إضافة مصدر بيانات آخر أسهل.

الملف [front/src/app/services.ts](front/src/app/services.ts) هو composition root؛ يركب مستودعات HTTP للكتالوج والحساب والطلبات. يجب ضبط `VITE_DATA_SOURCE=api`، وأي قيمة أخرى يرفضها التطبيق.

## تشغيل المشروع

### تشغيل الباك إند مباشرة

~~~bash
cd /home/hyzin/Projects/Foodify/back
source .venv/bin/activate
python run.py --env development --reload
~~~

### تشغيل الباك إند باستخدام Docker

~~~bash
cd /home/hyzin/Projects/Foodify/back
docker compose --env-file .env.development up -d --build
~~~

هذا يشغل API و MySQL و Redis و Mailpit حسب إعدادات compose.yaml.

### تشغيل الفرونت

~~~bash
cd Foodify/front
npm install
npm run dev
~~~

افتح:

~~~text
http://127.0.0.1:5173/#/login
~~~

الإعداد الافتراضي للفرونت هو:

~~~env
VITE_DATA_SOURCE=api
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
~~~

الواجهة تحتاج الباك إند حتى تعرض البيانات الحقيقية؛ لا يوجد وضع Demo بديل في التشغيل الحالي.

## مسار التكامل الكامل

مثال تسجيل الدخول:

~~~text
LoginPage
  → LoginForm
  → LoginUser use case
  → AuthRepository interface
  → HttpAuthRepository
  → FetchHttpClient
  → POST /api/v1/auth/browser/login
  → response DTO
  → Auth mapper
  → UserSession domain model
  → Auth state في الواجهة
~~~

نفس النمط مستخدم في التسجيل، تأكيد البريد، نسيان كلمة المرور، تغيير كلمة المرور، الملف الشخصي، والعناوين.

## Endpoints المستخدمة

### Authentication

| الوظيفة | HTTP endpoint |
|---|---|
| تسجيل مستخدم | POST /api/v1/auth/register |
| تسجيل الدخول للمتصفح | POST /api/v1/auth/browser/login |
| تأكيد البريد | POST /api/v1/auth/verify-email |
| إعادة إرسال التأكيد | POST /api/v1/auth/resend-verification |
| طلب نسيان كلمة المرور | POST /api/v1/auth/forgot-password |
| تغيير كلمة المرور | POST /api/v1/auth/reset-password |
| تحديث access token | POST /api/v1/auth/browser/refresh |
| تسجيل الخروج | POST /api/v1/auth/browser/logout |
| بدء OAuth | POST /api/v1/auth/oauth/{provider}/start |
| إنهاء OAuth للمتصفح | POST /api/v1/auth/browser/oauth/complete |

الـ provider المدعوم من الواجهة هو google أو facebook حسب إعدادات الباك إند.

### Profile and addresses

| الوظيفة | HTTP endpoint |
|---|---|
| قراءة المستخدم الحالي | GET /api/v1/users/me |
| تعديل المستخدم الحالي | PATCH /api/v1/users/me |
| قراءة العناوين | GET /api/v1/users/me/addresses |
| إضافة عنوان | POST /api/v1/users/me/addresses |
| تعديل عنوان | PUT /api/v1/users/me/addresses/{address_id} |
| حذف عنوان | DELETE /api/v1/users/me/addresses/{address_id} |
| تحديد العنوان الافتراضي | PUT /api/v1/users/me/default-address/{address_id} |

أي endpoint محمي يحتاج:

~~~bash
curl 'http://localhost:8000/api/v1/users/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer ACCESS_TOKEN_HERE'
~~~

## إدارة الـ session والـ tokens

التكامل يستخدم browser session آمنة:

1. بعد login، access token يظل في الذاكرة فقط ولا يتم تخزينه في localStorage.
2. الباك إند يضع refresh token في cookie باسم foodify_refresh مع HttpOnly.
3. كل request يرسل credentials: include و header اسمه X-Foodify-Client: web.
4. عند وجود access token يضاف Authorization: Bearer token.
5. إذا رجع API بـ 401، يحاول FetchHttpClient عمل refresh مرة واحدة ثم يعيد الطلب الأصلي.
6. الطلبات المتزامنة تشترك في refresh واحد حتى لا يتم إرسال refresh requests كثيرة.
7. logout يمسح session من الذاكرة ويطلب إلغاء cookie من الباك إند.

التنفيذ موجود في:

- [front/src/infrastructure/http/fetch-client.ts](front/src/infrastructure/http/fetch-client.ts)
- [front/src/infrastructure/http/browser-session.ts](front/src/infrastructure/http/browser-session.ts)
- [front/src/app/services.ts](front/src/app/services.ts)

## OAuth

تدفق OAuth في الفرونت كالتالي:

1. يتم إنشاء state عشوائي و PKCE code_verifier.
2. يتم اشتقاق code_challenge باستخدام SHA-256.
3. يتم حفظ القيم المؤقتة في sessionStorage فقط.
4. يتم فتح endpoint بداية OAuth في الباك إند.
5. provider يعيد المستخدم إلى callback في الباك إند.
6. الباك إند ينشئ callback ticket قصير العمر ويعيد المستخدم إلى الفرونت.
7. الفرونت يرسل ticket مع نفس code_verifier إلى browser/oauth/complete.
8. الباك إند يصدر browser session، ثم يتم مسح ticket والقيم المؤقتة.

لا يتم وضع access token أو refresh token في URL. الـ callback ticket يستخدم مرة واحدة ومدة صلاحيته قصيرة.

التنفيذ موجود في [front/src/features/auth/infrastructure/oauth-flow.ts](front/src/features/auth/infrastructure/oauth-flow.ts).

### إعداد مفاتيح Google وFacebook

الزرار لن يفتح مزود تسجيل الدخول طالما متغيرات OAuth غير موجودة. في [back/.env.development](back/.env.development) أضف بيانات كل مزود تريد تفعيله، واستبدل القيم التجريبية بمفاتيح حقيقية:

~~~env
OAUTH_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback

OAUTH_FACEBOOK_CLIENT_ID=your-meta-app-id
OAUTH_FACEBOOK_CLIENT_SECRET=your-meta-app-secret
OAUTH_FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/facebook/callback
OAUTH_FACEBOOK_GRAPH_VERSION=v26.0
~~~

يجب تسجيل نفس redirect URI حرفيًا في Google Cloud وMeta. بعد تعديل ملف البيئة أعد إنشاء API وخدمة البريد معًا؛ الـ containers الحالية لا تقرأ التعديل تلقائيًا:

~~~bash
cd /home/hyzin/Projects/Foodify/back
docker compose --env-file .env.development up -d --build --force-recreate --no-deps api email-worker
~~~

للتأكد من أن المزود أصبح مفعّلًا، يجب أن يرجع endpoint البداية 200 مع authorization_url بدل 503 oauth_unavailable:

~~~bash
curl -i -X POST 'http://localhost:8000/api/v1/auth/oauth/google/start' \
  -H 'Content-Type: application/json' \
  -H 'X-Foodify-Client: web' \
  --data '{"binding_challenge":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}'
~~~

افتح الواجهة من http://127.0.0.1:5173 في التطوير، لأن هذا هو العنوان المضبوط في FRONTEND_URL وOAuth يعتمد على sessionStorage المرتبط بالـ origin. استخدام localhost:5173 و127.0.0.1:5173 في نفس التدفق يضيع verifier ويظهر كأن جلسة OAuth انتهت.

## تأكيد البريد ونسيان كلمة المرور

الروابط التي يرسلها الباك إند تعتمد على:

~~~env
FRONTEND_URL=http://127.0.0.1:5173
~~~

وتكون بصيغة:

~~~text
http://127.0.0.1:5173/verify-email#token
http://127.0.0.1:5173/reset-password#token
~~~

بما أن الفرونت يستخدم HashRouter، الملف [front/src/app/bootstrap/external-links.ts](front/src/app/bootstrap/external-links.ts) يحول الرابط الفعلي إلى route داخلي، يقرأ token، ثم يمسحه من العنوان بعد استخدامه.

خدمة `email-worker` هي التي تبني رابط البريد وقت الإرسال من `FRONTEND_URL`، وليس API. عند تعديل العنوان يجب إعادة إنشاء الخدمتين؛ إعادة تشغيل API وحده تترك عامل البريد بإعداداته القديمة:

~~~bash
cd /home/hyzin/Projects/Foodify/back
sudo docker compose --env-file .env.development up -d --build --force-recreate --no-deps api email-worker
~~~

هذا الأمر يتطلب أن تكون MySQL وRedis وMailpit قيد التشغيل. لا يحذف بيانات قاعدة البيانات أو الـ volumes. `docker compose restart` وحده لا يطبق تغييرات متغيرات البيئة؛ استخدم أمر `up` أعلاه.

للتأكد من إعداد خدمة البريد الفعلي دون طباعة أي أسرار:

~~~bash
sudo docker compose --env-file .env.development exec email-worker python -c 'from app.core.config import get_settings; print(get_settings().frontend_url)'
~~~

الناتج المتوقع: `http://127.0.0.1:5173`. بعد ذلك اطلب رسالة جديدة من «نسيت كلمة المرور» أو «إعادة إرسال التأكيد». الرسائل التي وصلت سابقًا وفيها localhost:3000 لا يتغير محتواها بأثر رجعي.

## DTO mapping والأخطاء

الباك إند يرجع الخطأ بالشكل التالي:

~~~json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input",
    "details": null,
    "request_id": "..."
  }
}
~~~

الفرونت يحول هذا الشكل إلى AppError موحد يحتوي على code, message, status, و fields. الـ pages لا تتعامل مع raw Response ولا مع تفاصيل HTTP الداخلية.

كذلك يتم تحويل أسماء الحقول بين الطرفين في repository mappers:

~~~text
snake_case من API  ↔  camelCase داخل React/domain
~~~

مثال: phone_number يصبح phoneNumber، و is_default يصبح isDefault.

## الأمن والحماية

تمت مراعاة النقاط الأساسية من OWASP Top 10 في نطاق التكامل الحالي:

- refresh token في HttpOnly cookie وليس في localStorage.
- access token في الذاكرة فقط.
- CORS يسمح فقط بعناوين الواجهة المعروفة: localhost و 127.0.0.1 على المنافذ 5173 و 4173.
- الطلبات browser تستخدم credentials: include و X-Foodify-Client.
- OAuth يعتمد على state و PKCE.
- لا توجد tokens في redirect URL النهائي.
- callback ticket قصير العمر ويستخدم مرة واحدة.
- email endpoints لا تكشف إذا كان البريد موجودا لتقليل user enumeration.
- token الموجود في hash يتم مسحه بعد القراءة.
- CSP في الفرونت يسمح بالاتصال بالـ API المحدد فقط.
- تفاصيل الأخطاء الحساسة لا يتم عرضها في DOM.

## المشاكل التي ظهرت وتم إصلاحها

1. نُقلت بيانات المطاعم من ملفات الواجهة إلى قاعدة MySQL، وأصبح الفرونت يستخدم API فقط من خلال HTTP repositories.
2. كانت طبقة HTTP و browser session و OAuth ناقصة؛ تم فصلها إلى ملفات infrastructure مستقلة.
3. ظهرت أخطاء TypeScript بسبب اختلاف DTO بين الباك إند والفرونت؛ تم إضافة mappers للـ snake_case/camelCase.
4. روابط البريد كانت تشير إلى 3000؛ تم توحيدها على 5173 في development.
5. استخدام HashRouter مع روابط البريد و OAuth احتاج تحويل خارجي؛ تم وضع هذا في bootstrap بدل خلطه داخل الصفحات.
6. CORS داخل الكود تم تحديثه، لكن containers قديمة قد تظل تعمل بإعدادات قديمة. بعد أي تعديل في .env أو الكود أعد إنشاء API وخدمة البريد:

   ~~~bash
   cd /home/hyzin/Projects/Foodify/back
   docker compose --env-file .env.development up -d --build --force-recreate --no-deps api email-worker
   ~~~

7. ربط OAuth بالمتصفح يعتمد على challenge مشتق من verifier؛ يجب أن تستخدم البداية والإكمال نفس صيغة البصمة. التنفيذ الحالي يخزن بصمة challenge ويعيد اشتقاقها من verifier عند الإكمال. هذا وصف للعقد الحالي، ولا يعني أن إكمال OAuth فُحص بتسجيل دخول حقيقي.
8. كان FRONTEND_URL يستخدم localhost بينما Vite يعمل على 127.0.0.1؛ تم توحيده على 127.0.0.1 حتى لا تضيع sessionStorage الخاصة بـ OAuth.
9. نقل المشروع إلى Foodify/back غيّر المسارات المطلقة للـ virtual environment، لذلك تم إنشاء .venv جديد داخل مجلد الباك إند.
10. استمرار روابط البريد على 3000 بعد تحديث API كان سببه بقاء email-worker بالإعداد القديم. تم تصحيح أوامر التحديث لتشمل الخدمتين، وإضافة أمر لفحص FRONTEND_URL داخل خدمة البريد نفسها.

## التحقق الذي تم تشغيله

تم التحقق من سلامة الكود بدون إضافة أو تشغيل tests:

~~~bash
cd /home/hyzin/Projects/Foodify/front
npm run typecheck
npm run build

cd /home/hyzin/Projects/Foodify/back
APP_ENV=development .venv/bin/python -m compileall -q app
~~~

مسؤولية كتابة وتشغيل الاختبارات ما زالت مع فريق الـ testing كما هو مطلوب.

## مستندات إضافية

- [Frontend README](front/README.md)
- [Frontend functions and components](front/docs/FUNCTIONS.md)
- [Frontend architecture](front/docs/ARCHITECTURE.md)
- [Frontend integration](front/docs/INTEGRATION.md)
- [Backend README](back/README.md)
- [Postman documentation](back/postman/README.md)
