# دليل ربط Foodify بالباك إند

هذا المستند يشرح الربط المنفّذ بين واجهة React وباك إند FastAPI. المحاكاة ما زالت متاحة للتصميم عبر `VITE_DATA_SOURCE=demo`، بينما `api` هو مصدر التطوير الافتراضي.

ابدأ بـ [شرح الواجهة الكامل](../README.md)، ثم [فهرس الدوال والمكونات](FUNCTIONS.md) للوصول إلى التنفيذ. الجداول هنا توثق عقود API؛ بعض قدرات السيرفر، مثل logout-all أو كتابة الإحداثيات مباشرة، لا تملك إجراءً ظاهرًا في الواجهة الحالية.

## نطاق الربط

الواجهة تخص حساب العميل: التسجيل، الدخول، تأكيد البريد، استرجاع كلمة المرور، استكمال البيانات، وإدارة عناوين التوصيل. الكتالوج والطلبات والسلة ولوحات الموظفين خارج هذه المرحلة.

الباك إند الحالي موجود في المجلد الشقيق `../../back`، والمساران الأساسيان هما:

```text
/api/v1/auth
/api/v1/users
```

عقود الباك إند موثقة في `app/users/**/dto.py` والقيود المشتركة في `app/users/shared/dto/`. عند تغيير العقود لاحقًا تكون هذه الملفات وOpenAPI المولّد من السيرفر مرجع الربط.

## طريقة الربط المنفذة

1. تنفذ مستودعات HTTP واجهة الـ repository لكل feature داخل `infrastructure` باستخدام HTTP client مستقل.
2. DTOs الشبكة والـ mappers داخل adapter الربط؛ نماذج التطبيق تستخدم `camelCase`، والباك إند يستخدم `snake_case`.
3. أخطاء السيرفر تتحول إلى `AppError` قبل العودة للعرض.
4. تُحقن الـ adapters من نقطة تركيب الاعتمادات، والصفحات لا تحتوي `fetch`.
5. وضع API يستهلك روابط التأكيد من السيرفر، ويخفي أدوات البريد التجريبي. لا توجد عملية تأكيد محلية داخله.
6. يختار `VITE_DATA_SOURCE=api` adapters الشبكة من `src/app/services.ts`. عنوان التطوير الافتراضي هو `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`.

لا تضع `fetch` داخل الصفحات. كل طلب يمر من `FetchHttpClient`، وكل response يتحول إلى DTO ثم إلى نموذج domain داخل repository mapper. استخدم `VITE_DATA_SOURCE=demo` فقط للمعاينة المحلية دون باك إند.

حافظ على استقلال الواجهات عن تفاصيل HTTP. إذا تطلّب الربط تعديل توقيع repository، حدّث الـ use case والـ DTO المعنيين بشكل صريح بدل تمرير `Response` أو كائن شبكة إلى واجهة React.

### تحويل الأسماء بين الطبقات

| نموذج الواجهة | DTO الباك إند |
| --- | --- |
| `UserProfile.phoneNumber` | `user.phone` |
| `UserProfile.emailVerified` | `user.email_verified` |
| `UserProfile.profileComplete` | `user.profile_complete` |
| `UserProfile.defaultAddressId` | `user.default_address_id` |
| `Address.recipientName` | `address.recipient_name` |
| `Address.phoneNumber` | `address.phone` |
| `Address.countryCode` | `address.country_code` |
| `Address.deliveryInstructions` | `address.delivery_notes` |
| `Address.isDefault` | `address.is_default` |

النماذج الحالية لا تحتاج `permissions` أو `created_at` أو الإحداثيات في العرض. لا تضف بيانات الأدوار والصلاحيات إلى طلبات الكتابة؛ احتفظ بما يلزم منها داخل adapter أو نماذج النطاق عند توسعة المنتج.

## مصفوفة عمليات الحساب

| العملية | طريقة ومسار الباك إند | جسم الطلب | النتيجة |
| --- | --- | --- | --- |
| التسجيل | `POST /api/v1/auth/register` | `name`, `email`, `password` | `202` مع `{ message }` |
| الدخول من المتصفح | `POST /api/v1/auth/browser/login` | `email`, `password` + `X-Foodify-Client: web` | access token وملف المستخدم؛ refresh cookie HttpOnly |
| إعادة رسالة التأكيد | `POST /api/v1/auth/resend-verification` | `email` | `202` مع رسالة عامة |
| تأكيد البريد | `POST /api/v1/auth/verify-email` | `token` | `{ message }` |
| طلب استرجاع كلمة المرور | `POST /api/v1/auth/forgot-password` | `email` | `202` مع رسالة عامة |
| حفظ كلمة المرور الجديدة | `POST /api/v1/auth/reset-password` | `token`, `password` | `{ message }` ثم دخول جديد |
| تجديد جلسة المتصفح | `POST /api/v1/auth/browser/refresh` | بدون body؛ cookie تلقائيًا | access token جديد وملف المستخدم |
| خروج جلسة المتصفح | `POST /api/v1/auth/browser/logout` | بدون body؛ cookie تلقائيًا | `204` |
| خروج جميع الجلسات | `POST /api/v1/auth/logout-all` | بدون body؛ Bearer access token | `204` |
| قراءة الملف | `GET /api/v1/users/me` | بدون body؛ Bearer access token | ملف المستخدم |
| تعديل الملف | `PATCH /api/v1/users/me` | `name` و/أو `phone`؛ Bearer access token | ملف المستخدم المحدث |

لا تعيد عملية التسجيل access token. لا توجد عملية لتعديل البريد أو تغيير كلمة المرور من إعدادات الحساب في العقود الحالية. استرجاع كلمة المرور هو المسار المتاح لتعيين كلمة مرور جديدة.

### قيود بيانات الحساب

- `name`: بعد حذف المسافات الطرفية، من 1 إلى 100 حرف.
- `email`: بريد صالح، بحد أقصى 254 حرفًا؛ السيرفر يطبّع حالة الأحرف.
- `password` للتسجيل والتعيين الجديد: من 15 إلى 128 حرفًا. لا تقصّ المسافات من كلمة المرور.
- كلمة مرور الدخول: من 1 إلى 128 حرفًا؛ لا تُجبر حسابًا قائمًا على شروط تعيين كلمة مرور جديدة.
- `phone`: صيغة E.164 مثل `+201012345678`. واجهة الموبايل المصرية تعرض `+20` منفصلًا؛ حوّل القيمة المحلية قبل إرسالها.
- `PATCH /me` يتطلب حقلًا واحدًا على الأقل؛ `phone: null` يمسح الرقم، بينما `name: null` غير صالح.
- رموز التأكيد والاسترجاع: من 32 إلى 512 رمزًا، بأحرف URL-safe من `A-Z a-z 0-9 _ -`.

جميع request DTOs في الباك إند ترفض الحقول الزائدة. لا ترسل `confirmPassword` أو حالات الواجهة أو بيانات الدور ضمن طلب التسجيل.

### شكل الجلسة والملف

```ts
interface BackendUserDto {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  email_verified: boolean;
  roles: string[];
  permissions: string[];
  profile_complete: boolean;
  default_address_id: string | null;
  created_at: string;
}

interface BrowserSessionDto {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: BackendUserDto;
}
```

السيرفر يعتبر الملف مكتملًا عند وجود `phone` وعنوان افتراضي. اجعل adapter يقرأ `profile_complete` و`default_address_id` من الاستجابة؛ لا تستنتج أن أول عنصر في قائمة العناوين هو العنوان الافتراضي. لا يخزن المتصفح refresh token؛ cookie المسماة `foodify_refresh` تُرسل تلقائيًا مع `credentials: include`.

## مسار تأكيد البريد واسترجاع كلمة المرور

التسجيل ← شاشة مراجعة البريد ← رابط تأكيد يحتوي على token ← تنفيذ `verify-email` ← شاشة نجاح ← دخول باستخدام الطريقة المناسبة ← استكمال بيانات التوصيل عند الحاجة.

استرجاع كلمة المرور ← رسالة عامة حتى لو البريد غير مسجل ← رابط يحتوي على token ← تعيين كلمة مرور جديدة ← شاشة نجاح ← تسجيل دخول جديد. السيرفر يلغي الجلسات السابقة عند استرجاع كلمة المرور.

لا تكشف من الرسالة ما إذا كان البريد مسجلًا. رسالة التسجيل والإعادة والاسترجاع في الباك إند عامة عمدًا. اربط روابط البريد بالمسارات المقابلة في الواجهة، ثم نظّف الرمز من عنوان الصفحة بعد استهلاكه. الروابط التجريبية الحالية للمعاينة ولا تمثّل رمزًا موثوقًا من السيرفر.

## Google وFacebook

معرّفات provider في الباك إند: `google` و`facebook`.

```text
1. إنشاء binding_verifier عشوائي في المتصفح، ثم SHA-256 له بصيغة hex.
2. POST /api/v1/auth/oauth/{provider}/start
   { binding_challenge: "<64 lowercase hex characters>" }
3. الانتقال إلى authorization_url الذي يرجعه السيرفر.
4. السيرفر يستقبل callback المزود، ثم يعيد التوجيه إلى:
   <FRONTEND_URL>/oauth/callback#ticket=<one-time-ticket>
5. POST /api/v1/auth/browser/oauth/complete
   { ticket, binding_verifier }
6. استلام الجلسة، ثم استكمال الموبايل والعنوان عند الحاجة.
```

`binding_verifier` طوله 43–128 رمزًا من الأحرف URL-safe. احفظه مؤقتًا للطلب الجاري، وامسحه بعد النجاح أو الفشل. لا تمرّره في query string.

التذكرة قصيرة العمر وتُستهلك مرة واحدة. الباك إند لا يمرر access token داخل رابط الـ callback. حالة البريد غير المؤكد قد تعيد fragment بقيمة `error=email_verification_required`. `BrowserOAuthFlow` يحفظ verifier مؤقتًا ويستهلكه مرة واحدة بعد `/browser/oauth/complete`.

الواجهة تستخدم `HashRouter`. `src/app/bootstrap/external-links.ts` يحول مسار السيرفر الفعلي `/oauth/callback#ticket=...` (وكذلك روابط البريد) إلى مسار React. صفحة callback هي التي تمسح ticket من العنوان قبل طلب الإكمال؛ صفحات البريد تمسح token عند تحميل النموذج.

الـ origin الذي يبدأ OAuth يجب أن يطابق `FRONTEND_URL` حرفيًا حتى تظل sessionStorage الخاصة بـ verifier متاحة. الإعداد المحلي الحالي للواجهة `http://127.0.0.1:5173`. روابط البريد وcallback تبدأ بمسارات فعلية؛ عند النشر يجب أن تقدم الاستضافة index.html لهذه المسارات، بالإضافة إلى دعم روابط hash الداخلية.

إذا كانت هوية المزود تطابق بريد حساب قائم لم يُربط بهذا المزود، يرجع `oauth_account_link_required`. لا تربط الحساب محليًا اعتمادًا على تشابه البريد. الواجهة التجريبية لا تتواصل مع أي مزود، وتعرض معاينة للرحلة فقط.

## العناوين

| العملية | طريقة ومسار الباك إند | الاستجابة |
| --- | --- | --- |
| عرض العناوين | `GET /api/v1/users/me/addresses` | مصفوفة عناوين |
| إضافة عنوان | `POST /api/v1/users/me/addresses` | `201` مع العنوان |
| تعديل عنوان كامل | `PUT /api/v1/users/me/addresses/{address_id}` | العنوان المحدث |
| حذف عنوان | `DELETE /api/v1/users/me/addresses/{address_id}` | `204` |
| اختيار عنوان افتراضي | `PUT /api/v1/users/me/default-address/{address_id}` | **ملف المستخدم** المحدث |

كل العمليات السابقة تتطلب Bearer access token. `address_id` معرّف UUID. لا يقبل أي طلب `user_id` من الواجهة؛ ملكية العنوان تُستمد من الجلسة.

```ts
interface BackendAddressWriteDto {
  label: string;
  recipient_name: string;
  phone: string;
  country_code: string;
  city: string;
  area: string;
  street: string;
  building: string;
  floor: string | null;
  apartment: string | null;
  delivery_notes: string | null;
  latitude: number | string | null;
  longitude: number | string | null;
}

interface BackendAddressDto extends BackendAddressWriteDto {
  id: string;
  is_default: boolean;
  created_at: string;
}
```

`latitude` و`longitude` معرفان كـ Decimal في الباك إند؛ قد تظهر قيم الاستجابة كنصوص. يجب أن يتعامل mapper مع هذا الشكل، ويرجع نموذجًا ثابتًا للتطبيق. إرسال الإحداثيين اختياري، لكنهما يُرسلان معًا أو كلاهما `null`. الواجهة الحالية لا تحتاج خريطة أو إذن موقع.

| حقل العنوان | القيد |
| --- | --- |
| `label` | 1–50 حرفًا |
| `recipient_name` | 1–100 حرف |
| `phone` | E.164 |
| `country_code` | حرفان ISO؛ الواجهة المصرية تستخدم `EG` |
| `city`, `area` | 1–100 حرف لكل حقل |
| `street` | 1–200 حرف |
| `building` | 1–50 حرفًا |
| `floor`, `apartment` | `null` أو 1–30 حرفًا |
| `delivery_notes` | `null` أو 1–500 حرف |
| `latitude` | من -90 إلى 90؛ حتى 7 منازل عشرية |
| `longitude` | من -180 إلى 180؛ حتى 7 منازل عشرية |

`PUT` يستبدل جميع حقول العنوان؛ ابعث DTO كاملًا. لا ترسل `id` أو `is_default` أو `created_at` مع عملية الإضافة والتعديل. حوّل النصوص الاختيارية الفارغة إلى `null`.

أول عنوان يصبح افتراضيًا تلقائيًا. عند حذف العنوان الافتراضي يختار السيرفر أقدم عنوان متبقٍّ. الحد الأقصى 20 عنوانًا. بعد الحذف أو تغيير الافتراضي، حدّث الملف وقائمة العناوين معًا حتى لا تعرض الواجهة حالة قديمة.

## الأخطاء

الشكل العام:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [{ "field": "body.email", "type": "value_error" }],
    "request_id": "request-id"
  }
}
```

التنفيذ يقرأ code ويختار رسالة عربية آمنة، ويحول details إلى أخطاء حقول بعد إزالة بادئة body/query/path وتحويل أسماء الحقول مثل phone إلى phoneNumber. الأكواد غير المعروفة تستخدم رسالة عامة دون عرض body أو message خام. يحتفظ AppError بـ requestId وretryAfterSeconds من envelope/headers، ويقرأ Retry-After كعدد ثوانٍ أو تاريخ.

`LoginPage` تتعامل مع `email_not_verified` من المحاكاة و`email_verification_required` من API وتفتح شاشة مراجعة البريد. رابط المحاكاة غير الصالح يستخدم `invalid_token`، بينما عمليات البريد في السيرفر قد ترجع `invalid_action_token`. Callback OAuth يعرض تعليمات تأكيد البريد عند email_verification_required، ورسالة انتهاء جلسة لأخطاء state/ticket، ويلغي بيانات المحاولة عند عودة خطأ.

تسجيل بريد موجود في adapter المحاكاة يرجع `account_exists` لتسهيل تجربة النموذج. الباك إند الحقيقي يرجع رسالة `202` العامة؛ لا تضف فحص وجود البريد إلى adapter الإنتاج لمطابقة المحاكاة.

| code / حالة | تعامل الواجهة |
| --- | --- |
| `invalid_credentials` | رسالة عامة على نموذج الدخول |
| `email_verification_required` | مسار مراجعة البريد وإعادة الرسالة |
| `invalid_action_token` | رابط غير صالح أو منتهي مع طلب رابط جديد |
| `invalid_token`, `invalid_session`, `authentication_required` | محاولة تجديد واحدة عند الملاءمة، ثم مسح الجلسة والرجوع للدخول |
| `validation_error` / `422` | ربط تفاصيل الحقول مع النموذج الصحيح |
| `address_not_found` | تحديث القائمة وإظهار رسالة مناسبة |
| `address_limit_reached` | توضيح حد العناوين من دون فقدان بيانات النموذج |
| `oauth_cancelled`, `invalid_oauth_state`, `invalid_oauth_ticket` | إعادة بدء الرحلة الاجتماعية |
| `oauth_account_link_required` | العودة لطريقة الدخول الأصلية |
| `429` | رسالة عربية وretryAfterSeconds؛ إعادة التأكيد تلتزم بالمدة دون retry آلي |
| خطأ شبكة أو `503` | إمكانية المحاولة مجددًا مع الاحتفاظ بالمدخلات غير الحساسة |

## إدارة الجلسة والإعدادات عند الربط

`BrowserSessionManager` يضع access token في الذاكرة فقط، ويجمع استدعاءات refresh المتزامنة في promise واحدة. عند 401 يحاول FetchHttpClient تجديد الجلسة مرة واحدة ثم يعيد الطلب المحمي. رفض المحاولة الثانية بـ 401 يبطل الجلسة أيضًا. تسجيل الخروج ينتظر refresh جاريًا ثم يطلب /browser/logout؛ فشل الاتصال يُظهر خطأً قابلًا للمحاولة بدل الادعاء بنجاح الخروج.

refresh يعيد null ويمسح الجلسة عند 401؛ أخطاء الشبكة و5xx تنتقل للمستدعي مع الاحتفاظ بملف المستخدم. SessionProvider يشترك في onSessionInvalidated ويمسح user فورًا عند بطلان الجلسة. revision يمنع ردود الشبكة القديمة من الكتابة فوق جلسة أحدث. لا يُعاد طلب لحساب سابق تحت حساب آخر بعد تغير المستخدم.

رسائل التأكيد والاسترجاع يكوّن روابطها email-worker باستخدام FRONTEND_URL. عند تغيير البيئة، إعادة إنشاء api وحده لا تكفي. مع تشغيل خدمات البيانات استخدم من مجلد back:

```bash
docker compose --env-file .env.development up -d --build --force-recreate --no-deps api email-worker
```

ثم اطلب رسالة جديدة؛ الرسائل القديمة لا تتغير.

قيم `VITE_*` تظهر في حزمة المتصفح. استخدمها للإعدادات العامة فقط، مثل اسم البيئة أو عنوان API العام عند إضافة الربط. لا تضع فيها JWT secret أو client secret أو بيانات SMTP أو أسرار Google/Facebook. حفظ كلمة المرور أو نسخها إلى `localStorage` أو `sessionStorage` ليس جزءًا من هذا التطبيق.

## تسليم التكامل

راجع مع فريق الربط: نجاح العمليات وحالات الفشل، إعادة تحميل الصفحة، انتهاء الجلسة، الرجوع لمسار محمي، روابط التأكيد المنتهية، إلغاء OAuth، وترتيب تحديث الملف والعناوين. لم تُضَف أو تُشغَّل اختبارات في هذه المرحلة؛ الاختبارات مسؤولية الفريق المخصص لها حسب طلب المشروع.

## سياسة الاتصالات في الواجهة

نسخة البناء تضيف CSP من `vite.config.ts` وتسمح `connect-src` بأصل `VITE_API_BASE_URL` فقط عند اختيار `api`، أو تمنع الاتصالات عند اختيار `demo`. سياسة Vite أثناء dev منفصلة لتسمح بـ HMR.
