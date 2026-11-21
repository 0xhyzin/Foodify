# شرح Integration — Sprint 2

الملف ده يشرح الربط الموجود في الكود بين React وFastAPI وMySQL: المستخدم يختار متجرًا ومنتجات، يعدّل سلته، يختار عنوانه وطريقة الدفع، ثم يتابع الطلب. الواجهة تعرض بيانات السيرفر؛ حساب السعر والصلاحيات وتأكيد الدفع مسؤولية الباك.

ده توثيق للتنفيذ، وليس إثباتًا أن حسابات مزودي OAuth والدفع والبريد مضبوطة في كل بيئة. نتيجة التشغيل والاختبارات وحدودها في [سجل المراجعة النهائية](SPRINT_2_VERIFICATION.md).

## 1. الأجزاء بتتواصل إزاي؟

```text
React Page / Component
  → Application Use Case
  → Domain Repository Interface
  → HTTP Repository + DTO Mapper
  → FetchHttpClient
  → FastAPI Router → Service → Repository / Payment Gateway
  → MySQL أو الخدمة الخارجية
  ← Response DTO ← Domain Model ← React State
```

داخل `front/src/app/services.ts` يتم تركيب التطبيقات الفعلية وحقنها في الـproviders. الـcomponents لا تحتوي SQL أو مفاتيح Paymob، ومستودعات HTTP هي المسؤولة عن صيغة الطلبات وتحويل `snake_case` إلى `camelCase`.

في التطوير المتصفح يتصل مباشرة بـ`http://127.0.0.1:8000/api/v1`. في الإنتاج يستخدم `/api/v1` على نفس نطاق الواجهة، وملف `api/proxy.mjs` يمرر الطلب إلى FastAPI Cloud. راجع [شرح Deployment للسبرنت](SPRINT_2_DEPLOYMENT.md) لإعداد البيئة.

## 2. الحساب والجلسة قبل الطلب

Sprint 2 يعيد استخدام نظام الحسابات والعناوين من Sprint 1. مسار المستخدم الجديد:

1. `POST /auth/register` يحفظ التسجيل ويجهّز رسالة التأكيد؛ لا يصدر جلسة تسجيل دخول.
2. رابط الرسالة يفتح `/verify-email#token=...`. الـbootstrap يحوله إلى مسار HashRouter، ثم يمسح الرمز من عنوان الصفحة ويحفظه في ذاكرة النموذج.
3. الضغط على «تأكيد البريد ومتابعة بياناتي» يستدعي `POST /auth/browser/verify-email`.
4. الباك يؤكد البريد ويستهلك الرمز ويصدر الجلسة في transaction واحدة. لو فشل إنشاء الجلسة يحصل rollback.
5. الفرونت يعتمد الجلسة ثم يفتح استكمال الملف إذا كان الموبايل ناقصًا، وبعده عنوان التوصيل إذا لم يوجد عنوان افتراضي. الحساب المكتمل يفتح صفحة الحساب.

الـaccess token في الذاكرة فقط. الـrefresh token داخل HttpOnly cookie، ولا يرجع ضمن JSON لمسارات المتصفح. الطلبات المحمية تستخدم `Authorization: Bearer <ACCESS_TOKEN>`، والـHTTP client يضيف الهيدر تلقائيًا.

`BrowserSessionManager` يجمع طلبات refresh المتزامنة في طلب واحد. عند `401` يحاول `FetchHttpClient` تجديد الجلسة وإعادة الطلب مرة واحدة، مع منع إعادة طلب حساب قديم باستخدام جلسة حساب آخر. مسارات إنشاء الجلسة الخاصة بتأكيد البريد وOAuth لا تبدأ refresh تلقائيًا أثناء التحميل.

Google وFacebook يبدآن عبر `/auth/oauth/{provider}/start`. المتصفح يحتفظ بـbinding verifier في sessionStorage مؤقتًا، والباك يرجع ticket للاستخدام مرة واحدة إلى `/oauth/callback`. الفرونت يستبدلها بجلسة عبر `/auth/browser/oauth/complete` ثم يفتح استكمال البيانات. لا يتم ربط حساب قائم لمجرد تطابق البريد.

محليًا افتح `http://127.0.0.1:5173`؛ التحويل من `localhost:5173` يحدث قبل تشغيل React لأن sessionStorage مرتبطة بالأصل الذي بدأت منه رحلة OAuth. الـcallback المسجّل عند المزود يطابق إعداد الباك حرفيًا؛ قد يكون `localhost:8000`، وده منفصل عن أصل الفرونت.

## 3. الكتالوج والبحث

`HttpCatalogRepository` يقرأ بيانات المتاجر والفئات والمنتجات من API، والـmappers يحولونها إلى نماذج العرض. بيانات الـseed موجودة في `back/app/ordering/data/` وتدخل MySQL بأمر backend؛ React لا يستورد ملف الـseed.

| العملية | الطلب بعد `/api/v1` | الاستخدام |
|---|---|---|
| المتاجر | `GET /restaurants` | بحث، نوع متجر، تصنيف، ترتيب، رسوم ووقت التوصيل، pagination. |
| تفاصيل متجر | `GET /restaurants/{restaurant_id}` | معلومات المتجر قبل عرض قائمته. |
| فئات عامة | `GET /catalog/categories` | الفئات أعلى Marketplace. |
| فئات متجر | `GET /restaurants/{restaurant_id}/categories` | فئات قائمة متجر معين. |
| المنتجات | `GET /restaurants/{restaurant_id}/menu` | قائمة المنتجات وأسعارها وتوفرها. |
| المفضلة | `GET /users/me/favorites` | مفضلة المستخدم المسجل. |
| تغيير المفضلة | `PUT /users/me/favorites/{restaurant_id}` | حفظ الحالة المطلوبة دون تكرار سجلات الربط. |

الكتالوج العام لا يحتاج جلسة. المفضلة تحتاج جلسة. عند فشل API تظهر رسالة خطأ؛ لا يتم عرض كتالوج JS بديل. `VITE_DATA_SOURCE` يقبل `api` فقط. أسعار عينة الكتالوج والتقييمات ووقت التوصيل بيانات تجريبية، وليست تحديثًا حيًا من الشركات.

## 4. سلة مستقلة لكل متجر

مفتاح السلة المنطقي هو `(user_id, restaurant_id)` وعليه unique constraint. لذلك إضافة منتج من متجر جديد لا تمسح منتجات المتجر السابق. الطلب الواحد يخص متجرًا واحدًا، وكل متجر له checkout ورسوم ودفع مستقل.

| العملية | الطلب | البيانات |
|---|---|---|
| كل السلال غير الفارغة | `GET /carts` | pagination. |
| سلة متجر | `GET /carts/{restaurant_id}` | الباك يستمد المستخدم من الجلسة. |
| إنشاء/إحضار سلة | `POST /carts/{restaurant_id}` | لا يرسل `user_id`. |
| إضافة صنف | `POST /carts/{restaurant_id}/items` | `menu_item_id`, `quantity`. |
| تعيين كمية | `PATCH /carts/{restaurant_id}/items/{cart_item_id}` | `quantity`. |
| حذف صنف | `DELETE /carts/{restaurant_id}/items/{cart_item_id}` | الصنف والسلة يجب أن يكونا للمستخدم. |
| تفريغ سلة متجر | `DELETE /carts/{restaurant_id}` | لا يفرغ سلال المتاجر الأخرى. |

كل استجابة ترجع نسخة السلة وأسعارها و`revision`. الكميات أعداد صحيحة من 1 إلى 99. الباك يتحقق من أن المنتج تابع لنفس المتجر ومتاح. قيمة `total` المعروضة تأتي من حساب السيرفر، ويستخدم الباك `Decimal` للأموال.

في React يتم تجاهل نتائج الطلبات القديمة بعد تبديل الحساب، وإلغاء الطلبات عند مغادرة الصفحة عند توفر AbortSignal. تغيير بيانات سلة متجر يحدث تحديثًا لحالتها بدل حذف بقية السلال.

## 5. اختيار العنوان وإرسال الطلب

صفحة Checkout تعرض السلة وعناوين المستخدم وطرق الدفع المفعّلة. العناوين تتعامل مع مسارات `/users/me/addresses` الحالية؛ لا توجد نسخة ثانية من دفتر العناوين للسبرنت.

```http
POST /api/v1/checkout
Authorization: Bearer <ACCESS_TOKEN>
Idempotency-Key: <UNIQUE_KEY_FOR_THIS_CHECKOUT>
Content-Type: application/json
```

جسم الطلب يحتوي `restaurant_id`, `address_id`, `payment_method`, `expected_total`, `cart_revision`. لا يرسل الفرونت أسماء الأصناف وأسعارها لإجبار الباك على استخدامها.

الخدمة تنفّذ الآتي:

1. تقفل بيانات المستخدم والسلة أثناء المعاملة لمنع تعارض التحديثات.
2. تبحث عن طلب سابق بنفس `Idempotency-Key`. نفس المفتاح ونفس المدخلات يرجعان نفس الطلب؛ تغيير المدخلات مع إعادة المفتاح يرجع `409`.
3. تراجع أن السلة غير فارغة و`cart_revision` ما زالت مطابقة.
4. تقرأ الأسعار الحالية وتوفر المنتجات، وتتأكد أن العنوان مملوك للمستخدم.
5. تعيد حساب الإجمالي. اختلاف السعر عن `expected_total` يرجع `cart_price_changed` بدل تحصيل مبلغ مختلف دون مراجعة.
6. تحفظ الطلب وبنوده ونسخة عنوان التوصيل وطريقة الدفع وسجل الحدث الأول في transaction واحدة.

تُحفظ نسخة من أسماء المنتجات وأسعارها والعنوان وقت الطلب، حتى لا تتغير الفاتورة التاريخية بعد تعديل المنتج أو حذف العنوان. ده تكرار مقصود لتاريخ الطلب، بينما الكتالوج ودفتر العناوين يظلان جداول مستقلة.

## 6. رحلة Paymob كاملة

```text
اختيار بطاقة / محفظة
  → POST /checkout
  → الطلب awaiting_payment والسلة موجودة
  → POST /orders/{id}/payment
  → الباك ينشئ Paymob Intention
  → يرجع checkout_url + expires_at
  → الفرونت يراجع الرابط وينتقل لصفحة Paymob
  → العميل يدخل بيانات الدفع عند Paymob
  → Paymob يرسل callback إلى الباك
  → الباك يتحقق من HMAC والمبلغ والعملة والتكامل والطلب
  → يحفظ حالة الدفع ويؤكد الطلب
  → الفرونت يقرأ الحالة من GET /orders/{id}
```

بيانات البطاقة لا تمر عبر React أو قاعدة Foodify. الرابط الحالي `https://eg.checkout.paymob.com/`، والفرونت يقبل أيضًا المسار القديم المحدد للتوافق. يتحقق من HTTPS والمضيف والمسار ووجود `publicKey` و`clientSecret` مرة واحدة وصلاحية الرابط. إذا تعذر الانتقال التلقائي بعد نجاح التجهيز، يظهر رابط مباشر للبوابة.

أسرار Paymob وIntegration IDs موجودة في الباك فقط. إجمالي بنود Intention ورسوم التوصيل يجب أن يساوي إجمالي الطلب بالسنت؛ العدد الفعلي وسعر الوحدة يظهران في وصف كل سطر. تفاصيل الإصلاح في [شرح فتح بوابة الدفع](PAYMENT_CHECKOUT_FIX.md).

| الحالة | سلوك التكامل |
|---|---|
| `initializing` | التجهيز بدأ؛ لا ينشئ طلبًا خارجيًا ثانيًا بالتوازي. |
| `pending` مع رابط صالح | يعيد استخدام نفس جلسة الدفع المخزنة. |
| `payment_setup_rejected` | رفض صريح من المزود؛ تظهر رسالة آمنة، والمحاولة التالية تحتاج مراجعة السبب. |
| `initialization_unknown` | النتيجة الخارجية غير محسومة؛ يمنع تكرار إنشاء Intention تلقائيًا ويلزم التحقق لدى المزود. |
| رابط منتهي | يرجع `payment_expired` ويطلب مراجعة السلة وطلبًا جديدًا. |
| `paid` | لا يُسجَّل بمجرد redirect أو query parameter؛ يعتمد على callback موثوق. |

`POST /payments/paymob/callback` مخصص للمزود. `GET /payments/return/{order_id}` يعيد المتصفح لصفحة الطلب ويتجاهل نجاح/فشل query string. الـcallback يعالج التكرار دون تسجيل دفع جديد، ويرفض اختلاف المبلغ أو العملة أو Integration ID.

تأكيد الدفع يفرغ سلة الطلب فقط إذا كانت ما زالت بنفس revision؛ لو المستخدم أضاف منتجات جديدة أثناء الدفع، لا تُحذف تعديلاته. localhost لا يستقبل callback من الإنترنت؛ إكمال رحلة sandbox من المزود يحتاج عنوان HTTPS يمكنه الوصول إليه.

## 7. باقي طرق الدفع

- **Vodafone Cash / Orange Cash:** محافظ عبر Paymob عند تفعيل Wallet Integration؛ ليست تحويلًا يدويًا لرقم شخصي.
- **InstaPay:** تحويل يدوي إلى مستلم مضبوط في الباك. العميل يرسل reference عبر `/orders/{id}/transfer-claim`، ثم موظف مخول يراجع `/operations/orders/{id}/transfer-review`. إرسال reference لا يعني أن الطلب مدفوع.
- **Cash:** الطلب يبدأ `placed` والدفع `due_on_delivery`. عند الوصول لحالة `delivered` يُسجَّل الدفع النقدي كمدفوع.
- **Simulated/Sandbox المحلي:** محاكاة برمجية تقتصر على development/test إذا تم تفعيلها. ليست نفس إجراء Paymob Sandbox الخارجي، ولا إثبات تحصيل مالي.

الواجهة تعرض القيم التي يرجعها `GET /payments/methods`، وتعطل الوسيلة غير المفعلة بدل افتراض إعدادها.

## 8. سجل الطلبات والتتبع والإدارة

| العملية | المسار |
|---|---|
| سجل العميل | `GET /orders` |
| تفاصيل طلب | `GET /orders/{order_id}` |
| قائمة طلبات متجر للعمليات | `GET /restaurant/orders?restaurant_id=...` |
| تحديث مرحلة الطلب | `PATCH /operations/orders/{order_id}/status` |

العميل يقرأ طلباته فقط. مسارات العمليات تحتاج صلاحيات من الباك؛ إخفاء الزر في React ليس وسيلة الحماية. صلاحيات التشغيل الحالية عامة حسب permissions وليست نموذج staff-membership مستقلًا لكل مطعم.

التسلسل الحالي: `placed → preparing → ready → out_for_delivery → delivered`. لا يسمح الباك بالقفز بين المراحل أو بدء التحضير قبل تأكيد الدفع، باستثناء قواعد cash والمحاكاة. كل تغيير يحفظ event. صفحة التتبع تعرض أحداث السيرفر وتحدّث الحالة دوريًا؛ لا يوجد GPS حي أو موقع مندوب مصطنع.

## 9. التعامل مع الأخطاء والأمان

الباك يرجع envelope يحتوي `error.code`, `message`, `details`, `request_id`. `api-error.ts` يحول الأكواد إلى رسائل عربية آمنة ويحتفظ بمعرّف الطلب و`Retry-After` للتشخيص. لا تعرض الواجهة نص رد مزود الدفع أو الأسرار للمستخدم.

- `401`: تجديد جلسة مرة واحدة عند الملاءمة، ثم طلب الدخول.
- `403`: المستخدم لا يملك الصلاحية؛ لا تُكرَّر العملية ببيانات دور مرسلة من العميل.
- `404`: عنصر غير موجود أو ليس مملوكًا للمستخدم؛ لا تكشف بيانات حساب آخر.
- `409`: راجع السلة/السعر/مفتاح التكرار/حالة الطلب قبل إعادة الإرسال.
- `422`: أخطاء بيانات تربط بالحقول المناسبة.
- `429`: احترام وقت الانتظار، دون retry تلقائي لعملية دفع.
- `5xx` أو انقطاع الشبكة: إظهار إمكانية المحاولة حسب نوع العملية؛ إنشاء الدفع غير المحسوم لا يُعاد تلقائيًا.

الـproxy يمرر headers محددة فقط ويحافظ على cookies وIdempotency-Key، ويمنع تعديل عنوان الباك من المتصفح، ويحد حجم body، ولا يخزن استجابات الحساب أو يمرر redirects عشوائية. مسارات browser في الباك تفحص Origin وهيدر `X-Foodify-Client: web`. CORS وCSP جزء من الإعداد، بجانب التحقق من الهوية والملكية داخل كل خدمة.

## 10. أماكن التنفيذ والقراءة التالية

| الملف أو المجلد | دوره |
|---|---|
| `front/src/app/services.ts` | تركيب الخدمات وحقن HTTP adapters. |
| `front/src/infrastructure/http/` | HTTP client، الجلسة، وقراءة الأخطاء. |
| `front/src/features/marketplace/infrastructure/` | API repositories وDTO mapping للكتالوج والسلال والطلبات والدفع. |
| `front/src/features/marketplace/application/` | Use cases مستقلة عن JSX. |
| `back/app/{cart,checkout,orders,payments}/` | العمليات وقواعدها وعقودها. |
| `back/app/ordering/` | الجداول والمستودعات والقواعد المشتركة. |
| `api/proxy.mjs` | نقل طلبات Vercel إلى FastAPI. |
| `back/postman/Foodify.Sprint2.postman_collection.json` | تجربة العقود يدويًا من Postman؛ الاختبارات الآلية منفصلة. |

في مجموعتي Postman وملفات environments، `base_url` هو أصل الباك فقط مثل `http://localhost:8000` دون `/api/v1`. الطلبات نفسها تضيف البادئة؛ توحيد ذلك يمنع `404` عند استخدام نفس environment للحساب والسبرنت. مجموعة الحسابات تشمل مجلد `Browser sessions` لطلبات التأكيد والدخول والـrefresh والـlogout وOAuth الخاصة بواجهة React؛ اضبط `frontend_origin` على أصل الواجهة المسموح في الباك.

- [Backend Sprint 2 — English](../back/README_SPRINT_2.md).
- [شرح Frontend بالعربي](../front/README_SPRINT_2.md).
- [Deployment بالعربي](SPRINT_2_DEPLOYMENT.md).
- [نتائج الاختبارات والمراجعة](SPRINT_2_VERIFICATION.md).
- [تفاصيل تكامل الحساب والعناوين](../front/docs/INTEGRATION.md).
