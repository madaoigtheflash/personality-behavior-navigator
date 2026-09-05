#!/usr/bin/env python3
"""Build the complete taxonomy, combination library and local hybrid index."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REFS = ROOT / "references"
DIM = 384
CONTEXTS = ("协作", "初识", "冲突", "亲密")


ZODIACS = [
    dict(name="白羊座", dates="3月21日—4月19日", element="火", modality="本位",
         definition="以启动、直接和竞争为核心的文化原型；关注先行动再校准，能量外显、节奏偏快。",
         signals=["遇到机会时倾向迅速表态或先做一步", "不耐长时间含糊，偏好明确回应", "受阻时可能提高强度，冷却后又较快翻篇"],
         use="给清晰目标、短反馈周期和可自主推进的空间；提醒其在重要关系里加入停顿与确认。",
         risks="把急切误作恶意，或把主动误作长期承诺；原型放大时可能抢答、追问、先斩后奏。",
         question="你更希望现在先行动，还是先把风险和边界讲清？", expression="快速启动、直说重点", regulator="停十分钟、确认对方节奏"),
    dict(name="金牛座", dates="4月20日—5月20日", element="土", modality="固定",
         definition="以稳定、感官体验和资源守成为核心的文化原型；重视可持续、熟悉感与可靠兑现。",
         signals=["改变前会反复确认成本和可行性", "更相信持续行动而非即时热情", "受到催促时可能沉默、拖延或更坚持原方案"],
         use="用具体安排、稳定节奏和可见收益沟通；变更时给准备时间并说明不变部分。",
         risks="把谨慎误作冷淡，或把坚持美化成拒绝协商；原型放大时可能固守舒适区。",
         question="哪些部分必须保持稳定，哪些部分可以小步试验？", expression="稳步兑现、重视实际体验", regulator="设置小变更和复盘点"),
    dict(name="双子座", dates="5月21日—6月21日", element="风", modality="变动",
         definition="以信息交换、好奇和快速切换为核心的文化原型；通过说、问、连接概念来保持活力。",
         signals=["会同时追踪多个话题并快速联想", "用提问、玩笑或转述确认理解", "无聊或压力下可能频繁换题、承诺分散"],
         use="允许探索多个选项，再用书面摘要收束；把有趣讨论落成一个下一步。",
         risks="把活跃误作肤浅或把健谈误作真实亲密；原型放大时可能信息很多但执行不足。",
         question="这些想法里，你最想先验证哪一个？", expression="快速交流、跨题连接", regulator="一次只兑现一个下一步"),
    dict(name="巨蟹座", dates="6月22日—7月22日", element="水", modality="本位",
         definition="以照顾、安全感和关系记忆为核心的文化原型；对熟悉圈层和情绪氛围较敏感。",
         signals=["会记住关系细节并通过照顾表达投入", "决策时关注谁会受影响以及是否安全", "受伤时可能退回保护壳、间接表达或反复回想"],
         use="先承认感受与关系影响，再讨论解决；建立稳定联系规则而非猜测。",
         risks="把关心误作同意，或把敏感当作事实证据；原型放大时可能过度保护或情绪化回撤。",
         question="现在你更需要被理解、被陪伴，还是一起解决？", expression="照顾氛围、维系安全", regulator="把需要说清而非让人猜"),
    dict(name="狮子座", dates="7月23日—8月22日", element="火", modality="固定",
         definition="以自我表达、尊严和创造性领导为核心的文化原型；希望投入被看见，也愿意承担中心责任。",
         signals=["在群体中愿意站出来组织、展示或保护他人", "对公开否定和忽视较敏感", "认同目标时有持续热情，不认同时可能明显退场"],
         use="真诚指出具体贡献，私下给纠偏；提供能承担责任又不必证明价值的角色。",
         risks="把表现欲等同自恋，或用赞美换服从；原型放大时可能面子防御、控制舞台。",
         question="你希望这件事里承担什么角色，怎样的反馈对你最有用？", expression="鲜明表达、承担舞台", regulator="区分尊严受损与意见分歧"),
    dict(name="处女座", dates="8月23日—9月22日", element="土", modality="变动",
         definition="以改进、分辨和服务为核心的文化原型；习惯发现误差、优化流程并把关细节。",
         signals=["容易先看到哪里可以更准确或更高效", "通过帮忙、提醒和整理表达重视", "压力下可能过度检查、挑剔自己或他人"],
         use="给标准、优先级和完成定义；先确认对方是否需要建议，再提供优化。",
         risks="把纠错误作不满，或把高标准当唯一标准；原型放大时可能完美主义和微管理。",
         question="这次需要做到合格、优秀，还是接近完美？", expression="拆解细节、持续优化", regulator="先完成再改进，限制检查次数"),
    dict(name="天秤座", dates="9月23日—10月23日", element="风", modality="本位",
         definition="以平衡、互惠和关系协商为核心的文化原型；会比较多方立场并追求体面、公平的互动。",
         signals=["表达前常考虑各方接受度和措辞", "擅长找共同点、调解或提供多个方案", "压力下可能延迟决定、表面同意后再撤回"],
         use="给有限选项、明确截止时间和无惩罚的不同意空间；直接问真实偏好。",
         risks="把礼貌误作好感或承诺，把犹豫误作操控；原型放大时可能回避冲突、外包决定。",
         question="如果不用照顾任何人的期待，你自己最倾向哪个选项？", expression="比较立场、体面协商", regulator="给出清晰偏好和截止时间"),
    dict(name="天蝎座", dates="10月24日—11月22日", element="水", modality="固定",
         definition="以深度、信任和边界控制为核心的文化原型；重视隐私、忠诚和关系中的真实动机。",
         signals=["对表面答案不满足，会追踪一致性和隐含动机", "建立信任较慢，一旦投入可能很深", "受威胁时可能测试、收紧信息或长时间记住背叛"],
         use="保持诚实一致，尊重隐私；敏感问题先说明目的并允许拒答。",
         risks="把警觉浪漫化成洞察，把占有或测试解释成深情；原型放大时可能猜疑与控制。",
         question="要让这件事足够安全，你需要哪些透明度和边界？", expression="深入核验、重视忠诚", regulator="用直接询问替代测试和揣测"),
    dict(name="射手座", dates="11月23日—12月21日", element="火", modality="变动",
         definition="以探索、意义和自由为核心的文化原型；偏好拓展经验、直率表达和面向远方。",
         signals=["容易被新体验、旅行、学习或大问题激活", "说话直、先讲总体意义", "感到束缚时可能淡化细节、改计划或迅速离开"],
         use="说明目标意义并保留自主空间，同时把自由与兑现责任绑定。",
         risks="把自由误作不负责，或把直率当免除影响的理由；原型放大时可能过度承诺。",
         question="你想保留哪些自由，同时愿意承担哪些确定责任？", expression="扩展视野、直接乐观", regulator="把远景拆成日期与责任"),
    dict(name="摩羯座", dates="12月22日—1月19日", element="土", modality="本位",
         definition="以责任、结构和长期成就为核心的文化原型；重视等级、时间成本与可积累成果。",
         signals=["倾向先确定目标、路径和责任人", "用解决问题、承担任务表达重视", "压力下可能情感收缩、工作化或以结果压过过程"],
         use="带着事实、优先级和长期收益沟通；在效率之外明确关系影响和恢复时间。",
         risks="把克制误作无情，把成就当全部价值；原型放大时可能控制、悲观或过度工作。",
         question="这个目标的最低成功标准和可持续节奏是什么？", expression="结构推进、长期负责", regulator="把情绪与休息纳入计划"),
    dict(name="水瓶座", dates="1月20日—2月18日", element="风", modality="固定",
         definition="以独立、系统创新和群体视角为核心的文化原型；喜欢跳出惯例并保持思想自主。",
         signals=["会提出非主流框架或从系统层面重构问题", "尊重思想自由，偏好平等而非情绪强迫", "压力下可能抽离、理智化或固守反常规立场"],
         use="给问题空间和论证自由，再明确现实影响；避免用群体压力逼迫表态。",
         risks="把独立误作冷漠，把新奇当正确；原型放大时可能为了反对而反对。",
         question="你的新方案解决了什么，同时会给具体的人带来什么影响？", expression="独立建模、系统创新", regulator="把抽象原则落到人的体验"),
    dict(name="双鱼座", dates="2月19日—3月20日", element="水", modality="变动",
         definition="以共情、想象和边界流动为核心的文化原型；容易通过氛围、象征和情感联结理解世界。",
         signals=["能感受细微氛围并用故事、艺术或隐喻表达", "愿意包容复杂感受和多重可能", "压力下可能逃避现实、理想化或承担不属于自己的情绪"],
         use="先容纳感受，再用时间、责任和边界把愿望落地；确认帮助是否被请求。",
         risks="把共情误作事实，把拯救当亲密；原型放大时可能界限模糊、失望后消失。",
         question="哪些是你的感受和责任，哪些属于对方？", expression="共情想象、容纳复杂", regulator="写下边界、事实和下一步"),
]


MBTIS = [
    dict(type="ISTJ", stack=["Si","Te","Fi","Ne"], definition="以内倾感觉保存可靠经验，以外倾思维组织执行；偏好清晰职责、已验证方法和稳定兑现。", signals=["先核对先例、细节和规则", "承诺后按步骤完成", "突发变化多时容易谨慎或质疑"], use="提前给事实、标准、日期与变更原因；认可其稳定性并允许核验。", risks="过度依赖旧经验、把规则等同正确，压力下灾难化未知。", growth="小范围试验新方案，练习在不完美信息下做可逆决定。", channel="经验与执行", decision="可靠性、标准和责任"),
    dict(type="ISFJ", stack=["Si","Fe","Ti","Ne"], definition="以内倾感觉维持熟悉与连续，以外倾情感照顾关系；常用细致服务和稳定陪伴表达在意。", signals=["记得他人习惯和重要细节", "主动补位、维护和谐", "冲突时可能先压下自己需要"], use="真诚感谢具体付出，私下询问真实负担；给稳定安排和拒绝空间。", risks="过度承担、间接期待回报，压力下担忧各种坏可能。", growth="练习直接说需要与不愿意，并允许别人承担后果。", channel="熟悉经验与关系影响", decision="照顾、连续性和可行性"),
    dict(type="INFJ", stack=["Ni","Fe","Ti","Se"], definition="以内倾直觉收敛意义和方向，以外倾情感协调关系；常把长期图景、他人需要和内部逻辑整合。", signals=["从零散信息提炼单一主题或趋势", "关注话语对关系与群体的影响", "独处时反复分析意义，现实细节可能滞后"], use="先确认愿景与关系影响，再给少量可执行事实；允许安静加工，不逼迫即时表态。", risks="读心、过度负责他人感受、形成单一路径，压力下冲动感官补偿或信息过载。", growth="用 Ti 写出证据与反证，用 Se 做短时现实行动；未经验证不替他人定义动机。", channel="意义与关系影响", decision="长期一致性、价值影响和内在逻辑"),
    dict(type="INTJ", stack=["Ni","Te","Fi","Se"], definition="以内倾直觉形成长期模型，以外倾思维配置资源；偏好自主、战略一致与高杠杆行动。", signals=["迅速收敛核心问题和长期路径", "要求标准、效率与可验证结果", "对低效社交或反复解释耐心较低"], use="直说目标、约束和证据，允许独立方案；不同意时针对模型而非人格。", risks="过早收敛、忽略过程感受，压力下僵化控制或感官冲动。", growth="主动收集反例和一线反馈，把关系影响纳入成功标准。", channel="趋势与系统执行", decision="长期杠杆、效率和原则"),
    dict(type="ISTP", stack=["Ti","Se","Ni","Fe"], definition="以内倾思维拆解机制，以外倾感觉即时试验；偏好亲手解决、简洁交流与行动自由。", signals=["遇到问题先看结构和故障点", "在现场快速试错", "对冗长情绪说明可能沉默或退出"], use="给问题、工具和操作空间；表达情绪时同时说明具体请求。", risks="过度抽离、低估关系反馈，压力下突然寻求认可或情绪爆发。", growth="在解决前复述对方体验，并提前说明沉默不等于拒绝。", channel="机制与现场事实", decision="逻辑可行、即时反馈和自由"),
    dict(type="ISFP", stack=["Fi","Se","Ni","Te"], definition="以内倾情感守护个人价值，以外倾感觉回应当下体验；偏好真诚、审美、自由和少干预。", signals=["对喜欢与不喜欢有细腻但未必外显的判断", "通过行动、体验或创作表达", "被强迫定义时可能退开"], use="尊重其节奏与选择，给具体体验而非抽象施压；邀请表达真实偏好。", risks="回避结构、把沉默当边界已被理解，压力下突然严苛或控制。", growth="用简短 Te 清单表达期限、责任和请求，不靠别人猜。", channel="个人价值与当下体验", decision="真实感、自由和具体感受"),
    dict(type="INFP", stack=["Fi","Ne","Si","Te"], definition="以内倾情感辨别个人价值，以外倾直觉探索可能；重视真实、意义和不伤害核心身份的选择。", signals=["先问是否符合内心价值", "能看到人物和情境的多种可能", "对被误解或价值被压平较敏感"], use="先尊重价值和意图，再讨论结构；用邀请而非命令，让其自己选择表达。", risks="理想化、推迟落地、用感受代替共同事实，压力下突然苛刻效率化。", growth="把价值写成可观察行为和期限，每次只兑现一个小承诺。", channel="个人意义与多种可能", decision="真实性、可能性和价值一致"),
    dict(type="INTP", stack=["Ti","Ne","Si","Fe"], definition="以内倾思维追求模型自洽，以外倾直觉生成解释；偏好概念精确、探索自由和低压社交。", signals=["会追问定义、前提和例外", "同时提出多个假说", "执行重复事务或处理情绪暗示时可能延迟"], use="给完整问题和讨论空间，再共同约定一个实验；避免用身份或权威代替论证。", risks="分析停滞、忽略时限与影响，压力下对认可过敏或笨拙讨好。", growth="为分析设置停止条件，用一句话确认他人感受和下一步。", channel="概念逻辑与可能性", decision="自洽、解释力和可证伪性"),
    dict(type="ESTP", stack=["Se","Ti","Fe","Ni"], definition="以外倾感觉抓取现场机会，以内倾思维快速判断机制；偏好即时反馈、挑战和灵活行动。", signals=["迅速注意环境变化和可用资源", "边做边修正而非长时间预演", "节奏慢或限制多时容易失去耐心"], use="把目标变成短回合挑战，给实时反馈和清晰底线；长远风险用具体后果呈现。", risks="低估远期成本、用魅力越过讨论，压力下形成极端负面预感。", growth="重大决定强制隔夜并写三种长期后果。", channel="现场事实与实用机制", decision="即时可行、收益和行动自由"),
    dict(type="ESFP", stack=["Se","Fi","Te","Ni"], definition="以外倾感觉投入当下，以内倾情感判断真实喜欢；偏好鲜活体验、自然表达和具体回应。", signals=["用共同活动、气氛和即时照顾建立连接", "个人好恶鲜明但不一定理论化", "过度规划或批评气氛会迅速降温"], use="先共同体验和肯定真实感受，再给短而明确的安排；反馈具体、及时。", risks="回避枯燥规划、把当下热情当长期承诺，压力下悲观收窄。", growth="在兴奋时记录期限与资源，定期检查长期方向。", channel="当下体验与个人价值", decision="真实愉悦、现实反馈和自由"),
    dict(type="ENFP", stack=["Ne","Fi","Te","Si"], definition="以外倾直觉探索人和世界的可能，以内倾情感筛选价值；偏好灵感、真诚和自主成长。", signals=["快速联想并给人或项目看到新可能", "热情投入符合价值的方向", "重复维护和细节收尾可能波动"], use="允许发散，再共同选一个最有价值的下一步；把截止和责任可视化。", risks="过度承诺、理想化关系、厌倦维护，压力下执着细节或旧错。", growth="限制同时进行项目数，用固定复盘把灵感转成稳定行为。", channel="可能性与个人意义", decision="成长空间、真实性和行动影响"),
    dict(type="ENTP", stack=["Ne","Ti","Fe","Si"], definition="以外倾直觉生成新框架，以内倾思维检验逻辑；偏好辩论、重构和开放选项。", signals=["迅速发现替代方案和规则漏洞", "通过辩论测试想法而不一定反对人", "重复执行或被要求过早定论时可能逃开"], use="允许挑战前提并设清楚讨论终点；要求把最佳想法变成一次实验。", risks="为辩而辩、忽略情绪影响、承诺分散，压力下纠结细节。", growth="先征得辩论同意，记录决定并完成一个闭环再开新题。", channel="可能性与模型检验", decision="新颖性、逻辑和选择空间"),
    dict(type="ESTJ", stack=["Te","Si","Ne","Fi"], definition="以外倾思维组织结果，以内倾感觉维持标准；偏好明确责任、效率和经验证流程。", signals=["自然分配任务、设指标和追进度", "重视规则、记录与可复现性", "模糊讨论时会推动快速决定"], use="带数据、方案和责任边界；若需情绪支持，直接说明此刻不求解决。", risks="把效率压过人、把熟悉流程当唯一答案，压力下价值受伤却难表达。", growth="每次纠偏先询问障碍与影响，把不同价值作为约束条件。", channel="结果标准与可靠经验", decision="效率、责任和可复制性"),
    dict(type="ESFJ", stack=["Fe","Si","Ne","Ti"], definition="以外倾情感维护群体，以内倾感觉延续照顾方式；偏好互惠、明确礼仪和稳定联系。", signals=["主动组织、问候并注意谁被忽略", "依照共同习惯表达重视", "关系反馈模糊时可能焦虑或加大照顾"], use="及时回应并清楚表达感谢、不同意和界限；不要用含糊让其猜。", risks="过度在意评价、用照顾换一致，压力下逻辑挑剔或关系控制。", growth="把善意与他人自主分开，练习接受不回应和不同选择。", channel="群体影响与熟悉照顾", decision="互惠、稳定和共同接受度"),
    dict(type="ENFJ", stack=["Fe","Ni","Se","Ti"], definition="以外倾情感动员关系，以内倾直觉形成共同方向；偏好成长叙事、协作和有影响力的行动。", signals=["迅速感受群体氛围并组织共识", "能把人的潜力连成长远方向", "他人不配合时可能过度劝导或自责"], use="说明人和目标的双重影响，给其协调空间；同时明确每个人可拒绝。", risks="替别人决定何为成长、过度负责、压力下冷硬分析或操控氛围。", growth="在帮助前问许可，用事实检验洞察，允许关系里存在不一致。", channel="关系影响与共同愿景", decision="群体成长、意义和可实现性"),
    dict(type="ENTJ", stack=["Te","Ni","Se","Fi"], definition="以外倾思维推动结果，以内倾直觉锁定战略；偏好掌控资源、长期杠杆和清晰决策。", signals=["快速确定目标、指标和权责", "从长期趋势筛选高价值路径", "遇到低效或模糊时会直接接管"], use="直说目标、约束、数据和决策权限；挑战方案时带替代方案。", risks="控制、低估情绪与恢复成本，压力下价值爆发或关系切割。", growth="把授权、同意和关系影响列入指标；练习不接管也能支持。", channel="结果执行与战略方向", decision="杠杆、效率和长期控制"),
]


FUNCTIONS = [
    dict(code="Se", name="外倾感觉", definition="实时采集外界具体信息并直接响应机会、变化和身体体验。", signals=["注意现场细节和动作反馈", "边做边学、反应快速", "表达常引用眼前可见事实"], use="适合现场执行、危机响应、运动、手作和把抽象计划变成第一步。", overuse="追求刺激、忽略远期成本或在压力下冲动。", train="每天五分钟五感扫描；把一个想法变成十五分钟可完成的动作。", verify="你通常先观察现场并试一下，还是先形成完整模型？"),
    dict(code="Si", name="内倾感觉", definition="把当下信息与内部经验档案比较，追踪连续性、熟悉度和身体基线。", signals=["记得先例、流程和细节差异", "偏好稳定节奏和已验证方法", "能察觉身体或环境偏离常态"], use="适合质量控制、维护、复盘、风险清单和建立可靠习惯。", overuse="把过去当未来、抗拒变化或反复检查。", train="记录实际结果而非只记录担忧；每周做一个小型可逆变化。", verify="你判断新情况时会自然调用哪些具体旧经验？"),
    dict(code="Ne", name="外倾直觉", definition="从外界线索扩散出多种联系、解释和未来可能。", signals=["一个话题能联想到多个方向", "乐于假设、重构和头脑风暴", "容易看到替代用途或潜在人选"], use="适合创意、早期探索、风险情景、跨领域连接和打破单一答案。", overuse="选项过多、难以收束、用可能性逃避兑现。", train="先发散十个选项，再用三个标准只保留一个实验。", verify="面对问题，你会先生成几种解释还是很快锁定一个？"),
    dict(code="Ni", name="内倾直觉", definition="把分散信息压缩为内在模式、主题和较单一的长期方向。", signals=["常说核心、本质、趋势或最终会怎样", "需要独处等待洞见成形", "能用少量线索构建整体图景"], use="适合战略、意义整合、长期路径、叙事设计和复杂信息压缩。", overuse="读心、宿命化、过早收敛并忽略反证。", train="每个洞见写出三条证据、两条反证和一个可观察预测。", verify="什么新证据会让你放弃当前的核心解释？"),
    dict(code="Te", name="外倾思维", definition="用外部标准、数据、流程和资源配置推动可衡量结果。", signals=["自然问目标、期限、责任人和指标", "倾向把任务拆解并排序", "用可操作结果判断方案"], use="适合项目管理、决策矩阵、执行、标准化和把愿望变成计划。", overuse="把效率当唯一价值、控制他人或忽略情境感受。", train="计划中加入同意、关系影响、恢复成本和复盘窗口。", verify="这个方案的成功标准、责任人和截止日期是什么？"),
    dict(code="Ti", name="内倾思维", definition="在内部分析定义、前提、因果和结构是否自洽。", signals=["会追问概念边界和例外", "喜欢拆解机制、找逻辑漏洞", "需要时间独立思考后再回答"], use="适合诊断、建模、澄清概念、代码、因果分析和发现隐含假设。", overuse="分析瘫痪、忽略期限或把情绪当逻辑错误。", train="设置分析停止条件；每次结论附一个现实验证动作。", verify="你的结论依赖哪些前提，哪一条最可能错？"),
    dict(code="Fe", name="外倾情感", definition="评估表达对他人和群体的影响，协调共享价值、情绪与互动规范。", signals=["注意气氛、回应和谁被排除", "会调整措辞以维持合作", "通过组织、鼓励或照顾推动关系"], use="适合倾听、主持、团队协调、冲突降温和让信息更易被接收。", overuse="讨好、替人负责、压抑自己或用群体规范施压。", train="帮助前先问许可；区分理解对方、同意对方和替对方负责。", verify="你是在回应对方明确需要，还是猜测他希望你怎样？"),
    dict(code="Fi", name="内倾情感", definition="在内部辨别个人价值、真实感、喜欢与不愿跨越的底线。", signals=["重视是否违背内心和个体差异", "价值判断深但不一定公开解释", "对被定义、强迫一致或虚假表达敏感"], use="适合价值澄清、伦理边界、个体化选择、创作和识别真正愿意承担的承诺。", overuse="把个人感受当共同事实、拒绝协商或沉浸身份受伤。", train="把价值翻译成具体请求、行为边界和愿意承担的后果。", verify="这件事触碰了你的哪条价值？你希望对方做什么具体改变？"),
]


ELEMENT = {
    "火": {"tempo":"节奏偏快、先启动", "need":"挑战、热情和自主", "blind":"耐心、后果和他人节奏"},
    "土": {"tempo":"节奏稳、先确认可行", "need":"稳定、资源和兑现", "blind":"变化、新可能和情绪流动"},
    "风": {"tempo":"通过交流和比较推进", "need":"信息、观点和公平空间", "blind":"身体感受、沉默信息和落地维护"},
    "水": {"tempo":"先感受安全与关系氛围", "need":"信任、共情和情绪容纳", "blind":"事实分离、直接请求和责任边界"},
}

MODALITY = {
    "本位": {"move":"主动发起、推动议题", "check":"发起前确认授权，推动后等待反馈"},
    "固定": {"move":"维持立场、关系或资源", "check":"定期邀请反证，区分坚持与僵化"},
    "变动": {"move":"适应情境、切换方案", "check":"设收束点，避免无限调整或逃离"},
}

CONTEXT_RULES = {
    "协作": dict(goal="把偏好转成可交付的分工与反馈", observe="会议发言、任务选择、截止兑现和变更反应", adapt="先对齐目标与成功标准，再约定责任、日期和复盘点", metric="承诺是否按期兑现，变更是否提前说明"),
    "初识": dict(goal="用低压力互动判断双向兴趣与节奏", observe="是否主动反问、延伸话题、分享信息和提出下一次互动", adapt="从具体共同点开始，逐步试探抽象深度；给对方自然退出空间", metric="两到三轮后是否出现双向主动，而非只有礼貌回应"),
    "冲突": dict(goal="降低威胁，分开事实、影响、需要与修复", observe="是否打断、追问、沉默、泛化、辩解以及之后是否修复", adapt="先暂停升级，再用 FAR：事实 Facts、承认影响 Acknowledge、修复 Repair", metric="是否停止伤害行为、承担具体责任并出现稳定改变"),
    "亲密": dict(goal="在连接、自由、边界和长期兑现之间建立稳定协议", observe="需求表达、边界尊重、日常投入、冲突安全与共同计划", adapt="直接谈联系频率、独处、金钱、忠诚、身体边界和未来安排", metric="双方能否自愿说不、协商并持续兑现，而非靠猜测和追逐"),
}

PROTOCOLS = [
    ("事实—解释分离", "定义：把可观察事实与脑内解释分开。识别：出现‘他就是、一定、从来、故意’时暂停。使用：写下原话、动作、时间、频率和后果，再列至少两个解释；用一个低压力问题验证。"),
    ("FAR冲突修复", "定义：Facts事实、Acknowledge承认影响、Repair修复。识别：争论开始重复、音量升高或长消息堆叠时启动。使用：只说一个事实；承认对方受到的影响，不夹带辩解；提出一个可验证修复动作并允许对方拒绝。"),
    ("边界优先", "定义：明确同意和拒绝高于任何类型解释。识别：出现不要、停止、只做朋友、需要空间、拉黑、害怕或安全风险。使用：停止推进，确认必要安排；不绕过渠道、不测试、不把拒绝解释成星座或人格策略。"),
    ("两周微实验", "定义：用可逆、低风险行动检验类型假设。识别：你想改变模式但只有抽象愿望。使用：选择一个动作、场景和指标，连续两周记录；有效则保留，无效则改假设而非责怪人格。"),
    ("八维平衡训练", "定义：把认知功能当能力菜单而非身份。识别：主导视角反复造成同一后果。使用：从相反或劣势视角选十五分钟动作，例如 Ni 写反证、Fe 问许可、Ti 查前提、Se 做现实第一步。"),
]

CONSENSUS = [
    ("四象与三模式是星座内容的常用记忆框架", "社区常用火土风水和本位固定变动组织十二星座，并通过‘准不准’促进自我投射。使用时只能当文化隐喻，必须回到个体行为验证。"),
    ("最佳搭子与匹配排行最易传播", "大量高互动内容把16型做成恋爱排行或固定配对。热度说明传播偏好，不证明效度；本系统不输出注定合适或不合适。"),
    ("类型差异常被表达为聊不来", "N/S 等讨论中有人报告真实摩擦，也有评论指出共同兴趣、认知、情商、关系强度和平台算法是替代解释。可用做法是切换事实、经验、可能性、意义四种频道。"),
    ("八维被用作成长地图", "高收藏科普常把主导、辅助、第三、劣势写成思维惯性和训练方向。可取之处是转成动作；不可取之处是把网络功能位当生理事实。"),
    ("反标签与操纵担忧并存", "社区一面用MBTI强化身份，一面担心标签泄露弱点或被操纵。系统必须把类型限制为概率假设，禁止用来施压、预测刺激或绕过边界。"),
    ("星座与MBTI联动主要是娱乐叙事", "评论里同一星座自报多种MBTI，构成直接反例；所谓稀有人格、新版准确率或官方数据如无来源，不进入事实层。"),
]


def tokens(text: str) -> list[str]:
    text = text.lower()
    latin = re.findall(r"[a-z0-9]+", text)
    chars = [c for c in text if "\u4e00" <= c <= "\u9fff"]
    segments = re.findall(r"[\u4e00-\u9fff]+", text)
    grams: list[str] = []
    for seg in segments:
        for n in (2, 3, 4):
            grams.extend(seg[i:i+n] for i in range(max(0, len(seg)-n+1)))
    return latin + chars + grams


def hashed_vector(text: str, dim: int = DIM) -> np.ndarray:
    counts = Counter(tokens(text))
    vec = np.zeros(dim, dtype=np.float32)
    for tok, count in counts.items():
        digest = hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest()
        raw = int.from_bytes(digest, "little")
        idx = raw % dim
        sign = 1.0 if (raw >> 63) == 0 else -1.0
        vec[idx] += sign * (1.0 + math.log(count))
    norm = float(np.linalg.norm(vec))
    return vec / norm if norm else vec


def record(category: str, title: str, content: str, **meta) -> dict:
    rid = meta.pop("id", f"{category}-{hashlib.sha1((title+content).encode('utf-8')).hexdigest()[:12]}")
    return {"id": rid, "category": category, "title": title, "content": content, "metadata": meta}


def taxonomy_records() -> list[dict]:
    out: list[dict] = []
    for z in ZODIACS:
        content = (f"定义：{z['definition']} 日期：{z['dates']}；元素：{z['element']}；模式：{z['modality']}。"
                   f"识别：{'；'.join(z['signals'])}。使用：{z['use']} 验证问题：{z['question']} "
                   f"风险：{z['risks']} 证据等级：文化原型，仅作低权重假设。")
        out.append(record("zodiac", z["name"], content, id=f"zodiac-{z['name']}", sign=z["name"], element=z["element"], modality=z["modality"]))
    for m in MBTIS:
        content = (f"定义：{m['definition']} 常见四功能序列：{'-'.join(m['stack'])}。"
                   f"识别：{'；'.join(m['signals'])}。使用：{m['use']} 成长：{m['growth']} "
                   f"风险：{m['risks']} 证据等级：偏好假设，不是诊断。")
        out.append(record("mbti", m["type"], content, id=f"mbti-{m['type']}", mbti=m["type"], functions=m["stack"]))
    for f in FUNCTIONS:
        content = (f"定义：{f['definition']}。识别：{'；'.join(f['signals'])}。使用：{f['use']} "
                   f"过度使用风险：{f['overuse']} 训练：{f['train']} 验证问题：{f['verify']}")
        out.append(record("function", f"{f['code']} {f['name']}", content, id=f"function-{f['code']}", function=f["code"]))
    return out


def combination_records() -> list[dict]:
    out: list[dict] = []
    for z in ZODIACS:
        el = ELEMENT[z["element"]]
        mod = MODALITY[z["modality"]]
        for m in MBTIS:
            combo = f"{z['name']}×{m['type']}"
            stack = "-".join(m["stack"])
            overview = (
                f"定义：这是{z['name']}的{z['element']}元素/{z['modality']}模式文化原型与{m['type']}偏好模型的交叉工作假设，"
                f"不是统计相关或命运判断。外在表达可能呈现{z['expression']}，信息处理偏向{m['channel']}，四功能序列为{stack}。"
                f"识别：观察是否同时反复出现‘{z['signals'][0]}’与‘{m['signals'][0]}’，并检查在两个场景、四周以上是否稳定；"
                f"不一致可能表示场景切换、压力、测试误差或原型不适用。使用：{z['use']} {m['use']} "
                f"自我调整：{z['regulator']}；{m['growth']} 验证问题：{z['question']} "
                f"风险：{z['risks']}；{m['risks']} 明确表达和现实行动始终优先。"
            )
            out.append(record("combination", combo, overview, id=f"combo-{z['name']}-{m['type']}", sign=z["name"], mbti=m["type"], element=z["element"], modality=z["modality"], functions=m["stack"]))
            for context in CONTEXTS:
                rule = CONTEXT_RULES[context]
                content = (
                    f"定义：{combo}在{context}场景的目标是{rule['goal']}。低权重星座原型提示{el['tempo']}并需要{el['need']}；"
                    f"{z['modality']}模式常见动作是{mod['move']}；{m['type']}偏好通过{m['channel']}理解问题，并按{m['decision']}决策。"
                    f"识别：重点观察{rule['observe']}；候选线索包括{z['signals'][0]}、{m['signals'][0]}、{m['signals'][1]}。"
                    f"这些线索需跨情境重复，单次行为不能定型。使用：{rule['adapt']}；对这个组合尤其要{z['regulator']}，并采用‘{m['use']}’。"
                    f"训练动作：{m['growth']}；{mod['check']}。验证问题：{z['question']} "
                    f"成功指标：{rule['metric']}。风险：容易忽略{el['blind']}；同时警惕{m['risks']}。"
                    f"若出现明确拒绝、反复失信、越界或安全风险，停止类型推断并按事实处理。"
                )
                out.append(record("behavior", f"{combo}｜{context}", content,
                                  id=f"behavior-{z['name']}-{m['type']}-{context}", sign=z["name"], mbti=m["type"],
                                  context=context, element=z["element"], modality=z["modality"], functions=m["stack"]))
    return out


def auxiliary_records() -> list[dict]:
    out = [record("protocol", title, body, id=f"protocol-{i+1}") for i, (title, body) in enumerate(PROTOCOLS)]
    out += [record("consensus", title, body, id=f"consensus-{i+1}", evidence="小红书社区样本，非科学证据") for i, (title, body) in enumerate(CONSENSUS)]
    return out


def write_taxonomy_markdown() -> None:
    lines = ["# 十二星座、MBTI 16 型与荣格八维完整分类", "", "本表的固定三面是定义、识别、使用；星座为文化原型，MBTI/八维为偏好假设。真正决策应回到行为、边界与现实行动。", "", "## 十二星座文化原型", ""]
    for z in ZODIACS:
        lines += [f"### {z['name']}（{z['dates']}｜{z['element']}元素｜{z['modality']}模式）", "", f"- 定义：{z['definition']}", f"- 识别：{'；'.join(z['signals'])}。", f"- 使用：{z['use']}", f"- 风险：{z['risks']}", f"- 验证：{z['question']}", ""]
    lines += ["## MBTI 16 型", ""]
    for m in MBTIS:
        lines += [f"### {m['type']}（{'–'.join(m['stack'])}）", "", f"- 定义：{m['definition']}", f"- 识别：{'；'.join(m['signals'])}。", f"- 使用：{m['use']}", f"- 风险：{m['risks']}", f"- 成长：{m['growth']}", ""]
    lines += ["## 荣格八种认知功能", ""]
    for f in FUNCTIONS:
        lines += [f"### {f['code']}｜{f['name']}", "", f"- 定义：{f['definition']}", f"- 识别：{'；'.join(f['signals'])}。", f"- 使用：{f['use']}", f"- 过度使用：{f['overuse']}", f"- 训练：{f['train']}", f"- 验证：{f['verify']}", ""]
    (REFS / "taxonomy.md").write_text("\n".join(lines), encoding="utf-8")


def build_keyword_index(docs: list[dict]) -> dict:
    postings: dict[str, list[list[float]]] = defaultdict(list)
    lengths = []
    for idx, doc in enumerate(docs):
        counts = Counter(tokens(doc["title"] + " " + doc["content"]))
        lengths.append(sum(counts.values()))
        for tok, tf in counts.items():
            postings[tok].append([idx, tf])
    return {"doc_count": len(docs), "avgdl": sum(lengths) / max(1, len(lengths)), "lengths": lengths, "postings": postings}


def source_hashes() -> dict[str, str | None]:
    # Optional source documents are expected beside the Skill by default.
    # Override this without editing the repository by setting
    # PERSONALITY_KB_SOURCE_DIR to another directory.
    configured = os.environ.get("PERSONALITY_KB_SOURCE_DIR")
    workspace = Path(configured).expanduser() if configured else ROOT.parent
    names = ["MBTI与荣格八维关系识别参考.md", "星座-MBTI-荣格八维待人处事识别与调整系统-可行性方案.md", "GitHub项目参考-星座MBTI荣格八维与行为调整系统.md"]
    out = {}
    for name in names:
        path = workspace / name
        out[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return out


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    REFS.mkdir(parents=True, exist_ok=True)
    docs = taxonomy_records() + combination_records() + auxiliary_records()
    knowledge_path = DATA / "knowledge.jsonl"
    with knowledge_path.open("w", encoding="utf-8", newline="\n") as fh:
        for doc in docs:
            fh.write(json.dumps(doc, ensure_ascii=False) + "\n")
    vectors = np.vstack([hashed_vector(d["title"] + " " + d["content"]) for d in docs])
    np.save(DATA / "vectors.npy", vectors, allow_pickle=False)
    (DATA / "keyword_index.json").write_text(json.dumps(build_keyword_index(docs), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    write_taxonomy_markdown()
    counts = Counter(d["category"] for d in docs)
    manifest = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vector_method": "signed feature hashing over Chinese character 1-4 grams and alphanumeric tokens",
        "vector_dim": DIM,
        "retrieval": "cosine vector + BM25 keyword + metadata boost, fused with reciprocal rank fusion",
        "counts": dict(sorted(counts.items())),
        "total_records": len(docs),
        "expected": {"zodiac": 12, "mbti": 16, "function": 8, "combination": 192, "behavior": 768, "contexts_per_combination": 4},
        "source_hashes": source_hashes(),
        "knowledge_sha256": hashlib.sha256(knowledge_path.read_bytes()).hexdigest(),
    }
    (DATA / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
