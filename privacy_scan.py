from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIARY_DIR = BASE_DIR / "diaries"
README = BASE_DIR / "README.md"


@dataclass(frozen=True)
class Rule:
    name: str
    severity: str
    pattern: str
    why: str


RULES = [
    Rule(
        "local_absolute_path",
        "high",
        r"/Users/[A-Za-z0-9._-]+/|\.openclaw/workspace",
        "로컬 계정명/작업공간 구조가 공개 식별자와 연결될 수 있음",
    ),
    Rule(
        "health_medical_insurance",
        "high",
        r"마운자로|처방|질환|병원|진료영수증|진료세부|소견서|실손|보험청구|국민건강보험",
        "건강·진료·보험 관련 민감 추론 가능",
    ),
    Rule(
        "specific_location_movement",
        "high",
        r"영등포|금천|퇴계로|회현|명동|남대문|중문|제주|공항|항공권|배편|장례식|조문",
        "생활권/실시간 동선/오프라인 일정 추정 가능",
    ),
    Rule(
        "finance_legal_admin",
        "medium",
        r"은행|법인|위임장|실제소유자|신분증|여권|운전면허증|명의|양도|USIM|eSIM",
        "법인·금융·행정 상태가 누적 식별 단서가 될 수 있음",
    ),
    Rule(
        "account_security",
        "medium",
        r"비밀번호|마스터 패스워드|2FA|2단계 인증|Bitwarden|1Password|Dashlane|NordPass",
        "계정 보안 습관/도구 스택 노출 가능",
    ),
    Rule(
        "relationship_identifier",
        "medium",
        r"언니|가족|성과 결합|gaemi\.kim|iamdrunkendog|i\.am@gaemi\.kim",
        "인간관계·도메인·계정 식별자 연결 가능",
    ),
]


def iter_markdown_files(include_docs: bool = False) -> list[Path]:
    files = []
    if include_docs and README.exists():
        files.append(README)
    if DIARY_DIR.exists():
        files.extend(sorted(DIARY_DIR.glob("*.md")))
    return files


def scan_file(path: Path) -> list[tuple[Rule, int, str]]:
    findings: list[tuple[Rule, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings

    for line_no, line in enumerate(text.splitlines(), start=1):
        for rule in RULES:
            if re.search(rule.pattern, line, flags=re.IGNORECASE):
                findings.append((rule, line_no, line.strip()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan gaemilog markdown for privacy/OSINT risk markers.")
    parser.add_argument("--strict", action="store_true", help="exit 1 when any finding is present")
    parser.add_argument("--include-docs", action="store_true", help="also scan README/policy docs")
    parser.add_argument("--limit", type=int, default=120, help="maximum finding lines to print")
    args = parser.parse_args()

    all_findings: list[tuple[Path, Rule, int, str]] = []
    for path in iter_markdown_files(include_docs=args.include_docs):
        for rule, line_no, line in scan_file(path):
            all_findings.append((path, rule, line_no, line))

    if not all_findings:
        print("privacy_scan: no risk markers found")
        return 0

    print(f"privacy_scan: {len(all_findings)} risk marker(s) found")
    for path, rule, line_no, line in all_findings[: args.limit]:
        rel = path.relative_to(BASE_DIR)
        print(f"{rule.severity.upper()}\t{rule.name}\t{rel}:{line_no}\t{line[:180]}")

    if len(all_findings) > args.limit:
        print(f"... {len(all_findings) - args.limit} more finding(s) omitted")

    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
