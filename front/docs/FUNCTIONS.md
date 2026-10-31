# فهرس دوال ومكونات Foodify Frontend

هذا الفهرس يكمل [README الرئيسي](../README.md). يوضح مسؤولية الدوال والمكونات، مدخلاتها ونتائجها، والطبقة التي تستدعيها. الأسماء هنا مأخوذة من التنفيذ الحالي؛ بعض callbacks الصغيرة مكتوبة inline داخل JSX ولا تحمل اسمًا مستقلًا.

## 1. تشغيل التطبيق وتركيب الاعتمادات

| الملف | الدالة أو التعريف | المسؤولية ومسار التنفيذ |
| --- | --- | --- |
| [main.tsx](../src/main.tsx) | bootstrap على مستوى الملف | تحميل الخط وCSS، ثم `normalizeExternalLinks`، ثم `createRoot(...).render` تحت `StrictMode` |
| [app.tsx](../src/app/app.tsx) | `App()` | تركيب ErrorBoundary وServicesProvider وToastProvider وAppRouter؛ SessionProvider داخل فرع الحساب في router |
| [services.ts](../src/app/services.ts) | `createAppServices(): AppServices` | تركيب use cases فوق مستودعات HTTP؛ لا يوجد اختيار لمصدر Demo |
| نفس الملف | `createApiServices()` | إنشاء مدير الجلسة وHTTP client وOAuth flow ومستودعات HTTP، ثم إرجاع الخدمات |
| نفس الملف | `AppServices` | عقد الخدمة: `auth` و`account` و`demo`؛ ليس API response |
| نفس الملف | `DemoControls` | واجهة توافق قديمة؛ التنفيذ الحالي لا يعرض بيانات محاكاة ولا يغيّر مصدر البيانات |
| [config.ts](../src/app/config.ts) | `appConfig` | كائن ثابت يحدد البيئة وأصل API، ويرفض أي مصدر بيانات غير `api` |
| [external-links.ts](../src/app/bootstrap/external-links.ts) | `normalizeExternalLinks(): void` | تحويل روابط البريد وOAuth ذات المسار الفعلي والـ fragment إلى مسار HashRouter قبل بدء React |
| [vite.config.ts](../vite.config.ts) | callback الخاص بـ `defineConfig` | قراءة mode والبيئة وضبط React plugin وalias والمنفذ والبناء |
| نفس الملف | `transformIndexHtml()` | إضافة CSP إلى HTML أثناء build وفق مصدر البيانات وأصل API |

## 2. Providers والحالة العامة

| الملف | الدالة أو المكون | المدخلات والنتيجة |
| --- | --- | --- |
| [services-provider.tsx](../src/app/providers/services-provider.tsx) | `ServicesProvider({ services, children })` | توزيع AppServices عبر React Context |
| نفس الملف | `useServices()` | استرجاع الخدمات أو رمي خطأ إذا غاب provider |
| [session-provider.tsx](../src/app/providers/session-provider.tsx) | `SessionProvider({ children })` | تحميل المستخدم عند فتح صفحات التسجيل أو الحساب وإدارة `user/loading`؛ غير مستخدم لتصفح المطاعم |
| نفس الملف | `refresh()` | قراءة المستخدم وتحديثه إذا لم تتغير revision؛ خطأ الشبكة ينتقل للمستدعي مع الاحتفاظ بالملف |
| نفس الملف | `setUser(user)` | setter من React لتحديث المستخدم المعروض بعد نجاح عملية |
| نفس الملف | `useSession()` | إرجاع `user/loading/refresh/setUser`، مع التحقق من وجود provider |
| [toast-provider.tsx](../src/app/providers/toast-provider.tsx) | `ToastProvider({ children })` | عرض منطقة إعلان وإشعار واحد قابل للإغلاق |
| نفس الملف | `showToast(message)` | استبدال الإشعار السابق، وإعادة مؤقت الإغلاق لمدة 4500 ms |
| نفس الملف | `useToast()` | استرجاع `showToast` من context |
| [error-boundary.tsx](../src/app/error-boundary.tsx) | `ErrorBoundary.getDerivedStateFromError()` | تحويل الحالة إلى شاشة فشل عرض |
| نفس الملف | `ErrorBoundary.componentDidCatch(...)` | موضع مخصص مستقبلًا لتقرير خطأ؛ لا يوجد إرسال خارجي حاليًا |
| نفس الملف | `ErrorBoundary.render()` | عرض children أو واجهة استعادة بزر تحديث الصفحة |

## 3. المسارات والتخطيط

| الملف | الدالة أو المكون | المسؤولية |
| --- | --- | --- |
| [app-router.tsx](../src/app/router/app-router.tsx) | `AppRouter()` | تعريف HashRouter وفرع الكتالوج العام وفرع الحساب المحاط بـ SessionProvider |
| [route-guards.tsx](../src/app/router/route-guards.tsx) | `RequireSession()` | انتظار الجلسة ثم Outlet أو تحويل إلى login |
| نفس الملف | `GuestOnly()` | عرض صفحات الزائر فقط لغير المسجل؛ تحويل المسجل إلى الوجهة المناسبة |
| نفس الملف | `RequirePhone()` | منع الانتقال لخطوة عنوان onboarding دون موبايل |
| نفس الملف | `RequireCompleteProfile()` | التحقق من `profileComplete` قبل شاشة الجاهزية |
| [paths.ts](../src/app/router/paths.ts) | `accountDestination(user)` | اختيار profile onboarding، أو address onboarding، أو account |
| [route-effects.tsx](../src/app/router/route-effects.tsx) | `RouteEffects()` | تحديث عنوان document، التمرير للأعلى، وتركيز h1 بعد التنقل |
| [not-found-page.tsx](../src/app/router/not-found-page.tsx) | `NotFoundPage()` | شاشة لمسار غير معروف، مع العودة للحساب أو login حسب الجلسة |
| [account-layout.tsx](../src/app/layouts/account-layout.tsx) | `AccountLayout()` | header/footer وOutlet والهوية والمساعدة وأدوات demo المشروطة |
| نفس الملف | callback إعادة التجربة | `services.demo.reset` ثم مسح user والعودة إلى login وإظهار toast |
| [brand-panel.tsx](../src/app/layouts/brand-panel.tsx) | `BrandPanel()` | نص الهوية الأحمر ورسم CSS وأيقونات الأكل والبقالة |

## 4. Use cases الخاصة بالمصادقة

كل صف يشير إلى مجلد يحتوي `dto.ts` و`use-case.ts`. الـ factory تستقبل `AuthRepository` وتعيد دالة العملية. النتائج `Promise` حتى إذا كان نوع البيانات الناتجة `void`.

| المجلد | factory ← العملية | المدخل والنتيجة | ما يحدث |
| --- | --- | --- | --- |
| [sign-in](../src/features/auth/application/sign-in/use-case.ts) | `createSignIn → signIn` | `SignInDto { email, password } → UserProfile` | تطبيع البريد وفحص كلمة مرور الدخول ثم `repository.signIn` |
| [sign-up](../src/features/auth/application/sign-up/use-case.ts) | `createSignUp → signUp` | `SignUpDto { name, email, password } → void` | تطبيع الاسم والبريد والتحقق من كلمة جديدة ثم التسجيل |
| [confirm-email](../src/features/auth/application/confirm-email/use-case.ts) | `createConfirmEmail → confirmEmail` | `ConfirmEmailDto { token } → void` | `requireToken` ثم تفويض التأكيد |
| [resend-verification](../src/features/auth/application/resend-verification/use-case.ts) | `createResendVerification → resendVerification` | `ResendVerificationDto { email } → void` | تطبيع البريد وطلب إعادة التأكيد |
| [request-password-reset](../src/features/auth/application/request-password-reset/use-case.ts) | `createRequestPasswordReset → requestPasswordReset` | `RequestPasswordResetDto { email } → void` | تطبيع البريد وطلب رابط جديد |
| [reset-password](../src/features/auth/application/reset-password/use-case.ts) | `createResetPassword → resetPassword` | `ResetPasswordDto { token, password } → void` | فحص الرمز وكلمة جديدة ثم تفويض التعيين |
| [sign-in-with-provider](../src/features/auth/application/sign-in-with-provider/use-case.ts) | `createSignInWithProvider → signInWithProvider` | `google أو facebook → UserProfile` | بدء المزود عبر repository؛ في HTTP يغادر المتصفح قبل إرجاع user |
| [sign-out](../src/features/auth/application/sign-out/use-case.ts) | `createSignOut → signOut` | `بدون مدخل → void` | إنهاء الجلسة عبر repository |
| [get-session](../src/features/auth/application/get-session/use-case.ts) | `createGetSession → getSession` | `بدون مدخل → UserProfile أو null` | قراءة/استعادة المستخدم عبر repository |

`completeProviderSignIn({ ticket })` ضمن [AuthRepository](../src/features/auth/domain/auth-repository.ts) وتوصله `services.ts` مباشرة بالمستودع. لا يوجد factory منفصل لهذه العملية.

## 5. Use cases الخاصة بالحساب

الـ factories تستقبل `AccountRepository`. يوجد `dto.ts` بجانب كل use case.

| المجلد | factory ← العملية | المدخل والنتيجة | ما يحدث |
| --- | --- | --- | --- |
| [get-profile](../src/features/account/application/get-profile/use-case.ts) | `createGetProfile → getProfile` | `بدون مدخل → UserProfile` | قراءة ملف المستخدم الحالي |
| [update-profile](../src/features/account/application/update-profile/use-case.ts) | `createUpdateProfile → updateProfile` | `{ name, phoneNumber } → UserProfile` | تطبيع الاسم والموبايل ثم حفظهما |
| [list-addresses](../src/features/account/application/list-addresses/use-case.ts) | `createListAddresses → listAddresses` | `بدون مدخل → Address[]` | قراءة قائمة المستخدم |
| [save-address](../src/features/account/application/save-address/use-case.ts) | `createSaveAddress → saveAddress` | `AddressInput, id? → Address` | تطبيع العنوان؛ وجود id يعني تعديل |
| [remove-address](../src/features/account/application/remove-address/use-case.ts) | `createRemoveAddress → removeAddress` | `id → void` | فحص وجود المعرف ثم الحذف |
| [make-address-default](../src/features/account/application/make-address-default/use-case.ts) | `createMakeAddressDefault → makeAddressDefault` | `id → void` | فحص المعرف ثم تغيير الافتراضي |

## 6. Validation والنماذج والعقود

| الملف | الدالة أو النوع | المسؤولية |
| --- | --- | --- |
| [auth validation](../src/features/auth/domain/validation.ts) | `normalizeEmail(value)` | trim وlowercase وشكل بريد صالح وحد الطول |
| نفس الملف | `normalizeName(value)` | إزالة المسافات الطرفية وتوحيدها والتحقق من طول الاسم |
| نفس الملف | `validatePassword(password, isNew)` | طول 15–128 للجديدة أو 1–128 للدخول، دون trim للقيمة المرسلة |
| نفس الملف | `requireToken(token)` | رفض الرمز الفارغ ثم إعادة قيمته بعد trim |
| [account validation](../src/features/account/domain/validation.ts) | `asciiDigits(value)` | تحويل الأرقام العربية والفارسية إلى ASCII؛ helper داخلي |
| نفس الملف | `normalizeEgyptianPhone(value, field?)` | توحيد رقم مصري إلى +20 أو AppError مربوط باسم الحقل |
| نفس الملف | `requiredText(value, field, label, maximum)` | helper لفحص النص الإلزامي والطول |
| نفس الملف | `optionalText(value, field, label, maximum)` | helper يعيد نصًا محدودًا أو null |
| نفس الملف | `normalizeAddress(input)` | تطبيق قواعد كل حقول العنوان وإرجاع نسخة مطبعة |
| نفس الملف | `requireAddressId(id)` | رفض معرف فارغ؛ لا يتحقق من ملكية العنوان |
| [auth models](../src/features/auth/domain/models.ts) | `SignInInput/SignUpInput/EmailInput/TokenInput/ResetPasswordInput/CompleteProviderSignInInput/OAuthProvider` | عقود مدخلات مجال المصادقة |
| [account models](../src/features/account/domain/models.ts) | `UserProfile/Address/AddressInput` | نماذج الواجهة المستقلة عن snake_case للشبكة |
| [auth contract](../src/features/auth/domain/auth-repository.ts) | `AuthRepository` | العمليات التي تحتاجها طبقة التطبيق من مصدر المصادقة |
| [account contract](../src/features/account/domain/account-repository.ts) | `AccountRepository/UpdateProfileInput` | عمليات الحساب والعناوين ومدخل تعديل الملف |
| [OAuth contract](../src/features/auth/domain/oauth-flow.ts) | `OAuthFlowPort` | `start(provider)` و`complete(ticket)` كحد مستقل عن React |

## 7. HTTP والجلسة

### FetchHttpClient

الملف: [fetch-client.ts](../src/infrastructure/http/fetch-client.ts).

| الدالة | المسؤولية |
| --- | --- |
| `constructor(baseUrl, session)` | حقن أصل API ومدير الجلسة خلف interface |
| `request<T>(path, options?)` | إرسال طلب؛ عند 401 لطلب محمي يجرب refresh مرة ثم إعادة الطلب؛ يعيد JSON أو يرمي AppError |
| `send(path, options, accessToken?)` | إضافة headers وcredentials وbody وsignal؛ يحول فشل fetch إلى network_error |

### BrowserSessionManager

الملف: [browser-session.ts](../src/infrastructure/http/browser-session.ts).

| الدالة | المسؤولية |
| --- | --- |
| `constructor(baseUrl)` | حفظ عنوان API مع حالة جلسة وrefresh promise فارغتين |
| `accept(session)` | حفظ الجلسة في الذاكرة وإبلاغ المستمعين |
| `restore(force = false)` | استخدام الجلسة الحالية أو refresh واحد مشترك؛ force يتجاوز النسخة الموجودة |
| `current()` | إرجاع نسخة الجلسة المخزنة أو null |
| `clear()` | مسح الجلسة وإبلاغ المستمعين إذا كانت موجودة |
| `signOut()` | جمع طلبات الخروج المتزامنة ثم تفويضها إلى logoutFromCookie |
| `subscribe(listener)` | تسجيل مستمع؛ HTTP auth يمرر بطلان الجلسة إلى SessionProvider |
| `requestSession(path)` | نقل refresh/logout مباشرة مع توحيد خطأ الشبكة |
| `logoutFromCookie()` | منع refresh جديد وانتظار الجاري ثم حذف cookie؛ فشل الخروج يتيح المحاولة مجددًا |
| `refreshFromCookie(startedAt)` | طلب refresh وفحص DTO وrevision؛ تجاهل الرد القديم وإبطال الجلسة عند 401 |
| `notify()` | استدعاء listeners المسجلين |

### عقود وأخطاء الشبكة

| الملف | التعريف | المسؤولية |
| --- | --- | --- |
| [contracts.ts](../src/infrastructure/http/contracts.ts) | `HttpClient/RequestOptions` | عقد إرسال الطلب: method/body/authenticated/signal |
| نفس الملف | `BrowserSessionPort` | عقد مدير الجلسة الذي تحقن dependents من خلاله |
| نفس الملف | `BackendUserDto/BrowserSessionDto` | شكل المستخدم والجلسة في HTTP |
| [api-error.ts](../src/infrastructure/http/api-error.ts) | `fieldName(value)` | حذف بادئة body/query/path من اسم الحقل |
| نفس الملف | `fieldsFromDetails(details)` | تحويل مصفوفة تفاصيل الخطأ إلى خريطة رسائل |
| نفس الملف | `readApiError(response)` | قراءة error envelope أو رسالة احتياطية؛ يرجع AppError يحمل status |
| نفس الملف | `readJson<T>(response)` | قراءة JSON أو undefined لحالة 204، ورمي invalid_response عند فشل التحليل |
| نفس الملف | `retryAfterSeconds(value)` | قراءة مدة Retry-After كعدد ثوانٍ أو تاريخ |
| [session-dto.ts](../src/infrastructure/http/session-dto.ts) | `parseBrowserSession(value)` | التحقق من بيانات token/type/expiry/user قبل قبول الجلسة |
| [app-error.ts](../src/shared/domain/app-error.ts) | `ApplicationError` | عقد الخطأ: code/message/fields/status |
| نفس الملف | `AppError` و`ErrorMetadata` | خطأ موحد مع status وrequestId وretryAfterSeconds |
| نفس الملف | `getErrorMessage(error)` | رسالة AppError أو رسالة عربية عامة |

## 8. Repositories الحقيقية وmappers

### HttpAuthRepository

الملف: [http-auth-repository.ts](../src/features/auth/infrastructure/http-auth-repository.ts).

| الدالة | المسار أو الإجراء | النتيجة |
| --- | --- | --- |
| `signIn(input)` | `POST /auth/browser/login` ثم mapper وsession.accept | UserProfile |
| `signUp(input)` | `POST /auth/register` | void |
| `confirmEmail(input)` | `POST /auth/verify-email` | void |
| `resendVerification(input)` | `POST /auth/resend-verification` | void |
| `requestPasswordReset(input)` | `POST /auth/forgot-password` | void |
| `resetPassword(input)` | `POST /auth/reset-password` ثم مسح session | void |
| `signInWithProvider(provider)` | `oauth.start` | تحويل المتصفح؛ في API لا يرجع user من نفس الصفحة |
| `completeProviderSignIn({ ticket })` | `oauth.complete` | UserProfile |
| `signOut()` | `session.signOut` | void |
| `cancelProviderSignIn()` | `oauth.cancel` | تنظيف محاولة المزود |
| `onSessionInvalidated(listener)` | `session.subscribe` عند مسح الجلسة | دالة إلغاء الاشتراك |
| `getSession()` | current أو restore، ثم `GET /users/me` | UserProfile أو null |

طلب البيانات وقراءة JSON مسؤولية client؛ repository يحدد HTTP DTO ويحوله إلى domain. [auth-dto.ts](../src/features/auth/infrastructure/dto/auth-dto.ts) يفصل أنواع sign-in/sign-up/email/token/reset/message.

### HttpAccountRepository

الملف: [http-account-repository.ts](../src/features/account/infrastructure/http-account-repository.ts).

| الدالة | المسؤولية |
| --- | --- |
| `getProfile()` | GET /users/me ثم toUserProfile |
| `updateProfile(input)` | PATCH يرسل name وphone ثم تحويل الملف |
| `listAddresses()` | GET القائمة والتحقق أنها مصفوفة وتحويل عناصرها وتحديث cache الإحداثيات |
| `saveAddress(input, id?)` | POST للجديد أو PUT للتعديل؛ يسترجع الإحداثيات القديمة إذا لم تكن معروفة |
| `removeAddress(id)` | DELETE ثم حذف cache الخاص بالمعرف |
| `makeAddressDefault(id)` | PUT لمسار default-address؛ يترك إعادة تحميل الملف للعرض |
| `rememberCoordinates(dto)` | حفظ latitude/longitude في Map داخل adapter |

### Mappers

| الملف | الدالة | المدخل والنتيجة |
| --- | --- | --- |
| [user-profile-mapper.ts](../src/features/account/infrastructure/mappers/user-profile-mapper.ts) | `toUserProfile(dto)` | فحص BackendUserDto ثم UserProfile؛ تجاهل حقول العرض غير المطلوبة |
| [address-mapper.ts](../src/features/account/infrastructure/mappers/address-mapper.ts) | `isNullableText(value)` | helper لقبول نص أو null |
| نفس الملف | `isCoordinate(value)` | helper لقبول null أو رقم محدود أو نص رقمي محدود |
| نفس الملف | `toAddress(dto)` | فحص response ثم تحويل حقول العنوان إلى camelCase |
| نفس الملف | `nullableText(value)` | helper يحول النص الاختياري الفارغ إلى null |
| نفس الملف | `toAddressWriteDto(input, coordinates?)` | بناء body صريح للكتابة مع الاحتفاظ بالإحداثيات |
| [account-dto.ts](../src/features/account/infrastructure/dto/account-dto.ts) | `CoordinateDto/AddressCoordinatesDto/AddressWriteDto/AddressResponseDto/UpdateProfileDto` | عقود الشبكة للحساب؛ الإحداثيات قد تكون number أو string أو null |

## 9. BrowserOAuthFlow

الملف: [oauth-flow.ts](../src/features/auth/infrastructure/oauth-flow.ts).

| الدالة | المسؤولية |
| --- | --- |
| `verifierKey(provider)` | تكوين مفتاح sessionStorage لكل مزود |
| `randomVerifier()` | إنشاء 32 bytes عشوائية وتحويلها إلى Base64 URL-safe |
| `toBase64Url(bytes)` | حذف padding واستبدال الرموز غير المناسبة للـ URL |
| `challengeFor(verifier)` | SHA-256 بصيغة 64 حرف hex لربط المتصفح |
| `constructor(client, acceptSession)` | حقن client ودالة قبول جلسة الشبكة |
| `start(provider)` | حفظ verifier ومسح verifier المزود الآخر؛ POST البداية ثم window.location.assign |
| `complete(ticket)` | قراءة verifier، وPOST complete، ومسحه في finally، وقبول session وإرجاع UserProfile |
| `providerForTicket()` | اختيار المزود بناءً على وجود مفتاح معروف في sessionStorage؛ لا يفك ticket |
| `cancel()` | إلغاء المحاولة وزيادة revision ومسح verifier للمزودين |
| `readVerifier(provider)` | قراءة التخزين أو خطأ مفهوم عند منع sessionStorage |

`CompleteProviderSignIn` في نهاية الملف type alias لدالة، وليس use case factory مستقلًا. verifier هذا مختلف عن Google PKCE verifier الذي يولده الباك إند.

## 10. صفحات ومكونات المصادقة

الملفات داخل [auth/presentation](../src/features/auth/presentation).

| الملف | المكون والدوال المحلية | المسؤولية |
| --- | --- | --- |
| `pages/login-page.tsx` | `LoginPage/handleSubmit/fillDemoAccount` | الدخول، التعامل مع البريد غير المؤكد، تحديث user والتنقل، وملء حساب العرض عند demo |
| `pages/register-page.tsx` | `RegisterPage/handleSubmit` | التسجيل ثم مراجعة البريد |
| `pages/verify-email-page.tsx` | `VerifyEmailPage` | عرض البريد وإعادة الإرسال، وإتاحة EmailPreview فقط في demo |
| `pages/confirm-email-page.tsx` | `ConfirmEmailPage` | استخراج token وتمريره لمكون keyed بحسب الرمز |
| نفس الملف | `ConfirmEmailContent` | عرض زر التأكيد ونجاح العملية؛ hook الصفحة الأم يحفظ الرمز وينظف URL |
| `pages/forgot-password-page.tsx` | `ForgotPasswordPage/handleSubmit` | طلب reset ثم الانتقال إلى شاشة الرسالة العامة |
| `pages/reset-password-sent-page.tsx` | `ResetPasswordSentPage` | عرض نتيجة عامة ورابط طلب جديد، مع البريد التجريبي عند demo |
| `pages/reset-password-page.tsx` | `ResetPasswordPage` | استخراج token وتمريره للنموذج |
| نفس الملف | `ResetPasswordForm/handleSubmit` | مطابقة التأكيد، طلب reset، ومسح user ثم شاشة النجاح؛ hook الصفحة الأم ينظف URL |
| `pages/reset-password-success-page.tsx` | `ResetPasswordSuccessPage` | نجاح تغيير كلمة المرور ورابط الدخول |
| `pages/social-sign-in-page.tsx` | `SocialSignInPage/continueWithProvider` | التحقق من المزود، شرح العملية وبدؤها؛ في demo يكمل مباشرة |
| `pages/oauth-callback-page.tsx` | `OAuthCallbackPage` | قراءة ticket/error، ومنع تكرار الإكمال بـ ref، وتنظيف URL وتحديث الجلسة |
| نفس الملف | `oauthErrorMessage(code)` | رسائل مخصصة لبعض أخطاء OAuth ورسالة عامة للباقي |
| `components/social-buttons.tsx` | `SocialButtons/GoogleMark/FacebookMark` | روابط المزودين وشعارات SVG محلية |
| `components/email-preview.tsx` | `EmailPreview` | حوار معاينة رسالة من token تجريبي مع رابط التأكيد أو reset |
| `hooks/use-resend-verification.ts` | `useResendVerification/resend` | إرسال وعد محلي 60 ثانية بعد النجاح، أو مدة Retry-After بعد 429، مع نص مناسب لمصدر البيانات |
| `index.ts` | exports | تسهيل استيراد صفحات auth؛ لا يحتوي سلوكًا تنفيذيًا إضافيًا |

## 11. صفحات ومكونات الحساب

الملفات داخل [account/presentation](../src/features/account/presentation).

| الملف | المكون والدوال المحلية | المسؤولية |
| --- | --- | --- |
| `onboarding/complete-profile-page.tsx` | `CompleteProfilePage` | عرض الخطوة الأولى وProfileForm ثم توجيه المستخدم للعنوان |
| `onboarding/complete-address-page.tsx` | `CompleteAddressPage` | الخطوة الثانية وAddressForm مع إمكانية تأجيل العنوان |
| `onboarding/account-ready-page.tsx` | `AccountReadyPage` | شاشة جاهزية ورابط الحساب |
| `profile/profile-page.tsx` | `ProfilePage` | بيانات المستخدم وقراءة العناوين وإظهار الافتراضي وتنبيه الاستكمال وحوار الخروج |
| `profile/edit-profile-page.tsx` | `EditProfilePage` | إعادة استخدام ProfileForm ثم إشعار والعودة للحساب |
| `addresses/addresses-page.tsx` | `AddressesPage/reload` | القائمة والحذف والافتراضي؛ reload يجدد القائمة ثم ملف الجلسة |
| `addresses/address-editor-page.tsx` | `AddressEditorPage` | قراءة id واختيار مفتاح مكون يفرق بين الجديد والتعديل |
| نفس الملف | `AddressEditor` | قراءة العنوان من القائمة وحالات التحميل والخطأ وعدم وجوده، ثم AddressForm |
| `components/profile-form.tsx` | `ProfileForm/submit` | قيم الاسم والرقم؛ حفظ عبر use case ثم setUser وonSaved |
| `components/address-form.tsx` | `AddressForm` | حالة العنوان والمستلم واسم مكان مخصص مع الحفاظ على countryCode |
| نفس الملف | `update(key, value)` | تغيير حقل واحد في حالة النموذج |
| نفس الملف | `field(...)` | helper لإنشاء Field متكرر بالقيمة والخطأ المناسبين |
| نفس الملف | `submit(event)` | حفظ العنوان وتحديث الافتراضي من النتيجة ثم refresh؛ فشل القراءة لا يحول الحفظ الناجح إلى POST مكرر |
| `components/address-card.tsx` | `AddressCard` | عرض عنوان عادي أو compact، مع callbacks للحذف والافتراضي ورابط التعديل |
| `components/onboarding-steps.tsx` | `OnboardingSteps({ step })` | مؤشر بصري ودلالي للخطوة الحالية من خطوتين |

الحذف والافتراضي لا يتمان داخل AddressCard؛ الكارت يرسل الحدث للصفحة. ذلك يبقي عرض الكارت مستقلاً عن طريقة حفظ البيانات.

## 12. المكونات والـ hooks العامة

| الملف داخل src/shared | التعريف | المسؤولية |
| --- | --- | --- |
| [hooks/use-action.ts](../src/shared/hooks/use-action.ts) | `useAction()` | حالة pending/error/fieldErrors مع قفل يمنع الإرسال المكرر |
| نفس الملف | `run(action, onSuccess?)` | انتظار العملية وcallback النجاح، والتقاط الخطأ وتركيز أول حقل غير صالح |
| نفس الملف | `clearError()` | مسح خطأ العملية وأخطاء الحقول |
| [hooks/use-sensitive-search-param.ts](../src/shared/hooks/use-sensitive-search-param.ts) | `useSensitiveSearchParam(name)` | حفظ رمز الرابط في الذاكرة وتنظيف عنوانه باستخدام Router |
| [ui/button.tsx](../src/shared/ui/button.tsx) | `Button` | props زر HTML مع variant/loading/icon؛ التعطيل أثناء loading |
| [ui/field.tsx](../src/shared/ui/field.tsx) | `Field` | label/input/hint/error مع id وعلاقات aria |
| نفس الملف | `PasswordField` | حقل بمفتاح إظهار وإخفاء كلمة المرور |
| [ui/dialog.tsx](../src/shared/ui/dialog.tsx) | `Dialog` | إدارة showModal/close والإغلاق عبر Escape والخلفية والزر |
| [ui/page-heading.tsx](../src/shared/ui/page-heading.tsx) | `PageHeading` | h1 قابل للتركيز ووصف |
| [ui/status-view.tsx](../src/shared/ui/status-view.tsx) | `StatusView` | تكوين أيقونة وعنوان ووصف وchildren |
| [ui/back-link.tsx](../src/shared/ui/back-link.tsx) | `BackLink` | Link للرجوع داخل التطبيق |
| [ui/form-error.tsx](../src/shared/ui/form-error.tsx) | `FormError` | alert عند وجود رسالة، وإلا null |
| [ui/loading-state.tsx](../src/shared/ui/loading-state.tsx) | `LoadingState` | مؤشر تحميل ونص انتظار |

## 13. التنفيذ التجريبي

### DemoStore

الملف: [demo-store.ts](../src/infrastructure/demo/demo-store.ts).

| الدالة | المسؤولية |
| --- | --- |
| `constructor/reset` | تهيئة الحساب الافتراضي وعنوانه ومسح الحسابات والرموز والجلسة السابقة |
| `findByEmail(email)` | البحث عن الحساب ببريد مطبع |
| `currentAccount()` | الحساب النشط أو authentication_required |
| `toProfile(account)` | نسخة UserProfile مع حساب اكتمال الملف من الرقم والافتراضي |
| `issueToken(email, purpose)` | إصدار رمز معاينة 15 دقيقة لحساب معروف |
| `previewToken(email, purpose)` | إرجاع الرمز الساري للعرض أو null |
| `consumeToken(token, purpose)` | استهلاك الرمز مرة واحدة ورفض المنتهي أو المجهول |
| `simulateLatency(milliseconds = 320)` | Promise بتأخير لعرض حالة الانتظار |

`DemoAuthRepository` ينفذ جميع طرق `AuthRepository` داخل الذاكرة: التسجيل وتأكيد البريد وإعادة الرسالة وreset وsign-in/sign-out/get-session. `signInWithProvider` ينشئ حساب مزود وهميًا، و`completeProviderSignIn` يفوض إلى مزود Google التجريبي. لا يُرسل بريد ولا يفحص كلمة مرور حقيقية.

الملف: [demo-auth-repository.ts](../src/features/auth/infrastructure/demo-auth-repository.ts).

`DemoAccountRepository` ينفذ `getProfile/updateProfile/listAddresses/saveAddress/removeAddress/makeAddressDefault` فوق الحساب النشط في DemoStore. يحاكي حد 20 عنوانًا، والافتراضي الأول، وتغيير الافتراضي بعد الحذف، ويعيد نسخًا للعرض.

الملف: [demo-account-repository.ts](../src/features/account/infrastructure/demo-account-repository.ts).

## 14. مثال تتبع كامل

تعديل عنوان موجود:

~~~text
AddressEditorPage
  → AddressEditor يقرأ القائمة ويختار id
  → AddressForm.submit
  → useAction.run
  → services.account.saveAddress
  → createSaveAddress(...): normalizeAddress + requireAddressId
  → HttpAccountRepository.saveAddress
  → toAddressWriteDto مع الإحداثيات المحفوظة
  → FetchHttpClient.request
  → PUT /api/v1/users/me/addresses/{id}
  → readJson + toAddress
  → AddressForm ينتظر session.refresh
  → onSaved: toast ثم العودة لقائمة العناوين
~~~

الـ input يعبر حدودًا واضحة. الـ page لا تبني URL الخاص بـ API، والـ use case لا يعرف fetch، وmapper لا ينفذ التنقل.

## Marketplace والكتالوج

كتالوج المطاعم والمنتجات يُقرأ من FastAPI/MySQL عبر `HttpCatalogRepository`.
راجع [شرح تدفق الكتالوج](CATALOG.md) و[شرح Sprint 2](../README_SPRINT_2.md) لمسارات
الصفحات والسلة والطلبات والدفع. مكونات الواجهة لا تستورد ملف seed ولا تنشئ
قائمة متاجر محلية.
