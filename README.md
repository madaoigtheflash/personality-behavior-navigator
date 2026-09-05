# Personality Behavior Navigator

一个面向 Codex 的中文人格行为导航 Skill：用十二星座文化原型、MBTI 16 型与荣格八种认知功能提出可验证假设，再把观察转成沟通适配、边界判断和行为训练。

> 星座仅作为低权重文化原型；MBTI 与认知功能是偏好语言，不是诊断。明确表达、同意/拒绝、安全、守信和现实行动始终拥有最高权重。

## 数据规模

| 类别 | 数量 |
|---|---:|
| 十二星座 | 12 |
| MBTI 类型 | 16 |
| 认知功能 | 8 |
| 星座 × MBTI 组合 | 192 |
| 协作/初识/冲突/亲密行为卡 | 768 |
| 协议与社区共识 | 11 |
| 总知识条目 | 1007 |

本地索引包含 1007×384 特征哈希向量和 BM25 关键词索引，检索时使用 RRF 融合，无需联网下载嵌入模型。

## 安装

将仓库克隆到 Codex 个人技能目录：

```powershell
git clone https://github.com/madaoigtheflash/personality-behavior-navigator.git "$env:USERPROFILE\.codex\skills\personality-behavior-navigator"
```

然后在 Codex 中调用：

```text
使用 $personality-behavior-navigator，分析我在冲突后追问和过度解释的模式，区分事实、类型假设和替代解释，并设计两周调整实验。
```

## 本地检索

```powershell
python scripts\search_kb.py "白羊座 INFJ 冲突后容易过度解释" --top 8
python scripts\search_kb.py "Ni Fe Ti Se 如何平衡" --category function --top 8
python scripts\search_kb.py "同事协作" --sign 天秤座 --mbti ENFP --context 协作 --json
```

## 重建与验证

依赖 Python 3.10+ 和 NumPy。

```powershell
python scripts\build_kb.py
python scripts\validate_kb.py
```

如需让清单记录外部参考文档的哈希，可设置：

```powershell
$env:PERSONALITY_KB_SOURCE_DIR = '你的参考文档目录'
python scripts\build_kb.py
```

未设置时，脚本默认检查 Skill 的上级目录；文件不存在不会影响构建。

## 目录

```text
SKILL.md                    Codex 工作流和安全边界
agents/openai.yaml          Skill 展示元数据
references/                 分类、证据边界、组合方法及使用指南
data/knowledge.jsonl        结构化知识条目
data/vectors.npy            本地向量矩阵
data/keyword_index.json     BM25 倒排索引
scripts/build_kb.py         数据与索引生成器
scripts/search_kb.py        混合检索 CLI
scripts/validate_kb.py      完整性验证器
```

## 安全边界

- 不根据单句、生日或一次测试给他人定型。
- 不输出“注定匹配”“人格稀有度决定价值”等结论。
- 不把拒绝、拉黑或疏远解释成欲擒故纵。
- 不用于操纵、跟踪、施压、绕过边界或制造情感依赖。
- 新证据与类型假设冲突时，修改假设，而不是否定事实。

## 状态

首版完整性测试：12 星座、16 型、8 功能、192 个组合以及每组合 4 个场景均无缺漏；知识记录、向量行数与关键词索引一致。
