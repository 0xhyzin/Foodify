# مراجعة Foodify Frontend

راجعت كود الواجهة وعقود FastAPI، وأصلحت المشاكل التالية. التفاصيل هنا تصف تحليل الكود والإصلاحات، وليست نتيجة اختبارات unit/e2e أو رحلة دخول فعلية عند مزود خارجي.

## النتائج وما تم إصلاحه

| الأولوية | المشكلة قبل التعديل | الإصلاح | مكان التنفيذ |
| --- | --- | --- | --- |
| عالية | الواجهة تستخدم 127.0.0.1 بينما API الافتراضي يستخدم localhost؛ هذا يضع refresh cookie بنوع SameSite=Lax في طلبات بين موقعين مختلفين | توحيد عنوان API الافتراضي وأمثلة development/test على 127.0.0.1 | [config](../src/app/config.ts)، [Vite](../vite.config.ts) |
| عالية | مسح جلسة HTTP لا يمسح المستخدم المعروض في React | إضافة onSessionInvalidated إلى عقد المصادقة والاشتراك به من SessionProvider، مع تنفيذ نفس العقد في demo | [SessionProvider](../src/app/providers/session-provider.tsx)، [AuthRepository](../src/features/auth/domain/auth-repository.ts) |
| عالية | رد refresh أو قراءة ملف قديمة يمكنها الكتابة فوق تسجيل دخول أو ملف أحدث | أرقام revision تمنع قبول الرد المتأخر بعد تغيير الحالة | [مدير الجلسة](../src/infrastructure/http/browser-session.ts)، SessionProvider |
| عالية | logout يتداخل مع refresh جارٍ، ورفض الطلب بعد التجديد لا ينهي الجلسة | انتظار refresh قبل إبطال cookie، ومسح الجلسة عند رفض المحاولة الثانية بـ401 | مدير الجلسة، [HTTP client](../src/infrastructure/http/fetch-client.ts) |
| عالية | إعادة طلب سابق قد تستخدم جلسة حساب مختلف بعد تغير المستخدم | عدم إعادة الطلب إذا تغير user id، وعدم مسح جلسة أحدث بسبب رفض توكن سابق | HTTP client |
| عالية | إضافة عنوان تنجح ثم يفشل تحديث الملف؛ يظهر ذلك كفشل حفظ وقد يؤدي لإرسال POST جديد | اعتبار الكتابة ناجحة وتحديث الافتراضي من النتيجة، مع إشعار منفصل عند فشل القراءة التالية | [AddressForm](../src/features/account/presentation/components/address-form.tsx) |
| متوسطة | تنظيف token/ticket يستخدم history خارج Router بعد تشغيل React | hook يحفظ القيمة في الذاكرة ويزيلها عبر setSearchParams مع replace | [useSensitiveSearchParam](../src/shared/hooks/use-sensitive-search-param.ts) |
| متوسطة | فشل OAuth أو مغادرة شاشة البداية قد يترك verifier أو يكمل تحويلًا لم يعد مطلوبًا | cancel وrevision للمحاولة، وتنظيف التخزين عند الفشل أو عودة خطأ أو إلغاء البداية | [OAuth flow](../src/features/auth/infrastructure/oauth-flow.ts)، [SocialSignInPage](../src/features/auth/presentation/pages/social-sign-in-page.tsx) |
| متوسطة | authorization_url لا يقيد الوجهة، وحالة تعطيل التخزين غير موضحة | السماح بـ HTTPS على مسارات Google/Facebook المتوقعة فقط، ورسائل واضحة لفشل sessionStorage | OAuth flow |
| متوسطة | OAuth callback يعرض خطأ عامًا إذا احتاج Facebook لتأكيد البريد | تعليمات تأكيد البريد وإعادة الدخول بنفس المزود بدل رسالة غير مفهومة | [OAuthCallbackPage](../src/features/auth/presentation/pages/oauth-callback-page.tsx) |
| متوسطة | استجابة الجلسة تُقبل دون تحقق فعلي من token/type/expiry/user | parseBrowserSession يرفض DTO غير المكتملة قبل اعتماد الجلسة | [session-dto](../src/infrastructure/http/session-dto.ts) |
| متوسطة | حقول أخطاء API مثل phone وdelivery_notes لا تطابق أسماء النموذج | تحويل أسماء الحقول، ورسائل عربية آمنة للأكواد المعروفة، وحفظ requestId وRetry-After | [api-error](../src/infrastructure/http/api-error.ts)، [AppError](../src/shared/domain/app-error.ts) |
| متوسطة | عملية متأخرة تبدأ callback نجاح أو تغير state بعد غلق المكون | useAction يتحقق من بقاء المكون قبل تحديثه أو بدء onSuccess | [useAction](../src/shared/hooks/use-action.ts) |
| متوسطة | عنوان الحساب يظل في وضع تحميل بعد فشل الطلب، وخطأ القراءة يتداخل مع حوار الخروج | زر إعادة تحميل وفصل حالة تحميل العنوان عن حالة logout | [ProfilePage](../src/features/account/presentation/profile/profile-page.tsx) |
| متوسطة | «مكان تاني» لا يفتح اسمًا مخصصًا، وتعديل العنوان يفرض countryCode=EG | حقل اسم مخصص والاحتفاظ بدولة العنوان المقروءة | AddressForm |
| منخفضة | عداد إعادة التأكيد يتجاهل Retry-After، والنصوص في API تصف الوضع التجريبي | الالتزام بمدة 429، ونصوص مناسبة لـ API/demo، وتوحيد minLength للاسم مع domain | [useResendVerification](../src/features/auth/presentation/hooks/use-resend-verification.ts)، المساعدة والتسجيل |

## الحفاظ على المعمارية

الصفحات ما زالت تستدعي الخدمات عبر ServicesProvider. إبطال الجلسة يمر من AuthRepository دون استيراد مدير HTTP داخل React provider. معالجة الشبكة وDTOs داخل infrastructure، وhook تنظيف الروابط داخل shared/hooks. لم تُضف مكتبة خارجية أو يُغيّر مخطط قاعدة البيانات أو API.

الشرح العام وفهرس الدوال ودليل التكامل حُدّثوا ليصفوا التنفيذ بعد الإصلاح.

## إعداد التشغيل المحلي

~~~dotenv
VITE_DATA_SOURCE=api
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
~~~

استخدم http://127.0.0.1:5173/#/login، وأعد تشغيل Vite بعد تغيير ملف البيئة.

FRONTEND_URL في الباك إند يجب أن يطابق أصل الواجهة. توحيد عنوان API في المتصفح لا يغيّر Google/Facebook redirect URI المسجلة عند المزود؛ هذه ما زالت من إعدادات الباك إند. إذا كنت تستخدم .env محليًا بقيمة localhost القديمة، حدث VITE_API_BASE_URL كما في المثال.

## التحقق وحدوده

أوامر التحقق:

~~~bash
npm run typecheck
npm run build
VITE_DATA_SOURCE=api VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run build -- --outDir /tmp/foodify-frontend-api-review
~~~

فحص الأنواع والبناء لا يشغلان tests. بناء API يُكتب في مجلد مؤقت مستقل، بينما البناء الافتراضي في dist.

لم أضف أو أشغّل اختبارات، ولم أنفذ دخولًا حقيقيًا بحساب Google/Facebook أو إرسال بريد. تفعيل المزودين، ومطابقة redirect URIs، وتشغيل email-worker بالإعداد الحالي، وCORS وخصائص cookie في النشر، وإعداد fallback لمسارات البريد تبقى متطلبات تشغيل مستقلة موضحة في [README](../README.md) و[دليل التكامل](INTEGRATION.md).
