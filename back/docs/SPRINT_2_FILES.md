# Sprint 2 — فهرس الملفات

شرح تدفق التنفيذ بالكامل في [README_SPRINT_2.md](../README_SPRINT_2.md). هذا الفهرس يوضح مكان كل مجموعة ومسؤوليتها.

| المسار | المسؤولية |
| --- | --- |
| `app/restaurants/` | تصفح المتاجر والفئات والمنيو والمفضلة؛ كل عملية داخل فولدر مستقل. |
| `app/cart/` | قراءة سلال المستخدم وإنشاؤها وتعديلها وإفراغ سلة متجر بعينه. |
| `app/checkout/` | التحقق من السلة والعنوان والسعر، ومفتاح منع الطلب المكرر، وإنشاء Order snapshot. |
| `app/orders/` | سجل العميل وتفاصيل طلبه وقائمة فريق العمليات وتحديث المراحل. |
| `app/payments/` | وسائل الدفع، بدء Hosted Checkout، استقبال callback، ودعوى/مراجعة InstaPay. |
| `app/ordering/models.py` | كيانات المطاعم والمنيو والسلال والطلبات والمدفوعات والفئات والمفضلة والأحداث. |
| `app/ordering/shared/` | DTOs والعقود والقواعد والـmappers والمبالغ المشتركة. |
| `app/ordering/infrastructure/` | SQLAlchemy repositories وتهيئة حالة طرق الدفع. |
| `migrations/versions/20261031_0004_marketplace_payments.py` | MySQL schema والقيود والفهارس والجداول الجديدة. |
| `scripts/seed_catalog.py` | تحميل بيانات العرض المعتمدة محليًا عند التشغيل الصريح فقط. |
| `postman/Foodify.Sprint2.postman_collection.json` | طلبات الـAPI القابلة للاستيراد إلى Postman. |
| `../front/src/features/marketplace/` | واجهة Marketplace، طبقات domain/application/infrastructure/presentation، ومستودعات HTTP التي تقرأ بيانات API. |
| `../shared/demo-catalog.json` و`../shared/demo-categories.json` | مدخل seed للباك إند لمزامنة بيانات العرض إلى MySQL؛ لا تستورده الواجهة. |

لم تُعدّل اختبارات الفريق ولم تُنشأ أو تُشغّل test suites. لم تُطبق Migration 0004 على قاعدة مستضافة ولم تُنشر التعديلات. إعداد Paymob المحلي مستبعد من Git؛ لا تضع مفاتيح الخدمة في هذه الوثائق أو Postman أو الواجهة.
