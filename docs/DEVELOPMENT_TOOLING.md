# أدوات العمل على Foodify

الأدوات دي للمساعد أثناء التطوير، وليست dependencies داخل تطبيق المستخدم.

## Codex والـskills

اتثبتت المهارات المطلوبة لـCodex في المسار المشترك `~/.agents/skills`:

- `frontend-design`: تنفيذ الشكل المعتمد، الـtypography والألوان والمسافات.
- `web-design-guidelines`: مراجعة الـaccessibility، الـforms، الـfocus والـresponsive layout.
- `vercel-react-best-practices`: فصل المكونات، تحميل صفحات الدفع والطلبات والموظفين بـlazy loading، وإلغاء الطلبات القديمة.
- `playwright-cli`: مراجعة الواجهة يدويًا داخل Chromium وأخذ screenshots. لم تتم إضافة ملفات tests.

تم تحديث Playwright CLI عالميًا. إضافة skills جديدة تبقى متاحة لاكتشاف Codex في الدور التالي؛ يمكن للمساعد قراءة تعليماتها واستخدامها فورًا في الجلسة الحالية.

## RTK على Codex نفسه

الإصدار المثبت `1.1.0`. تم تشغيل:

```bash
rtk init --global --codex --dry-run
rtk init --global --codex
rtk init --global --codex --show
```

الإعدادات المسجلة:

- `~/.codex/RTK.md`: تعليمات المخرجات المختصرة.
- `~/.codex/AGENTS.md`: مرجع ملف التعليمات.
- `~/.codex/hooks.json`: hook اسمه `rtk hook codex` قبل أوامر shell المدعومة.

التفعيل التلقائي للـhook يحتاج إعادة تشغيل Codex. في الجلسة الحالية تم استخدام أوامر RTK مباشرة بالفعل؛ مثل `rtk git status` و`rtk npm run typecheck`. الأمر `rtk gain` يعرض التوفير المقاس؛ التوفير يختلف حسب نوع المخرجات ولا توجد نسبة ثابتة مضمونة.

## Graphify

اتثبتت الحزمة الرسمية `graphifyy` في venv منفصل:

```text
~/.local/share/foodify-tools/graphify
```

والـCLI متاح باسم `graphify`، ومهارته مثبتة في `~/.codex/skills/graphify`.

الفهرسة المستخدمة محلية للكود فقط:

```bash
GRAPHIFY_BACKEND=none graphify extract front/src --code-only --no-cluster --no-dedup --out graphify-out/front
GRAPHIFY_BACKEND=none graphify extract back/app --code-only --no-cluster --no-dedup --out graphify-out/back
graphify query 'CheckoutService lock_cart' --graph graphify-out/back/graphify-out/graph.json --budget 600
```

المخرجات محفوظة في `graphify-out/` ومُستبعدة محليًا من Git عبر `.git/info/exclude`. لم تتم فهرسة ملفات `.env`، ولم يتم إرسال الكود إلى LLM خارجي. الفهرس يساعد في تحديد العلاقات والملفات، وبعده تُقرأ الملفات اللازمة للتعديل.

المراجع: [Codex skills](https://learn.chatgpt.com/docs/build-skills)، [Codex hooks](https://learn.chatgpt.com/docs/hooks)، [RTK](https://github.com/rtk-ai/rtk)، [Graphify](https://github.com/Graphify-Labs/graphify).
