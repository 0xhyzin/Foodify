# ضوابط الأمان

هذا المستند يصف ضوابط التنفيذ الحالي ومسؤوليات تشغيله. المرجع هو [OWASP Top 10:2025](https://top10.owasp.org/2025/)؛ القائمة إطار لتحديد المخاطر، ولا تعني أن هذا المشروع خضع لاختبار اختراق أو حصل على اعتماد أمني. لم تنشأ أو تشغل اختبارات ضمن المهمة؛ التحقق الأمني العملي قبل الإنتاج مسؤولية الفريق المختص.

## الربط مع OWASP Top 10:2025

| الخطر | الضوابط الموجودة | ما يحتاجه النشر/الفريق |
| --- | --- | --- |
| A01 Broken Access Control | Bearer dependency تفحص المستخدم والجلسة؛ صلاحيات منفصلة؛ العنوان يجلب دائمًا بـ`id + user_id`؛ لا توجد حقول أدوار قابلة للتعديل العام. | تطبيق `require_permission` صراحة على أي endpoints إدارية مستقبلية، ومراجعة صلاحيات موظفي التشغيل. |
| A02 Security Misconfiguration | Settings تفحص environment وHTTPS والأسرار وSMTP؛ production يرفض docs/debug؛ CORS وHost بقوائم صريحة؛ reload للتطوير فقط. | Secret manager، TLS proxy، قواعد شبكة وإعدادات خدمات مستقلة لكل مرحلة. |
| A03 Software Supply Chain Failures | dependencies معلنة في requirements، Dockerfile مستقل، لا ننفذ كودًا مأخوذًا من input. | مراجعة تحديثات الاعتمادات، تثبيت إصدار build منشور ومراجعة صور Docker وفحص الثغرات في CI. |
| A04 Cryptographic Failures | Argon2id لكلمات المرور؛ JWT محدود الخوارزمية؛ بصمات SHA-256 للتوكنات العشوائية؛ Fernet للرسائل المعلقة؛ SMTP TLS مطلوب في production. | إدارة المفاتيح وتدويرها، تشفير الأقراص والنسخ الاحتياطية، وتأمين وصلات MySQL وRedis حسب بيئة النشر. |
| A05 Injection | SQLAlchemy parameters، لا SQL من input؛ DTOs ترفض الحقول الإضافية وتحدد الأطوال وصيغة الأرقام والإحداثيات. | الواجهة تعرض نص الاسم/العنوان كنص وتطبق output escaping عند عرض HTML. |
| A06 Insecure Design | تسجيل العميل يسند customer فقط؛ reset/email tokens مرة واحدة؛ refresh rotation وإلغاء الجلسات؛ حد 20 عنوانًا تحت قفل المستخدم؛ OAuth completion مرتبط بمتصفح البداية. | مراجعة threat model عند إضافة الدفع والطلبات والموظفين، ووضع حدود مالية وعمليات موافقة مناسبة حينها. |
| A07 Authentication Failures | حد كلمة المرور 15–128؛ رسائل عامة للمسارات الحساسة؛ Redis limits مشتركة؛ بريد مؤكد قبل إصدار الجلسة؛ Google/Meta identity validation. | ضبط OAuth consent/review وSMTP reputation، ومراقبة محاولات الدخول؛ MFA للموظفين مرحلة لاحقة. |
| A08 Software or Data Integrity Failures | تحقق JWT claims والتوقيع؛ OAuth state وnonce/PKCE حسب provider؛ قيود unique وFK وCHECK؛ migrations صريحة. | حماية CI/CD وصلاحيات migrations والنسخ الاحتياطية وعمليات الاستعادة. |
| A09 Security Logging and Alerting Failures | request ID؛ أخطاء عامة بلا bodies أو tokens؛ logs worker تستخدم job ID ونوع الفشل؛ access logs معطلة لمنع تسريب authorization codes. | تجميع logs آمن ومحددات retention وتنبيهات rate limits وoutbox والاعتمادات؛ لا يوجد SIEM جاهز داخل المشروع. |
| A10 Mishandling of Exceptional Conditions | handlers موحدة؛ rollback عند فشل request؛ Redis يفشل مغلقًا بـ503؛ timeouts للشبكة والبريد؛ outbox retries محدودة؛ body size limit قبل JSON parsing. | مراقبة الجاهزية والموارد، إجراءات تشغيل عند dead-letter وفشل الخدمات، ومراجعة load قبل الإنتاج. |

## كلمات المرور والجلسات

`Argon2PasswordHasher` يستخدم Argon2id بذاكرة 64 MiB و3 iterations و4 lanes، مع salt تديره المكتبة. لا نخزن كلمة مرور صريحة ولا نستخدم SHA-256 لكلمات المرور. يقبل DTO كلمات مرور طويلة ومسافات وحروف Unicode دون فرض تركيب حروف وأرقام. رسائل الدخول الخاطئ موحدة؛ تنفيذ dummy hash يقلل فرق الزمن بين بريد غير موجود وحساب قائم. المراجع: [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)، [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

الـ access token JWT موقع وليس مشفرًا؛ يحتوي IDs وclaims لازمة للمصادقة فقط. لا يحتوي البريد أو الهاتف أو العنوان أو الصلاحيات. يتحقق `JwtTokenCodec` من `HS256` فقط ومن `iss/aud/exp/iat/nbf/sub/sid/jti/type`. كل request محمي يطابق `sid` مع جلسة MySQL غير ملغاة وغير منتهية، ثم يقرأ حالة المستخدم وأدواره الحالية. لهذا فإن logout/reset يمنعان استخدام الجلسة في requests لاحقة حتى قبل انتهاء الـ JWT. مرجع طبيعة JWT: [FastAPI JWT security](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).

الـ refresh token عشوائي ويخزن digest فقط. التدوير يستهلك القديم ويصدر بديلًا في transaction مع قفل الصفوف. إعادة استخدام refresh قديم تلغي الجلسة المرتبطة، لذلك يجب أن يمنع العميل تنفيذ refresh متزامن من عدة requests. عمر الجلسة الافتراضي 30 يومًا من إنشائها ولا يتم تمديده عند كل refresh؛ الـ access الافتراضي 15 دقيقة. `logout` يلغي جلسة واحدة و`logout-all` يلغي جميع جلسات المستخدم.

واجهة الـ API الحالية ترجع التوكنات في JSON وتستقبل Bearer header؛ لا تنشئ session cookies. تطبيق الهاتف يستخدم مخزن النظام الآمن، ومتصفح الويب يحتاج استراتيجية حفظ مناسبة مثل BFF وHttpOnly cookies مع ضوابط CSRF على طبقة الـBFF. لا تحفظ access/refresh tokens في `localStorage`. [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

## تأكيد البريد والاسترجاع

التوكنات العشوائية ذات entropy كافية تخزن SHA-256 digest؛ هذه غير كلمات المرور المختارة بشريًا. التوكن مقيد بنوعه ووقت انتهاء واستخدام واحد. إعادة الإرسال تلغي توكنات الغرض السابق. مسار reset يقبل حسابًا محليًا مؤكد البريد فقط، ثم يغير hash ويلغي كل الجلسات. حساب OAuth بلا كلمة مرور يسترجع الوصول عبر مقدم الخدمة؛ لا يحوله forgot-password إلى حساب بكلمة مرور.

`register` و`resend-verification` و`forgot-password` ترجع `202` بنفس الرسالة للحسابات المؤهلة وغير المؤهلة. قائمة المدخلات وصيغة الرد تمنع كشف الحسابات مباشرة، لكن الرد العام ليس وعدًا بإخفاء جميع فروق التوقيت على الشبكة. الرابط يحمل token في fragment، والواجهة ترسله عبر body ثم تمسحه. مرجع تصميم الاسترجاع: [OWASP Forgot Password](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

رسالة البريد تحتوي token قابلًا للاستعمال، لذلك تحفظ مؤقتًا داخل `email_outbox` مشفرة بـFernet في transaction إنشاء action token نفسها. worker يفكها عند الإرسال فقط، ويمسح payload بعد التسليم أو انتهاء الرابط. محاولات التسليم at-least-once: فشل commit بعد قبول SMTP قد يؤدي لتسليم الرسالة مرة ثانية؛ action token نفسه يظل مرة واحدة. بعد 10 محاولات تصبح المهمة متوقفة لقرار المشغل؛ راقبها واحذف البيانات المشفرة القديمة وفق سياسة retention.

## OAuth

الـ API لا يقبل provider access token يرسله العميل كإثبات هوية، بل ينفذ authorization-code flow مع مقدم الخدمة. `state` مرة واحدة ومقيد بالمزود والانتهاء. Google يستخدم PKCE S256 وnonce وفحص ID token باستخدام Google JWKS ثابت؛ تأكيد البريد تلقائيًا مقصور على Gmail أو Workspace المؤكد ذي `hd`، والبريد الخارجي يحتاج تأكيد Foodify. هذا يتبع [إرشادات Google لسلطة تأكيد البريد](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token). Facebook يفحص token metadata وapp ID والانتهاء وهوية المستخدم، ويعامل البريد على أنه غير مؤكد محليًا.

الـ callback يتجه دائمًا إلى `FRONTEND_URL` المضبوط؛ العميل لا يختار redirect URL. التذكرة النهائية صالحة لدقيقتين ولمرة واحدة، ومقيدة ببصمة binding verifier. لا يضع الخادم access/refresh tokens في الروابط ولا يخزن provider tokens. تطابق البريد وحده لا يربط حسابين. راجع [OAUTH.md](OAUTH.md) للمزودين والـ claims والمراجع الرسمية.

## حدود الطلبات والخصوصية

حد عام 120 request لكل IP في 60 ثانية، وحد auth 30 request في 15 دقيقة، وحد عمل البريد 5 لكل بريد في 15 دقيقة وlogin 10 لكل بريد. Redis يستخدم مفاتيح تحتوي hash للهوية بدل البريد أو IP الخام، وnamespace للبيئة. إذا تعطل Redis ترجع المسارات المحددة `503` بدل إيقاف الحماية صامتًا. `429` يحتوي `Retry-After`.

runner لا يثق في forwarded headers افتراضيًا؛ خلف reverse proxy سيعبر `request.client` عن الـpeer المباشر. اضبط `TRUSTED_PROXY_IPS` على عناوين أو نطاقات الـproxy الفعلية لتفعيل قراءة العناوين التي يمررها هذا الـpeer فقط؛ wildcard و`/0` مرفوضان. أبقِ التطبيق خلفه في شبكة خاصة واضبط حدود الـproxy؛ لا تحول `X-Forwarded-For` من أي عميل إلى مصدر موثوق. لا تسجل query strings الخاصة بـOAuth callbacks أو request bodies الحساسة أو Authorization في الـproxy أو أدوات المراقبة.

`MAX_REQUEST_BYTES` الافتراضي 1 MiB ويطبق حتى على streamed bodies. أسماء/عناوين DTO محددة الطول. الردود تحمل no-store وnosniff وframe restrictions وrequest ID؛ production يضيف HSTS. CORS لا يسمح بـwildcard أو credentials، وTrustedHost يطابق الأسماء المضبوطة. لا يعد CORS بديلًا عن مصادقة الخادم.

رقم الهاتف يتحقق من الصيغة فقط، وليس ملكيته؛ لا يوجد SMS OTP. العنوان بيانات شخصية ظاهرة للمستخدم المالك ويحتاج حماية قواعد البيانات والنسخ الاحتياطية وسياسة احتفاظ تحددها جهة التشغيل. لا يحتوي هذا الإصدار على لوحة إدارة، MFA، CI security scanner أو تدقيق مستقل؛ إضافتها تنفذ في مراحلها بمتطلبات واضحة.
