Fixed X-Experiment-Trace-Dir for Week 8（baseline）

- 客户端路径：`reproducibility_logs/WEEK8_FIXED_SERVER_TRACE_ROOT` → 指向已跑过的 `week8_20260507_074242/`（symlink）。
- **续跑、断点恢复时请始终传同一**：`--trace-dir <repo>/reports/deliverables_week8_prompt_baseline/reproducibility_logs/WEEK8_FIXED_SERVER_TRACE_ROOT`
- 解析后的真实目录与中断前已有 `effective_prompt.txt` / `request.json` **同一棵目录树**，服务端追溯根连续。
- Orchestrator：`reports/scripts/run_week8_two_prompt_profiles.sh` 已固化上述 `--trace-dir`。
- Extended 的另一套固定根：`.../deliverables_week8_prompt_extended/reproducibility_logs/WEEK8_FIXED_SERVER_TRACE_ROOT`（实目录）。
