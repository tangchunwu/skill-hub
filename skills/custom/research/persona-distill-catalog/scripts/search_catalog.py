#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path


CATALOG_PATH = Path(__file__).resolve().parent.parent / "references" / "catalog.tsv"


def load_catalog():
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def norm(value):
    return (value or "").casefold()


def score_item(item, terms, category_filter):
    score = 0
    hay_name = norm(item["name"])
    hay_category = norm(item["category"])
    hay_summary = norm(item["summary"])
    hay_url = norm(item["url"])

    if category_filter:
        if category_filter not in hay_category:
            return -1
        score += 3

    for term in terms:
        if term in hay_name:
            score += 6
        if term in hay_category:
            score += 3
        if term in hay_summary:
            score += 2
        if term in hay_url:
            score += 1

    if not terms:
        score += 1

    return score


def search(items, query, category, limit):
    terms = [norm(term) for term in query.split() if term.strip()]
    category_filter = norm(category.strip()) if category else ""
    ranked = []

    for item in items:
        score = score_item(item, terms, category_filter)
        if score < 0:
            continue
        if terms and score == 0:
            continue
        ranked.append((score, item))

    ranked.sort(key=lambda pair: (-pair[0], pair[1]["category"], pair[1]["name"]))
    return [item for _, item in ranked[:limit]]


def print_text(results):
    if not results:
        print("No matching catalog entries.")
        return

    print(f"Found {len(results)} catalog entr{'y' if len(results) == 1 else 'ies'}:")
    for idx, item in enumerate(results, start=1):
        print(f"{idx}. {item['name']} [{item['category']}]")
        print(f"   url: {item['url']}")
        print(f"   summary: {item['summary']}")


def main():
    parser = argparse.ArgumentParser(description="Search the local persona distill catalog.")
    parser.add_argument("terms", nargs="*", help="Search terms")
    parser.add_argument("--query", default="", help="Search query")
    parser.add_argument("--category", default="", help="Filter by category substring")
    parser.add_argument("--limit", type=int, default=8, help="Maximum results")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--list-categories", action="store_true", help="List available categories")
    args = parser.parse_args()

    items = load_catalog()

    if args.list_categories:
        categories = sorted({item["category"] for item in items})
        if args.format == "json":
            print(json.dumps(categories, ensure_ascii=False, indent=2))
        else:
            for category in categories:
                print(category)
        return

    query = " ".join([args.query, *args.terms]).strip()
    results = search(items, query, args.category, args.limit)

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_text(results)


if __name__ == "__main__":
    main()
