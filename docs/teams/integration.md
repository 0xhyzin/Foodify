# تيم Integration — ربط الأجزاء ببعض

مسؤولية التيم ده إن الواجهة والباك يتفقوا على نفس المعنى ونفس صيغة البيانات، وإن رحلة المستخدم تفضل سليمة بين الصفحات والـAPI وخدمات الدفع. فتح request ناجح وحده مش كفاية؛ لازم نتيجته تتحول صح، والجلسة تفضل صحيحة، والسلوك وقت الفشل ما يكررّش الطلب أو الدفع.

## 1. بنستخدم إيه؟ وليه؟

| الأداة أو النمط | دورها |
|---|---|
| Repository Interface | يحدد المطلوب من الميزة من غير ربط JSX بتفاصيل HTTP. |
| HTTP Repository | ينفذ العقد الفعلي مع FastAPI ويحول البيانات. |
| DTO | يصف صيغة الشبكة بدقة، ويفصلها عن حالة الشاشة. |
| Mapper | يحول أسماء وأنواع حقول السيرفر لنموذج الواجهة. |
| FetchHttpClient | يجمع إعدادات الاتصال والـheaders والجلسة والأخطاء. |
| BrowserSessionManager | يمسك access token في الذاكرة ويجدد الجلسة من cookie. |
| OpenAPI | مرجع مولّد لمسارات FastAPI والمدخلات والمخرجات والأمان. |
| Postman | طلبات يدوية جاهزة لتجربة العقود والتشخيص. |
| pytest + TestClient | اختبار اتصال API بالخدمات والمستودعات وقاعدة معزولة. |
| Node test runner | اختبار وحدات الفرونت والـproxy وربط HTTP adapters. |

الـIntegration مش معناه وضع fetch في كل component. الربط مركزي ومنظم بحيث أي تغيير في صيغة السيرفر يتعالج في adapter وmapper مناسبين.

## 2. اتفقنا على عقد إيه؟

الـAPI تبدأ بـ`/api/v1`. بيانات عمليات Marketplace داخل envelope بالشكل `{ data: ... }`. بعض مسارات الحسابات ترجع نموذجًا مباشرًا مثل جلسة المتصفح؛ لذلك لا نفترض نفس envelope لكل endpoint.

| في استجابة الباك | في نموذج الفرونت | ليه التحويل؟ |
|---|---|---|
| `restaurant_id` | `restaurantId` | naming convention موحد للواجهة. |
| `menu_item_id` | `productId` | العرض يتعامل مع منتج بغض النظر عن اسم جدول الباك. |
| `delivery_fee` | `deliveryFee` | اسم مناسب لنماذج TypeScript. |
| `default_address_id` | `defaultAddressId` | تحديد العنوان الافتراضي من قيمة السيرفر. |
| `phone` | `phoneNumber` | نموذج مستقل عن DTO الباك. |
| `checkout_url`, `expires_at` | `url`, `expiresAt` | نتيجة Use Case بدء الدفع. |

المبالغ مثل `"45.25"` تظل strings في النقل ونماذج الأموال الحالية. الباك يحسبها باستخدام Decimal؛ تحويل أسعار التحصيل إلى أرقام JavaScript ثم إرجاعها كمرجع نهائي يسبب أخطاء تقريب، لذلك الباك يعيد الحساب بنفسه.

## 3. تركيب الخدمات وحقن الاعتمادات

`front/src/app/services.ts` هو Composition Root: ينشئ BrowserSessionManager، ثم FetchHttpClient، ثم HTTP repositories ويحقنها في Use Cases والـProviders.

```text
CheckoutPage
  → services.marketplace.orders
  → checkout use case
  → HttpOrderRepository
  → FetchHttpClient
  → POST /checkout
```

الـdomain يعرّف interfaces من غير React أو fetch. الـpresentation لا يقرأ ملفات secrets، والـinfrastructure هو المكان الوحيد الذي يعرف شكل request الفعلي.

## 4. الكتالوج الحقيقي في قاعدة البيانات

التسليم القديم كان ممكن يعرض داتا JS مستقلة عن السيرفر. اتوحد مصدر البيانات: الباك يزرع عينة الكتالوج في MySQL، والواجهة تستدعي `/restaurants` و`/catalog/categories` وقوائم المنتجات.

فتح قائمة متجر:

1. الصفحة تستخرج restaurant ID من route.
2. `HttpCatalogRepository` يقرأ بيانات المتجر والمنتجات مع pagination.
3. الـmapper يحول DTO إلى Merchant وProduct.
4. React يعرض الاسم والصورة والسعر وحالة التوفر.
5. انقطاع API يظهر loading/error/retry، ولا يعرض بيانات ثابتة بديلة.

وجود JSON seed في الباك مش معناه إن React بتقرأ JSON ده. هو مدخل لعملية مزامنة إلى MySQL، وبعدها القراءة دائمًا من API.

## 5. السلال: نفس المستخدم، أكثر من متجر

كل مسار للسلة يحتوي restaurant ID، والمستخدم يحدده access token. على سبيل المثال `/carts/A/items` و`/carts/B/items` عمليتان لسلتين مختلفتين.

الـIntegration يتأكد أن:

- كل Use Case يمرر ID المتجر الصحيح دون الاعتماد على آخر متجر اتفتح في الواجهة.
- تحديث كمية يرجع نسخة السلة الجديدة وrevision الحالي من السيرفر.
- الـUI لا يمسح بقية السلال بعد تحديث سلة واحدة.
- نتيجة request قديم لا تظهر لحساب آخر بعد logout أو تبديل الحساب.

حماية ملكية السلة موجودة في الباك حتى لو المستخدم كتب ID مختلفًا بيده خارج الواجهة.

## 6. مثال كامل: شراء وجبتين ببطاقة

افترض إن المستخدم أضاف صنفًا سعره `45.25` مرتين ورسوم توصيل `10.00`. الإجمالي المتوقع في الاستجابة `100.50`.

1. الفرونت يعرض السلة ويأخذ منها revision مثل `2`، ويطلب العناوين ووسائل الدفع.
2. العميل يختار عنوانًا محفوظًا و`card`.
3. الـUse Case يمرر للـrepository بيانات المتجر والعنوان والوسيلة وexpectedTotal وcartRevision ومفتاح idempotency ثابت لهذه المحاولة.
4. الـrepository يحولها إلى `restaurant_id`, `address_id`, `payment_method`, `expected_total`, `cart_revision` ويضع المفتاح في `Idempotency-Key`.
5. الباك يتحقق من الملكية والتوفر وrevision ويحسب `45.25 × 2 + 10.00` بنفسه.
6. الاستجابة ترجع order بحالة `awaiting_payment`. نجاح حفظ الطلب لا يعني نجاح الدفع.
7. الفرونت يستدعي `/orders/{id}/payment`. الباك ينشئ Paymob Intention أو يعيد جلسة قائمة صالحة.
8. الرابط وصلاحيته يمران على validator، ثم ينتقل المتصفح إلى Paymob لكتابة البطاقة هناك.
9. Paymob يرسل callback إلى الباك. بعد HMAC ومطابقة بيانات العملية، الباك يحفظ `paid` ويؤكد الطلب.
10. صفحة الطلب تقرأ الحالة من `/orders/{id}` وتعرضها. query string في عنوان الرجوع ليست مصدر حقيقة.

إعادة الضغط أو انقطاع رد checkout لا ينشئ طلبًا جديدًا بنفس المفتاح. أما timeout وقت إنشاء الدفع الخارجي فيحتاج تمييزًا: قد يكون المزود أنشأ الجلسة بالفعل، فلا نعيد الإنشاء تلقائيًا.

## 7. الأخطاء اللي اتعالجت في الربط

| المشكلة | سببها | الإصلاح |
|---|---|---|
| البريد يتأكد ثم يرجع المستخدم للدخول | المسار القديم يؤكد فقط من غير إصدار جلسة. | مسار browser confirmation يرجع جلسة؛ الفرونت يعتمدها ويكمل onboarding. |
| Google يرجع ومش لاقي جلسة OAuth | بدء الرحلة على localhost والرجوع على127 مع sessionStorage مختلفة. | توحيد أصل التطوير قبل بدء React، مع إبقاء verifier سريًا ومؤقتًا. |
| جلسة جديدة تمسحها استعادة قديمة | refresh متأخر يتعارض مع login/confirmation. | revision guards وتجنب refresh تلقائي في صفحات إصدار الجلسة. |
| العميل لا يصل لنموذج البطاقة | رفض تجهيز Paymob وغموض حالة الفشل أو صيغة البنود. | رابط Checkout صالح، تجميع بنود مطابق للإجمالي، وتصنيف الرفض الصريح مقابل النتيجة المجهولة. |
| Postman يرجع404 رغم صحة المسار في الكود | Sprint2 base_url فيها `/api/v1` بينما environment لا تحتويها. | base_url أصبحت أصل الباك فقط، والبادئة داخل كل طلب في المجموعتين. |
| الحالة المدفوعة قابلة للتزييف من رجوع المتصفح | الثقة في query parameter بدل السيرفر. | صفحة الرجوع تعرض الحالة المخزنة؛ تحديث الدفع يحتاج callback موثوقًا. |

## 8. الجلسة وCORS والـproxy

محليًا الواجهة على `127.0.0.1:5173` والباك على8000، فـOrigin مختلف بسبب المنفذ. إعداد CORS يسمح بالأصل المحدد وcredentials، والطلبات ترسل `credentials: include` حتى تصل refresh cookie.

في الإنتاج المتصفح يطلب `/api/v1` من نفس نطاق Vercel، و`api/proxy.mjs` ينقل الطلب إلى FastAPI Cloud. الوسيط يحافظ على Bearer وcookie وOrigin و`X-Foodify-Client` وIdempotency-Key، ويرجع Set-Cookie كما صدرت من الباك.

الوسيط يقبل مسارات API محددة الصيغة ولا يقبل وجهة backend من العميل. توقيع عنوان IP يتم بسر خادم مشترك حتى يقدر الباك يميز العنوان الذي مر عبر وسيط موثوق. ده لا يغني عن authentication أو rate limiting أو ownership.

## 9. تأكيد البريد وGoogle خطوة بخطوة

رموز التأكيد والتذاكر الخارجية تصل في fragment ثم تُنظَّف من عنوان الصفحة. صفحة تأكيد البريد تتطلب ضغطة صريحة حتى لا يستهلك ماسح روابط البريد الرمز بمجرد فتح GET.

عند نجاح تأكيد البريد أو OAuth:

```text
HTTP session DTO
  → validation + user mapper
  → BrowserSessionManager.accept()
  → SessionProvider.setUser()
  → accountDestination()
      لا موبايل → onboarding/profile
      لا عنوان افتراضي → onboarding/address
      البيانات مكتملة → account
```

الـrefresh token HttpOnly، والـaccess token في الذاكرة. لا نضع أيًا منهما في رابط العودة أو localStorage. OAuth verifier هو قيمة مؤقتة في sessionStorage لربط الرحلة بتبويبها، وليس بديلًا عن access token.

## 10. إيه اللي اتختبر؟

Integration الفرونت يركّب HTTP client الحقيقي والمستودعات والـmappers وإدارة الجلسة، مع محاكاة حد HTTP فقط. الباك Integration يمر من FastAPI routers والخدمات والمستودعات إلى SQLite معزولة. اختبارات الـproxy تفحص forwarding والكوكيز ومنع الوجهات الخاطئة دون الاتصال بخدمة حقيقية.

ده يختلف عن اختبار متصفح ← Vercel ← FastAPI Cloud ← Aiven ← Paymob حقيقي. النوع الأخير محتاج حسابات مزودين وإعدادات HTTPS ومفاتيح sandbox صحيحة، ومش نتيجة تلقائية لنجاح اختباراتنا المعزولة.

راجع [الاختبارات](testing.md) للأوامر والنتائج و[كل الحالات](test-catalog.md) للسيناريوهات الفردية.

## 11. تسليم التيم لباقي الفرق

- للفرونت: نماذج Domain ثابتة ورسائل خطأ عربية ومسارات جلسة موحدة.
- للباك: requests تطابق DTOs، ومفاتيح التكرار ومعرفات الموارد وصيغ المبالغ كما اتفقنا.
- للـDeployment: قائمة بالأصول والمسارات التي تحتاج rewrite وcookies وcallbacks ومتغيرات عامة مقابل أسرار خادم.
- للتستات: سيناريوهات نجاح وفشل وتكرار وتبديل حساب وفقد اتصال، بدل الاقتصار على happy path.

لو حد سأل «Integration عمل إيه غير إنه كتب fetch؟» الإجابة: ربط عقود البيانات والهوية والأموال وحالة الطلب بين الطرفين، وعالج التكرار والسباقات والأخطاء حتى تكمل رحلة المستخدم بدون فقد جلسة أو تكرار طلب.

## 12. عقود Sprint 3 بين البوابات الخمس والباك

في Sprint 3 تم توحيد DTOs وMappers وخطأ كل بوابة داخل `front/src/modules/orders/` و`front/src/modules/notifications/`:

| المسار (Backend API) | دور الواجهة والـ Adapter | ملاحظة العقد |
|---|---|---|
| `GET /admin/users` · `POST /admin/staff` · `PATCH /admin/users/{id}/roles` | `HttpOperationsRepository` (`StaffAccount`, `CreateStaffInput`, `UpdateUserRolesInput`) | ترجمة كود `cannot_demote_self` وربط `restaurant_id` عبر `restaurant_staff`. |
| `POST /operations/restaurants` · `PATCH` · `menu-items` · `staff` | `HttpOperationsRepository` (`AdminRestaurant`, `AdminMenuItem`, `StaffOption`) | نفس Envelope `{ data: ... }` والأسعار نصوص Decimal بلا تقريب. |
| `GET /kitchen/orders` · `PATCH /kitchen/orders/{id}/status` | `KitchenPage` + `HttpOperationsRepository` | ربط انتقال `confirmed -> preparing -> ready_for_pickup`. |
| `GET /delivery/couriers` · `POST/PATCH /orders/{id}/delivery-assignment` · `GET /delivery/my-orders` · `PATCH /delivery/orders/{id}/status` | `HttpDeliveryRepository` | إظهار `deliveryAddress` والهاتف في بوابة المندوب (`courier`) فقط. |
| `GET /notifications` · `PATCH /{id}/read` · `POST /read-all` | `HttpNotificationRepository` + `NotificationBell` | عرض عدد غير المقروء ورسائل الأحداث الـ12؛ التحقق بالعقد في `Foodify.Sprint3.postman_collection.json`. |
