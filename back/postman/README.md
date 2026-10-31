# استخدام Postman

استورد `Foodify.postman_collection.json` وملف البيئة المناسب: `development` أو `test` أو `production`. الـ collection يحتوي طلبات يدوية وأمثلة responses، بدون scripts أو assertions أو اختبارات. لا توجد أسرار فعلية داخل الملفات.

واجهة React لا تستخدم refresh token في body؛ هي تستخدم مسارات المتصفح المحمية (`/api/v1/auth/browser/*`) مع `X-Foodify-Client: web` وHttpOnly cookie. الـ collection الحالي يحافظ على مسارات JSON الأصلية للتشغيل اليدوي، لذلك استخدم الواجهة لتجربة جلسة المتصفح كاملة.

## الوصول لتنفيذ الطلب في الكود

كل طلب يقابله فولدر عملية داخل `app/users/`: **Login** في `login/`، **Register customer** في `register/`، و**Add delivery address** في `addresses/add_address/`. داخل كل فولدر DTO وواجهة خدمة وservice وdependency وrouter مستقلة. راجع [دليل الدوال](../docs/FUNCTIONS.md) لجدول يربط بقية طلبات Postman بالخدمات والبيانات المتأثرة. تجميع المسارات داخل `app/users/router.py` يحافظ على عناوين الطلبات وحقولها، لذلك لا يحتاج إعادة التقسيم تغيير متغيرات البيئة أو طريقة استخدام الـcollection.

## الإعداد

1. شغل MySQL وRedis والـ API والـ email worker ونفذ migration والـseed كما في [README](../README.md).
2. اختر البيئة في Postman واضبط `base_url`؛ الافتراضي development هو `http://localhost:8000` وtest هو `http://localhost:8001`. رابط production مثال يحتاج التعديل.
3. ضع `name` و`email` و`password` و`phone` محليًا. كلمة المرور الجديدة 15–128 حرفًا والرقم بصيغة E.164. استخدم بريدًا تملك الوصول إليه في البيئات التي ترسل بريدًا حقيقيًا.
4. احفظ كلمات المرور والتوكنات كقيم محلية خاصة. لا تصدر environment يحتويها ولا تشاركه مع الفريق. اختيار نوع `secret` يخفي العرض ولا يغني عن حماية ملف التصدير.

طلبات المصادقة العامة وhealth تضبط `noauth`. طلبات الملف والعناوين والخروج ترث Bearer auth من الـcollection باستخدام `{{access_token}}`.

## التسجيل والدخول

1. أرسل **Register customer** مرة واحدة. الرد `202` عام؛ لا يرجع user ID أو token تأكيد ولا يثبت وصول الرسالة.
2. افتح Mailpit في development على `http://localhost:8025` واقرأ رابط `/verify-email#token=...`. انسخ قيمة `token` فقط إلى `email_verification_token`، ثم أرسل **Verify email**. لا تحتاج صفحة frontend منفذة لنسخ القيمة يدويًا.
3. إذا انتهى الرابط أرسل **Resend email verification** واقرأ الرسالة الجديدة؛ الرابط الجديد يلغي السابق. تنفيذ resend اختياري وليس خطوة لازمة بعد كل register.
4. أرسل **Login** وانسخ `access_token` و`refresh_token` من الرد إلى متغيري البيئة بالاسم نفسه. لا يوجد script ينسخهما تلقائيًا.
5. أرسل **Get my profile** ثم **Update my profile** لإضافة الهاتف، و**Add delivery address** لإضافة عنوان. انسخ `id` من استجابة العنوان إلى `address_id` لباقي طلبات العناوين.

أول عنوان يصبح افتراضيًا. `PUT` يستبدل بيانات العنوان كاملة، و**Set default delivery address** يختار العنوان الموجود في `address_id`. حذف الافتراضي يختار أقدم عنوان متبقٍ أو يجعل الملف غير مكتمل عند حذف آخر عنوان.

## الجلسة والاسترجاع

- **Refresh session** يستقبل `refresh_token` في body. بعد النجاح انسخ **التوكنين الجديدين** فورًا؛ إعادة استخدام refresh قديم تلغي الجلسة المرتبطة به. نفذ refresh واحدًا في كل مرة.
- **Logout current session** يلغي الجلسة الحالية ويعيد `204` بلا body. **Logout all sessions** يلغي جلسات الحساب كلها. بعدها تحتاج login جديدًا.
- **Forgot password** يرسل رسالة فقط لحساب محلي نشط ومؤكد البريد. انسخ token من رابط `/reset-password#token=...` إلى `password_reset_token` واضبط `new_password`، ثم أرسل **Reset password**. بعد النجاح حدّث متغير `password` محليًا وادخل مجددًا؛ جميع الجلسات القديمة ألغيت.
- الحساب الذي أنشئ عبر OAuth بلا كلمة مرور يسترجع الوصول عبر مقدم الخدمة. الرد العام على forgot-password لا يغير هذه السياسة.

## Google وFacebook

اضبط credentials وcallback لدى المزود أولًا كما في [دليل OAuth](../docs/OAUTH.md). العملية تحتاج متصفحًا؛ لا يشغل Postman شاشة موافقة المستخدم نيابة عنه.

ولد verifier وchallenge محليًا بهذه الأداة القياسية، ثم انسخ القيم إلى `binding_verifier` و`binding_challenge`:

```bash
python - <<'PY'
import hashlib
import secrets
verifier = secrets.token_urlsafe(48)
print('binding_verifier:', verifier)
print('binding_challenge:', hashlib.sha256(verifier.encode()).hexdigest())
PY
```

1. أرسل **Start Google sign-in** أو **Start Facebook sign-in**، ثم افتح `authorization_url` في المتصفح.
2. أكمل موافقة المزود. سيرجع المتصفح إلى `FRONTEND_URL/oauth/callback#ticket=...`. يمكن نسخ ticket من شريط العنوان أثناء التطوير حتى إذا لم يوجد frontend يعمل على هذا العنوان.
3. ضع التذكرة في `oauth_ticket` وأرسل **Complete social sign-in** مع verifier الأصلي خلال دقيقتين. انسخ access وrefresh إلى متغيرات البيئة.
4. عند ظهور `#error=email_verification_required` اقرأ رسالة التأكيد وأرسل **Verify email**، ثم ابدأ تدفق OAuth جديدًا. Facebook لا يعتبر البريد مؤكدًا محليًا بمجرد أن المزود أرجعه.

طلب **Callback reference — browser/provider only** للتوثيق؛ لا ترسله بعد أن نفذه المتصفح، لأن state والكود يستخدمان مرة واحدة. `oauth_state` و`authorization_code` متغيران مرجعيان فقط. لا تستخدم كودًا أو ticket من محاولة مع verifier محاولة أخرى.

## الأخطاء والأمثلة

الـ saved responses أمثلة للعرض وليست نتائج تنفيذ فعلي. راجع [دليل الدوال](../docs/FUNCTIONS.md) لتفاصيل كل مسار. `422` يعني مراجعة حقول body، و`401` يعني حاجة لمصادقة صالحة، و`403` بريد غير مؤكد أو permission ناقصة، و`429` يتطلب الانتظار وفق `Retry-After`، و`503` يعني مراجعة الخدمات والإعدادات. لا يشغل استيراد الـcollection أي request تلقائيًا.


## Sprint 2

استورد [Foodify.Sprint2.postman_collection.json](Foodify.Sprint2.postman_collection.json) لطلبات المطاعم وإنشاء السلة وإدارتها والعناوين والطلبات اليدوية. لا توجد scripts أو tests. إعدادات وصلاحيات Checkout والمحاكاة موضحة في [SPRINT_2.md](../docs/SPRINT_2.md).
