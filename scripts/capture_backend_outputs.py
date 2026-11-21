"""Run isolated backend tests once and export sanitized HTTP evidence for the team.

No application, test, environment or database code is changed. A temporary pytest
plugin observes TestClient responses and explicitly mocked provider transports.
Only sanitized records reach disk; no credentials are loaded from .env files.
"""

from __future__ import annotations

import collections
import importlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pytest


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "backend-team-output"
TEMP = ROOT / "tmp" / "backend-output-capture"
REDACTED = "[REDACTED]"


class Sanitizer:
    """Remove secret fields and nested URL secrets before serializing captures."""

    sensitive = {
        "password", "newpassword", "currentpassword", "confirmpassword", "passwordhash",
        "token", "accesstoken", "refreshtoken", "actiontoken", "oauthtoken", "oauthstate",
        "clientsecret", "clientkey", "secretkey", "apikey", "publickey", "secret", "jwtsecret",
        "emailencryptionkey", "hmac", "hmacsecret", "signature", "ticket", "state", "nonce",
        "bindingverifier", "bindingchallenge", "codeverifier", "codechallenge",
        "authorizationcode", "authorization", "cookie", "setcookie", "encryptedtoken",
        "checkouttoken", "pan", "cardnumber", "cvv", "cvc", "securitycode",
    }

    def __init__(self):
        self.secrets: set[str] = set()

    @classmethod
    def is_sensitive(cls, key: str, *, query: bool = False) -> bool:
        normalized = re.sub(r"[^a-z0-9]", "", key.casefold())
        return normalized in cls.sensitive or (query and normalized == "code")

    def remember(self, value):
        if isinstance(value, str) and len(value) >= 4:
            self.secrets.add(value)

    def learn(self, value):
        if isinstance(value, dict):
            for key, child in value.items():
                if self.is_sensitive(str(key)):
                    self.remember(child)
                else:
                    self.learn(child)
        elif isinstance(value, list):
            for child in value:
                self.learn(child)
        elif isinstance(value, str) and value.startswith(("http://", "https://", "/")):
            self.url(value, learn_only=True)

    def url(self, value: str, *, learn_only: bool = False) -> str:
        try:
            parts = urlsplit(value)
            query = self.parameters(parts.query, learn_only=learn_only)
            fragment = parts.fragment
            if "?" in fragment:
                route, params = fragment.split("?", 1)
                fragment = route + "?" + self.parameters(params, learn_only=learn_only)
            elif "=" in fragment:
                fragment = self.parameters(fragment, learn_only=learn_only)
            netloc = parts.netloc
            if "@" in netloc:
                self.remember(netloc.rsplit("@", 1)[0])
                netloc = REDACTED + "@" + netloc.rsplit("@", 1)[1]
            return urlunsplit((parts.scheme, netloc, parts.path, query, fragment))
        except ValueError:
            return "[WITHHELD: invalid URL]"

    def parameters(self, value: str, *, learn_only: bool = False) -> str:
        result = []
        for key, child in parse_qsl(value, keep_blank_values=True):
            if self.is_sensitive(key, query=True):
                self.remember(child)
                child = REDACTED
            elif child.startswith(("http://", "https://")):
                child = self.url(child, learn_only=learn_only)
            result.append((key, child))
        return urlencode(result, safe="/:[]")

    def text(self, value: str) -> str:
        # OAuth/checkout URLs and callback Location fragments can contain secrets.
        value = re.sub(r"https?://[^\s<>\"']+", lambda m: self.url(m.group()), value)
        value = re.sub(r"\b(Bearer|Token|Basic)\s+[^\s\"',<>]+", r"\1 [REDACTED]", value, flags=re.I)
        value = re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", REDACTED, value)
        for secret in sorted(self.secrets, key=len, reverse=True):
            value = value.replace(secret, REDACTED)
        return value

    def clean(self, value, *, key: str = ""):
        # Preserve error.code and token_type; only known security fields are masked.
        if self.is_sensitive(key):
            return REDACTED if value is not None else None
        if key in {"code", "token_type"} and isinstance(value, str):
            return value
        if isinstance(value, dict):
            return {name: self.clean(child, key=str(name)) for name, child in value.items()}
        if isinstance(value, list):
            return [self.clean(child) for child in value]
        if isinstance(value, str):
            if value.startswith(("http://", "https://")):
                value = self.url(value)
            return self.text(value)
        return value

    def headers(self, headers) -> list[dict[str, str]]:
        result = []
        for key, value in headers.multi_items():
            normalized = key.casefold()
            if normalized == "set-cookie":
                first, separator, flags = value.partition(";")
                name, _, secret = first.partition("=")
                self.remember(secret.strip('"'))
                value = name + "=" + REDACTED + (separator + flags if separator else "")
            elif normalized == "cookie":
                cookies = []
                for pair in value.split(";"):
                    name, _, secret = pair.strip().partition("=")
                    self.remember(secret.strip('"'))
                    cookies.append(name + "=" + REDACTED)
                value = "; ".join(cookies)
            elif normalized in {"authorization", "proxy-authorization"}:
                scheme, _, secret = value.partition(" ")
                self.remember(secret)
                value = scheme + " " + REDACTED
            elif self.is_sensitive(key):
                self.remember(value)
                value = REDACTED
            elif normalized in {"location", "content-location"}:
                value = self.url(value)
            result.append({"name": key, "value": self.text(value)})
        return result


class BackendOutputPlugin:
    def __init__(self, destination: str):
        self.destination = Path(destination)
        self.sanitizer = Sanitizer()
        self.current_test = None
        self.current_markers = []
        self.records = []
        self.results = {}
        self.patches = []

    def pytest_configure(self, config):
        from starlette.testclient import TestClient

        # Starlette versions can use httpx or httpx2; intercept the actual client.
        self._install(TestClient, scope="backend_api", mocked=False)
        for module_name in ("httpx", "httpx2"):
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
            self._install(module.Client, scope="provider_mock", mocked=True)

    def _install(self, client_type, *, scope: str, mocked: bool):
        own = client_type.__dict__.get("_send_single_request")
        original = client_type._send_single_request
        plugin = self

        def capture(client, request):
            if mocked:
                transport = client._transport_for_url(request.url)
                if type(transport).__name__ != "MockTransport":
                    return original(client, request)
            response = original(client, request)
            response.read()
            plugin.record(request, response, scope=scope)
            return response

        client_type._send_single_request = capture
        self.patches.append((client_type, own))

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_protocol(self, item, nextitem):
        self.current_test = item.nodeid
        self.current_markers = [name for name in ("unit", "integration") if item.get_closest_marker(name)]
        yield
        self.current_test = None
        self.current_markers = []

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report):
        if report.longrepr:
            report.longrepr = self.sanitizer.text(str(report.longrepr))
        report.sections[:] = [(name, self.sanitizer.text(content)) for name, content in report.sections]
        if report.when == "call" or report.failed:
            self.results[report.nodeid] = report.outcome

    @staticmethod
    def body(message):
        if not message.content:
            return None
        if "json" not in message.headers.get("content-type", "").casefold():
            return {"withheld": "Non-JSON body omitted; may contain sensitive or binary data.", "byte_length": len(message.content)}
        try:
            return json.loads(message.content)
        except (ValueError, UnicodeDecodeError):
            return {"withheld": "Invalid JSON body omitted.", "byte_length": len(message.content)}

    def record(self, request, response, *, scope: str):
        request_body = self.body(request)
        response_body = self.body(response)
        self.sanitizer.learn(request_body)
        self.sanitizer.learn(response_body)
        self.sanitizer.url(str(request.url), learn_only=True)
        request_headers = self.sanitizer.headers(request.headers)
        response_headers = self.sanitizer.headers(response.headers)
        record = {
            "sequence": len(self.records) + 1,
            "test_nodeid": self.current_test,
            "test_markers": self.current_markers.copy(),
            "scope": scope,
            "environment": "isolated_test_sqlite_in_memory",
            "provider_mode": "mocked_in_process_no_live_provider_calls",
            "request": {
                "method": request.method,
                "url": self.sanitizer.url(str(request.url)),
                "path": request.url.path,
                "headers": request_headers,
                "body": self.sanitizer.clean(request_body),
            },
            "response": {
                "status": response.status_code,
                "headers": response_headers,
                "body": self.sanitizer.clean(response_body),
            },
        }
        # Only the sanitized representation is retained for export.
        self.records.append(record)

    def pytest_sessionfinish(self, session, exitstatus):
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        body = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "Actual backend pytest execution; responses were observed, not invented.",
            "redaction_note": (
                "Secrets are removed before records are retained or written: passwords, access/refresh/action tokens, "
                "OAuth state/tickets/verifiers/challenges/codes, HMAC/signatures, Paymob public/client secrets, "
                "Authorization and cookie values, and PAN/CVV. Nested URL query/fragment secrets are masked. "
                "error.code, token_type, IDs, amounts, request IDs and cookie attributes are preserved. "
                "Non-JSON bodies are withheld. All identities/data are isolated fixtures. Google/Paymob are "
                "mocked; no production database, real account, real delivery, live payment or email was used."
            ),
            "pytest_exit_code": int(exitstatus),
            "tests": {
                "collected": session.testscollected,
                "outcomes": dict(collections.Counter(self.results.values())),
            },
            "record_count": len(self.records),
            "api_status_counts": dict(collections.Counter(str(r["response"]["status"]) for r in self.records if r["scope"] == "backend_api")),
            "provider_mock_status_counts": dict(collections.Counter(str(r["response"]["status"]) for r in self.records if r["scope"] == "provider_mock")),
            "records": self.records,
        }
        self.destination.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for client_type, own in reversed(self.patches):
            if own is None:
                delattr(client_type, "_send_single_request")
            else:
                client_type._send_single_request = own


def operation_coverage(capture: dict, spec_path: Path) -> dict:
    """Match observed requests to documented methods; unobserved output stays absent."""
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
    operations = []
    for path, definitions in spec["paths"].items():
        for method, definition in definitions.items():
            if method not in methods:
                continue
            parts = re.split(r"(\{[^}]+\})", path)
            pattern = "^" + "".join("[^/]+" if part.startswith("{") else re.escape(part) for part in parts) + "$"
            found = [record for record in capture["records"] if (
                record["scope"] == "backend_api"
                and record["request"]["method"].lower() == method
                and re.fullmatch(pattern, record["request"]["path"])
            )]
            operations.append({
                "method": method.upper(), "path": path,
                "operation_id": definition.get("operationId"),
                "captured": bool(found), "record_count": len(found),
                "statuses": sorted({record["response"]["status"] for record in found}),
            })
    return {
        "openapi_source": str(spec_path.relative_to(ROOT)),
        "documented_operations": len(operations),
        "captured_operations": sum(operation["captured"] for operation in operations),
        "note": "Only actual captured HTTP requests count. No responses are invented for uncaptured operations.",
        "operations": operations,
    }


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    module_source = str(Path(__file__).resolve())
    plugin_source = (
        "import importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('_foodify_capture_impl', {module_source!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
        "def pytest_configure(config):\n"
        f"    config.pluginmanager.register(module.BackendOutputPlugin({str(OUTPUT / 'api-responses.json')!r}), 'foodify-output-capture')\n"
    )
    (TEMP / "foodify_backend_capture.py").write_text(plugin_source, encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(TEMP) + os.pathsep + environment.get("PYTHONPATH", "")
    environment["COVERAGE_FILE"] = str(TEMP / ".coverage")
    command = [
        str(ROOT / "back" / ".venv" / "bin" / "python"), "-m", "pytest", "tests", "-vv",
        "-p", "foodify_backend_capture", "--cov=app",
        "--cov-report=json:" + str(OUTPUT / "coverage.json"), "--cov-report=term-missing",
        "--junitxml=" + str(OUTPUT / "backend-results.xml"),
        "-o", "junit_logging=no", "-o", "junit_log_passing_tests=false",
    ]
    result = subprocess.run(command, cwd=ROOT / "back", env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    safe_log = Sanitizer().text(result.stdout)
    (OUTPUT / "test-output.txt").write_text(safe_log, encoding="utf-8")
    coverage_start = safe_log.find("coverage: platform")
    coverage_text = safe_log[coverage_start:] if coverage_start >= 0 else safe_log
    (OUTPUT / "coverage.txt").write_text(coverage_text, encoding="utf-8")
    summary = {"pytest_exit_code": result.returncode, "output_directory": str(OUTPUT)}
    if (OUTPUT / "api-responses.json").exists():
        capture = json.loads((OUTPUT / "api-responses.json").read_text(encoding="utf-8"))
        summary.update({key: capture[key] for key in ("tests", "record_count", "api_status_counts", "provider_mock_status_counts")})
        spec_path = ROOT / "docs" / "teams" / "assets" / "openapi.json"
        if spec_path.exists():
            capture["operation_coverage"] = operation_coverage(capture, spec_path)
            (OUTPUT / "api-responses.json").write_text(json.dumps(capture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            summary["operation_coverage"] = {
                key: capture["operation_coverage"][key]
                for key in ("documented_operations", "captured_operations")
            }
    if (OUTPUT / "coverage.json").exists():
        summary["coverage"] = json.loads((OUTPUT / "coverage.json").read_text())["totals"]
    if (OUTPUT / "backend-results.xml").exists():
        summary["junit_testcases"] = len(list(ET.parse(OUTPUT / "backend-results.xml").getroot().iter("testcase")))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
