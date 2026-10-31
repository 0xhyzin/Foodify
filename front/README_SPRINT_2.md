# Foodify Frontend — Sprint 2

شرح واجهات Marketplace وربطها مع الباك. التنفيذ React + TypeScript + Vite، بنفس الجلسة وطبقات الحساب الموجودة، وتصميم عربي RTL بأحمر/أبيض وأسود.

## الصفحات

| Route | الصفحة والوظيفة |
| --- | --- |
| `/#/` | المتاجر، البحث عن متجر أو منتج، الفئات، الترتيب، وفلاتر التوصيل. |
| `/#/?section=restaurant` | المطاعم. |
| `/#/?section=dessert` | الحلويات والقهوة. |
| `/#/?section=grocery` | البقالة والسوبر ماركت. |
| `/#/?section=offers` | المتاجر ذات التوصيل المجاني؛ لا يتم اختراع خصم غير موجود في الباك. |
| `/#/?section=favorites` | المتاجر المحفوظة للحساب الحالي. |
| `/#/restaurants/:restaurantId` | بيانات المتجر، المنتجات، وسلة المتجر المستقلة. |
| `/#/carts` | كل السلال؛ التعديل أو الإفراغ يكون لمتجر واحد فقط. |
| `/#/checkout/:restaurantId` | اختيار عنوان ووسيلة دفع، مراجعة الأسعار، وإرسال checkout بمفتاح منع التكرار. |
| `/#/orders` | سجل الطلبات بصفحات. |
| `/#/orders/:orderId` | ملخص الطلب، الدفع، مراحل التتبع، عنوان التوصيل، والطباعة. |
| `/#/operations` | شاشة فريق إدارة الطلبات؛ الأمان النهائي على صلاحيات الباك. |

واجهات login/register/Google/Facebook/confirm-email/reset-password/profile/addresses السابقة مستمرة. السلال والطلبات تحتاج تسجيل دخول؛ checkout يحتاج اكتمال بيانات الحساب.

## تقسيم الملفات

كل الشغل الجديد في `src/features/marketplace/`:

- `domain`: models وواجهات Catalog/Cart/Order/Payment repositories. الأسعار strings؛ العرض عبر `Intl.NumberFormat`.
- `application`: use cases فيها validation الكمية وcheckout وفحص وجهة Paymob قبل الانتقال إليها.
- `infrastructure`: HTTP DTOs/mappers وclass مستقلة لكل repository؛ جميع بيانات المتجر والسلة والطلب تقرأ من API.
- `presentation/components`: مكونات العرض القابلة لإعادة الاستخدام، بدل جمع الواجهة في ملف واحد.
- `presentation/pages`: ربط المكونات لكل صفحة.
- `presentation/hooks`: تحميل بيانات قابل للإلغاء، وpolling للطلب أثناء ظهور التبويب.
- `marketplace-provider.tsx`: سلال ومفضلة الحساب الحالي، وحماية العرض من نتائج requests خاصة بحساب قديم.
- `marketplace-layout.tsx`: header والتنقل وسلالي والحساب والـfooter.
- `app/services.ts`: composition root يختار implementations ويحقنها. المكونات لا تحتوي fetch مباشرًا.

## أهم المكونات

| Component | مسؤوليته |
| --- | --- |
| `MerchantCard` | اسم/شعار/تقييم/وقت ورسوم المتجر، وفتح قائمته أو إضافته للمفضلة. |
| `ProductCard` | المنتج وسعره ووصفه وزر إضافة لسلة متجره. |
| `CartPanel` | الكميات والحذف والإجمالي وزر checkout؛ تأكيد إفراغ هذه السلة فقط. |
| `FoodPhoto` | يعرض رابط الصورة المحفوظ في MySQL، مع أيقونة بديلة عند غياب الصورة أو فشل تحميلها. |
| `MerchantLogo` | يعرض مسار الشعار القادم من حقل `logo` في API، ويتحقق من المصدر قبل تحميله. |
| `OrderSummary` | بنود الطلب والأسعار ورسوم التوصيل والملخص القابل للطباعة. |
| `OrderTimeline` | مراحل محفوظة من الباك؛ لا يغير الحالة ولا يحاكي مندوبًا متحركًا. |
| `OperationalOrder` | تفاصيل الطلب وتحديث المرحلة ومراجعة التحويل لموظف مخول. |
| `ResourceState` | تحميل أو خطأ أو empty state مع إجراء مناسب. |

## الربط بالـAPI

الـHTTP repositories تستخدم `FetchHttpClient` الحالي؛ يضيف Bearer token و`X-Foodify-Client`، ويتعامل مع تجديد الجلسة والأخطاء بنفس آلية الحساب. أضيف دعم `Idempotency-Key` إلى RequestOptions.

- تحميل الكتالوج/المنيو عام، أما السلال والمفضلة والطلبات فتابعة للحساب.
- add/update/remove/clear كلها ترسل `restaurant_id` في مسار السلة.
- المبلغ النهائي من السيرفر. checkout يرسل الإجمالي الذي راجعه المستخدم ونسخة السلة، والسيرفر يرفض أي تغيير قبل التحصيل.
- مفتاح checkout يعاد استخدامه عند إعادة نفس المحاولة؛ لا يولد مفتاحًا جديدًا بعد timeout بلا سبب.
- عند الدفع بالبطاقة/المحفظة، React ينتقل لرابط Paymob HTTPS معتمد بعد حفظ الطلب. لا توجد حقول PAN/CVV/OTP داخل Foodify.
- الرجوع من Paymob لا يجعل الطلب paid. صفحة الطلب تقرأ الحالة من الباك دوريًا.
- InstaPay يظهر بيانات المستلم المحفوظة مع الطلب، ويقدم العميل reference للمراجعة فقط.
- السلال الأخرى لا تُمسح بعد checkout أو تأكيد دفع متجر واحد.
- لا تتم إضافة provider secrets أو access/refresh tokens إلى localStorage.

## مصدر الكتالوج

مصدر بيانات المتاجر والفئات والمنتجات والأسعار وروابط الصور في التطبيق هو MySQL. `shared/demo-catalog.json` ملف seed يستخدمه الباك إند فقط لمزامنة عينة من 8 متاجر مصرية و24 منتجًا؛ الواجهة لا تستورده ولا تستخدمه كبديل عند تعطل الاتصال. قاعدة الاستضافة لم تُزامن معها العينة بعد لأن عنوان MySQL الحالي لا يحل عبر DNS العام.

`HttpCatalogRepository` يطلب القوائم من FastAPI، ثم يحول DTOs إلى نماذج المجال. صفحات React تعرض هذه النماذج فقط. إذا تعطل الاتصال تظهر حالة خطأ بدل استبدال بيانات قاعدة البيانات بداتا محلية. إعداد Vite يرفض أي قيمة غير `VITE_DATA_SOURCE=api`.

روابط الصور مخزنة في عمود `artwork` للمتجر والمنتج، وContent Security Policy تسمح بمضيفي الصور المحددين في الكود. الأسعار والأوقات والتقييمات بيانات عرض تجريبية؛ ليست مزامنة حية من الشركات.

## الواجهة والـUX

ألوان منضبطة بالأحمر/الأبيض والأسود، IBM Plex Sans Arabic، خطوط ومسافات وأزرار موحدة، RTL، وتدرج واضح بين اسم المتجر والسعر والإجراء. الهاتف له layout يتكيف من غير قص للمحتوى، والفئات والتنقل لها scroll أفقي عند الحاجة.

التحكم بالكيبورد، labels للـinputs وأزرار الأيقونات، focus ظاهر، skip link، حالات loading/empty/error، spinner أثناء الإرسال، reduced motion، وأسماء إجراءات مباشرة موجودة. الصفحات الثقيلة محملة بـlazy loading، والـrequests القديمة يتم إلغاؤها أو تجاهل نتائجها.

## التشغيل

```bash
cd front
npm install
npm run dev
```

للـAPI المحلي:

```text
VITE_DATA_SOURCE=api
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

مراجعة النوع والبناء فقط، دون تشغيل test suites:

```bash
npm run typecheck
npm run build:production
```

قبل نشر الفرونت، يجب نشر الباك المتوافق، وتطبيق migration `20261031_0005`، ثم مزامنة الكتالوج إلى MySQL. ملف مفاتيح Paymob يخص الباك فقط. التفاصيل الكاملة في [README السبرنت](../back/README_SPRINT_2.md) و[شرح تدفق الكتالوج](docs/CATALOG.md).

## التحقق

تم تشغيل typecheck وproduction build، وتحميل الواجهة ومراجعتها يدويًا في Chromium عبر Playwright CLI. لم تتم إضافة أو تشغيل unit/integration/end-to-end test suites. سجل نتيجة المراجعة اليدوية النهائية محفوظ في [SPRINT_2_VERIFICATION.md](../docs/SPRINT_2_VERIFICATION.md).
