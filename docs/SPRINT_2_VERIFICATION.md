# Sprint 2 — سجل التحقق

سُجلت النتائج من فحوص الكود وتجربة الواجهة محليًا. لم يتم تشغيل test suites حسب طلب صاحب المشروع.

## Frontend

- `npm run typecheck` نجح.
- `npm run build:production` نجح وأنتج ملفات Vite للإنتاج.
- تمت مراجعة الواجهة في Chromium على سطح المكتب والهاتف بعرض 390px. عرض المستند بقي ضمن عرض الشاشة، ولم تظهر أخطاء Console بعد إعادة تحميل الصفحة.
- تدفق Demo يدويًا: تسجيل الدخول بحساب العرض، فتح مطعمين وإضافة منتج إلى كل سلة، ظهور سلتين مستقلتين، إنشاء طلب تجريبي لمتجر واحد، ظهور صفحة التأكيد والتتبع، وبقاء سلة المتجر الآخر بعد إفراغ سلة الطلب الأول.
- هذه تجربة عرض فقط؛ الطلبات والدفع والتوصيل غير حقيقية في وضع Demo.

## Backend

- Python `compileall` نجح لمجلدات `app` و`migrations` و`scripts`.
- تم تحميل OpenAPI بنجاح وفيه 43 مسارًا، منها المطاعم والسلال والـcheckout وPaymob callback.
- تم توليد SQL للمigrations حتى revision `20261031_0004` في وضع offline. لم يتم الاتصال بقاعدة البيانات أو تطبيق migration عليها.
- Postman collection صالحة JSON، وتحتوي 30 طلبًا؛ تمت مطابقة method وroute لكل طلب مع OpenAPI ولم يظهر مسار غير موجود.
- فحص Ruff للأخطاء `E`, `F`, `I` في ملفات الباك المتغيرة مرّ دون أخطاء.

## ما لم يُتحقق منه

- لم تُشغّل unit/integration/end-to-end tests، ولم تتم إضافة tests.
- لم يُختبر اتصال فعلي بقاعدة MySQL أو خدمة Paymob Sandbox. إعداد `back/.env.payments.development` لا يحتوي حاليًا قيمًا فعّالة لهذه المتغيرات: `PAYMOB_SECRET_KEY`, `PAYMOB_PUBLIC_KEY`, `PAYMOB_HMAC_SECRET`, `PAYMOB_CARD_INTEGRATION_ID`, `PAYMOB_WALLET_INTEGRATION_ID`. لذلك البطاقات والمحافظ تظل غير متاحة في التطبيق حتى تضاف القيم الصحيحة إلى الملف ثم يعاد تشغيل الباك.
- لم تُنشر التغييرات ولم تُطبق migration على قاعدة مستضافة.
