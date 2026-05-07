本目录 = 每次跑 Week 7/8 时**自动**传给服务端的 X-Experiment-Trace-Dir 根路径；服务在每次成功的 POST /generate|/refine|/edit 下写入子文件夹（含 effective_prompt.txt；request_meta.json 与 request.json 内容相同，大块 base64 为长度+哈希摘要）。

【完整、未删 base64 的请求体】由评估脚本自动写入同级上一层的：
  ../reproducibility_complete/
请打开其中的 README_REPRODUCIBILITY.zh.md 与 INDEX.json。

若需自定义追溯根目录，请使用命令行 --trace-dir（须落在仓库根或 /tmp 下）。
