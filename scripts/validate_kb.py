#!/usr/bin/env python3
"""Validate taxonomy coverage, cross-product coverage and index integrity."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict

import numpy as np

from build_kb import CONTEXTS, DATA, FUNCTIONS, MBTIS, ZODIACS


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    required = [DATA / "knowledge.jsonl", DATA / "vectors.npy", DATA / "keyword_index.json", DATA / "manifest.json"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        fail("缺少生成文件：" + "、".join(missing))
    knowledge = DATA / "knowledge.jsonl"
    docs = [json.loads(line) for line in knowledge.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [d["id"] for d in docs]
    if len(ids) != len(set(ids)):
        fail("知识条目 id 重复")
    counts = Counter(d["category"] for d in docs)
    expected = {"zodiac": 12, "mbti": 16, "function": 8, "combination": 192, "behavior": 768, "protocol": 5, "consensus": 6}
    for key, value in expected.items():
        if counts[key] != value:
            fail(f"{key} 数量错误：{counts[key]} != {value}")
    signs = {z["name"] for z in ZODIACS}
    mbtis = {m["type"] for m in MBTIS}
    funcs = {f["code"] for f in FUNCTIONS}
    if {d["metadata"]["sign"] for d in docs if d["category"] == "zodiac"} != signs:
        fail("星座集合不完整")
    if {d["metadata"]["mbti"] for d in docs if d["category"] == "mbti"} != mbtis:
        fail("MBTI 集合不完整")
    if {d["metadata"]["function"] for d in docs if d["category"] == "function"} != funcs:
        fail("认知功能集合不完整")
    combo_set = {(d["metadata"]["sign"], d["metadata"]["mbti"]) for d in docs if d["category"] == "combination"}
    expected_combos = {(s, m) for s in signs for m in mbtis}
    if combo_set != expected_combos:
        fail(f"组合缺漏：{sorted(expected_combos - combo_set)}")
    behavior = defaultdict(set)
    for d in docs:
        if d["category"] == "behavior":
            meta = d["metadata"]
            behavior[(meta["sign"], meta["mbti"])].add(meta["context"])
    for combo in expected_combos:
        if behavior[combo] != set(CONTEXTS):
            fail(f"场景缺漏：{combo} -> {behavior[combo]}")
    vectors = np.load(DATA / "vectors.npy", allow_pickle=False)
    if vectors.shape != (len(docs), 384):
        fail(f"向量尺寸错误：{vectors.shape}")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.all((norms > 0.99) & (norms < 1.01)):
        fail("存在未归一化向量")
    index = json.loads((DATA / "keyword_index.json").read_text(encoding="utf-8"))
    if index["doc_count"] != len(docs) or len(index["lengths"]) != len(docs):
        fail("关键词索引与文档数量不一致")
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(knowledge.read_bytes()).hexdigest()
    if manifest["knowledge_sha256"] != digest:
        fail("知识库哈希与清单不一致")
    print(json.dumps({"ok": True, "total_records": len(docs), "counts": dict(sorted(counts.items())), "vectors": list(vectors.shape), "combinations": len(combo_set), "contexts_per_combination": len(CONTEXTS)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise
