# كتالوج المتاجر والمنتجات في MySQL

بيانات صفحة المطاعم تُحفظ في MySQL، ويقرأها التطبيق من خلال FastAPI. ملف
`back/app/ordering/data/demo-catalog.json` ليس مصدرًا للواجهة؛ هو ملف إدخال يستخدمه سكربت
الباك إند لإضافة بيانات العرض إلى قاعدة البيانات. يحتوي على 8 متاجر مصرية بين
مطاعم وحلويات وبقالة، ولكل متجر 3 منتجات، بإجمالي 24 منتجًا. أسماء المنتجات
والأسعار وروابط الصور والتصنيفات تُحفظ في سجلات قاعدة البيانات.

ملفا العينة موجودان داخل حزمة الباك إند في `back/app/ordering/data/`.
يقرأهما السكربت باستخدام `importlib.resources`، لذلك يصل إليهما من نسخة المشروع
المحلية، وصورة Docker، وحزمة Python المبنية. لا يحتاج الباك إلى مجلد `shared/`
خارج مجلد النشر، ولا توجد نسخة أخرى من الكتالوج داخل React.

المعرّفات ثابتة ومحددة مسبقًا حتى تكون المزامنة قابلة لإعادة التشغيل. السكربت
يحدّث سجلات الكتالوج المعروفة فقط، ويوقف عرض بيانات الديمو القديمة. لا يحذف
متاجر أو منتجات أو سلال أو طلبات أو حسابات، ويحافظ على المراجع الموجودة بينها.
الأسعار والتقييمات وأوقات التوصيل أمثلة للعرض وليست تحديثًا مباشرًا من المتاجر.

## تعديل قاعدة البيانات

Migration `20261031_0005` يوسّع عمود `artwork` في جدولي `restaurants` و
`menu_items` من 30 إلى 2048 حرفًا حتى يتسع لرابط الصورة الكامل. لا يغيّر بيانات
الحسابات أو السلال أو الطلبات أو الدفع. عملية الرجوع ترفض تقصير العمود إذا كان
هناك رابط أطول من 30 حرفًا، حتى لا تفقد البيانات.

## تشغيل المزامنة محليًا

من مجلد `back/`، بعد إعداد اتصال قاعدة البيانات وتطبيق الـmigrations:

```bash
python -m scripts.seed_catalog
```

عند تشغيل الباك من Docker، نفّذ من مجلد `back/`:

```bash
docker compose --env-file .env.development run --rm api python -m scripts.release
docker compose --env-file .env.development run --rm api python -m scripts.seed_catalog
```

يتحقق السكربت من اتصال قاعدة البيانات ومطابقة إصدار الـmigrations قبل تغيير
الكتالوج. إذا كانت الجداول قديمة، يخرج برسالة تطلب تنفيذ `scripts.release`،
من دون بدء تعديل بيانات المطاعم. لا يُشغَّل seed الكتالوج تلقائيًا عند بدء الـAPI.

## تشغيلها على قاعدة الإنتاج

طبّق الـmigration أولًا، ثم شغّل السكربت من نسخة موثوقة من المشروع بعد توفير
إعداد اتصال الإنتاج في متغيرات البيئة. لا تضع كلمات المرور أو المفاتيح في Git
أو داخل ملفات المصدر. الإنتاج يحتاج الخيارين التاليين معًا:

```bash
APP_ENV=production FOODIFY_ALLOW_DEMO_CATALOG_SEED=true \
  python -m scripts.seed_catalog --allow-production
```

يعرض السكربت عدد المتاجر والمنتجات والفئات التي زامنها. يمكن إعادة تشغيله؛ فهو
يحدّث السجلات التابعة له فقط ولا يحذف بيانات المستخدمين أو الطلبات.

## مصدر الأسماء والصور

الصور روابط فعلية لصور المنتجات من قوائم المطاعم والمتاجر، ولم تُنشأ صور
مولدة. روجعت الأسماء والمنتجات مقابل [قائمة ماكدونالدز على طلبات](https://www.talabat.com/egypt/restaurant/665416/mcdonalds-mourad-st?aid=7730)،
[قائمة KFC](https://www.talabat.com/egypt/restaurant/737383/kfc-open-air-mall-madinaty?aid=7555)،
[قائمة Pizza Hut](https://www.talabat.com/egypt/restaurant/666423/pizza-hut?aid=7745)،
[كشري التحرير](https://www.talabat.com/egypt/restaurant/676359/koshary-el-tahrir-talaat-harb?aid=7769)،
[حلواني العبد](https://www.talabat.com/egypt/restaurant/508623/el-abd?aid=7761)،
[Starbucks](https://www.talabat.com/egypt/restaurant/518125/starbucks-nile-city-boat-zamalek-cairo-tower?aid=7729)،
[كتالوج Carrefour مصر](https://www.carrefouregypt.com/mafegy/en/c/FEGY1630500)،
و[موقع سعودي ماركت](https://seoudisupermarket.com/en). قد تتغير الأسعار أو الصور أو
توافر المنتج لدى صاحب العلامة التجارية.
