# تسجيل الدخول باستخدام Google وFacebook

هذا الجزء مسؤول عن إثبات هوية المستخدم عند مزود خارجي. حساب Foodify، أدوار المستخدم، تأكيد البريد، استكمال رقم الهاتف والعنوان، وإصدار جلسة JWT تظل مسؤولية خدمات التطبيق.

## مسار تسجيل الدخول

1. الواجهة تولد `binding_verifier` عشوائيًا آمنًا بطول 43–128 حرفًا من حروف Base64 URL-safe. يُحفظ مؤقتًا في `sessionStorage` للمتصفح، أو مخزن آمن مناسب لتطبيق الهاتف. لا يُضاف إلى رابط.
2. الواجهة تحسب `binding_challenge = SHA256(binding_verifier)` وتحوّله إلى 64 حرفًا hexadecimal صغيرة.
3. ترسل `POST /api/v1/auth/oauth/google/start` أو `POST /api/v1/auth/oauth/facebook/start` مع JSON:

   ```json
   {"binding_challenge": "<64 lowercase hexadecimal characters>"}
   ```

4. التطبيق يخزن محاولة قصيرة العمر تحتوي بصمة `state` مع `binding_challenge` وبيانات الحماية الخاصة بالمزود. الرد يحتوي `authorization_url`؛ الواجهة تفتح هذا الرابط في المتصفح.
5. المزود يرجع إلى `GET /api/v1/auth/oauth/{provider}/callback` باستخدام `code` و`state`. التطبيق يستهلك المحاولة مرة واحدة، ويتحقق من المزود، ثم يختار حساب Foodify بناءً على `(provider, subject)`.
6. بعد نجاح حساب مؤكد البريد، يرجع المتصفح إلى عنوان ثابت: `FRONTEND_URL/oauth/callback#ticket=...`. الـfragment يحتوي تذكرة مؤقتة لا تستخدم إلا مرة واحدة؛ لا يحتوي access token أو refresh token.
7. الواجهة تقرأ التذكرة من الـfragment وتحذف الـfragment من تاريخ الصفحة، ثم ترسل:

   ```http
   POST /api/v1/auth/oauth/complete
   Content-Type: application/json
   ```

   ```json
   {"ticket": "<one-time completion ticket>", "binding_verifier": "<original client secret>"}
   ```

8. التطبيق يطابق بصمة الـverifier مع محاولة البداية قبل إصدار جلسة Foodify. الواجهة تحذف الـverifier بعد النجاح، وتعرض استكمال بيانات المستخدم إذا كان رقم الهاتف أو عنوان التوصيل ناقصًا.

وجود `state` وحده لا يثبت أن المتصفح الذي أنهى تسجيل الدخول هو الذي بدأه. الـbinding verifier يربط بداية التدفق بنهايته، بالإضافة إلى منع إعادة استخدام `state` والتذكرة. الـverifier مختلف عن Google PKCE verifier؛ الأول ملك الواجهة لربط التدفق، والثاني يولده ويحفظه الباك اند لحماية تبادل كود Google.

## سياسة الحسابات والبريد

| الحالة | السلوك |
| --- | --- |
| الهوية الخارجية موجودة بنفس المزود و`subject` | فتح حساب Foodify المرتبط بعد تطبيق شروط الحساب وتأكيد البريد. |
| الهوية جديدة وبريدها مستخدم في حساب آخر | رفض الربط التلقائي؛ تسجيل الدخول إلى الحساب الموجود أولًا. ربط الحسابات الصريح ليس ضمن هذه المرحلة. |
| Google يرجع Gmail مؤكدًا أو Workspace مؤكدًا مع claim `hd` وهوية جديدة | إنشاء حساب مؤكد البريد، بعد التحقق الكامل من ID token. |
| Google Account يستخدم بريدًا خارجيًا دون `hd` | يرسل Foodify رسالة تأكيد محلية؛ `email_verified` من Google وحده لا يكفي لإثبات الملكية الحالية لهذا البريد. |
| Facebook يرجع بريدًا وهوية جديدة | إنشاء حساب غير مؤكد وإرسال رسالة تأكيد من Foodify. المتصفح يرجع `#error=email_verification_required`؛ بعد التأكيد يعاد تدفق Facebook من البداية للحصول على جلسة. |
| هوية جديدة لا ترجع بريدًا | خطأ `oauth_email_required`؛ يستخدم المستخدم التسجيل بالبريد. Facebook قد لا يرجع البريد حتى مع طلب صلاحية `email`. |

الاسم والبريد قابلان للتغيير؛ مفتاح الهوية الخارجية هو `provider + subject`. لا نثق في البريد الذي يرسله العميل، ولا نستخدم البريد وحده لربط هوية خارجية بحساب موجود. رقم الهاتف والعنوان وتفاصيل التوصيل تُدخل من خلال مسارات ملف المستخدم المعتادة؛ لا تؤخذ من المزود.

## إعداد Google

أنشئ OAuth client مناسبًا لتطبيق ويب في Google Cloud، واضبط consent screen وauthorized redirect URI بالقيمة المطابقة تمامًا:

```dotenv
OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback
```

يسأل التطبيق عن `openid email profile` فقط، ويستخدم authorization code وPKCE بطريقة `S256` و`nonce`. التحقق من ID token يتم باستخدام مفاتيح Google العامة، مع السماح بـ`RS256` فقط والتحقق من التوقيع و`aud` و`iss` و`exp` و`iat` و`sub` و`nonce` و`azp` عند وجوده. عنوان JWKS ثابت في الكود؛ لا يؤخذ من طلب العميل أو من رأس JWT. المصادر: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)، [Google OIDC API reference](https://developers.google.com/identity/openid-connect/reference)، [Google discovery document](https://accounts.google.com/.well-known/openid-configuration).

قبول تأكيد Google للبريد مقصور على Gmail أو Workspace المؤكد مع `hd`؛ حساب Google ببريد خارجي يحتاج رابط Foodify حتى لو كان `email_verified=true`. المرجع: [Google: email authority](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token).

## إعداد Facebook

أنشئ تطبيق Meta، فعّل Facebook Login، واضبط valid OAuth redirect URI بالقيمة المطابقة:

```dotenv
OAUTH_FACEBOOK_CLIENT_ID=your-meta-app-id
OAUTH_FACEBOOK_CLIENT_SECRET=your-meta-app-secret
OAUTH_FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/facebook/callback
OAUTH_FACEBOOK_GRAPH_VERSION=v26.0
```

التطبيق يستخدم confidential server authorization-code flow مع `state` وclient secret. لا يفترض أن مسار Facebook web اليدوي يدعم PKCE أو Google OIDC nonce؛ يتم ربط البداية والنهاية باستخدام binding verifier الخاص بالتطبيق. مصدر عقد التدفق: [Meta official OAuth2 client source](https://github.com/facebookarchive/php-graph-sdk/blob/5.x/src/Facebook/Authentication/OAuth2Client.php). مرجع الـweb flow: [Meta manual login flow](https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/).

بعد تبادل الكود، يفحص التطبيق `/debug_token` ويتحقق من `is_valid` و`app_id` ونوع `USER` والانتهاء و`user_id`. ثم يقرأ `id,name,email` من `/me`، ويطابق `id` مع الهوية المفحوصة. يرسل `appsecret_proof` لاستعلام الهوية. البريد المسترجع يظل غير مؤكد في Foodify. مصدر فحص البيانات: [Meta official access token metadata source](https://github.com/facebookarchive/php-graph-sdk/blob/5.x/src/Facebook/Authentication/AccessTokenMetadata.php).

الإصدار الافتراضي مثبت عند `v26.0`؛ تم التحقق من قيمته في [Meta official Python SDK configuration](https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/apiconfig.py) بتاريخ 2026-10-20. تغييره قرار نشر صريح مع مراجعة changelog. صفحات مستندات Meta المباشرة أعادت HTTP 429 أثناء العمل، ولذلك استُخدم كود Meta الرسمي للتحقق من عقد التدفق وفحص التوكن.

## حدود المسؤوليات والاعتمادات

| المكون أو الدالة | المسؤولية والمدخلات والمخرجات |
| --- | --- |
| `OAuthGateway` في `app/shared/ports.py` | واجهة تعتمد عليها خدمات تسجيل الدخول؛ يمكن تبديل المزود الفعلي دون ربط خدمة التطبيق بـHTTP أو مكتبة JWT الخارجية. |
| `OAuthIdentity` | DTO ثابت يحمل المزود وsubject والبريد وحالة تأكيده والاسم؛ لا يحمل أي provider token. |
| `SocialOAuthGateway(settings)` | محول HTTP الفعلي للمزودين، بإعدادات محقونة. لا ينشئ حسابات ولا يصدر جلسات Foodify. |
| `authorization_url(provider, state, code_verifier, nonce)` | يفحص الإعدادات ويبني رابط موافقة المزود. يضيف challenge وnonce لـGoogle فقط. لا يظهر client secret في الرابط. |
| `exchange_identity(provider, code, code_verifier, nonce)` | يختار تدفق التحقق المناسب ويرجع `OAuthIdentity` بعد نجاح التحقق. |
| `_exchange_google_identity(...)` | يرسل الكود إلى Google في body، ثم يفحص ID token بواسطة JWKS وقيود claims. |
| `_google_email_is_authoritative(claims,email)` | يسمح بتأكيد البريد تلقائيًا لـGmail أو Workspace المؤكد ذي `hd`؛ غيرهما يحتاج رسالة تأكيد محلية. |
| `_exchange_facebook_identity(code)` | يرسل الكود في body، يفحص token metadata، ثم يجلب هوية المستخدم ويطابقها. |
| `_request_json(...)` | طلب HTTP بمهلة 10 ثوانٍ واتصال 5 ثوانٍ، دون اتباع redirects؛ يحول أخطاء الشبكة والمزود إلى أخطاء عامة آمنة. يغلق العميل بعد الطلب. |
| `_require_provider_configuration(provider)` | يرفض المزود غير المدعوم أو غير المضبوط؛ غياب credentials لا يمنع بقية التطبيق من العمل. |
| `_create_pkce_challenge(verifier)` | يفحص صيغة وطول verifier، ويحسب SHA-256 ثم Base64 URL-safe دون padding. |
| `_required_string(...)` | يرفض claims الإجبارية المفقودة أو ذات نوع غير متوقع. |
| `_optional_email(...)` | يسمح بغياب البريد، ويرفض صيغة قيمة غير نصية أو طويلة؛ قرار طلب البريد لحساب جديد في خدمة التطبيق. |
| `_display_name(...)` | اسم عرض محدود الطول أو اسم افتراضي عند غياب claim الاسم. |
| `_require_unexpired_facebook_token(metadata)` | يرفض توكنًا منتهيًا أو metadata غير صالحة أو صلاحية وصول بيانات انتهت. |
| `_authentication_failed()` و`_provider_unavailable()` | أخطاء `AppError` عامة لا تعرض استجابة المزود أو أسراره. |

المفاتيح العامة لـGoogle مخزنة مؤقتًا في الذاكرة لمدة خمس دقائق داخل `PyJWKClient`. لا يتم الاحتفاظ بـprovider access tokens أو refresh tokens أو ID tokens في قاعدة البيانات. JWKS requests لها مهلة مستقلة 10 ثوانٍ. المرجع: [PyJWT API](https://pyjwt.readthedocs.io/en/stable/api.html#jwt.PyJWKClient).

## متطلبات التشغيل

- لكل بيئة OAuth client وcallback وإعدادات منفصلة؛ لا تستخدم production secret في development أو test.
- `PUBLIC_BASE_URL` هو عنوان الباك اند العام، و`FRONTEND_URL` هو أصل الواجهة الموثوق الذي يستقبل التذكرة. لا يوجد redirect URL يختاره العميل أثناء التدفق.
- إعدادات المزود الثلاثة يجب أن توجد معًا أو تُترك كلها فارغة. عدم إعداد مزود ينتج `oauth_unavailable` دون كسر التسجيل بالبريد.
- production يتطلب HTTPS. استخدم callback بعنوان HTTPS في Google وMeta واحمِ الأسرار داخل secret manager أو متغيرات بيئة النشر.
- إعدادات الـapp review وصلاحيات المستخدمين الخارجيين وconsent screen تتم في حساب المزود؛ بيانات المشروع المحلية لا تنشئ OAuth clients أو توافق عليها تلقائيًا.
- لا تسجل query strings لمسارات callback، ولا bodies تحتوي أكوادًا أو تذاكر أو verifier، ولا رؤوس `Authorization`. أبقِ `httpx` و`httpcore` عند `WARNING`؛ استعلام Facebook debug token يحتوي توكنًا مؤقتًا في query حسب عقد المزود.
- لا يُنفذ استدعاء مزود حقيقي قبل ضبط credentials. لم تُضف أو تُشغّل اختبارات لهذا الجزء تنفيذًا لطلب فصل مسؤولية فريق الاختبارات.
