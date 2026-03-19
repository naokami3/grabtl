.PHONY: fmt lint test audit ci

## フォーマット
fmt:
	ruff format src/ tests/

## リント & 型チェック
lint:
	ruff check src/ tests/
	ruff format --check src/ tests/
	mypy src/

## テスト
test:
	pytest

## セキュリティ監査
audit:
	pip-audit

## ライセンスチェック
licenses:
	pip-licenses --order=license --format=markdown

## CI 相当の全チェック
ci: lint test audit
