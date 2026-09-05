#!/usr/bin/env python3
"""Search the local personality behavior knowledge base with hybrid retrieval."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from build_kb import DATA, hashed_vector, tokens


def load_docs() -> list[dict]:
    path = DATA / "knowledge.jsonl"
    if not path.exists():
        raise SystemExit("知识库尚未生成，请先运行 python scripts/build_kb.py")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def bm25(query: str, index: dict) -> np.ndarray:
    n = index["doc_count"]
    scores = np.zeros(n, dtype=np.float32)
    qtokens = set(tokens(query))
    k1, b = 1.5, 0.75
    avgdl = max(float(index["avgdl"]), 1.0)
    lengths = index["lengths"]
    postings = index["postings"]
    for tok in qtokens:
        plist = postings.get(tok)
        if not plist:
            continue
        df = len(plist)
        idf = math.log(1.0 + (n - df + 0.5) / (df + 0.5))
        for doc_id, tf in plist:
            denom = tf + k1 * (1.0 - b + b * lengths[doc_id] / avgdl)
            scores[doc_id] += idf * (tf * (k1 + 1.0) / denom)
    return scores


def metadata_score(query: str, doc: dict) -> float:
    q = query.lower()
    meta = doc.get("metadata", {})
    values = [doc.get("title", ""), meta.get("sign", ""), meta.get("mbti", ""), meta.get("context", ""), meta.get("function", "")]
    score = 0.0
    for value in values:
        if isinstance(value, str) and value and value.lower() in q:
            score += 1.0
    return score


def rank_positions(scores: np.ndarray, candidates: np.ndarray) -> dict[int, int]:
    ids = np.flatnonzero(candidates)
    ordered = ids[np.argsort(-scores[ids], kind="stable")]
    return {int(doc_id): rank + 1 for rank, doc_id in enumerate(ordered)}


def search(query: str, docs: list[dict], vectors: np.ndarray, index: dict, args: argparse.Namespace) -> list[dict]:
    candidates = np.ones(len(docs), dtype=bool)
    for i, doc in enumerate(docs):
        meta = doc.get("metadata", {})
        if args.category and doc.get("category") != args.category:
            candidates[i] = False
        if args.sign and meta.get("sign") != args.sign:
            candidates[i] = False
        if args.mbti and meta.get("mbti") != args.mbti.upper():
            candidates[i] = False
        if args.context and meta.get("context") != args.context:
            candidates[i] = False
    if not candidates.any():
        return []

    qvec = hashed_vector(query)
    vector_scores = vectors @ qvec
    keyword_scores = bm25(query, index)
    meta_scores = np.array([metadata_score(query, d) for d in docs], dtype=np.float32)
    vrank = rank_positions(vector_scores, candidates)
    krank = rank_positions(keyword_scores, candidates)
    mrank = rank_positions(meta_scores, candidates)
    fused = defaultdict(float)
    for doc_id in np.flatnonzero(candidates):
        i = int(doc_id)
        fused[i] = 1.0 / (60 + vrank[i]) + 1.15 / (60 + krank[i]) + 0.55 / (60 + mrank[i])
    ordered = sorted(fused, key=fused.get, reverse=True)[: args.top]
    return [{
        "rank": rank,
        "id": docs[i]["id"],
        "category": docs[i]["category"],
        "title": docs[i]["title"],
        "content": docs[i]["content"],
        "metadata": docs[i].get("metadata", {}),
        "score": round(fused[i], 6),
        "vector_score": round(float(vector_scores[i]), 6),
        "keyword_score": round(float(keyword_scores[i]), 6),
    } for rank, i in enumerate(ordered, 1)]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="检索星座×MBTI×荣格八维行为知识库")
    p.add_argument("query", help="自然语言查询")
    p.add_argument("--top", type=int, default=8, help="返回条数")
    p.add_argument("--category", choices=["zodiac", "mbti", "function", "combination", "behavior", "consensus", "protocol"])
    p.add_argument("--sign", help="星座，例如白羊座")
    p.add_argument("--mbti", help="MBTI，例如 INFJ")
    p.add_argument("--context", choices=["协作", "初识", "冲突", "亲密"])
    p.add_argument("--json", action="store_true", help="输出 JSON")
    return p.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    if args.top < 1 or args.top > 100:
        raise SystemExit("--top 必须在 1 到 100 之间")
    docs = load_docs()
    vectors = np.load(DATA / "vectors.npy", allow_pickle=False)
    index = json.loads((DATA / "keyword_index.json").read_text(encoding="utf-8"))
    results = search(args.query, docs, vectors, index, args)
    if args.json:
        print(json.dumps({"query": args.query, "count": len(results), "results": results}, ensure_ascii=False, indent=2))
        return
    if not results:
        print("没有命中过滤条件，请放宽 --category/--sign/--mbti/--context。")
        return
    for item in results:
        print(f"[{item['rank']}] {item['title']}  ({item['category']}, score={item['score']})")
        print(item["content"])
        print()


if __name__ == "__main__":
    main()
