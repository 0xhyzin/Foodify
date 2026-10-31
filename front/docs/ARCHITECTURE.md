# معمارية واجهة Foodify

الواجهة تطبق Clean Architecture بشكل مبسّط، مع تنظيم حسب الـ feature وبناء العرض من مكونات صغيرة. التركيز على حساب العميل في هذه المرحلة؛ أغلب العمليات لها DTO وuse case مستقل، والصفحات لا تعرف كيفية تخزين البيانات أو إرسالها.

ميزة `marketplace` مستقلة وتحتوي نماذج المجال وعقود المستودعات وحالات الاستخدام ومحوّلات HTTP وصفحات ومكونات العرض. بيانات المطاعم والمنتجات لا تأتي من ملف داخل React؛ يقرأها `HttpCatalogRepository` من API بعد حفظها في MySQL. تفاصيل المسار في [CATALOG.md](CATALOG.md). `MarketplaceLayout` يحيط بصفحات التسوق، والجلسة مشتركة مع صفحات الحساب.

الشرح الشامل للواجهة في [README](../README.md)، ومسؤولية الدوال والمكونات بالتفصيل في [FUNCTIONS.md](FUNCTIONS.md). أغلب العمليات لها use case مستقل؛ `completeProviderSignIn` موصلة حاليًا مباشرة من composition root إلى repository.

## اتجاه الاعتمادات

```text
Presentation: صفحات React ومكونات النماذج
        │ تستدعي
        ▼
Application: DTO + use case لكل عملية
        │ تعتمد على
        ▼
Domain: models + repository interfaces + validation
        ▲ تنفّذ الواجهات
        │
Infrastructure: HTTP repositories أو demo repositories داخل الذاكرة

App composition: تنشئ التنفيذ الفعلي وتحقنه في React
Shared: مكونات العرض العامة، إدارة أخطاء موحدة، hooks مشتركة
```

النطاق وطبقة التطبيق لا يستوردان React أو Router أو HTTP client. طبقة العرض تستقبل الخدمات من context؛ تبديل التنفيذ يتم في نقطة تركيب الاعتمادات. `infrastructure` تعرف النماذج والواجهات التي تنفّذها، وتفاصيلها لا تتسرب إلى الصفحات.

## الحدود بين الطبقات

| الطبقة | مسؤوليتها | أمثلة |
| --- | --- | --- |
| `domain` | تعريف نماذج العمل، واجهات الاعتماد، وقواعد التحقق | `UserProfile`, `Address`, `AuthRepository`, `AccountRepository` |
| `application` | تنفيذ عملية واحدة، التحقق من الـ input، والتفويض للـ repository | الدخول، إنشاء حساب، حفظ عنوان |
| `infrastructure` | تنفيذ الاتصال بالخدمات | `FetchHttpClient` ومستودعات HTTP؛ ملفات محاكاة الحساب القديمة غير مركبة في التشغيل الحالي |
| `presentation` | النماذج والتنقل والعرض وأخطاء الحقول | صفحات التسجيل والحساب |
| `app` | تركيب الاعتمادات والـ providers والمسارات وإعداد البيئة | `AppServices`, `ServicesProvider`, Router |
| `shared` | أدوات مستقلة تستخدمها أكثر من feature | `Button`, `Field`, `Dialog`, `AppError`, `useAction` |

نموذج الواجهة ليس هو request DTO الخاص بالباك إند. مثلًا `Address.phoneNumber` اسم مفهوم للتطبيق، وتحويله إلى `phone` مكانه adapter التكامل. يمكن للـ adapter تجاهل بيانات استجابة لا يحتاجها العرض.

## ملفات الأساس

| الملف | الدور |
| --- | --- |
| `src/app/services.ts` | عقد `AppServices`: خدمات الحساب والمصادقة، مع أدوات معاينة منفصلة `DemoControls` |
| `src/app/config.ts` | قراءة إعدادات البيئة العامة والتحقق من مصدر البيانات المدعوم |
| `src/infrastructure/demo/demo-store.ts` | حالة المحاكاة في الذاكرة: الحسابات والعناوين والجلسة وروابط المعاينة |
| `src/infrastructure/http/` | transport موحد، تحويل أخطاء API، وإدارة جلسة cookie/access token |
| `src/features/auth/infrastructure/http-auth-repository.ts` | ربط عمليات auth بالـ browser API وOAuth |
| `src/features/account/infrastructure/http-account-repository.ts` | ربط الملف والعناوين مع DTO mappers |
| `src/app/providers/services-provider.tsx` | حقن الخدمات واسترجاعها باستخدام `useServices()` |
| `src/app/providers/session-provider.tsx` | حالة المستخدم الحالي: `user`, `loading`, `setUser()`, `refresh()` |
| `src/app/providers/toast-provider.tsx` | إشعارات مشتركة عبر `showToast()` ومنطقة إعلان لقارئات الشاشة |
| `src/app/router/paths.ts` | `accountDestination()` لاختيار الخطوة التالية بحسب الموبايل والعنوان الافتراضي |
| `src/app/router/app-router.tsx` | تعريف مسارات الصفحات باستخدام `HashRouter` وتجميعها تحت `AccountLayout` |
| `src/app/router/route-guards.tsx` | تنظيم الدخول وصفحات الزائر وترتيب خطوات الاستكمال |
| `src/app/router/route-effects.tsx` | تحديث عنوان الصفحة والتمرير وتركيز العنوان بعد التنقل |
| `src/app/layouts/account-layout.tsx` | هيكل الموقع المشترك: header، مساحة النموذج، المساعدة، وأدوات العرض |
| `src/app/layouts/brand-panel.tsx` | لوحة الهوية الحمراء المستقلة عن منطق الحساب |
| `src/app/error-boundary.tsx` | حالة استعادة عند خطأ غير متوقع أثناء عرض React |
| `src/shared/domain/app-error.ts` | `ApplicationError` و`AppError` لخطأ يمكن عرضه وربطه بالحقول |
| `src/shared/hooks/use-action.ts` | حالة العملية، منع إرسالها مرتين، معالجة الأخطاء، والتركيز على أول حقل غير صالح |

`refresh()` في SessionProvider تعيد قراءة المستخدم من `getSession()`. في API يجدد `FetchHttpClient` الجلسة مرة واحدة عند `401`، بينما تظل access token في الذاكرة وrefresh token داخل HttpOnly cookie. وضع demo لا يستخدم رموزًا حقيقية.

## تقسيم الـ features

```text
src/features/
├── auth/
│   ├── domain/
│   │   ├── models.ts
│   │   ├── auth-repository.ts
│   │   ├── oauth-flow.ts
│   │   └── validation.ts
│   ├── application/
│   │   └── <operation>/
│   │       ├── dto.ts
│   │       └── use-case.ts
│   ├── infrastructure/
│   │   ├── dto/auth-dto.ts
│   │   ├── http-auth-repository.ts
│   │   ├── oauth-flow.ts
│   │   └── demo-auth-repository.ts
│   └── presentation/
│       ├── components/
│       └── pages/
└── account/
    ├── domain/
    │   ├── models.ts
    │   ├── account-repository.ts
    │   └── validation.ts
    ├── application/
    │   └── <operation>/
    │       ├── dto.ts
    │       └── use-case.ts
    ├── infrastructure/
    │   ├── dto/account-dto.ts
    │   ├── mappers/
    │   ├── http-account-repository.ts
    │   └── demo-account-repository.ts
    └── presentation/
        ├── components/
        ├── onboarding/
        ├── profile/
        └── addresses/
```

وجود مجلد لكل عملية يمنع تراكم جميع وظائف المستخدم في ملف واحد. واجهتا الـ repository مقسمتان حسب قدرات `auth` و`account`؛ لا نحتاج interface منفصلة لكل زر أو مكوّن عرض. الفصل يكون عند حدود الاعتماد الفعلية.

## رحلة طلب داخل التطبيق

مثال حفظ عنوان:

```text
صفحة العنوان تجمع المدخلات
  → useAction.run() يمنع الإرسال المتزامن ويدير pending/errors
  → use case حفظ العنوان يتحقق من DTO ويطبّع الحقول
  → AccountRepository.saveAddress(input, id?)
  → HttpAccountRepository يرسل DTO إلى API
  → يعود نموذج Address
  → الصفحة تحدّث العرض والتنقل والإشعار
```

في وضع API تبقى مسؤولية الصفحة كما هي. `HttpAccountRepository` يختار المسار ويبني request DTO ويحول response إلى نموذج التطبيق. `FetchHttpClient` يتولى headers وcredentials وBearer وتجديد الطلب وتحويل أخطاء HTTP. `BrowserSessionManager` يستخدم `fetch` مباشرة لعمليتي refresh/logout حتى لا يدخل تجديد الجلسة في retry متكرر.

## مكونات العرض

| المكون | مسؤوليته |
| --- | --- |
| `Button` | أنماط الأزرار وحالة التحميل والتعطيل |
| `Field` وحقول الإدخال المتخصصة | label وhint والخطأ ومعرفات الوصول |
| `Dialog` | حوار تفاعلي، إغلاق بـ Escape، حبس التركيز وإعادته |
| `PageHeading` | عنوان ووصف متناسقان للصفحات |
| `BackLink` | رجوع واضح إلى المسار المناسب |
| `FormError` | عرض خطأ العملية العام |
| `LoadingState` | حالة انتظار أثناء قراءة الجلسة أو البيانات |
| `StatusView` | شاشات النجاح والتأكيد مع الإجراء التالي |

المكونات العامة في `shared/ui` لا تستدعي الخدمات ولا تتخذ قرارات تخص المصادقة. المكونات التي تحمل معنى للحساب أو العنوان تبقى داخل feature المالكة لها. النصوص العربية وRTL والأيقونات والخط جزء من العرض؛ لا تدخل قواعد العمل.

## الجلسة والتنقل

`SessionProvider` مصدر حالة المستخدم الحالية داخل React. تحديث حالة المستودع وحده لا يكفي لتحديث العرض؛ صفحات الدخول والخروج وتعديل البيانات تحدّث context أو تعيد قراءته عند الحاجة.

يشترك SessionProvider في `AuthRepository.onSessionInvalidated`، ويوصل HTTP repository هذا الحدث بمدير الجلسة. مسح جلسة الشبكة يحدث المستخدم المعروض مباشرة، وrevision يمنع استجابة قديمة من إعادة المستخدم. Demo repository يقدم نفس العقد لأحداث الخروج وإعادة تعيين كلمة المرور.

بعد الدخول، `accountDestination(user)` يختار:

1. `/onboarding/profile` عند غياب الموبايل.
2. `/onboarding/address` عند غياب العنوان الافتراضي.
3. `/account` عند اكتمال البيانات.

حماية المسارات في المتصفح تنظّم تجربة الاستخدام فقط؛ صلاحيات البيانات عند التكامل تظل مسؤولية السيرفر. تستخدم النسخة الحالية `HashRouter` لتعمل الملفات الثابتة من دون اشتراط إعداد rewrite على الخادم.

## معايير الإضافة والتعديل

عند إضافة عملية جديدة:

1. حدّد النموذج وعقد المستودع داخل `domain` عند الحاجة.
2. أنشئ مجلد العملية تحت `application`، واجعل له `dto.ts` و`use-case.ts`.
3. نفّذ السلوك في adapter البيانات، مع إعادة نماذج النطاق وأخطاء التطبيق.
4. أنشئ صفحة أو مكوّنًا صغيرًا داخل `presentation` واستدعِ use case من حدث المستخدم.
5. أضف المسار إلى Router وحدّث توثيق الرحلة والعقود.

لا تنقل مكوّنًا إلى `shared` لمجرد احتمال إعادة استخدامه. انقله عندما يكون عامًا فعلًا، وتجنب ربطه ببيانات مستخدم أو adapter محدد. لا تضف توابع جانبية للشبكة إلى validation أو مكونات الحقول.

## إعدادات البيئات والجودة

`development` و`test` و`production` مراحل تشغيل وبناء منفصلة باستخدام Vite modes. كل build يقرأ من FastAPI؛ إعداد Vite يرفض `VITE_DATA_SOURCE` غير `api`. ملفات `.env.*.example` أمثلة لقيم عامة؛ قيم `VITE_*` مرئية في المتصفح.

تُستخدم TypeScript لفحص العقود وبناء Vite لإنتاج ملفات `dist/`. أوامر `build:test` و`dev:test` تختار بيئة test؛ لا تشغل اختبارات. لم تتم إضافة أو تشغيل unit/e2e tests بطلب المشروع، ويتولى فريق الاختبارات ذلك لاحقًا.
