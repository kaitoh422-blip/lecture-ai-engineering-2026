"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from functools import cache
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定された講義回のテーマ、ねらい、要点を取得する。

    質問に「第3回」「3回目」「lecture 3」のような講義回の指定が
    含まれている場合は、他のツールを使用する場合でも必ずこのツールを使う。
    用語の定義だけを調べたい場合には使用しない。

    Args:
        lecture: 確認する講義回。1始まりの整数を指定する。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def make_quiz(lecture: int) -> str:
    """指定した回の用語から 1つを選び、
    確認問題と答えを返す。
    「第2回の確認問題を出して」のように、
    復習用の問題を求められたときに使う。
    """
    terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語は見つかりませんでした。"

    term = random.choice(terms)
    return json.dumps(
        {
            "question": f"「{term['term']}」の意味は？",
            "answer": term["definition"],
        },
        ensure_ascii=False,
    )

def save_learning_log(topic: str, content: str) -> str:
    """学習した内容をMarkdown形式で learning_log フォルダに保存する。

    利用者が学習内容の記録や保存を明確に希望したときに使う。
    ファイルを作成する操作なので、実行前に必ず利用者の承認を得ること。
    単なる質問への回答や、保存を依頼されていない場面では使用しない。

    Args:
        topic: 学習したテーマを短く表したタイトル。
        content: 保存する学習内容、結果、考察。
    """
    log_dir = DATA_DIR.parent / "learning_log"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = log_dir / f"{timestamp}.md"

    markdown = (
        f"# {topic.strip()}\n\n"
        f"- 記録日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"## 学習内容\n\n"
        f"{content.strip()}\n"
    )

    path.write_text(markdown, encoding="utf-8")
    return f"学習記録を保存しました: {path.relative_to(DATA_DIR.parent)}"