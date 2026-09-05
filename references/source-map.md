# 来源地图

## 可选输入文档

构建脚本会在 Skill 上级目录查找以下可选文档；也可通过环境变量 `PERSONALITY_KB_SOURCE_DIR` 指定目录。文档不存在时不影响知识库生成。

- `MBTI与荣格八维关系识别参考.md`：模型谱系、八维观察表、16 型四功能、关系硬指标与证据边界。
- `星座-MBTI-荣格八维待人处事识别与调整系统-可行性方案.md`：五层关系雷达、四种沟通频道、白羊 INFJ 工作假设、FAR 修复与十二周训练。
- `GitHub项目参考-星座MBTI荣格八维与行为调整系统.md`：可复用项目、产品架构、隐私与实现取舍。

## 网络共识层

小红书抽样方法、代表笔记和争议见 `xiaohongshu-consensus.md`。只保存归纳，不把评论当作个体诊断规则。

## 数据生成

`scripts/build_kb.py` 是分类和组合库的单一事实源。它生成：

- `references/taxonomy.md`
- `data/knowledge.jsonl`
- `data/vectors.npy`
- `data/keyword_index.json`
- `data/manifest.json`

`scripts/validate_kb.py` 检查分类、组合、场景和索引完整性。
