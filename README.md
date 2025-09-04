# 索邦大学课程日历生成（M1/M2 UFR Info）

Next.js App Router + Rust (WASM/CLI) 生成可订阅的课程日历（ICS）。Rust 工具拉取官方 ICS 并预处理为 JSON；服务端 API 基于 WASM 生成 ICS，前端选择年级/专业/课程组得到订阅链接。

- 前端路由：内置国际化，使用 `[locale]` 路由（`/zh`、`/fr`）。根路径 `/` 重定向到 `/zh`。
- 数据管线：`data/download/*.ics` → `data/preprocessed/<source>.json`（按来源拆分）→ 前端读取 `public/preprocessed/index.json`（年级索引）。

快速开始
- `bun run preprocess` — 生成 `data/preprocessed/*.json` 和 `public/preprocessed/index.json`
- `bun run dev` — 打开 `http://localhost:3000/zh`
- 选择课程和组后点击生成，支持复制链接、webcal 导入、下载 ICS

脚本（Bun）
- `bun run fetch`：下载 ICS 到 `data/download/`（使用 ETag/Backoff；需要 env）
- `bun run preprocess`：解析 ICS，输出：
  - `data/preprocessed/<source>.json`（例如 `M1_DAC.json`）
  - `public/preprocessed/index.json`（年级索引，结构如下）
- `bun run build:wasm`：编译 Rust `ics_wasm` 到 `public/wasm/ics_wasm.wasm`

索引结构（public/preprocessed/index.json）
```
{
  "M1": {
    "<code>|<source>": { "name": "...", "code": "...", "groups": ["1", "anglais"...], "source": "M1_SESI" },
    ...
  },
  "M2": { ... }
}
```
- 同一代码在不同来源不会合并（按来源拆分）。
- 组完整保留（包括仅有一个组的课程）。

API
- `GET/POST /api/build-ics`
  - 输入：`{ master_year, parcours, items: [{ code, source, group? }], calendar_name }`
  - 按 `source` 加载 `data/preprocessed/<source>.json`，仅在该来源匹配 `code`/`group`；并合并该来源的特殊事件
  - 事件 `SUMMARY` 使用原始 ICS 内容
  - 日历名为 `"<master_year> <parcours>"`

环境变量
- `CAL_USERNAME`, `CAL_PASSWORD`（仅 `fetch` 需要）

常见规则
- 代码归一化：常规课程归 3 位数字（如 `UM5IN653` → `653`）；OIP/Anglais 等文本课程保留文本码
- 组识别：`TD/TP/CM/TME/CS` 与 `Gr2/Groupe 2/G2`；`(en anglais)` 作为课程的 `anglais` 组
- 名称：优先用代码后连字符的下一个 token（如 `UM5IN653-IG3DA-Cours` → `IG3DA`）
