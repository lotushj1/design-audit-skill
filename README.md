# Design Audit Skill

平面設計稽核 skill,針對社群圖卡、廣告圖、活動海報、簡報封面、輪播圖與產品宣傳圖做交付前檢查。

這個 skill 不是設計拆解,也不是主觀美感建議。它會列出所有可觀察問題、位置、判定依據與非數值改善方向,並內建台灣語境與廣告風險提醒。

## Usage

安裝後,把圖片丟給 Claude,說類似這些話就會觸發:

- 「幫我檢查這張圖能不能交付」
- 「這組輪播圖交付前幫我稽核一下」
- 「幫我看這張廣告圖有沒有錯字或廣告風險」

輸出範例(節錄):

```markdown
## promo-banner.png

作品類型:廣告圖
可交付性:建議修改後交付
整體判斷:主標與優惠條件層級混亂,且優惠文字有廣告風險。

### 完整問題清單

| 嚴重度 | 檢查目標 | 位置 | 問題 | 判定依據 | 改善方向 |
|---|---|---|---|---|---|
| High | 視覺層級 | 上方主標與副標 | 主副標層級太接近 | 第一眼不容易判斷哪一句是主訊息 | 需要拉開主標與副標的視覺層級 |

### 文字與廣告風險提醒

| 原文 | 風險類型 | 可能問題 | 建議改法 |
|---|---|---|---|
| 保證最低價 | 疑似廣告風險 | 絕對化說法,無佐證時可能有誤導風險 | 改為可佐證、條件清楚的說法 |
```

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

## What It Doesn't Do

- Logo 設計評審
- 品牌識別系統與品牌一致性檢查
- 書籍、型錄等長篇排版
- 印刷出血、色彩模式、刀模等印前工程
- UI 介面設計細節
- 法律意見(廣告風險只標示「疑似風險 / 建議確認」,不下違法結論)

## Behavior

- 列出所有檢出的問題,不因輸出精簡而省略。
- 每條問題都要指出位置、判定依據與改善方向。
- 不給 px、百分比、倍數、距離、字級等具體數值。
- 不給主觀建議,例如「更高級」「更活潑」「更有質感」。
- 不輸出優點區塊。
- 多張圖會逐張檢查,並補整組輪播邏輯問題。
- 一律以繁體中文與台灣用語輸出。

## Requirements

需要支援視覺輸入(圖片)的 Claude 模型與環境,例如 Claude Code、Claude.ai 或 Claude API。

## Files

```text
design-audit-skill/
├── SKILL.md
└── references/
    └── taiwan-ad-risk.md
```

## Install

skill 目錄名稱需與 skill 名稱一致(`design-audit`)。

**個人層級(Claude Code)**——所有專案可用:

```bash
ln -s /path/to/design-audit-skill ~/.claude/skills/design-audit
```

**專案層級(Claude Code)**——跟著 repo 走,團隊共用:

```bash
cp -r /path/to/design-audit-skill your-project/.claude/skills/design-audit
```

其他環境(Claude.ai、Claude API)的安裝方式見官方文件:[Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)。

## Legal Note

The Taiwan advertising risk reference is for design review and risk spotting only. It is not legal advice. For high-risk commercial campaigns, regulated products, or formal compliance review, confirm with legal counsel or the relevant authority.

法規會變動。`references/taiwan-ad-risk.md` 內標有資料查核日期,建議定期比對官方來源更新。

## License

MIT
