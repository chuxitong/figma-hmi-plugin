# 第 3 周——安装并核验 UI2Code^N

这一周完成了真模型环境下的 smoke test。**当前正式管线**均以 `GET /health` 中 **`model_kind: ui2coden`**、`ui2code_n_active: true` 为准；不满足则 **`hmi_week78_eval.py` 直接退出**，避免把占位后端混进周报数据。环境与权重说明散落在 `help/` 与往期 `reports/deliverables_week4/*`（若仍引用）。
