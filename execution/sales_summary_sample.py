#!/usr/bin/env python3
"""
sales_summary_sample.py — 일별/월별 매출 집계 샘플 스크립트

목적:
  Zero-Inference Rule 예제 — AI가 숫자를 직접 계산하지 않고,
  이런 스크립트의 결과를 인용하도록 하는 모범 사례.

사용법:
  python execution/sales_summary_sample.py [CSV 경로]

기본값:
  CSV 경로 생략 시 아래 sample_data를 사용 (수강생이 구조 이해용).

실제 사용 시:
  1. 본인 결제 데이터를 CSV로 내보낸다 (라이브클래스, 스마트스토어, 페이팔 등)
  2. 아래 CSV_SCHEMA에 맞춰 컬럼명 매핑
  3. 크론이나 수동 실행으로 일/주/월 단위 집계
  4. 결과물(sales_summary.md)을 AI가 참조

CSV_SCHEMA (예시):
  date,product,amount,channel,status
  2026-04-01,부트캠프1기,2800000,homepage,paid
  2026-04-01,VOD단품,99500,instagram,paid
"""

import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# --- 샘플 데이터 (수강생이 CSV 없을 때 동작 확인용) ------------------------
sample_data = [
    {"date": "2026-04-01", "product": "메인코스", "amount": 450000, "channel": "instagram", "status": "paid"},
    {"date": "2026-04-01", "product": "입문코스", "amount": 99000, "channel": "youtube", "status": "paid"},
    {"date": "2026-04-02", "product": "메인코스", "amount": 450000, "channel": "instagram", "status": "paid"},
    {"date": "2026-04-02", "product": "1:1 코칭", "amount": 1500000, "channel": "community", "status": "paid"},
    {"date": "2026-04-03", "product": "입문코스", "amount": 99000, "channel": "instagram", "status": "paid"},
    {"date": "2026-04-03", "product": "입문코스", "amount": 99000, "channel": "instagram", "status": "refunded"},
    {"date": "2026-04-04", "product": "메인코스", "amount": 450000, "channel": "youtube", "status": "paid"},
    {"date": "2026-04-05", "product": "메인코스", "amount": 450000, "channel": "instagram", "status": "paid"},
    {"date": "2026-04-05", "product": "VOD단품", "amount": 49000, "channel": "email", "status": "paid"},
    {"date": "2026-04-06", "product": "메인코스", "amount": 450000, "channel": "community", "status": "paid"},
    {"date": "2026-04-07", "product": "1:1 코칭", "amount": 1500000, "channel": "community", "status": "paid"},
]


# --- 유틸 함수 --------------------------------------------------------------

def load_csv(path: Path) -> list[dict]:
    """CSV 파일을 읽어 dict 리스트로 반환. 금액은 int 변환."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["amount"] = int(row["amount"])
            rows.append(row)
    return rows


def filter_paid(rows: list[dict]) -> list[dict]:
    """환불 제외, 결제 완료만 집계."""
    return [r for r in rows if r["status"] == "paid"]


def group_by_date(rows: list[dict]) -> dict[str, int]:
    buckets = defaultdict(int)
    for r in rows:
        buckets[r["date"]] += r["amount"]
    return dict(sorted(buckets.items()))


def group_by_product(rows: list[dict]) -> dict[str, int]:
    buckets = defaultdict(int)
    for r in rows:
        buckets[r["product"]] += r["amount"]
    return dict(sorted(buckets.items(), key=lambda x: -x[1]))


def group_by_channel(rows: list[dict]) -> dict[str, int]:
    buckets = defaultdict(int)
    for r in rows:
        buckets[r["channel"]] += r["amount"]
    return dict(sorted(buckets.items(), key=lambda x: -x[1]))


def refund_rate(all_rows: list[dict]) -> float:
    if not all_rows:
        return 0.0
    refunds = sum(1 for r in all_rows if r["status"] == "refunded")
    return refunds / len(all_rows) * 100


# --- 리포트 출력 ------------------------------------------------------------

def format_money(amount: int) -> str:
    return f"{amount:,}원"


def print_report(all_rows: list[dict]) -> None:
    paid = filter_paid(all_rows)
    total = sum(r["amount"] for r in paid)

    print("=" * 60)
    print("  매출 집계 리포트 (sales_summary_sample.py)")
    print(f"  생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    print(f"총 매출 (결제 완료): {format_money(total)}")
    print(f"거래 건수: {len(paid)}건")
    print(f"평균 객단가 (AOV): {format_money(total // len(paid)) if paid else '0원'}")
    print(f"환불률: {refund_rate(all_rows):.1f}%")
    print()

    print("-- 일별 매출 --")
    for date, amount in group_by_date(paid).items():
        print(f"  {date}: {format_money(amount)}")
    print()

    print("-- 상품별 매출 (내림차순) --")
    for product, amount in group_by_product(paid).items():
        pct = amount / total * 100 if total else 0
        print(f"  {product}: {format_money(amount)}  ({pct:.1f}%)")
    print()

    print("-- 채널별 매출 (내림차순) --")
    for channel, amount in group_by_channel(paid).items():
        pct = amount / total * 100 if total else 0
        print(f"  {channel}: {format_money(amount)}  ({pct:.1f}%)")
    print()

    print("=" * 60)
    print("  📌 김이사 참고: 이 결과를 그대로 보고서에 인용하십시오.")
    print("     추정/계산 금지 (Zero-Inference Rule).")
    print("=" * 60)


# --- 메인 ------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            print(f"[오류] CSV 파일을 찾을 수 없습니다: {csv_path}", file=sys.stderr)
            sys.exit(1)
        rows = load_csv(csv_path)
        print(f"[정보] {csv_path}에서 {len(rows)}건 로드")
    else:
        rows = sample_data
        print("[정보] 샘플 데이터 사용 (실사용 시 CSV 경로 인자로 전달)")
    print()

    print_report(rows)


if __name__ == "__main__":
    main()
