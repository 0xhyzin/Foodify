# Sprint 2 — نطاق التنفيذ والحالة

## المطلوب المنفذ

- واجهة React عربية للمتاجر والمطاعم والحلويات والقهوة والبقالة، والبحث والتصنيفات والفلاتر والمفضلة.
- سلة مستقلة لكل مستخدم ومتجر، وطلب واحد لكل متجر مع الإبقاء على بقية السلال.
- إدارة عناوين المستخدم، checkout مع إعادة تسعير في الخادم ومفتاح idempotency، وسجل الطلبات والتأكيد والتتبع.
- Backend FastAPI مقسم حسب العمليات إلى DTO وinterface وservice وdependencies وrouter، مع repositories وDependency Injection.
- Paymob Hosted Checkout للبطاقات والمحافظ التي فعّلها حساب Paymob. InstaPay تحويل يدوي لا يصبح مدفوعًا إلا بمراجعة موظف مخول.
- MySQL schema وMigration 0004، seed اختياري لكتالوج العرض، Postman collection، وREADME تفصيلي.
- عدم إنشاء أو تشغيل test suites بناءً على طلب صاحب المشروع.

## نتيجة المراجعة الحالية

- `front`: `npm run typecheck` و`npm run build:production` اكتملتا بنجاح.
- تم تشغيل تدفق Demo في Chromium يدويًا: دخول العرض، سلتان لمتجرين، checkout لأحدهما، صفحة تأكيد/تتبع، وبقاء سلة المتجر الآخر.
- Python compileall نجح، وتم تحميل OpenAPI وفيه 43 مسارًا. تم توليد SQL لجميع migrations حتى 0004 في وضع offline دون الاتصال بقاعدة بيانات.
- لم يتم تشغيل اختبارات، أو تطبيق migration على قاعدة بيانات بعيدة، أو نشر التعديلات.

تفاصيل العمل والملاحظات الأمنية في [شرح الباك](../back/README_SPRINT_2.md) و[شرح الواجهة](../front/README_SPRINT_2.md). ملخص التحقق في [SPRINT_2_VERIFICATION.md](SPRINT_2_VERIFICATION.md).

## ما يلزم لتفعيل Sandbox

يحتاج Paymob إلى Secret Key وPublic Key وHMAC Secret ومعرف تكامل البطاقة ومعرف تكامل المحافظ من حساب Sandbox، ويجب أن يتطابق وضع المفاتيح ومعرفات التكامل. ضع القيم في `back/.env.payments.development` دون `#` ثم أعد تشغيل الباك. الإعداد المحلي الحالي لا يحتوي قيمًا فعّالة، لذلك سيظل Paymob غير متاح حتى تُضاف. لا ترسل هذه القيم عبر المحادثة ولا تضعها في الواجهة أو Git.
