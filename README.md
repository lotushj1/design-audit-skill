# Design Audit Skill

平面設計稽核 skill，針對社群圖卡、廣告圖、活動海報、簡報封面、輪播圖與產品宣傳圖做交付前檢查。

這個 skill 不是設計拆解，也不是主觀美感建議。它會列出所有可觀察問題、位置、判定依據與非數值改善方向，並內建台灣語境與廣告風險提醒。

## What It Checks

- 核心訊息是否清楚
- 視覺層級是否正確
- 閱讀動線是否順
- 文字可讀性是否足夠
- 對齊與留白是否穩
- 圖文關係是否互相支援
- 色彩與對比是否服務重點
- CTA / 行動目標是否明確
- 完成度細節
- 文字正確性、台灣語境與廣告風險

## Behavior

- 列出所有檢出的問題，不因輸出精簡而省略。
- 每條問題都要指出位置、判定依據與改善方向。
- 不給 px、百分比、倍數、距離、字級等具體數值。
- 不給主觀建議，例如「更高級」「更活潑」「更有質感」。
- 不檢查品牌一致性。
- 不輸出優點區塊。
- 多張圖會逐張檢查，並補整組輪播邏輯問題。

## Files

```text
design-audit-skill/
├── SKILL.md
└── references/
    └── taiwan-ad-risk.md
```

## Install

Copy this folder into your local skills directory, or symlink it:

```bash
ln -s /path/to/design-audit-skill ~/.claude/skills/design-audit
```

## Legal Note

The Taiwan advertising risk reference is for design review and risk spotting only. It is not legal advice. For high-risk commercial campaigns, regulated products, or formal compliance review, confirm with legal counsel or the relevant authority.

## License

MIT
