# Foodify — Sprint 2: Backend + Frontend Integration

الملف ده يشرح التنفيذ الحالي للسبرنت الثاني بعد مراجعة شغل الباك إند واعتماد تصميم الـUI/UX. المشروع الأساسي فيه `front/` لـReact و`back/` لـFastAPI، والداتابيز **MySQL**.

**حالة التسليم:** الكود والـmigration والربط موجودة محليًا. لم تُطبّق migration الكتالوج أو تُزرع البيانات؛ عنوان MySQL المحفوظ حاليًا يرجع NXDOMAIN من DNS العام، لذلك لم يتم الاتصال أو تغيير القاعدة. لم تُنشر هذه التعديلات بعد. لم تُكتب أو تُشغّل test suites بناءً على طلب صاحب المشروع.

## 1. إيه اللي اتعمل في Sprint 2؟

| الجزء | التنفيذ |
| --- | --- |
| Marketplace | مطاعم، حلويات وقهوة، وبقالة؛ أقسام رئيسية، بحث باسم المتجر أو المنتج، ترتيب بالتقييم/السرعة/رسوم التوصيل، توصيل مجاني، وحد أقصى لوقت التوصيل. |
| كتالوج المطاعم | ملف seed يزامن 8 متاجر و24 منتجًا وفئات المطاعم والحلويات والبقالة إلى MySQL؛ الواجهة تقرأها من API فقط. لم تُشغّل المزامنة على قاعدة الإنتاج بعد بسبب مشكلة عنوان الاتصال الموضحة أدناه. |
| Favorite stores | المفضلة محفوظة لكل مستخدم في bridge table، والإضافة/الإزالة idempotent. |
| Independent carts | سلة مستقلة لكل مستخدم ولكل متجر. فتح متجر آخر لا يمسح السلة السابقة. كل سلة لها رسومها وطلبها ودفعها. |
| Cart management | إضافة، زيادة/تعيين الكمية، حذف صنف، إفراغ سلة واحدة بعد التأكيد، وقراءة كل السلال غير الفارغة. |
| Checkout | عنوان مملوك للمستخدم، متجر واحد، أصناف متاحة، مراجعة الأسعار ونسخة السلة، وحفظ الطلب دون قبول مبلغ يحدده العميل كقيمة تحصيل. |
| Payments | Paymob Hosted Checkout للبطاقة ومحافظ فودافون/أورانج المفعلة في الحساب؛ InstaPay بتحويل يدوي ومراجعة مخولة؛ cash عند الاستلام؛ simulation في development/test فقط. |
| Orders | ملخص الطلب، حالة الدفع، تفاصيل عنوان التوصيل، سجل الطلبات، تفاصيل طلب محدد وملخص قابل للطباعة. |
| Tracking | سجل أحداث محفوظ في MySQL، ومراحل تحضير/تجهيز/خروج للتوصيل/تسليم يغيّرها موظف مخول. لا توجد حركة مندوب أو GPS وهمية. |
| Operations | شاشة React وقائمة API لطلبات متجر، تحديث المرحلة بالتسلسل، ومراجعة التحويلات. |
| Documentation | الملف ده، Postman، migrations حتى 0005، SQL schema وERD، وشرح أدوات التطوير. |

إدارة العناوين وتسجيل الدخول والجلسة كانت موجودة من Sprint 1 وأعيد استخدامها؛ لم يتم عمل نظام حسابات موازٍ.

## 2. المشاكل اللي اتصلحت

مراجعة تسليم الباك الأصلي موثقة في [SPRINT_2_REVIEW.md](docs/SPRINT_2_REVIEW.md). المراجعة الأولى فصلت SQL عن الـrouters، وضبطت ownership والصلاحيات وحساب الأموال والتزامن ونسخة عنوان الطلب، وميّزت الدفع التجريبي عن التحصيل الحقيقي.

بعد اعتماد واجهة Marketplace، اتصلحت النقاط التالية:

1. القيد القديم كان `UNIQUE(user_id)`؛ اتبدل بـ`UNIQUE(user_id, restaurant_id)`. اتلغى سلوك إجبار العميل يمسح سلة المطعم الأول قبل دخول التاني.
2. المسارات القديمة `/cart` ما كانتش تحدد متجرًا. المسارات الحالية بتحدد `restaurant_id`، مع قائمة `/carts` لكل السلال.
3. الفرونت كان يقرأ قائمة JS محلية. دلوقتي يقرأ بيانات المتاجر والمنتجات من HTTP repositories فقط؛ إعداد Vite يرفض وضع الديمو، وفشل API يظهر للمستخدم بدل إظهار بيانات محلية.
4. Checkout القديم كان محاكاة فقط ويفرغ السلة فورًا. الطلب الإلكتروني الآن يبدأ `awaiting_payment`، ويحتفظ بالسلة إلى أن يصل تأكيد دفع موثوق.
5. تكرار الضغط أو إعادة المحاولة يستخدم نفس `Idempotency-Key`. مفتاح الطلب مربوط بالمتجر والعنوان والوسيلة والمبلغ المُراجع و`cart_revision`.
6. لو السعر أو الكمية اتغيروا قبل الإرسال، الباك يرفض بـ409 ويطلب مراجعة السلة. سعر التحصيل النهائي دائمًا من MySQL وبـ`Decimal`.
7. إشعار نجاح في query string أو ضغطة زر من العميل لا يسجل الطلب كمدفوع. Paymob يحتاج HMAC صحيحًا ومطابقة بيانات العملية، وInstaPay يحتاج مراجعة فعلية من موظف عنده `payments:review`.
8. التتبع بقى بيانات من السيرفر. العميل لا يستطيع نقل الطلب للمرحلة التالية.
9. بيانات السلال المعروضة في React تتنظف عند تغير الحساب، ونتيجة request قديم لا تُعرض لحساب آخر.
10. خطأ أو timeout أثناء إنشاء Paymob intention لا يؤدي تلقائيًا لإنشاء عملية أخرى قد تسبب تحصيلًا مكررًا؛ الحالة تصبح بحاجة للمراجعة.

## 3. المعمارية وتقسيم الكود

### Backend: operation-based clean architecture

```text
back/app/
  restaurants/
    list_restaurants/  get_restaurant/  list_categories/  list_menu/
    browse_categories/  list_favorites/  set_favorite/
  cart/
    create_cart/  get_cart/  list_carts/
    add_item/  update_item/  remove_item/  clear_cart/
  checkout/submit_order/
  orders/
    list_orders/  get_order/  list_restaurant_orders/  update_status/
  payments/
    list_methods/  start_payment/  process_callback/
    claim_transfer/  review_transfer/
    infrastructure/paymob.py
    shared/
  ordering/
    models.py
    infrastructure/  # SQLAlchemy repositories + payment-method configuration
    shared/          # DTO views, ports, money rules, mapping and cart guards
```

كل operation لها `dto.py` و`interfaces.py` و`service.py` و`dependencies.py` و`router.py`:

| الملف | مسؤوليته |
| --- | --- |
| `router.py` | HTTP، Authentication/Permission، ونوع الاستجابة. |
| `dto.py` | شكل المدخلات والمخرجات وقيودها. العقود المشتركة يعاد استخدامها بدل نسخها. |
| `interfaces.py` | Protocol للخدمة، بحيث الـrouter لا يعتمد على class تنفيذية مباشرة. |
| `service.py` | use case واحدة؛ تحقق business rules ثم تستدعي repository/gateway ports. |
| `dependencies.py` | تركيب الخدمة واعتمادياتها عن طريق `Depends`. |
| Repository adapter | SQL وloading/locking فقط. |
| `UnitOfWork` | `flush` و`commit` و`rollback`؛ حدود المعاملة واضحة في الخدمة. |

`execute()` اسم موحد داخل خدمة عملية واحدة؛ اسم الفولدر والكلاس، مثل `CheckoutService` أو `ProcessCallbackService`، يحدد الفعل. الدوال المساعدة لها أسماء توضّح وظيفتها مثل `lock_owned_order` و`confirm_paid_order`.

### Frontend: component-based architecture

```text
front/src/features/marketplace/
  domain/
    models.ts
    catalog-repository.ts  cart-repository.ts
    order-repository.ts    payment-repository.ts
    money.ts
  application/
    services.ts
    checkout/use-case.ts
    update-quantity/use-case.ts
    start-payment/use-case.ts
  infrastructure/
    http-*-repository.ts
    dto.ts  mappers.ts  composition.ts
  presentation/
    marketplace-provider.tsx
    marketplace-layout.tsx
    hooks/use-resource.ts  hooks/use-order.ts
    components/
    pages/
    marketplace.css
```

- `front/src/app/services.ts` هو composition root للواجهة؛ يحقن مستودعات HTTP فقط. لا توجد مستودعات Demo للكتالوج.
- المكونات لا تعمل `fetch` مباشرة. الربط موجود في HTTP adapters، باستخدام `FetchHttpClient` الحالي.
- تم نقل `SessionProvider` ليغطي الموقع والحساب معًا، بدل جلسة منفصلة لكل جزء.
- `MarketplaceProvider` يحتفظ بالسلال والمفضلة المعروضة للحساب الحالي، ويعزل نتائج الطلبات القديمة بعد تبديل الحساب.
- مكونات قابلة لإعادة الاستخدام: `MerchantCard`, `ProductCard`, `CartPanel`, `MerchantLogo`, `FoodPhoto`, `OrderSummary`, `OrderTimeline`, `OperationalOrder`.
- صفحات checkout/history/tracking/operations محملة بـ`lazy` و`Suspense` لتقليل كود البداية.
- الـRTL، الهاتف، labels، keyboard focus، empty/error/loading states وreduced motion موجودة في الواجهة.

## 4. قاعدة البيانات والعلاقات

| العلاقة | التمثيل |
| --- | --- |
| User → Carts | One-to-many؛ سلة لكل متجر، بقيد مركب للمستخدم والمتجر. |
| Restaurant → Carts | One-to-many. المستخدم والمتجر يرتبطان عبر Cart ذات البيانات الخاصة بها. |
| Cart → CartItems | One-to-many؛ لا يتكرر المنتج داخل السلة بسبب `(cart_id, menu_item_id)`. |
| Restaurant → MenuItems | One-to-many؛ لا يسمح بإضافة منتج متجر داخل سلة متجر آخر. |
| Restaurant ↔ BrowseCategory | Many-to-many عبر `restaurant_categories`. |
| User ↔ FavoriteRestaurant | Many-to-many عبر `favorite_restaurants`. |
| User/Restaurant → FoodOrders | One-to-many. الطلب مرتبط بمتجر واحد. |
| FoodOrder → FoodOrderItems | One-to-many. |
| FoodOrder → Payment | سجل دورة دفع واحد؛ Paymob intention واحدة يعاد فتح رابطها ما دامت صالحة. |
| Payment → PaymentEvents | One-to-many؛ event ID يمنع تطبيق callback مكرر. |
| FoodOrder → OrderEvents | One-to-many؛ مرحلة وتوقيت وملاحظة ومن نفذ التغيير. |

الـrole/permission bridges السابقة مستمرة كما هي. عناوين المستخدم والـmenu الحالي مصدر البيانات التشغيلية. **اسم وسعر صنف الطلب وعنوان التوصيل محفوظون كـhistorical snapshot عمدًا**، بحيث تعديل المنيو أو حذف عنوان لاحقًا لا يغيّر طلبًا قديمًا؛ ده ليس تكرارًا غير مقصود.

التفاصيل في [SPRINT_2_SCHEMA.md](docs/SPRINT_2_SCHEMA.md)، والـmigration الخاصة بالدفع والسلال [0004](migrations/versions/20261031_0004_marketplace_payments.py) وتوسعة رابط الصورة [0005](migrations/versions/20261031_0005_catalog_image_urls.py).

## 5. تدفق السلة والـcheckout

1. المستخدم يسجل الدخول بالجلسة الموجودة. الـaccess token يظل في الذاكرة، والـrefresh cookie يديرها نفس session adapter.
2. React يطلب `/carts`. إضافة صنف ترسل ID المنتج والكمية إلى سلة متجر محدد.
3. الباك يقفل صف المستخدم ثم السلة أثناء الكتابة، ويفحص انتماء المنتج للمتجر والكمية المتاحة. الحدود الحالية 1–99 للوحدة و50 صنفًا مختلفًا للسلة.
4. الحسابات المالية تتم في السيرفر. قيم JSON المالية strings؛ الفرونت يعرضها بـ`Intl.NumberFormat`.
5. صفحة checkout تقرأ السلة والمتجر والعناوين ووسائل الدفع بالتوازي. المستخدم يختار عنوانًا ووسيلة متاحة.
6. الطلب يرسل `restaurant_id`, `address_id`, `payment_method`, `expected_total`, `cart_revision` ومعهم header `Idempotency-Key` UUID.
7. `expected_total` إقرار بأن المستخدم راجع الإجمالي، وليس مصدر سعر. السيرفر يعيد التسعير ويرفض الاختلاف بدل تحصيل مبلغ جديد بصمت.
8. تحفظ نسخة البنود والعنوان داخل Order في معاملة. الكاش والمحاكاة يسجلان الطلب ويُفرغان سلة هذا المتجر فقط. الدفع الإلكتروني/التحويل يحتفظان بالسلة لحين التأكيد.
9. عند تأكيد الدفع تُفرغ نفس السلة **إذا لم تتغير منذ الـcheckout**. لو العميل عدلها أثناء الدفع، تحفظ النسخة الحالية بدل ضياع التعديلات؛ يجب مراجعتها قبل طلب آخر. السلال الأخرى لا تتغير.
10. إعادة نفس طلب checkout بنفس المفتاح والبيانات تعيد نفس Order. إعادة المفتاح ببيانات مختلفة ترجع409.

## 6. Paymob: البطاقة والمحافظ

الدفع يستخدم **Hosted Unified Checkout**؛ لا توجد inputs لرقم البطاقة أو CVV أو OTP داخل React، ولا يتم حفظها في Foodify.

التدفق:

```text
React checkout
  → POST /checkout: Order awaiting_payment
  → POST /orders/{id}/payment
  → Backend creates Paymob Intention
  → React redirects to the allowlisted Paymob HTTPS checkout
  → Paymob POST callback to backend
  → Verify HMAC + order/amount/currency/integration
  → Record PaymentEvent and confirm Order
  → User returns to order page, which reads the authenticated Order API
```

- الطلب إلى Paymob يتم من الباك بـSecret Key، وamount بالسنت/القرش.
- `intention_order_id` محفوظ للربط مع `order.id` في callback.
- توقيع callback يستخدم HMAC SHA-512 ومقارنة constant-time وبنفس ترتيب الحقول الرسمي.
- نتحقق من المبلغ والعملة وIntegration ID للوسيلة؛ لا نعتمد على أي status في redirect أو على `is_live` غير الموقّع.
- الرد يحتوي رابط intention مؤقتًا فقط؛ الـclient secret المخزن داخل الرابط مشفر في MySQL، ولا يوضع في localStorage أو logs.
- عملية الشبكة لا تحتفظ بقفل MySQL أثناء انتظار Paymob.
- callbacks المكررة لا تكرر التحصيل/تأكيد الطلب، وcallback فاشلة متأخرة لا تُرجع دفعًا مؤكدًا إلى failed.
- Refund/Void موثق يغيّر حالة الدفع ويظهر ضرورة المراجعة التشغيلية. تنفيذ طلب refund نفسه من واجهة Foodify غير مضاف.
- خطأ/timeout غير محسوم في إنشاء intention يصبح `initialization_unknown`؛ لا نحاول إنشاء intention أخرى تلقائيًا. الدعم يراجع حساب Paymob ويربط/يسوّي العملية قبل أي محاولة أخرى. لم يتم إضافة API reconciliation تلقائي.
- Vodafone Cash وOrange Cash يستخدمان wallet integration المفعلة في حساب التاجر؛ Paymob يدير تحقق المحفظة. وجود الاسم في الواجهة لا يغني عن تفعيل الوسيلة في الحساب.
- `PAYMOB_LIVE=false` يوضح أن العملية Sandbox في تفاصيل الطلب، حتى لو أعاد المزود نتيجة اختبار ناجحة.

### إعداد الحساب

انسخ القيم المطلوبة من [.env.payments.example](.env.payments.example) إلى ملف البيئة الفعلي في الباك فقط:

| المتغير | تجيبه منين؟ |
| --- | --- |
| `PAYMOB_SECRET_KEY` | Paymob Dashboard → Developers → API Keys، Secret Key. |
| `PAYMOB_PUBLIC_KEY` | نفس الصفحة، Public Key. |
| `PAYMOB_HMAC_SECRET` | إعدادات HMAC الخاصة بالحساب/التكامل. |
| `PAYMOB_CARD_INTEGRATION_ID` | Developers → Payment Integrations، تكامل online cards. |
| `PAYMOB_WALLET_INTEGRATION_ID` | تكامل mobile wallets المفعّل لحسابك. |
| `PAYMOB_LIVE` | false للاختبار؛ true مع كل مفاتيح وIDs الـLive فقط. |

اضبط `PUBLIC_BASE_URL` على الباك HTTPS، و`FRONTEND_URL` على الفرونت. notification URL هي:

```text
https://YOUR_BACKEND/api/v1/payments/paymob/callback
```

مسار العودة للعميل يستخدم الباك `/api/v1/payments/return/{order_id}` ثم يحوله إلى React `/#/orders/{order_id}`. تجاهل أي `success=true` في عنوان العودة؛ واجهة الطلب تعرض الحالة الموثقة من API. التجربة المحلية للـcallback تحتاج عنوان HTTPS عام أو tunnel آمن. لا تضع keys في README أو Postman أو Git.

المراجع الرسمية: [Create Intention](https://developers.paymob.com/paymob-docs/intention-apis/create-intention)، [Transaction callbacks](https://developers.paymob.com/paymob-docs/developers/transaction-callbacks)، [HMAC Transaction Callback](https://developers.paymob.com/paymob-docs/developers/webhook-callbacks-and-hmac/hmac/hmac-transaction-callback)، [Checkout integration](https://developers.paymob.com/paymob-docs/integration-paths/apis).

## 7. InstaPay والكاش

InstaPay هنا **تحويل يدوي**، وليس API مباشرًا يدّعي تأكيد البنك تلقائيًا:

1. إعداد `INSTAPAY_RECIPIENT` و`INSTAPAY_RECIPIENT_NAME`؛ بدونهما الوسيلة غير متاحة.
2. بيانات المستلم تحفظ مع Payment عند checkout؛ تعديل الإعدادات لاحقًا لا يغيّر تعليمات طلب قديم.
3. العميل يحول المبلغ ويقدم reference. الحالة تصبح `pending_review`، والطلب يظل بانتظار الدفع.
4. موظف مخول يراجع الحساب البنكي فعليًا، ثم يكتب رقم العملية المؤكد وملاحظة ويوافق/يرفض.
5. عند الموافقة فقط يصبح الدفع paid؛ `verified_reference` عليه unique constraint لمنع احتساب التحويل نفسه مرتين، والمراجعة تُسجل باسم الموظف.

الكاش يسجل `due_on_delivery` عند إنشاء الطلب. تأكيد الموظف لمرحلة delivered يعني تأكيد التسليم والتحصيل. الواجهة توضح ده في اسم الزر.

## 8. التتبع وصلاحيات الموظفين

التسلسل المسموح:

```text
awaiting_payment → placed → preparing → ready → out_for_delivery → delivered
```

الانتقال الأول من تأكيد الدفع، والانتقالات التالية من موظف عنده `orders:manage`. لا يمكن القفز من placed مباشرة إلى delivered. الدفع غير المؤكد أو refunded يمنع بدء/استكمال التحضير.

- العميل عنده `orders:create` و`orders:read_own` فقط لطلباته.
- `operations_manager` و`admin` يديران طلبات المتاجر في هذا الإصدار كفريق عمليات مركزي، ومعهما `payments:review`.
- لا ندّعي وجود restaurant-owner tenancy أو تخصيص موظف لكل فرع. الدور ده يحتاج جدول assignments وفحص صلاحية نطاق المتجر قبل استخدام الشاشة كبوابة لمطاعم مستقلة.
- دور courier وصلاحياته القديمة موجودة، لكن تعيين مندوب وتتبع GPS والاتصال بمندوب محدد خارج التنفيذ الحالي. لا يعرض الموقع بيانات مندوب وهمية.
- شاشة التتبع تقرأ كل5 ثوانٍ أثناء ظهور التبويب، وتتوقف عند delivered/refunded، وتلغي requests عند مغادرة الصفحة.

## 9. مسارات الـAPI الحالية

كل المسارات تبدأ بـ`/api/v1`. `Bearer JWT` مطلوب فيما عدا الكتالوج العام ووسائل الدفع وPaymob callback الموقّعة.

| Method | Path | الوظيفة |
| --- | --- | --- |
| GET | `/restaurants` | كتالوج مع filters وpagination. |
| GET | `/restaurants/{id}` | بيانات المتجر وفئاته. |
| GET | `/restaurants/{id}/menu` | المنتجات المتاحة. |
| GET | `/restaurants/{id}/categories` | فئات المنيو داخل المتجر. |
| GET | `/catalog/categories` | فئات التصفح العامة. |
| GET | `/users/me/favorites` | IDs المتاجر المفضلة للمستخدم. |
| PUT | `/users/me/favorites/{restaurant_id}` | حفظ/إزالة باستخدام `favorite: true/false`. |
| GET | `/carts` | السلال غير الفارغة للمستخدم. |
| POST / GET / DELETE | `/carts/{restaurant_id}` | إنشاء/قراءة/إفراغ سلة متجر. |
| POST | `/carts/{restaurant_id}/items` | إضافة صنف. |
| PATCH / DELETE | `/carts/{restaurant_id}/items/{cart_item_id}` | تعيين كمية/حذف صنف. |
| POST | `/checkout` | حفظ طلب مع Idempotency-Key. |
| GET | `/orders` | تاريخ العميل بصفحات. |
| GET | `/orders/{id}` | تفاصيل وتتبع طلب مملوك للعميل. |
| GET | `/restaurant/orders?restaurant_id=...` | قائمة موظفي العمليات. |
| PATCH | `/operations/orders/{id}/status` | انتقال مخول للمرحلة التالية. |
| GET | `/payments/methods` | الوسائل المتاحة فعليًا في إعدادات الباك. |
| POST | `/orders/{id}/payment` | بدء/إعادة فتح Paymob checkout الخاصة بالعميل. |
| POST | `/payments/paymob/callback?hmac=...` | استقبال transaction callback موثّقة. |
| POST | `/orders/{id}/transfer-claim` | تقديم مرجع تحويل InstaPay. |
| POST | `/operations/orders/{id}/transfer-review` | مراجعة استلام تحويل. |

المسارات القديمة `/cart` لم تعد عقد السلال الحالي. استخدم [Postman Sprint 2](postman/Foodify.Sprint2.postman_collection.json).

مثال checkout:

```json
{
  "restaurant_id": "RESTAURANT_UUID",
  "address_id": "OWNED_ADDRESS_UUID",
  "payment_method": "card",
  "expected_total": "310.00",
  "cart_revision": 2
}
```

أرسل `Authorization: Bearer ACCESS_TOKEN` و`Idempotency-Key: UUID`. اقرأ الإجمالي والنسخة من GET cart قبل الإرسال.

## 10. الأمان الموجود في الربط

- Bearer authentication مع ownership للسلال والعناوين والطلبات؛ لا يقبل الـDTO user_id لتحديد صاحب العملية.
- DTOs ترفض الحقول الزائدة، IDs بصيغة UUID وحدود للكمية والصفحات والبحث.
- SQLAlchemy parameterized queries؛ البحث يعامل `%` و`_` كنص، وترتيب النتائج من allowlist.
- قيود FK/Unique/Check ومعاملات وأقفال للحالات المتزامنة، مع عدم اعتماد السعر على الفرونت.
- كل endpoint للموظف يفحص permission من الباك؛ إخفاء الزر في React مجرد UX.
- أسرار Paymob في الباك فقط، وHMAC بمقارنة آمنة، وقائمة ثابتة لوجهة البوابة في use case الفرونت.
- لا PAN/CVV/OTP ولا تفاصيل callback الخام في logs أو browser storage.
- الردود تحمل `Cache-Control: no-store` وrequest ID والأخطاء في نفس error envelope السابق.
- CORS explicit origins، والـproxy الحالي يسمح بـIdempotency-Key، مع security headers وCSP السابقين.
- جلسات الدخول وقواعد cookies وCSRF والحماية من enumeration وحدود الطلبات السابقة مستمرة. السلة والطلبات في MySQL، وRedis/Valkey للـrate limiting وليس مصدرًا لبيانات الطلب.
- ملف بيانات العينة مدخل seed للباك إند فقط؛ لا توجد بيانات مطاعم أو أسعار ثابتة داخل حزمة الفرونت، ولا توجد أسرار دفع فيها.

دي إجراءات لتغطية مخاطر من OWASP، وليست شهادة أن التطبيق خالٍ من الثغرات. المراجعة الأمنية واختبارات الدفع والتزامن والحمل قبل الإنتاج مسؤولية مرحلة التحقق المخصصة.

## 11. التشغيل والـenvironments

من داخل `back/` بعد تجهيز إعدادات التطوير وMySQL وValkey:

```bash
source .venv/bin/activate
APP_ENV=development python -m scripts.release
APP_ENV=development python -m scripts.seed_catalog
python run.py --env development
```

`release` يطبق migrations ويحدث reference roles/permissions. مزامنة الكتالوج عملية منفصلة ومحددة. تستخدم `shared/demo-catalog.json` و`shared/demo-categories.json` كمدخل للباك إند، ثم تحفظ الأسماء والأسعار والفئات وروابط الصور في MySQL. تفاصيلها في [شرح كتالوج قاعدة البيانات](docs/DEMO_CATALOG.md). لم يتم تشغيلها بعد على قاعدة الاستضافة لأن عنوان MySQL لا يحل عبر DNS.

من داخل `front/`:

```bash
npm install
npm run dev
```

الإعدادات المعتادة:

```text
VITE_DATA_SOURCE=api
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

الواجهة تستخدم API في كل البيئات؛ إعداد `VITE_DATA_SOURCE` غير `api` مرفوض. لا توجد بيانات متجر ثابتة في React. إذا تعطل الباك إند أو قاعدة البيانات تعرض الواجهة حالة خطأ بدل عرض كتالوج مختلف.

development/test/production لهم ملفات إعدادات منفصلة. `APP_ENV=test` مرحلة تشغيل مستقلة ولا يعني أننا كتبنا أو شغّلنا test suites. production يتطلب HTTPS وأسرارًا صحيحة وإعدادات الأمان الحالية، ومفاتيح Paymob Live المتطابقة عند الانتقال للتحصيل الفعلي.

قبل نشر الفرونت الجديد، انشر الباك المتوافق وطبّق migration `20261031_0005` ثم شغّل مزامنة الكتالوج على **قاعدة MySQL المقصودة**؛ نسخة الباك المنشورة القديمة لا تعرف مسارات Sprint 2. لا ترفع الفرونت قبل نجاح الخطوات دي.

## 12. التحقق وحدوده

- تم فحص Python compilation وتحميل SQLAlchemy mappers وتوليد OpenAPI.
- تم توليد MySQL migration SQL في الوضع Offline. ده لا يثبت نجاح تطبيق DDL على MySQL حقيقية.
- تم تشغيل TypeScript typecheck وproduction build.
- تمت مراجعة الواجهة يدويًا عبر Playwright CLI؛ تفاصيل ولقطات النتيجة في [دليل الفرونت](../front/README_SPRINT_2.md).
- MySQL المحلي غير متاح في البيئة وقت التنفيذ. عنوان Aiven الموجود في إعدادات النشر لا يحلّ في DNS العام، لذلك فشل الاتصال قبل تطبيق migration أو إضافة بيانات. لا توجد أي كتابة تمت على قاعدة الاستضافة.
- لم يتم إجراء تحصيل فعلي على الإنتاج. مفاتيح Paymob تبقى في إعدادات الباك إند فقط، ويجب مراجعة وضع Sandbox/Live قبل أي تحصيل.
- لم تتم كتابة أو تشغيل unit/integration/end-to-end test suites حسب تعليمات صاحب المشروع. تيم الاختبارات يراجع خصوصًا التزامن، callbacks المتأخرة/المكررة، أسعار السلة، فشل الشبكة، صلاحيات الموظفين، وتطابق migrations على MySQL.

[شرح أدوات Codex/RTK/Graphify](../docs/DEVELOPMENT_TOOLING.md).
