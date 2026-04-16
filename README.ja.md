[![header](https://capsule-render.vercel.app/api?type=waving&color=2D5A27&fontColor=FDF6E3&height=180&section=header&text=md-dedupe&fontSize=42&desc=Markdown%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%81%AE%E9%87%8D%E8%A4%87%E6%A4%9C%E5%87%BA%E3%83%BB%E7%B5%B1%E5%90%88%E3%83%84%E3%83%BC%E3%83%AB&descSize=16)](https://github.com/izag8216/md-dedupe)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-78%20passing-green.svg)]()

Markdownベースのナレッジベースは時間とともに重複ファイルが蓄積されます -- エクスポートされたノート、クリップした記事、ブックマークファイル、研究ノート。**md-dedupe** は完全重複と類似重複の両方を検出します。すべてローカル処理、外部API不要。

[English](README.md) | [日本語](#)

## インストール

```bash
pip install md-dedupe
```

## クイックスタート

```bash
# 重複をスキャン
md-dedupe scan /path/to/markdown/files

# URL・フロントマター検出を有効化
md-dedupe scan /path/to/files --check-urls --check-frontmatter

# 類似度閾値を調整
md-dedupe scan /path/to/files --threshold 0.7

# レポート生成
md-dedupe report /path/to/files --format markdown -o report.md

# インタラクティブマージ（デフォルトはdry-run）
md-dedupe merge /path/to/files --interactive

# マージを実行
md-dedupe merge /path/to/files --interactive --apply
```

## 機能

- **完全重複検出** -- SHA-256ボディハッシュ（フロントマター除外）
- **類似重複検出** -- n-gram Jaccard類似度 + サイズプレフィルタ
- **URLベース検出** -- 共通URLを持つファイルをグループ化
- **フロントマター比較** -- title, date, source フィールドで照合
- **Union-Find クラスタリング** -- 複数検出方式の結果を統合
- **複数レポート形式** -- ターミナル（Rich）、JSON、Markdown
- **インタラクティブマージ** -- TUIで重複をレビュー・解消
- **安全なデフォルト** -- dry-runモード、マージ前に自動バックアップ
- **外部API不要** -- すべての処理がローカル

## 設定

プロジェクトルートに `.md-dedupe.toml` を作成:

```toml
threshold = 0.8
ngram_size = 3
check_urls = true
check_frontmatter = true
min_size = 50
url_overlap = 0.8
frontmatter_fields = ["title", "date", "source"]
exclude = [".git", ".obsidian", "node_modules", "__pycache__", ".venv"]
```

## パフォーマンス

| 手法 | 計算量 | 説明 |
|------|--------|------|
| 完全重複 | O(n) | SHA-256単一パス |
| サイズフィルタ | O(n log n) | サイズ差20%以内のペアのみ比較 |
| URL検出 | O(n) | URL→ファイルインデックス構築後、積集合 |
| 類似検出 | O(k) | k = サイズフィルタ後の候補ペア数 |

3000+ファイルを30秒以内に処理。

## ライセンス

MIT
