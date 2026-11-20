# 連結判定驗收

2026-11-20 讀回兩個公開測試來源。W3C 的主機別名回傳 HTTP 301，最終落點是同一站的 WCAG 2.2 文件。此情境應比對最終內容。另一個不存在的文件路徑回傳 HTTP 404，應標為失效。使用新的網址和日期重跑時，保留當次讀回與最後的結果。

- [W3C 來源別名](https://w3.org/TR/WCAG22/) → [最終文件](https://www.w3.org/TR/WCAG22/)
- [刻意不存在的公開測試路徑](https://www.w3.org/TR/WCAG22/release-qa-missing-page-20261120)

帶登入牆、暫時逾時和權限失敗的案例採合成回應。在標明離線驗收的案例中依合成回應判讀；雙 QR 圖的 `.invalid` 網域保留給解碼測試。

[臺北資訊設計夜](fixtures/wcag-poster/)是原始匯出與修正版複驗案例。提供核定交付單和兩個 PNG，核對實際尺寸、透明像素、活動日期、CTA 與兩張圖上的 QR。使用同一引擎回讀 W3C 的兩種網域及最終落點。可單跑 `uv run --python 3.12 --with-requirements requirements.txt python -m unittest discover -s evals -v` 驗證檔案與解碼流程。
