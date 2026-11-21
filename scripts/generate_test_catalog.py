"""Build a documentation inventory from actual JUnit results, never source guesses."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = [
    ("Backend — Unit", "backend-unit.xml"),
    ("Backend — Integration", "backend-integration.xml"),
    ("Frontend — Unit", "frontend-unit.xml"),
    ("Frontend — Integration", "frontend-integration.xml"),
    ("Vercel proxy — isolated handler", "proxy.xml"),
    ("Postman — contracts", "contracts.xml"),
]


def generate() -> None:
    results = []
    for label, filename in REPORTS:
        source = ROOT / "output" / "verification" / filename
        root = ET.parse(source).getroot()
        cases = []
        for case in root.iter("testcase"):
            status = "passed"
            if case.find("failure") is not None or case.find("error") is not None:
                status = "failed"
            elif case.find("skipped") is not None:
                status = "skipped"
            cases.append({"name": case.get("name", ""), "class": case.get("classname", ""), "status": status})
        results.append({
            "suite": label,
            "total": len(cases),
            **{status: sum(case["status"] == status for case in cases) for status in ("passed", "failed", "skipped")},
            "cases": cases,
        })
    destination = ROOT / "docs" / "teams"
    (destination / "assets" / "test-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# فهرس حالات الاختبار الفعلية", "",
        "الفهرس ده مولّد من تقارير JUnit الناتجة عن تشغيل الاختبارات، وليس من عدد دوال المصدر. الحالات Parameterized تُعد منفصلة لأن كل قيمة تتحقق من سلوك مختلف.", "",
        "شرح الهدف من المجموعات وطريقة عزلها في [Unit وIntegration Tests](testing.md). أسماء الحالات الإنجليزية هي أسماء السيناريوهات الفعلية داخل ملفات الاختبار.", "",
        "| المجموعة | الحالات | ناجح | فاشل | متجاهل |", "|---|---:|---:|---:|---:|",
    ]
    for suite in results:
        lines.append(f"| {suite['suite']} | {suite['total']} | {suite['passed']} | {suite['failed']} | {suite['skipped']} |")
    for suite in results:
        lines.extend(["", "## " + suite["suite"], "", "| السيناريو | النتيجة |", "|---|---|"])
        for case in suite["cases"]:
            name = case["name"].replace("|", "\\|").replace("\n", " ")
            status = {"passed": "ناجح", "failed": "فاشل", "skipped": "لم يُنفّذ"}[case["status"]]
            lines.append(f"| `{name}` | {status} |")
    (destination / "test-catalog.md").write_text("\n".join(lines) + "\n")
    print(json.dumps([{key: value for key, value in suite.items() if key != "cases"} for suite in results]))


if __name__ == "__main__":
    generate()
