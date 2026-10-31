# دليل الدوال ومسار كل وظيفة

## Sprint 2

الشرح الكامل ومطابقة متطلبات 6.5 وفهرس كل عملية في [README_SPRINT_2.md](../README_SPRINT_2.md)، بما فيها `POST /cart` لإنشاء سلة المستخدم أو إرجاع الموجودة.

دوال المطاعم والسلة والطلبات منفصلة حسب العملية. مساراتها وعقودها وتسلسل Checkout في [SPRINT_2.md](SPRINT_2.md)، وفهرس ملفاتها في [SPRINT_2_FILES.md](SPRINT_2_FILES.md).


كل عملية لها فولدر داخل `app/users/`، وكل خدمة تنفذ حالة استخدام واحدة عن طريق `execute()`. المسارات أدناه تحت `/api/v1` ما عدا health. الـrouter لا ينفذ SQL؛ dependencies تنشئ خدمات وrepositories باستخدام نفس MySQL session لكل request. منشئات الكلاسات `__init__` تحفظ الاعتمادات فقط، ولا تنفذ تسجيلًا أو migrations تلقائية.

## الملفات الخمسة لكل عملية

خذ تسجيل الدخول مثالًا:

| الملف | الدالة أو العقد | دوره |
| --- | --- | --- |
| `app/users/login/dto.py` | `LoginRequest` و`LoginResponse` | مدخلات email/password ومخرجات التوكنات؛ يعيد استخدام الأنواع العامة دون نسخ قواعد التحقق. |
| `app/users/login/interfaces.py` | `LoginServiceInterface.execute` | واجهة خدمة الدخول التي يعتمد عليها الـrouter. |
| `app/users/login/service.py` | `LoginService.execute` | فحص الاعتماد والحالة، وإنشاء الجلسة وحفظ الـtransaction. |
| `app/users/login/dependencies.py` | `get_service` | حقن repositories وhasher وsession issuer وUnitOfWork المطلوبة للدخول فقط. |
| `app/users/login/router.py` | `login_customer` | يستقبل POST وينادي الخدمة ويرجع response؛ لا يحتوي منطق hash أو SQL. |

ينطبق النمط نفسه على جميع العمليات؛ الجداول التالية تسمي فولدر العملية والخدمة التابعة له. داخل الفولدر توجد DTOs والواجهة وDI والـrouter الخاصة بالعملية. `app/users/router.py` يجمع routers فقط، وليس مكانًا لتنفيذ حالات الاستخدام.

## التسجيل والبريد وكلمة المرور

| HTTP | فولدر العملية: دالة router → الخدمة | التنفيذ والنتيجة |
| --- | --- | --- |
| `POST /auth/register` | `register/`: `register_customer` → `RegisterService.execute` | `RegisterRequest(name,email,password)`؛ hash، بحث البريد، إنشاء User بدور customer، action token وoutbox، commit؛ رد عام 202 سواء البريد قائمًا أم جديدًا. |
| `POST /auth/resend-verification` | `resend_verification/`: `resend_email_verification` → `ResendVerificationService.execute` | بريد مطبع؛ حساب نشط غير مؤكد → قفل المستخدم، إلغاء روابط التأكيد السابقة، إنشاء رابط ورسالة، commit؛ رد عام 202. |
| `POST /auth/verify-email` | `verify_email/`: `confirm_customer_email` → `VerifyEmailService.execute` | توكن التأكيد؛ بصمة، قفل المستخدم ثم التوكن، فحص الغرض/الانتهاء/الاستخدام، تأكيد البريد وإلغاء روابط التأكيد، commit؛ message 200. |
| `POST /auth/forgot-password` | `forgot_password/`: `request_password_reset` → `ForgotPasswordService.execute` | بريد مطبع؛ إرسال فقط لحساب محلي نشط مؤكد البريد؛ لا يكشف أهلية البريد؛ message 202. |
| `POST /auth/reset-password` | `reset_password/`: `reset_customer_password` → `ResetPasswordService.execute` | token/password؛ hash جديد، فحص token من نوع password_reset، تغيير hash، استهلاك الروابط وإلغاء الجلسات، commit؛ message 200. |

خدمات التسجيل والبريد والاسترجاع ترجع `None` بعد تنفيذ العملية؛ الـrouter يبني DTO الرسالة المحلية (`RegisterResponse` أو `VerifyEmailResponse` مثلًا) ويحدد status code.

الجداول الأساسية: `users` و`user_roles` و`action_tokens` و`token_types` و`email_outbox`، مع `auth_sessions` عند تغيير كلمة المرور. رسائل التأكيد والاسترجاع لا تعيد raw token في response. روابط البريد هي صفحات frontend مستقبلية، وتستخدم Mailpit لقراءة قيمة fragment أثناء العمل اليدوي من Postman.

## الدخول وإدارة الجلسات

| HTTP | فولدر العملية: دالة router → الخدمة | التنفيذ والنتيجة |
| --- | --- | --- |
| `POST /auth/login` | `login/`: `login_customer` → `LoginService.execute` | email/password؛ تحقق hash ثم قفل المستخدم وإعادة فحصه، اشتراط تأكيد البريد، إنشاء جلسة وتوكنات، commit؛ 200. |
| `POST /auth/refresh` | `refresh_session/`: `rotate_session_tokens` → `RefreshSessionService.execute` | refresh_token؛ بصمة وقفل المستخدم والجلسة والتوكن، استهلاك القديم وإصدار بديل، commit؛ 200؛ إعادة استخدام القديم تلغي الجلسة. |
| `POST /auth/logout` | `logout/`: `logout_current_session` → `LogoutService.execute` | Bearer access token؛ فك claims وقفل المستخدم والجلسة ثم إلغاؤها وcommit؛ 204 بلا body. |
| `POST /auth/logout-all` | `logout_all/`: `logout_all_sessions` → `LogoutAllService.execute` | مستخدم مصادق؛ قفل المستخدم وتحديث جلساته غير الملغاة ثم commit؛ 204. |

عقود استجابة الدخول وrefresh وOAuth completion تستخدم بيانات التوكنات المشتركة: `access_token, refresh_token, token_type="bearer", expires_in, user`. `expires_in` بالثواني. الجداول الأساسية `auth_sessions` و`refresh_tokens` مع قراءة `users` وroles/permissions. خدمة إصدار الجلسة مشتركة؛ login وrefresh والخروج خدمات عمليات منفصلة.

## Google وFacebook

| HTTP | فولدر العملية: دالة router → الخدمة | التنفيذ والنتيجة |
| --- | --- | --- |
| `POST /auth/oauth/{provider}/start` | `oauth/start/`: `start_social_sign_in` → `StartOAuthService.execute` | binding_challenge؛ provider هو google أو facebook؛ إنشاء state ومحاولة قصيرة العمر وcommit؛ 200 authorization_url. |
| `GET /auth/oauth/{provider}/callback` | `oauth/callback/`: `finish_provider_callback` → `OAuthCallbackService.execute` | state وcode أو error من المزود؛ استهلاك state، استعلام المزود، ربط الهوية/إنشاء حساب، إنشاء ticket أو انتظار تأكيد البريد؛ 303 إلى frontend fragment. |
| `POST /auth/oauth/complete` | `oauth/complete/`: `complete_social_sign_in` → `CompleteOAuthService.execute` | ticket/binding_verifier؛ قفل المستخدم والتذكرة، مطابقة hash/الانتهاء، استهلاكها وإنشاء جلسة ثم commit؛ 200 توكنات. |

`StartOAuthService` يعيد `StartOAuthResponse(authorization_url)`، و`OAuthCallbackService` يعيد `OAuthCallbackResult(fragment)`؛ الـrouter يضيف عنوان frontend المضبوط ويصدر redirect. `CompleteOAuthService` يعيد `CompleteOAuthResponse` بالتوكنات.

callback يحفظ استهلاك state قبل الاتصال بالمزود حتى لا يعاد استخدام الكود. حساب provider موجود يجلب عن طريق `(provider,subject)`؛ هوية جديدة ببريد موجود ترفض الربط التلقائي. الحساب الجديد يأخذ customer فقط؛ إذا كان البريد غير مؤكد ينشئ outbox ويرجع انتظار التأكيد. الجداول `oauth_states/social_accounts/oauth_tickets` مع `users` وإصدار الجلسة عند complete. تفاصيل OAuth adapter وضوابط المزود في [OAUTH.md](OAUTH.md).

## الملف الشخصي والعناوين

الـID المرسل للعنوان يتحقق كـUUID قبل دخوله الخدمة. المستخدم يحدد دائمًا من Bearer session، ولا يقبل body أي `user_id` لتغيير الملكية.

| HTTP | فولدر العملية: دالة router → الخدمة | التنفيذ والنتيجة |
| --- | --- | --- |
| `GET /users/me` | `get_profile/`: `get_my_profile` → `GetProfileService.execute` | يجلب المستخدم ويعيد ملفه دون password hash أو provider tokens؛ 200. |
| `PATCH /users/me` | `update_profile/`: `update_my_profile` → `UpdateProfileService.execute` | يقفل المستخدم ويعدل فقط name/phone المرسلة ثم commit؛ null phone يمسح الرقم؛ الطلب الفارغ أو name=null مرفوض؛ 200. |
| `GET /users/me/addresses` | `addresses/list_addresses/`: `list_my_addresses` → `ListAddressesService.execute` | يجلب عناوين المالك بترتيب الإنشاء ويحسب is_default من مؤشر المستخدم؛ 200. |
| `POST /users/me/addresses` | `addresses/add_address/`: `add_my_address` → `AddAddressService.execute` | يقفل المستخدم، يتحقق من حد 20، يضيف العنوان وflush؛ يضبط الافتراضي إذا لم يوجد ثم commit؛ 201. |
| `PUT /users/me/addresses/{address_id}` | `addresses/update_address/`: `replace_my_address` → `UpdateAddressService.execute` | يقفل المستخدم ويجلب العنوان بشرط ملكيته، يستبدل بيانات DTO كاملة ثم commit؛ 200. |
| `DELETE /users/me/addresses/{address_id}` | `addresses/delete_address/`: `delete_my_address` → `DeleteAddressService.execute` | يقفل المستخدم؛ إذا حذف الافتراضي ينقل المؤشر لأقدم متبقٍ أو null وflush قبل delete؛ commit ثم 204. |
| `PUT /users/me/default-address/{address_id}` | `addresses/set_default_address/`: `set_my_default_address` → `SetDefaultAddressService.execute` | يقفل المستخدم ويتحقق من ملكية العنوان ثم يحرك المؤشر وcommit؛ 200 ملف العميل. |

العناوين تستخدم `users` و`addresses`؛ جميع شروط القراءة والكتابة تتضمن `id + user_id`. العنوان الغائب والمملوك لغير المستخدم يعيدان نفس 404. لا يوجد service واحد يجمع عمليات الملف والعناوين؛ كل صف في الجدول له فولدره وservice وواجهة وDI وrouter.

## الأدوات المشتركة بين العمليات

كل أداة هنا تؤدي مسؤولية واحدة تستخدمها عدة عمليات، وتتلقى dependencies من خلال interfaces. لا تجمع دوال التسجيل والدخول والاسترجاع في service عام.

| الملف | المسؤولية ومسار البيانات |
| --- | --- |
| `users/shared/email_actions.py: EmailActionService.queue_email_action / require_action` | إنشاء raw action token، إلغاء سابقه لنفس الغرض، إضافة digest/expiry إلى `action_tokens` ورسالة مشفرة إلى outbox؛ وكذلك جلب action token والتحقق من غرضه واستخدامه وانتهائه مع قفل المستخدم والتوكن. خدمة العملية تملك commit. |
| `users/shared/session_issuer.py: SessionIssuer.create_session / issue_token_pair` | إنشاء `auth_sessions` بعمر ثابت وflush، وإصدار JWT وrefresh digest ثم بناء بيانات التوكنات؛ يستخدمه login وrefresh وOAuth completion. خدمة العملية تملك commit. |
| `users/shared/access_authenticator.py: AccessAuthenticator.authenticate_access` | فك JWT والتحقق من جلسة حية ومطابقة المستخدم ونشاط الحساب وتأكيد البريد؛ يرجع User بأدواره وصلاحياته الحالية. |
| `users/shared/guards.py` | `require_active_user` يتحقق من وجود المستخدم ونشاطه مع اختيار القفل للكتابة؛ `require_owned_address` يتحقق من الملكية؛ أخطاء موحدة دون كشف حساب آخر. |
| `users/shared/interfaces.py` | عقود تخزين User/Address/ActionToken/Session/Social والعقود المشتركة اللازمة لحقن الأدوات. |
| `shared/ports.py` | عقود PasswordHasher وTokenCodec وEmailSender وUnitOfWork والخدمات الخارجية العامة. |

## DTOs: حدود البيانات

DTO كل عملية في `operation/dto.py`، ويعيد استخدام الأنواع المناسبة من `users/shared/dto/`:

| الملف أو العقد | المسؤولية |
| --- | --- |
| `shared/dto.py: APIModel` | `extra="forbid"` وقراءة ORM attributes عند الحاجة؛ أساس request/response DTOs. |
| `users/shared/dto/credentials.py` | `EmailRequest` يطبع البريد بـstrip/casefold وحد 254؛ `Password` يقيد كلمة المرور الجديدة إلى 15–128؛ `OpaqueToken` يقيد action/refresh token بصيغة URL-safe. كلمة المرور الحالية 1–128 في `login/dto.py`. لا يزيل dots أو plus tags. |
| `users/shared/dto/primitives.py` | قواعد الاسم والهاتف E.164 والنصوص القصيرة. |
| `users/shared/dto/profile.py` | `UserResponse` و`user_response`؛ أدوار وصلاحيات دون تكرار، وprofile_complete محسوب من phone + default_address_id؛ timestamps بتوقيت UTC. |
| `users/shared/dto/address.py` | `AddressWriteRequest` و`AddressResponse` و`address_response`؛ حقول العنوان وحدود الإحداثيات وزوجها وحساب is_default من default_address_id. |
| `users/shared/dto/tokens.py` | حقول استجابة زوج التوكنات، مع ملف المستخدم. |
| `users/shared/dto/messages.py` | الاستجابة النصية العامة لعمليات البريد والتغيير. |
| `update_profile/dto.py` | name/phone فقط؛ يرفض body فارغًا وname=null، ويفرق بين phone الغائب وphone=null. |
| `oauth/start/dto.py` و`oauth/complete/dto.py` | challenge بصيغة 64 hex صغيرة؛ ticket بصيغة OpaqueToken بطول 32–512، وbinding_verifier بصيغة URL-safe بطول 43–128. |

## repositories وحدود التخزين

المكان `app/users/shared/repositories/`؛ كل ملف له كيان/مسؤولية تخزين واضحة. دوال add/delete تغير unit of work فقط، وخدمة العملية تقرر flush/commit. الواجهات في `users/shared/interfaces.py`، لذلك يمكن تبديل adapter مع الحفاظ على التوقيعات.

| الملف والكلاس | الدوال وما تقرأه أو تغيره |
| --- | --- |
| `users.py: SqlAlchemyUserRepository` | `get_by_id(user_id,for_update)` يقرأ users والأدوار والصلاحيات ويجدد بيانات identity map عند القفل؛ `get_by_email(email)` يقرأ البريد الفريد؛ `add(user)` يسجل إضافة. |
| `addresses.py: SqlAlchemyAddressRepository` | `get_owned(address_id,user_id)` يقرأ بعنوان ومالك معًا؛ `list_for_user(user_id)` يرتب بـcreated_at ثم id؛ `add/delete` يسجل إضافة/حذف دون commit. |
| `actions.py: SqlAlchemyActionTokenRepository` | `get_customer_role/get_type_id` يقرآن lookup ويرجعان 503 عند غياب seed؛ `find(hash,purpose,for_update)` يقرأ action token؛ `invalidate(user_id,purpose)` يستهلك السابق؛ `add(token)` يضيف. |
| `sessions.py: SqlAlchemySessionRepository` | `get(session_id,for_update)` يقرأ الجلسة؛ `add/add_refresh` يسجل جلسة أو refresh digest؛ `find_refresh(hash,for_update)` يبحث بالبصمة؛ `revoke_all(user_id)` يلغي الجلسات غير الملغاة. |
| `social.py: SqlAlchemySocialRepository` | `find_account/add_account` للهوية الخارجية؛ `add_state/get_state` لمحاولة OAuth مع قفل عند القراءة؛ `add_ticket/get_ticket` للتذكرة المرتبطة بالعميل وقفل اختياري. |

## تركيب الاعتمادات

| المكان | الدالة أو النمط | النتيجة |
| --- | --- | --- |
| `operation/dependencies.py` | `get_service(...)` | ينشئ service العملية ويحقن الأدوات المطلوبة لها فقط، بنفس DB session. |
| `users/shared/dependencies/repositories.py` | `get_user_repository/get_address_repository/get_action_repository/get_session_repository/get_social_repository` | adapters التخزين على نفس DB session. |
| `users/shared/dependencies/resources.py` | `get_password_hasher/get_dummy_hash/get_token_codec` | cached Argon2 adapter وhash وهمي وJWT codec، دون تنفيذ login أو إصدار جلسة. |
| `users/shared/dependencies/resources.py` | `get_rate_limiter/get_oauth_gateway/get_unit_of_work/get_email_sender` | موارد Redis وprovider وUnitOfWork وoutbox sender؛ JWKS cache يعاد استخدامه داخل العملية. |
| `users/shared/dependencies/services.py` | `get_email_actions/get_session_issuer/get_access_authenticator` | تركيب أدوات إجراءات البريد وإصدار الجلسة والتحقق من access token على واجهاتها المشتركة. |
| `app/dependencies.py` | `get_bearer_token(credentials)` | يستخرج Bearer header أو يرفع 401؛ لا يقبل query token. |
| `app/dependencies.py` | `get_current_user(token,service)` | يتحقق من JWT والجلسة عن طريق AccessAuthenticator ويرجع هوية مصادقًا عليها. |
| `app/dependencies.py` | `require_permission(permission)` ثم `check(user)` | dependency factory تراجع permission داخل roles الحالية وترجع user أو 403. |
| `app/dependencies.py` | `limit_api_requests(request)` | 120/IP/60s لكل مسارات `/api/v1`. |
| `app/dependencies.py` | `limit_auth_requests(request)` | 30/IP/900s لكل auth router، بالإضافة للحد العام. |
| `app/dependencies.py` | `limit_email_action(scope,email,limit)` | 5/email/900s افتراضيًا، و10 لمحاولات login. |

## الإعدادات والأمان والـworker

| الملف والدالة | المسؤولية |
| --- | --- |
| `core/config.py: get_settings()` | اختيار dotenv من APP_ENV، ثم cached Settings؛ متغيرات النظام تتقدم على الملف. |
| `Settings.validate_security_settings()` | فحص MySQL/Redis والأسرار وSMTP وURLs وCORS/Hosts وprovider completeness، وقيود production. |
| `core/api_docs.py: configure_swagger_docs(app)` | تسجيل صفحة Swagger وملف JavaScript المخصص عند تفعيل docs في البيئة. |
| `core/swagger_ui.js: FoodifySwaggerCurlPlugin` | عرض `Authorization: Bearer ACCESS_TOKEN_HERE` في أمر curl للمسار المحمي قبل إدخال التوكن، ثم القيمة الحقيقية بعد Authorize. القيمة التوضيحية تخص عرض المثال فقط ولا تُرسل مع الطلب. |
| `shared/tokens.py: generate_token()` / `hash_token(raw)` | توليد عشوائي آمن وبصمة SHA-256 للتوكنات العشوائية، دون اعتماد على HTTP أو JWT. |
| `Argon2PasswordHasher.hash/verify` | password hashing وفحص hash مع فشل آمن للـhash غير الصحيح. |
| `JwtTokenCodec.encode_access/decode_access` | إصدار JWT قصير العمر والتحقق من الخوارزمية والـclaims وإرجاع AccessClaims. |
| `infrastructure/database.py: get_engine()` | engine MySQL cached مع pool health/recycle وإخفاء parameters. |
| `get_session_factory()` | جلسات request بـautoflush=False وexpire_on_commit=False. |
| `get_db()` | yield session لكل request؛ rollback عند exception وإغلاق دائمًا. |
| `get_expected_revision_heads()` | قراءة migration heads المطلوبة لهذا الإصدار من الملفات، دون اتصال بقاعدة البيانات. |
| `check_database_readiness()` | مقارنة Alembic heads المطبقة على MySQL بما يتطلبه الإصدار؛ يرفض قاعدة غير مجهزة أو migration غير مكتمل. |
| `SqlAlchemyUnitOfWork.flush/commit/rollback` | تنفيذ حدود الـtransaction وتحويل IntegrityError إلى PersistenceConflict دون تسريب SQL للخدمات. |
| `infrastructure/models.py: new_id()` | UUID عشوائي للكيانات ذات ID نصي. |
| `OutboxEmailSender.send_action_email(...)` | تشفير snapshot الرسالة باستخدام Fernet وإضافته للـsession دون إرسال SMTP أو commit. |
| `SMTPEmailSender.send_action_email(...)` | إنشاء رسالة verify/reset برابط frontend fragment وإرسالها عبر SMTP مع timeouts وTLS حسب المرحلة. |
| `RedisRateLimiter.check(scope,key,limit,window)` | hash للهوية، عداد وTTL ذري بـLua؛ 429 مع انتظار، و503 إذا Redis غير متاح. |
| `RedisRateLimiter.close()` | غلق client pool عند الحاجة. |
| `SecurityMiddleware.__call__` | body limit، request ID، security headers وno-store؛ يتحقق من Content-Length ويحد streamed body. |
| `JsonTrustedHostMiddleware.__call__` و`_forward_valid_host` | تطبيق تحقق Starlette من Host وإرجاع error envelope عند الرفض، مع تمرير الطلبات المسموح بها. |
| `shared/errors.py: error_response(...)` | بناء error envelope موحد مع request_id. |
| `register_exception_handlers(app)` | handlers للأخطاء المتوقعة وvalidation وHTTP وSQLAlchemy والأخطاء غير المتوقعة؛ يحجب bodies والتفاصيل الداخلية. |
| `shared/time.py: utcnow()` | UTC naive مناسب لـMySQL DATETIME. |
| `worker.py: deliver_next_email()` | قفل مهمة مؤهلة بـSKIP LOCKED، فك التشفير، إرسال/إسقاط المنتهي ومسح payload؛ retries بحد 10 ثم تدخل المشغل. |
| `worker.py: main()` | loop مستقل يستجيب SIGTERM/SIGINT ويتوقف بأمان؛ ينتظر عند الفراغ أو فشل الاعتمادات. |
| `run.py: main()` | parsing للمرحلة وoverrides، منع reload خارج development، ثم Uvicorn factory؛ لا migrations/seed. |
| `main.py: create_app()` | إعداد FastAPI وhandlers وmiddleware وrouters؛ docs حسب البيئة. |
| `main.py: lifespan()` | إغلاق Redis client والتخلص من engine عند إيقاف التطبيق. |
| `main.py: liveness()` | `/health/live` يثبت حياة عملية HTTP فقط. |
| `main.py: readiness()` | `/health/ready` يفحص MySQL وتطابق migration heads وRedis؛ لا يفحص تسليم SMTP أو consent OAuth. |

معاملات `UnitOfWork.commit/flush/rollback` ينفذها adapter مستقل فوق SQLAlchemy Session؛ لا يوجد commit تلقائي على نهاية الـrequest. `RoleType/TokenTypeCode/SocialProvider` أسماء ثابتة للكود، بينما lookup tables والـseed تحفظ القيود والعلاقات.

## أوامر إدارة المخطط والبيانات المرجعية

| الدالة | المسؤولية |
| --- | --- |
| `migrations/env.py: run_migrations_offline()` | توليد MySQL DDL من revisions دون فتح اتصال. |
| `migrations/env.py: run_migrations_online()` | تطبيق revisions على قاعدة المرحلة المحددة صراحة. |
| `migrations/versions/...: upgrade()` | إنشاء 14 جدولًا وقيودها، ثم FK العنوان الافتراضي بعد إنشاء الجدولين. |
| `migrations/versions/...: downgrade()` | إزالة الجداول؛ أمر مدمر للبيانات ولا يعمل تلقائيًا. |
| `scripts.seed.seed_reference_data(session)` | تجهيز 5 أدوار و14 صلاحية و4 أنواع توكن والروابط الناقصة، وتحديث الأسماء المعرفة في الكود؛ دون إنشاء مستخدمين أو commit داخلي. |
| `scripts.seed.main()` | تحميل إعدادات المرحلة وفتح transaction للـseed وطباعة أعداد التغييرات فقط. |
| `scripts.cleanup.prune_retained_records(session,days_retention,apply)` | حساب المرشحين للحذف؛ حذفهم فقط عند apply، مع الحفاظ على تاريخ refresh للجلسات الحية. |
| `scripts.cleanup.main()` | قراءة retention و`--apply`؛ العرض فقط هو الافتراضي، وفتح transaction وعرض أعداد الصفوف. |

تفاصيل الاحتفاظ موجودة في [دليل migrations](../migrations/README.md). لم تنشأ أو تشغّل اختبارات ضمن إعادة التقسيم. لم يتطلب التعديل تنفيذ requests أو اتصالًا بقاعدة فعلية أو تسجيل دخول لدى مزود خارجي؛ المسارات وعقود الـAPI وقواعد البيانات محفوظة.
