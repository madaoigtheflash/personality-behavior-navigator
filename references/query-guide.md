# 检索与使用指南

## 一、知识库组成

- `zodiac`：12 个太阳星座文化原型，每个条目含定义、识别、使用、风险与验证问题。
- `mbti`：16 型，每个条目含四功能序列、定义、识别、使用、压力风险与成长动作。
- `function`：Se、Si、Ne、Ni、Te、Ti、Fe、Fi 八项能力。
- `combination`：12×16=192 个组合总览。
- `behavior`：每个组合在协作、初识、冲突、亲密四个场景的行为卡，共 768 条。
- `consensus`：小红书社区叙事与反例的归纳，不代表科学结论。
- `protocol`：事实记录、FAR 修复、边界、实验与复盘协议。

## 二、常用命令

```powershell
python scripts/search_kb.py "白羊 INFJ 冲突后反复解释" --top 10
python scripts/search_kb.py "如何识别外倾情感 Fe" --category function --top 6
python scripts/search_kb.py "第一次认识如何沟通" --context 初识 --top 8
python scripts/search_kb.py "天秤 ENFP" --sign 天秤座 --mbti ENFP --top 8 --json
```

过滤值：

- `--category`：`zodiac|mbti|function|combination|behavior|consensus|protocol`
- `--sign`：中文星座名，如 `白羊座`
- `--mbti`：四字母大写，如 `INFJ`
- `--context`：`协作|初识|冲突|亲密`

## 三、分数怎么读

检索采用三路排序：字符向量余弦、BM25 关键词和元数据精确匹配，再用 RRF 融合。`score` 只表示“与查询有多相关”，不表示内容真伪或人格匹配度。`vector_score` 适合找近义表达，`keyword_score` 适合命中星座、MBTI、功能和场景词。

## 四、推荐问法

高质量问题包含四个槽位：

`场景 + 可观察行为 + 初步类型假设 + 想改变的结果`

例如：“我是白羊座 INFJ。冲突后会连续发长消息解释，对方说需要空间。我想练习停止追问和更短的修复表达。”

低质量问题：“天秤都很冷吗？”“哪个 MBTI 一定适合我？”这类问题应改写成行为问题。

## 五、五步使用法

1. 用类型条目理解术语。
2. 用组合卡生成两到三个假设。
3. 用场景行为卡选择一个微动作。
4. 连续记录两周结果。
5. 如果无效，修改假设，不责怪人格。
