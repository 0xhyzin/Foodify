# Foodify Frontend — شرح التنفيذ الكامل

واجهة حساب العميل في Foodify، مبنية بـ React وTypeScript وVite. الواجهة عربية باتجاه RTL، بتصميم أحمر وأبيض ونصوص داكنة، وتعمل مع FastAPI أو بمصدر بيانات تجريبي داخل الذاكرة.

هذا الملف يشرح الموجود فعليًا في `front`: ماذا تم تنفيذه، أين يوجد الكود، وكيف تنتقل البيانات من الشاشة إلى API ثم تعود للعرض.

## دليل القراءة

- [نطاق العمل والتقنيات](#نطاق-العمل-والتقنيات)
- [التشغيل والبيئات](#التشغيل-والبيئات)
- [تقسيم المشروع والمعمارية](#تقسيم-المشروع-والمعمارية)
- [بداية تشغيل التطبيق وحقن الاعتمادات](#بداية-تشغيل-التطبيق-وحقن-الاعتمادات)
- [إدارة الحالة والجلسة](#إدارة-الحالة-والجلسة)
- [الشاشات والمسارات](#الشاشات-والمسارات)
- [رحلات المستخدم](#رحلات-المستخدم)
- [الربط بالباك-إند وتحويل البيانات](#الربط-بالباك-إند-وتحويل-البيانات)
- [التحقق والأخطاء](#التحقق-والأخطاء)
- [المكونات والتصميم وإمكانية الوصول](#المكونات-والتصميم-وإمكانية-الوصول)
- [المحاكاة](#المحاكاة)
- [الحماية وحدود التنفيذ](#الحماية-وحدود-التنفيذ)
- [الأعطال التي عولجت وطريقة تشخيصها](#الأعطال-التي-عولجت-وطريقة-تشخيصها)
- [تعديل المشروع وتسليمه](#تعديل-المشروع-وتسليمه)
- [فهرس الدوال والمكونات](docs/FUNCTIONS.md)
- [نتائج مراجعة الكود والإصلاحات](docs/REVIEW.md)
- [تفاصيل المعمارية](docs/ARCHITECTURE.md)
- [عقود التكامل](docs/INTEGRATION.md)

## نطاق العمل والتقنيات

المنفذ هو جزء المستخدم العادي:

- إنشاء الحساب وتسجيل الدخول والخروج.
- تأكيد البريد وإعادة إرسال رسالة التأكيد.
- نسيان كلمة المرور وتعيين كلمة مرور جديدة.
- بدء تسجيل الدخول بـ Google وFacebook واستقبال نتيجة OAuth.
- استكمال الاسم ورقم الموبايل وعنوان التوصيل.
- عرض الملف الشخصي وتعديل الاسم والرقم.
- إضافة عناوين التوصيل وتعديلها وحذفها واختيار الافتراضي.
- حالات الانتظار والخطأ والنجاح والبيانات الفارغة.
- عرض تجريبي مستقل عن الباك إند.

الكتالوج والسلة والطلبات والدفع ولوحات الأدمن والمحضر والدليفري لم تُنفذ ضمن هذه الواجهة. وجود `roles` في نموذج المستخدم لا يعني وجود شاشات لإدارة الأدوار.

| التقنية | استخدامها الفعلي |
| --- | --- |
| React 19 | بناء المكونات والصفحات وإدارة دورة العرض |
| TypeScript 5.9 | تعريف العقود وفحص الأنواع؛ إعداد `strict` مفعّل |
| Vite 8 | سيرفر التطوير، HMR، واستخراج ملفات البناء |
| React Router 7 | التنقل و`HashRouter` والمسارات المحمية |
| React Context | حقن الخدمات وحالة المستخدم والإشعارات |
| Fetch API | طلبات الشبكة داخل infrastructure |
| Lucide React | أيقونات المكونات والحالات |
| IBM Plex Sans Arabic | خط عربي مستورد محليًا من الحزمة |
| CSS | التخطيط والألوان والحالات والاستجابة للشاشات |

هذه التقنيات موثقة من [package.json](package.json)؛ النسخ المثبتة بالتحديد موجودة في `package-lock.json`. لا توجد مكتبة Redux أو Axios أو مكتبة نماذج خارجية ضمن التنفيذ الحالي.

## التشغيل والبيئات

المتطلبات: Node.js إصدار `22.12` أو أحدث وnpm.

~~~bash
cd /home/hyzin/Projects/Foodify/front
npm ci
npm run dev
~~~

افتح `http://127.0.0.1:5173/#/login`. المنفذ `5173` ثابت في Vite؛ إذا كان مشغولًا يتوقف التشغيل بدل اختيار منفذ آخر.

تغييرات React وCSS تظهر أثناء التطوير عبر HMR. بعد تعديل ملفات البيئة أعد تشغيل Vite.

### إعداد مصدر البيانات

يوجد مثال لكل مرحلة. للتطوير المحلي:

~~~bash
cp .env.development.example .env.development
~~~

محتواه:

~~~dotenv
VITE_APP_ENV=development
VITE_DATA_SOURCE=api
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
~~~

| المتغير | المسؤولية |
| --- | --- |
| `VITE_APP_ENV` | اسم البيئة داخل `appConfig.environment` |
| `VITE_DATA_SOURCE` | يختار `api` أو `demo`؛ أي قيمة أخرى ترفضها الإعدادات |
| `VITE_API_BASE_URL` | أصل API ومساره المشترك؛ لا تكرر `/api/v1` في repository |

`VITE_APP_ENV` لا يختار ملف البيئة بنفسه؛ اختيار الملف يتم من Vite mode. القيم التي تبدأ بـ `VITE_` تظهر في حزمة المتصفح، لذلك تحتوي إعدادات عامة فقط. أسرار OAuth وJWT وSMTP تظل داخل الباك إند.

### أوامر npm

| الأمر | ما ينفذه |
| --- | --- |
| `npm run dev` | development على `127.0.0.1:5173` |
| `npm run dev:test` | تشغيل Vite بـ mode اسمه `test` |
| `npm run typecheck` | `tsc -b --pretty false` لفحص الأنواع |
| `npm run build` | فحص الأنواع ثم بناء production |
| `npm run build:test` | فحص الأنواع ثم بناء بـ mode اسمه `test` |
| `npm run build:production` | بناء production صراحة |
| `npm run preview` | معاينة ملفات `dist` محليًا؛ المنفذ المعتاد `4173` |

الملفات `.env.*.example` أمثلة فقط؛ Vite لا يقرأ امتداد `.example` تلقائيًا. الوضع الافتراضي هو `api` في كل المراحل، ويمكن اختيار `demo` صراحةً لعرض التصميم. عنوان API الاحتياطي في التطوير هو `http://127.0.0.1:8000/api/v1`، وفي build الإنتاج هو `/api/v1` عبر proxy النقل في Vercel. مثال test يختار `8001` عندما تنسخه إلى `.env.test`. تفاصيل النشر والمتغيرات موجودة في [دليل النشر](../docs/DEPLOYMENT.md).

للنشر الحقيقي، انسخ `.env.production.example` إلى `.env.production` واضبط `VITE_DATA_SOURCE=api` ورابط API المنشور عبر HTTPS، ثم ابنِ المشروع. إعدادات Vite تُدمج وقت البناء، فتغيير ملف البيئة بعد البناء يستلزم بناءً جديدًا.

كلمة `test` في أوامر Vite تعني بيئة تشغيل وبناء. لم تُضف أو تُشغّل اختبارات آلية لهذه المهمة.

## تقسيم المشروع والمعمارية

~~~text
front/
├── index.html
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
├── .env.development.example
├── .env.test.example
├── .env.production.example
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx
│   ├── styles.css
│   ├── app/
│   │   ├── app.tsx
│   │   ├── config.ts
│   │   ├── services.ts
│   │   ├── error-boundary.tsx
│   │   ├── bootstrap/external-links.ts
│   │   ├── providers/
│   │   ├── router/
│   │   └── layouts/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── domain/
│   │   │   ├── application/<operation>/dto.ts + use-case.ts
│   │   │   ├── infrastructure/
│   │   │   └── presentation/components + hooks + pages
│   │   └── account/
│   │       ├── domain/
│   │       ├── application/<operation>/dto.ts + use-case.ts
│   │       ├── infrastructure/dto + mappers + repositories
│   │       └── presentation/components + onboarding + profile + addresses
│   ├── infrastructure/
│   │   ├── http/
│   │   └── demo/
│   └── shared/
│       ├── domain/app-error.ts
│       ├── hooks/use-action.ts
│       └── ui/
└── docs/
    ├── ARCHITECTURE.md
    ├── INTEGRATION.md
    └── FUNCTIONS.md
~~~

التقسيم حسب وظيفتين أساسيتين: `auth` و`account`. داخل كل وظيفة توجد الطبقات التالية:

| الطبقة | مسؤوليتها | ما لا تعرفه |
| --- | --- | --- |
| `domain` | النماذج والواجهات وقواعد التحقق | React وHTTP وDOM |
| `application` | عملية واحدة: تحضير المدخلات ثم تفويض التنفيذ عبر interface | شكل صفحة React أو endpoint |
| `infrastructure` | تنفيذ repository والتعامل مع API أو المحاكاة وتحويل DTO | التنقل وشكل الأزرار |
| `presentation` | النماذج والمكونات والتنقل وعرض النتائج | تفاصيل التخزين والـ fetch |
| `app` | تركيب الاعتمادات والإعدادات والـ providers والـ router | تنفيذ قواعد البيانات |
| `shared` | مكونات وأدوات مشتركة عامة | تفاصيل feature بعينها |

### اتجاه الاعتماد ومسار الاستدعاء

~~~text
Page / Form
    → services.auth أو services.account
    → Use case
    → Repository interface في domain
    → HTTP repository أو Demo repository
    → HTTP client في وضع api
    → FastAPI
    → Response mapper
    → Domain model
    → React state
~~~

هذا يصف مسار التنفيذ. في الاعتماد بين الملفات، الـ use case يعتمد على interface، وHTTP repository ينفذ هذه الواجهة. الاختيار والربط يحدثان في `services.ts`.

مثال موجود بالفعل:

~~~text
account/application/save-address/
├── dto.ts       تعريف SaveAddressDto وSaveAddressResult
└── use-case.ts  createSaveAddress(repository) → saveAddress(input, id?)
~~~

الدالة الناتجة تطبّع العنوان وتتحقق من المعرف عند التعديل، ثم تستدعي `AccountRepository.saveAddress`. لذلك قواعد التحقق لا تتكرر في صفحة الإضافة وصفحة التعديل.

### تطبيق مبادئ الفصل وSOLID

- صفحة React تعرض البيانات، وuse case يجهز العملية، وrepository يعزل مصدر البيانات.
- `AuthRepository` منفصل عن `AccountRepository`، و`OAuthFlowPort` منفصل عن نقل HTTP.
- `HttpAuthRepository` و`DemoAuthRepository` يقدمان نفس عقد المصادقة.
- إضافة adapter جديد تتم في infrastructure مع ترك واجهة الاستخدام كما هي.
- حقن الاعتمادات يتم بالدوال والـ constructors وReact Context، دون حاوية DI خارجية.
- المكونات العامة مثل `Button` و`Field` تستقبل props، ولا تستدعي API.

الفصل مبسط: ليس لكل زر interface، وبعض use cases مجرد تحقق وتفويض. عملية `completeProviderSignIn` موصلة مباشرة من composition root إلى repository، ولا يوجد لها مجلد use case مستقل حاليًا.

## بداية تشغيل التطبيق وحقن الاعتمادات

ترتيب التنفيذ عند فتح الموقع:

1. المتصفح يحمل [index.html](index.html) المحدد بـ `lang="ar"` و`dir="rtl"`.
2. [src/main.tsx](src/main.tsx) يستورد الخط والأشكال، ويشغل `normalizeExternalLinks()` قبل React لمعالجة روابط الإيميل وOAuth.
3. ينشئ React root داخل `#root` ويعرض `App` تحت `StrictMode`.
4. [src/app/app.tsx](src/app/app.tsx) ينشئ الخدمات مرة واحدة على مستوى الملف.
5. [src/app/services.ts](src/app/services.ts) يقرأ `appConfig` ويختار adapters.
6. يتم تركيب providers ثم تشغيل router.

~~~text
ErrorBoundary
└── ServicesProvider
    └── SessionProvider
        └── ToastProvider
            └── AppRouter
                └── AccountLayout
                    └── الصفحة المطابقة للمسار
~~~

عند اختيار `api` تنشأ الكائنات التالية:

~~~text
BrowserSessionManager
        ↓
FetchHttpClient
        ↓
BrowserOAuthFlow
        ↓
HttpAuthRepository + HttpAccountRepository
        ↓
Use cases → AppServices
~~~

عند اختيار `demo` يُنشأ `DemoStore` واحد يشترك فيه مستودع المصادقة ومستودع الحساب. هذا يجعل بيانات تسجيل المستخدم متاحة للعناوين والملف داخل نفس جلسة المعاينة.

`ServicesProvider` يوزع الخدمات، و`useServices()` يسترجعها. الصفحة لا تنشئ repository بنفسها. الـ alias `@/` يشير إلى `src/` في إعدادات Vite وTypeScript.

## إدارة الحالة والجلسة

الحالة موزعة حسب مسؤوليتها:

| نوع الحالة | المكان |
| --- | --- |
| قيم النموذج وفتح الحوارات | `useState` داخل الصفحة أو المكون |
| الانتظار والخطأ وأخطاء الحقول | `useAction` |
| المستخدم المعروض ومرحلة استعادة الجلسة | `SessionProvider` |
| آخر إشعار نجاح | `ToastProvider` |
| access token واستعادة refresh | `BrowserSessionManager` |
| بيانات المحاكاة | `DemoStore` |

### الفرق بين حالة React وجلسة الشبكة

`SessionProvider` يحتفظ بـ `user` و`loading`، ويقدم `setUser` و`refresh`. `refresh()` هنا تعيد قراءة المستخدم بواسطة `services.auth.getSession()`؛ لا تعني دائمًا إصدار token جديد.

`BrowserSessionManager` يحتفظ باستجابة الجلسة، ومنها access token، في الذاكرة. لديه `restore(force)` لاستعادة الجلسة من cookie، و`current` و`accept` و`clear` و`signOut` و`subscribe`.

الصفحات تحدث React context بعد الدخول وتعديل الملف والخروج، وتستخدم `refresh()` بعد تغييرات العناوين. يشترك `SessionProvider` في `auth.onSessionInvalidated` لمسح المستخدم فور بطلان الجلسة. رقم revision يمنع استجابة قديمة من استعادة مستخدم انتهت جلسته أو الكتابة فوق ملف أحدث. أخطاء الشبكة أثناء refresh تنتقل للمستدعي مع الاحتفاظ بالملف الحالي.

### استعادة الجلسة بعد تحديث الصفحة

1. access token السابق يختفي لأنه كان في الذاكرة.
2. `SessionProvider` يطلب `getSession()`.
3. `HttpAuthRepository` يطلب `BrowserSessionManager.restore()` عند غياب جلسة في الذاكرة.
4. يرسل المدير `POST /auth/browser/refresh` مع cookie تلقائيًا.
5. إذا نجح الطلب، يحتفظ بالجلسة الجديدة ثم يقرأ `GET /users/me` للحصول على الملف الحالي.
6. عند `401` من refresh ترجع جلسة فارغة؛ تبقى صفحات الدخول متاحة.

### الطلبات المحمية وتجديد التوكن

`FetchHttpClient` يرسل `Authorization: Bearer <access_token>` للطلب المحمي إذا توفر التوكن. عند `401` يحاول `restore(true)` مرة واحدة ثم يعيد الطلب مرة واحدة عند نجاح التجديد.

الطلبات المتزامنة تشترك في `refreshPromise` داخل نفس مدير الجلسة. إذا جُدد التوكن بالفعل بواسطة طلب آخر يُستخدم بدل تدويره مجددًا. إذا رفض السيرفر المحاولة الثانية بـ 401 تُمسح الجلسة. لا تُعاد عملية تخص حسابًا سابقًا تحت حساب جديد. لا يوجد مؤقت لتجديد التوكن مسبقًا، ولا تكرار مفتوح للطلبات.

طلبات login/register/email/OAuth مضبوطة بـ `authenticated: false` حتى لا تدخل في دورة refresh. مدير الجلسة يستخدم `fetch` مباشرة لطلبي refresh/logout لتجنب استدعاء نفسه عبر retry.

### تسجيل الخروج

`ProfilePage` تعرض حوار تأكيد، ثم تستدعي `services.auth.signOut()`. مدير الجلسة ينتظر refresh جارٍ قبل طلب logout حتى يكون حذف cookie آخر خطوة. عند النجاح أو 401 يمسح الذاكرة ويبلغ React فيعود المستخدم للدخول. إذا فشل الاتصال أو رجع خطأ من الخادم، يبقى الحوار برسالة وإمكانية إعادة المحاولة؛ لا تعرض الواجهة خروجًا ناجحًا لم يتم على السيرفر.

## الشاشات والمسارات

يستخدم المشروع `HashRouter`. المسار `/login` يظهر في عنوان المتصفح كالتالي:

~~~text
http://127.0.0.1:5173/#/login
~~~

| المسار داخل Router | المكون | السلوك |
| --- | --- | --- |
| `/` | `Navigate` | التحويل إلى تسجيل الدخول |
| `/login` | `LoginPage` | بريد وكلمة مرور وروابط الدخول الاجتماعي |
| `/register` | `RegisterPage` | اسم وبريد وكلمة مرور |
| `/verify-email?email=...` | `VerifyEmailPage` | مراجعة البريد وإعادة إرسال التأكيد |
| `/verify-email/confirm?token=...` | `ConfirmEmailPage` | تأكيد الرمز بزر صريح ثم حالة نجاح |
| `/forgot-password` | `ForgotPasswordPage` | طلب رابط تعيين كلمة المرور |
| `/reset-password/sent?email=...` | `ResetPasswordSentPage` | رسالة عامة ومساعدة لطلب رابط جديد |
| `/reset-password?token=...` | `ResetPasswordPage` | كلمة مرور جديدة وتأكيدها |
| `/reset-password/success` | `ResetPasswordSuccessPage` | نجاح والعودة للدخول |
| `/oauth/google` و`/oauth/facebook` | `SocialSignInPage` | شرح ومتابعة المزود المختار |
| `/oauth/callback` | `OAuthCallbackPage` | إكمال ticket أو عرض خطأ المزود |
| `/onboarding/profile` | `CompleteProfilePage` | استكمال الاسم والرقم |
| `/onboarding/address` | `CompleteAddressPage` | أول عنوان توصيل |
| `/onboarding/complete` | `AccountReadyPage` | اكتمال بيانات الحساب |
| `/account` | `ProfilePage` | عرض الملف والعنوان الافتراضي والخروج |
| `/account/edit` | `EditProfilePage` | تعديل الاسم والموبايل |
| `/account/addresses` | `AddressesPage` | القائمة والإضافة والحذف والافتراضي |
| `/account/addresses/new` | `AddressEditorPage` | إنشاء عنوان |
| `/account/addresses/:id/edit` | `AddressEditorPage` | تعديل عنوان بعد قراءته من القائمة |
| أي مسار آخر | `NotFoundPage` | رسالة ورابط للعودة إلى صفحة معروفة |

### حراسة المسارات

- `RequireSession` ينتظر تحميل الجلسة، ثم يفتح المحتوى أو يعيد المستخدم للدخول.
- `GuestOnly` يمنع عرض login/register/social للمستخدم المسجل ويختار وجهته المناسبة.
- `RequirePhone` يسبق خطوة العنوان في onboarding.
- `RequireCompleteProfile` يحمي شاشة اكتمال الحساب.

`accountDestination(user)` يختار `/onboarding/profile` إذا غاب الرقم، ثم `/onboarding/address` إذا غاب العنوان الافتراضي، وإلا `/account`.

شاشات الحساب والعناوين تتطلب جلسة فقط. يستطيع المستخدم تأجيل العنوان وفتح حسابه؛ يظهر تنبيه باستكمال البيانات. guards تنظم تجربة الواجهة، أما التصريح الفعلي على البيانات فينفذه الباك إند.

## رحلات المستخدم

### إنشاء الحساب وتأكيد البريد

1. `RegisterPage` تجمع الاسم والبريد وكلمة المرور.
2. `createSignUp` يطبّع الاسم والبريد ويتحقق من كلمة المرور.
3. `HttpAuthRepository.signUp` يرسل بيانات التسجيل فقط.
4. تنتقل الصفحة إلى مراجعة البريد؛ لا تُنشأ جلسة دخول تلقائية.
5. بعد فتح الرابط الخارجي، `normalizeExternalLinks` يحوله إلى مسار تأكيد داخل Router.
6. `useSensitiveSearchParam` يحتفظ بالرمز في الذاكرة ويحذفه من العنوان عبر React Router، ثم `ConfirmEmailContent` تعرض زر التأكيد الصريح. هذا يبقي حالة Router متزامنة مع عنوان المتصفح.
7. بعد نجاح `confirmEmail` تظهر شاشة نجاح والعودة للدخول.
8. إذا حاول المستخدم الدخول قبل التأكيد، تتعامل الصفحة مع `email_not_verified` و`email_verification_required` وتفتح شاشة مراجعة البريد.

إعادة إرسال التأكيد تمر من `useResendVerification`، وبعد النجاح يبدأ عداد محلي لمدة 60 ثانية. هذا العداد تحسين للواجهة؛ حدود الإرسال الفعلية مسؤولية السيرفر.

### الدخول واستكمال البيانات

1. `LoginPage.handleSubmit` يستدعي `services.auth.signIn` عبر `useAction.run`.
2. الـ use case ينظف البريد ويتحقق من كلمة المرور، ثم repository ينفذ الطلب.
3. عند النجاح يُحفظ access token في مدير الجلسة، ويُحول `dto.user` إلى `UserProfile`.
4. الصفحة تستدعي `setUser` ثم `accountDestination`.
5. `ProfileForm` يحفظ الاسم والرقم من خلال use case تعديل الملف.
6. `AddressForm` تجمع العنوان وبيانات المستلم وتحفظها؛ أول عنوان يصبح افتراضيًا وفق الباك إند.
7. النموذج يعيد قراءة المستخدم لتحديث `profileComplete` و`defaultAddressId`، ثم يعرض اكتمال الحساب.

### نسيان كلمة المرور

1. إدخال البريد في `ForgotPasswordPage`.
2. طلب `requestPasswordReset`.
3. عرض رسالة عامة: «لو البريد ده مرتبط بحساب…» حتى لا تعتمد الواجهة على كشف وجوده.
4. فتح رسالة البريد والرابط الخارجي.
5. إدخال كلمة المرور وتأكيدها في `ResetPasswordForm`.
6. تطابق كلمتي المرور يفحص محليًا؛ لا يرسل `passwordConfirmation` إلى API.
7. طلب `resetPassword` يحتوي `token` و`password` فقط.
8. عند النجاح تُمسح جلسة الشبكة و`user`، ثم تظهر شاشة النجاح وتسجيل الدخول مجددًا.

الخادم يلغي الجلسات السابقة وفق سياسة reset الخاصة به. الفرونت لا يعدّل password hash ولا يرسل البريد بنفسه.

### Google وFacebook

1. `SocialButtons` ينقل المستخدم إلى شاشة المزود.
2. زر المتابعة يستدعي `BrowserOAuthFlow.start` في وضع API.
3. ينشئ المتصفح verifier عشوائيًا بـ `crypto.getRandomValues`، ويحسب `SHA-256` له بصيغة hex.
4. يحفظ verifier تحت `foodify.oauth.verifier.google` أو `foodify.oauth.verifier.facebook` في `sessionStorage`.
5. يرسل `binding_challenge` إلى endpoint البداية، ثم يفتح `authorization_url`.
6. الباك إند يتولى التواصل مع المزود والتحقق من `state` والهوية. Google PKCE وnonce ينفذهما الباك إند؛ verifier المتصفح هنا لربط البداية والنهاية.
7. يعود المتصفح إلى `FRONTEND_URL/oauth/callback#ticket=...`.
8. bootstrap يحوّل الرابط إلى مسار Router. صفحة callback تمسح ticket من العنوان ثم ترسلها مع verifier الأصلي.
9. يتم حذف verifier في `finally` لطلب الإكمال، ثم حفظ جلسة المتصفح وتوجيه المستخدم لاستكمال بياناته.

المعرفات والأسرار الحقيقية تضبط في `../back/.env.development`، وتفاصيل إعداد المزودين في [دليل OAuth للباك إند](../back/docs/OAUTH.md). `FRONTEND_URL` يجب أن يطابق أصل الصفحة التي بدأت منها العملية حرفيًا؛ `localhost` و`127.0.0.1` لهما `sessionStorage` منفصلة.

الواجهة تعرض رسائل لإلغاء الدخول وغياب البريد وضرورة استخدام طريقة الدخول الأصلية. كود `email_verification_required` يعرض تعليمات واضحة: افتح رسالة التأكيد ثم أعد الدخول بنفس المزود. تُمسح بيانات المحاولة عند فشل البداية أو عودة خطأ أو إلغاء الرحلة. رابط التحويل يجب أن يكون HTTPS على نطاق Google أو Facebook المحدد في الكود، ولا تقبل الواجهة وجهة عشوائية.

### إدارة العناوين

`AddressesPage` تحمل القائمة وتعرض كل عنصر باستخدام `AddressCard`. يوجد عرض فارغ للقائمة، وإعادة محاولة إذا فشلت القراءة، وتوقف أزرار التعديل أثناء العملية.

إضافة وتعديل العنوان يستخدمان `AddressForm` نفسه. بيانات المستلم تبدأ باسم المستخدم ورقمه، ويمكن تعديلها. النموذج يعرض المدينة والمنطقة والشارع والعمارة والدور والشقة وتعليمات التوصيل. اختيار «مكان تاني» يفتح اسمًا مخصصًا، وتعديل عنوان يحافظ على countryCode الموجودة. بعد نجاح الحفظ لا يتحول فشل قراءة الملف التالية له إلى فشل حفظ؛ يمنع ذلك طلب POST مكررًا لنفس العنوان، مع إظهار إشعار إذا تعذر تحديث بقية البيانات.

حذف العنوان يتطلب حوار تأكيد. بعد الحذف أو اختيار الافتراضي تعيد الصفحة تحميل القائمة والملف معًا حتى يتحدث مؤشر العنوان الافتراضي. تعرض الواجهة حد 20 عنوانًا؛ السيرفر هو صاحب قرار قبول العدد.

لا يوجد endpoint لقراءة عنوان واحد في adapter الحالي؛ شاشة التعديل تقرأ قائمة العناوين وتختار المعرف المطلوب.

## الربط بالباك إند وتحويل البيانات

### طبقة النقل

[FetchHttpClient](src/infrastructure/http/fetch-client.ts) يضيف:

~~~text
Accept: application/json
X-Foodify-Client: web
Authorization: Bearer <access_token>  للطلبات المحمية عندما يتوفر التوكن
Content-Type: application/json      عندما يوجد body
credentials: include
~~~

يدعم `RequestOptions` اختيار method وbody و`authenticated` و`AbortSignal`. وجود signal في العقد لا يعني أن كل صفحة تستخدم إلغاء الطلب حاليًا.

### مصفوفة العمليات المستخدمة من الواجهة

المسارات التالية تضاف إلى `VITE_API_BASE_URL` الذي ينتهي بـ `/api/v1`:

| العملية | HTTP |
| --- | --- |
| التسجيل | `POST /auth/register` |
| الدخول | `POST /auth/browser/login` |
| تأكيد البريد | `POST /auth/verify-email` |
| إعادة التأكيد | `POST /auth/resend-verification` |
| طلب الاسترجاع | `POST /auth/forgot-password` |
| تعيين كلمة مرور | `POST /auth/reset-password` |
| استعادة الجلسة | `POST /auth/browser/refresh` |
| الخروج | `POST /auth/browser/logout` |
| بدء OAuth | `POST /auth/oauth/{provider}/start` |
| إكمال OAuth | `POST /auth/browser/oauth/complete` |
| قراءة الملف | `GET /users/me` |
| تعديل الملف | `PATCH /users/me` |
| عرض العناوين | `GET /users/me/addresses` |
| إضافة عنوان | `POST /users/me/addresses` |
| تعديل عنوان | `PUT /users/me/addresses/{id}` |
| حذف عنوان | `DELETE /users/me/addresses/{id}` |
| اختيار الافتراضي | `PUT /users/me/default-address/{id}` |

`logout-all` موجود ضمن عقود الباك إند، لكنه ليس إجراءً موصولًا بواجهة الحساب الحالية.

### ثلاثة أنواع من البيانات

| النوع | مكانه | مثال |
| --- | --- | --- |
| Domain model | `features/*/domain` | `UserProfile.phoneNumber` |
| Application DTO | بجوار use case | `UpdateProfileDto` |
| HTTP DTO | `infrastructure/dto` وعقود HTTP المشتركة | `UpdateProfileDto.phone` في عقد الشبكة |

قد تتشابه الأسماء، لكن كل نوع يخص حدًا مختلفًا. لا يُرسل كائن React أو form state كامل إلى API.

### تحويل الحقول

| داخل React | في API |
| --- | --- |
| `phoneNumber` | `phone` |
| `emailVerified` | `email_verified` |
| `profileComplete` | `profile_complete` |
| `defaultAddressId` | `default_address_id` |
| `recipientName` | `recipient_name` |
| `countryCode` | `country_code` |
| `deliveryInstructions` | `delivery_notes` |
| `isDefault` | `is_default` |

التحويل موجود في [user-profile-mapper.ts](src/features/account/infrastructure/mappers/user-profile-mapper.ts) و[address-mapper.ts](src/features/account/infrastructure/mappers/address-mapper.ts). يتحققان من شكل الحقول المطلوبة وقت التشغيل، لأن TypeScript وحده لا يثبت صلاحية JSON الخارجي.

`toAddressWriteDto` يرسل حقول الكتابة صراحة، ويحول النصوص الاختيارية الفارغة إلى `null`. لا يرسل `id` أو `isDefault` أو بيانات الدور.

`PUT` يستبدل العنوان كاملًا. لذلك `HttpAccountRepository` يحتفظ بإحداثيات العناوين المقروءة داخل `Map`، ويعيد إرسالها عند التعديل حتى لا يمسح إحداثيات غير معروضة في النموذج. لا توجد خريطة أو أداة تغيير إحداثيات في هذه المرحلة.

### روابط البريد الخارجية

رسالة الباك إند تحتوي مثلًا:

~~~text
http://127.0.0.1:5173/verify-email#token=...
http://127.0.0.1:5173/reset-password#token=...
~~~

`normalizeExternalLinks` يحولها قبل بدء React إلى route يحتوي الرمز داخل hash، ثم تمسحه صفحة التأكيد أو reset من عنوان المتصفح وتحفظه مؤقتًا في props أثناء الاستخدام.

فتح رابط داخلي يبدأ بـ `/#/` يعمل مع استضافة ثابتة. روابط البريد وOAuth تبدأ بمسار فعلي مثل `/reset-password`؛ الاستضافة يجب أن تقدم `index.html` لهذه المسارات أيضًا. Vite يوفر ذلك في التطوير، ويجب ضبط fallback في الاستضافة النهائية.

عند تحديث الصفحة بعد تنظيف الرمز من العنوان، يلزم فتح الرابط الأصلي مرة أخرى إذا لم تُكمل العملية.

## التحقق والأخطاء

### التحقق من المدخلات

| القيمة | ما يطبقه الفرونت |
| --- | --- |
| البريد | trim وحروف صغيرة وشكل بريد وحد أقصى 254 |
| الاسم | trim وتوحيد المسافات، طول 1–100 في domain |
| كلمة المرور الجديدة | 15–128 حرفًا، ورفض قيمة كلها فراغات |
| كلمة مرور الدخول | 1–128 حرفًا، دون فرض حد التسجيل على حساب قائم |
| كلمة المرور | لا تُقص المسافات منها قبل الإرسال |
| رمز البريد | التحقق المحلي من كونه غير فارغ؛ التحقق الكامل عند السيرفر |
| الموبايل | تحويل أرقام عربية وفارسية، وصيغ مصرية إلى `+20` |
| العنوان | أطوال الحقول المطلوبة وتحويل الاختياري الفارغ إلى `null` |
| countryCode | حرفان كبيران؛ النموذج الحالي يستخدم `EG` |
| address ID | غير فارغ؛ صلاحية UUID وملكية العنوان عند السيرفر |

`normalizeEgyptianPhone` يقبل صيغة مثل `01012345678` أو `1012345678` أو `+201012345678` أو `00201012345678`، ويعيد صيغة E.164 مصرية موحدة.

النماذج تستخدم `noValidate` لتوحيد رسائل الخطأ عبر validation و`useAction`. خصائص الحقول مثل `maxLength` و`autoComplete` تساعد الإدخال، ويظل الباك إند المرجع النهائي.

### توحيد الأخطاء

`ApplicationError` يعرّف `code` و`message` و`fields?` و`status?`. `AppError` ينفذ العقد ويرث `Error`. `getErrorMessage` يستخدم رسالة `AppError` أو رسالة عامة للخطأ غير المتوقع.

`readApiError` يقرأ غلاف `error`، ويحول `details` إلى خريطة أخطاء حقول، ويزيل بادئات مثل `body.`. `readJson` يتعامل مع `204` كاستجابة بلا body ويرفض JSON غير الصالح.

`useAction` يوفر:

- `pending` لتعطيل الإرسال وعرض التحميل.
- `error` لرسالة العملية.
- `fieldErrors` لأخطاء الحقول.
- `run(action, onSuccess)` لتشغيل العملية ومعالجة النتيجة.
- `clearError()` لتنظيف الرسائل.
- قفلًا متزامنًا بـ `useRef` يمنع تكرار نفس الإرسال.
- تركيز أول حقل يحمل `aria-invalid="true"` بعد الفشل.

أخطاء قواعد domain وأكواد API المعروفة تظهر برسائل عربية. الأخطاء غير المعروفة تستخدم رسالة عامة بدل عرض body أو رسالة خام من مصدر خارجي. أسماء حقول API تُحول إلى أسماء النموذج، مثل phone → phoneNumber وdelivery_notes → deliveryInstructions، فتظهر أخطاء التحقق تحت حقولها.

`AppError` يحتفظ أيضًا بـ `requestId` و`retryAfterSeconds`. يُقرأ Retry-After سواء كان عدد ثوانٍ أو تاريخًا؛ عداد إعادة التأكيد يلتزم بمدة 429. لا يوجد retry آلي لأخطاء 429. `useAction` يتجاهل تحديث الحالة وبدء callback النجاح إذا كانت الصفحة قد أُغلقت بالفعل.

### ErrorBoundary

[ErrorBoundary](src/app/error-boundary.tsx) يعرض شاشة لاستعادة العرض إذا فشل render، مع زر تحديث الصفحة. أخطاء طلبات الشبكة تعالجها الصفحات و`useAction`. لا يوجد ربط بخدمة مراقبة أخطاء خارجية.

## المكونات والتصميم وإمكانية الوصول

### المكونات المشتركة

| المكون | الاستخدام |
| --- | --- |
| `Button` | أنماط primary/secondary/ghost/danger وتحميل وتعطيل |
| `Field` | label وhint وخطأ ومعرفات ربط بعنصر الإدخال |
| `PasswordField` | حقل كلمة مرور مع إظهار وإخفاء |
| `FormError` | رسالة عامة بـ `role="alert"` |
| `PageHeading` | عنوان ووصف الصفحة مع قابلية نقل التركيز |
| `StatusView` | أيقونة وعنوان ووصف وإجراءات للنجاح والخطأ |
| `LoadingState` | مؤشر انتظار بـ `role="status"` |
| `Dialog` | حوار HTML أصلي عبر `showModal` وإغلاق بـ Escape |
| `BackLink` | رجوع داخلي باستخدام Router |

`SocialButtons` و`EmailPreview` و`ProfileForm` و`AddressForm` و`AddressCard` و`OnboardingSteps` تخص الـ features؛ لم توضع داخل shared لأنها تحمل معنى من مجال الحساب.

### نظام الشكل

[src/styles.css](src/styles.css) يضم متغيرات التصميم:

| المتغير | القيمة | الاستخدام |
| --- | --- | --- |
| `--red` | `#d42135` | لون الهوية والأزرار |
| `--red-deep` | `#b8192a` | hover |
| `--ink` | `#171719` | النص الأساسي |
| `--secondary` | `#66646c` | النص الثانوي |
| `--line` | `#dedce1` | الحدود والفواصل |
| `--soft` | `#f8f7f8` | الخلفيات المحايدة |
| `--pale` | `#fff2f3` | الخلفية الحمراء الخفيفة |
| `--radius` | `14px` | تدوير العناصر المشتركة |

`AccountLayout` يضم header وfooter والمساعدة ومساحة الصفحة، و`BrandPanel` يضم لوحة الهوية والرسم المبني بـ CSS والأيقونات. لا يوجد طلب صور خارجي لعرض الهوية.

على سطح المكتب التخطيط عمود للنموذج وعمود للهوية. تحت `700px` تتحول لوحة الهوية لشريط مختصر وتُخفى الرسمة والنصوص الزائدة. توجد تعديلات أيضًا عند `1240px` و`920px` و`370px`، ودعم تقليل الحركة عبر `prefers-reduced-motion`.

الـ CSS الحالي ملف مشترك واحد، بينما مكونات React مقسمة حسب مسؤوليتها؛ لا يوجد CSS Module مستقل لكل مكون.

### تحسينات الوصول المنفذة

- `lang="ar"` و`dir="rtl"` مع `bdi` و`dir="ltr"` للبريد والأرقام عند الحاجة.
- labels مرتبطة بالحقول، و`aria-describedby` للتلميح والخطأ.
- `aria-invalid` و`aria-busy` و`aria-pressed` للحالات المناسبة.
- عناوين وإشعارات مقروءة لقارئات الشاشة.
- رابط «انتقل للمحتوى» ظاهر عند التركيز.
- `RouteEffects` يحدث عنوان الصفحة ويعيد التمرير وينقل التركيز إلى `h1`.
- مؤشر `focus-visible` ودعم استخدام لوحة المفاتيح.
- `ToastProvider` يعرض إشعارًا لمدة 4.5 ثوانٍ مع إغلاق يدوي و`aria-live="polite"`.
- الحوارات تعتمد على سلوك `dialog` الأصلي للتركيز وعزل الخلفية.

هذه خصائص منفذة في الكود، ولا تعني إجراء تدقيق اعتماد كامل لمعايير WCAG.

## المحاكاة

اختر `VITE_DATA_SOURCE=demo` ثم أعد تشغيل Vite. `DemoStore` يحتفظ بحسابات وعناوين ورموز تأكيد واسترجاع داخل الذاكرة، مع تأخير صناعي قصير لعرض loading.

حساب المعاينة:

~~~text
email: mariam@example.com
password المعروضة: Demo Foodify account!
~~~

المحاكاة تتحقق من مدخلات كلمة المرور عبر use case، لكنها لا تحفظ كلمة المرور ولا تقارنها بكلمة سر مخزنة. أي كلمة مرور غير فارغة تقبلها قواعد الدخول تصلح لحساب تجريبي معروف؛ هذا سلوك معاينة فقط.

في هذا الوضع تظهر أدوات إضافية: ملء حساب العرض، صندوق بريد تجريبي، وشريط «عن النسخة دي». Google وFacebook ينشئان هوية محلية دون الاتصال بالمزود.

الرموز التجريبية صالحة 15 دقيقة وتُستهلك مرة واحدة. `services.demo.reset()` أو تحديث الصفحة يمسح الحالة. في وضع API أدوات `demo` تعيد `null` أو لا تنفذ شيئًا، وأزرار المعاينة مخفية؛ لا يمكن بها تأكيد بريد حقيقي أو مسح قاعدة البيانات.

## الحماية وحدود التنفيذ

- access token في الذاكرة؛ refresh token تضعه خدمة الباك إند في HttpOnly cookie.
- كلمات المرور لا تخزن في `localStorage` أو `sessionStorage`.
- `sessionStorage` يُستخدم مؤقتًا لـ OAuth verifier.
- الـ tokens والتذاكر تُقرأ من fragment ثم تُزال من العنوان بواسطة صفحاتها.
- `index.html` يضبط referrer policy إلى `no-referrer`.
- سياسة CSP تضاف وقت build؛ scripts/styles/fonts من نفس المصدر، و`connect-src` يسمح بـ `'self'` وأصل API في وضع api، ويمنع الاتصالات في وضع demo.
- sourcemaps معطلة في build.
- المصادقة وملكية العناوين وقيود البيانات تنفذ على السيرفر أيضًا؛ حراسة المسارات ليست تصريحًا أمنيًا على API.

CORS وخصائص cookie وOAuth provider settings وإرسال البريد ليست إعدادات React. الطلب الحقيقي يحتاج تشغيل API وقاعدة البيانات وRedis وعامل البريد وضبط المزودين.

حدود المرحلة الحالية تشمل عدم وجود تغيير بريد أو تغيير كلمة مرور من داخل الحساب، وعدم وجود حذف حساب أو خرائط أو دعم هواتف دول متعددة. نصوص المساعدة وإعادة التأكيد تراعي وضع api أو demo. لا تُستخدم أدوات المحاكاة لتغيير حساب حقيقي.

## الأعطال التي عولجت وطريقة تشخيصها

| العطل | التفسير والمعالجة |
| --- | --- |
| الواجهة كانت تعتمد على demo | أضيف اختيار المصدر وتركيب HTTP repositories من `services.ts` |
| اختلاف حقول API والعرض | أضيفت DTOs وmappers؛ مثل `phone` إلى `phoneNumber` |
| استجابة غير مكتملة | mappers و`readJson` يرجعان `invalid_response` |
| رابط البريد يفتح خارج Router | bootstrap يحول المسار الفعلي إلى route داخل hash |
| OAuth يفقد verifier بعد الرجوع | توحيد `FRONTEND_URL` مع origin الذي بدأ التدفق |
| OAuth completion يرفض التذكرة | تحقق من وجود verifier الأصلي ونفس origin وصلاحية ticket وعقد البصمة على الباك إند؛ لا تعتبرها وحدها دليلًا على خطأ في المقارنة |
| CORS يمنع طلبات المتصفح | تضبط أصول `5173/4173` وheader `X-Foodify-Client` على API ثم تُحدث الخدمة |
| `redirect_uri_mismatch` من Google | callback الخاص بـ API يجب أن يطابق OAuth Client؛ لا يوضع في Privacy/Terms |
| `oauth_unavailable` | بيانات المزود غير مضبوطة في الباك إند أو الخدمة لم تقرأ التحديث |
| الإيميل ما زال يشير إلى `3000` | عامل البريد منفصل؛ تحديث API وحده يترك worker بإعداد قديم |
| تعديل عنوان يمسح الإحداثيات | adapter يحتفظ بالإحداثيات ويعيد إرسالها مع PUT الكامل |

للمشكلة الخاصة بروابط البريد، القيمة المحلية الحالية في الباك إند:

~~~dotenv
FRONTEND_URL=http://127.0.0.1:5173
~~~

مع تشغيل خدمات البيانات، حدث API وعامل البريد معًا:

~~~bash
cd /home/hyzin/Projects/Foodify/back
sudo docker compose --env-file .env.development up -d --build --force-recreate --no-deps api email-worker
~~~

ثم اطلب رسالة جديدة. محتوى الرسائل القديمة لا يتغير. الأمر يشمل خدمات التطبيق ولا يحذف volumes أو بيانات المستخدمين.

عند فتح build المعاينة على `4173` يجب أن تطابق إعدادات callback وCORS عنوان المعاينة المستخدم؛ وجود `4173` في CORS وحده لا يغير `FRONTEND_URL`.

## تعديل المشروع وتسليمه

### أين تعدل كل نوع من المتطلبات؟

| التغيير | مكانه |
| --- | --- |
| ألوان ومسافات واستجابة الشاشات | `src/styles.css` |
| زر أو حقل مشترك | `src/shared/ui` |
| شكل شاشة الدخول | `features/auth/presentation/pages/login-page.tsx` |
| نموذج عنوان مشترك | `features/account/presentation/components/address-form.tsx` |
| قواعد الاسم والبريد وكلمة المرور | `features/auth/domain/validation.ts` |
| قواعد الموبايل والعنوان | `features/account/domain/validation.ts` |
| عنوان endpoint أو request DTO | repository و`infrastructure/dto` الخاص بالـ feature |
| أسماء response fields | mappers |
| طريقة اختيار api/demo | `app/config.ts` و`app/services.ts` |
| المسارات وترتيب الاستكمال | `app/router` |
| تحويل روابط البريد وOAuth | `app/bootstrap/external-links.ts` |
| أسرار Google/Facebook وعنوان البريد | ملفات البيئة في `../back` |

### إضافة وظيفة جديدة

1. حدد نموذجها ومدخلاتها وما يلزم إضافته إلى repository interface.
2. أنشئ `application/<operation>/dto.ts` و`use-case.ts`.
3. نفذها في HTTP adapter، وفي demo adapter إذا كانت مطلوبة للمعاينة.
4. اربط الدالة داخل `createAppServices` للفرعين.
5. أضف مكونًا أو صفحة تستدعي `useServices` و`useAction`.
6. أضف route وحراسته عند الحاجة.
7. حدث توثيق العقود والدوال.

إضافة متجر أو طلبات مستقبلًا تكون في feature جديدة مثل `catalog` أو `orders`، بدل إضافة منطقها إلى auth أو جمع كل الوظائف في user service واحد.

### حدود التحقق وتسليم الفريق

طلب المشروع يفصل مسؤولية الاختبارات عن التنفيذ. مراجعة الفرونت شملت تصحيح الكود وفحص الأنواع والبناء دون إضافة أو تشغيل tests. راجع [تقرير المراجعة](docs/REVIEW.md) لمعرفة الأعطال وإصلاحاتها وحدود التحقق. أوامر typecheck وbuild لا تثبت وحدها نجاح OAuth أو إعدادات SMTP الحقيقية.

ابدأ قراءة الكود بالترتيب: `main.tsx` → `app.tsx` → `services.ts` → `app-router.tsx` → use case العملية → repository → mapper. وللبحث عن وظيفة بعينها استخدم [فهرس الدوال والمكونات](docs/FUNCTIONS.md).
