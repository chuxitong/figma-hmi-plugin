# 第 7 周——按指令编辑 + **真 Figma** 上下文对照（毕业论文主证据）

本周交付分两块，**写作文时不能混成一个「都做了 variables」的结论**：

**A.** 四条顺序 **`/edit`**：仍在 `mockups/png/04-operator-panel.png` + 脚本 **`synthetic_context`** 上走完，用来展示：**指令是否合理落实、是否存在整页牵连改写**。定性填法见 `WEEK7_MANIFEST.json` 里的 `edit_qualitative_template_for_thesis_zh`。

**B.（答辩主图来源）`**--context-mode from-json`：使用本机插件导出的 **`figma_native/*.payload.json`** 各跑一次 **`/generate`**。插图改为**两张各自独立**的全宽幻灯片：**`THESIS_slide_image_only_context`** 与 **`THESIS_slide_full_figma_context`**（避免旧三栏拼图字太小）。

**复盘命令**与服务端 HEALTH 校验见 **`help/毕业论文实验-Git与Figma真实上下文.zh.md` §4**；可追溯请求体只在 **`reproducibility_complete/*.full.json.gz`**，不以单独剧情 `prompts.json` 顶替。
