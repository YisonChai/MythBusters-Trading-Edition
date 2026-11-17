from pathlib import Path
import csv,json,collections,datetime as dt,platform
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[1];O=R/'results'
def read(n):return list(csv.DictReader((O/n).open()))
v=read('variant_results.csv');m=read('market_manifest.csv');c=read('calibration.csv');tr=read('trades.csv');summary=json.loads((O/'run_summary.json').read_text())
lookup={(int(x['duration_min']),x['variant'],x['scenario']):x for x in v}
def num(x):return f'{float(x):,.2f}'
labels={'terminal_e05_p87':'终局模型，5%差值+87%持续率','terminal_e05_nofilter':'终局模型，5%差值，不加持续率','terminal_e03_p87':'终局模型，3%差值+87%持续率','terminal_e03_band':'终局模型，3%+87%+价格带','terminal_e05_band':'终局模型，5%+87%+价格带','literal_e05_p87':'一步概率字面版，5%+87%','literal_e03_band':'一步概率字面版，3%+87%+价格带','calibrated_e05':'经验终局校准基线，5%差值','favorite_fixed':'固定第2分钟买热门边','market_edge':'市场价作同边概率，无额外优势'}
# Per-day accounting grouped by entry day (not mark-to-market PnL).
daily=collections.defaultdict(lambda:{'n':0,'net':0.,'fee':0.})
for x in tr:
 day=dt.datetime.fromtimestamp(int(x['t']),ZoneInfo('Asia/Taipei')).date().isoformat();key=(x['duration_min'],x['variant'],x['scenario'],day);daily[key]['n']+=1;daily[key]['net']+=float(x['net_pnl']);daily[key]['fee']+=float(x['fee'])
with (O/'daily_entry_cohorts.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['duration_min','variant','scenario','entry_date_taipei','trades','net_pnl_after_eventual_settlement','fees']);w.writerows([list(k)+[z['n'],z['net'],z['fee']] for k,z in sorted(daily.items())])
manifest=[json.loads(x) for x in (R/'logs/download_manifest.jsonl').read_text().splitlines()];counts=collections.Counter(x['http_status'] for x in manifest);times=[dt.datetime.fromisoformat(x['retrieved_at']).astimezone(ZoneInfo('Asia/Taipei')) for x in manifest]
s='''# 实际回测结果：两个门槛有没有可验证的优势？

## 结论先说

**已经在 Bot 的电脑实际跑完，不是只给方案。此次预先固定的研究版本没有验证“5%概率差+87%状态持续率”可稳定盈利，更没有验证原帖所说的月赚46.8万美元。**

但边界同样重要：这不是 Bonereaper 源码复刻，也不是对所有马尔可夫模型的否定。原帖缺失状态定义、训练方法及执行细节，我们不能把自行补全的模型冒充原策略。

**所有以下收益均为真实合约历史价格上的代理计算，不是真实成交或可执行收益。** 没有历史bid/ask和深度，不可能保证当时能以图表价买到100份。文件中的“净收益”只指指定情景扣除模型费用后的模拟账本，不代表已赚到的钱。

## 1. 实际下载和使用的数据

- 1440个已结算真实市场：BTC和ETH各720个；其中15分钟1152个、1小时288个。
- 六天市场开盘窗口：2026年11月11日08:00至11月17日08:00，台北时间（UTC+8），末端不包含。这是近期可取得分钟数据的窗口，不是原帖历史盈利截图所覆盖的窗口。
- 测试窗口：11月14日08:00至11月17日08:00（台北时间），720个市场；15分钟576个、1小时144个。初始前三天训练，此后三天逐日扩展训练，当天模型冻结。
- 双边价格：2880条官方分钟历史序列，保存原始JSON；每个市场保留完整规则、真实结算赢家和元数据。
- 测试集共有16560个有效一分钟观测。每个市场每个策略最多一笔，不把分钟观测当独立交易。
- 1小时市场按实际Binance开收盘规则，下载288根官方小时K线交叉检查，288个结果全部吻合。
- 15分钟市场按实际Chainlink TWAP规则，用官方eventMetadata中的finalPrice/priceToBeat交叉核对：1151个吻合，1个未提供这两个元数据字段。这1个仍使用官方已结算赢家，没有改用Binance冒充。
- 另下载20个市场的真实成交样本用于覆盖检查；它们不是本研究模拟订单的实际成交证明。
- 无市场被排除。初始发现过去年同名小时slug，已通过带2026年份的正确slug修正；探索探针文件未进入研究数据。

'''
s+=f"抓取记录时间：{min(times).strftime('%Y-%m-%d %H:%M:%S')} 至 {max(times).strftime('%H:%M:%S')}（台北时间）。请求状态统计：{dict(counts)}。首次批量limit=100返回406，服务器要求压缩；改为本来只需的20条/页后成功。没有修改身份、凭证或绕过地区限制。\n\n"
s+='''## 2. 哪些是原帖，哪些是研究者补全

原帖能复现的文字部分：每分钟扫描、差值门槛0.05、持续率门槛0.87；配图另有0.03和0.83至0.97价格带。

我们在首次拟合前固定的假设：
- 当前Up合约价格分20个0.05宽的桶，结合剩余分钟数，构造时间相关的马尔可夫转移；末步使用真实Up/Down结算标签，递推最终Up概率。
- BTC/ETH在同一种产品内合并训练，不混合15分钟Chainlink规则和1小时Binance规则。
- 伪计数平滑强度10，状态最小出边样本数30；经验终局校准基线向市场价收缩20条。
- 持续率由训练数据的价格桶一步矩阵计算。这个“状态”是明确声明的实验定义，不是已知原bot的状态。
- 字面版本取一步最可能状态概率，用它与对应边合约价相减，专门检验这种概率语义错误会怎样。它并不因此成为正确终局概率。
- 每市场首次触发交易100份，持有到真实结算；初始模拟现金10000美元，两资产并发共享资金，不加杠杆。并不是投入10000美元实盘。

共10个策略变体、5种成本情景，全部报告，没有在测试集上挑参数。协议首次保存于11月17日17:20:02，最终代码和协议在17:23:28冻结，首次收益计算在此后。hash见logs/protocol_freeze.json。

## 3. 全部变体结果

表中是序列价格加该市场元数据手续费的fee_only情景，**仍没有真实买卖价差及可成交保证**。金额单位美元。

| 合约 | 预先固定变体 | 模拟交易数 | 胜率 | 扣费模拟盈亏 | 初始现金归一收益 |
|---|---|---:|---:|---:|---:|
'''
for D in [15,60]:
 for key,label in labels.items():
  x=lookup[D,key,'fee_only'];wr='不适用' if not x['win_rate'] else f'{100*float(x["win_rate"]):.2f}%'
  s+=f'| {D}分钟 | {label} | {x["trades"]} | {wr} | {num(x["net_pnl"])} | {float(x["return_on_initial_pct"]):.3f}% |\n'
s+='''
最接近原帖两个门槛的合理终局版：
- 15分钟：35笔，35笔中的17笔赢，净亏60.73美元。
- 1小时：15笔，0笔赢，净亏27.19美元。这些多是低价边，亏损额小，不能把0%胜率解释成每笔亏100美元。
- 字面一步概率版没有任何一笔满足我们固定状态定义下的条件。零交易不证明所有状态划分都无效，只说明不能直接拿那段if说“我就复刻了”。

不能隐瞒的正结果：1小时去掉87%过滤，142笔的扣费代理收益为+655.57美元；3%+87%+价格带的13笔为+54.12美元、恰好全赢。前者不属于原帖两个条件，后者只有13笔且高赔率区间本来就高胜率，均不能由此推断长期稳盈。后者普通bootstrap下界偏乐观，有限样本未出现的尾部亏损不会被重采样凭空补出。

## 4. 交易成本和延迟会改变结论

以下均为显式压力情景，不是编造的历史盘口。原序列+1分或+2分，是成本假设，不是当时真实ask。延迟情景以真实下一分钟可见价格和原价较差者加2分，价格超过1或没有下一分钟可用点就不成交，因而交易数可能变化。

| 合约/变体 | 原价、不扣费 | 原价+手续费 | 再加1分/份 | 延迟1分钟、较差价+2分、手续费 |
|---|---:|---:|---:|---:|
'''
for D,key in [(15,'terminal_e05_p87'),(60,'terminal_e05_p87'),(15,'terminal_e05_nofilter'),(60,'terminal_e05_nofilter'),(15,'terminal_e03_band'),(60,'terminal_e03_band')]:
 vals=[lookup[D,key,z] for z in ['quote0','fee_only','stress1','stress2_delay']]
 s+=f'| {D}分钟，{labels[key]} | '+' | '.join(f'{num(x["net_pnl"])}（{x["trades"]}笔）' for x in vals)+' |\n'
s+='''
1小时去掉持续率过滤的142笔，保持相同142笔时，扣费收益从+655.57降到延迟压力情景的-140.96美元。说明这个正结果对执行条件敏感，并非已经找到稳定套利。

15分钟无过滤版甚至是毛赚217.50、费用708.26，扣费后亏490.76美元。只截图毛收益会得出相反结论。

手续费使用每份合约当前保存的feeSchedule：rate=0.07、exponent=1，费=N×rate×q×(1-q)，按5位小数取整；文件还包括费率翻倍情景。虽然研究窗口很近、各合约都有费率元数据，接口不是不可变的历史费率审计档案，所以仍不把这叫精确历史账户会计。未加入未验证的返佣、gas、资金成本或保证成交的假设。

严格可执行口径：**NA**。官方只取得历史价格与成交，没有取得对应时刻的历史买卖盘和深度；已结算合约的当前book接口返回404。第三方历史盘口服务需要注册/API key，本次没有注册或付费。因此executable_net_pnl列留空并写明原因，不用虚构盘口填洞。无法断言当时在什么价能成交100份，也无法给出保证保守的真实收益下界。

## 5. 预测能力也没有胜过市场价基线

Brier越低越好。以下使用全部测试观测，非只看成交样本：

| 合约 | 市场Up价格基线 | 终局马尔可夫 | 经验校准基线 | 一步概率字面版（语义本就不匹配） |
|---|---:|---:|---:|---:|
'''
for D in [15,60]:
 vals=[]
 for mod in ['p_market','p_terminal','p_calibrated','p_literal_up']:
  x=next(x for x in c if int(x['duration_min'])==D and x['model']==mod and float(x['probability_low'])==0 and float(x['probability_high'])==1);vals.append(f'{float(x["brier"]):.6f}')
 s+=f'| {D}分钟 | '+' | '.join(vals)+' |\n'
s+='''
两种产品中，终局模型都没有优于直接使用市场价格。此结果只针对当前这个明确状态定义，不代表未知的外部价格信号一定没有价值。

市场簇bootstrap的描述性95%区间中，1小时无过滤版为约-553.21至+1783.48美元，跨过0。只有3个测试日，BTC/ETH及邻近市场又相关，不能把这个区间当严格显著性检验，也不能年化或推导月赚多少。

## 6. 回撤、资金和执行边界

- 回撤在variant_results.csv中为“已实现权益回撤”，未到期仓位按成本保留，不是逐秒盯市风险。
- 15分钟两门槛版扣费后的最大已实现回撤194.61美元，最高同时占款96.97美元。
- 1小时两门槛版回撤27.19美元，最高同时占款7.47美元。
- 1小时无过滤版扣费回撤638.70美元；延迟压力情景回撤1082.58美元。
- 初始10000美元是统一模拟账本分母，不是策略最优本金；同时占款小也不代表可以安全按倍数放大。没有盘口深度，容量与放大后的冲击完全未验证。

## 7. 自检与可复现性

- 6项关键函数单元测试通过。
- 18项真实数据审计通过：未来数据、终局标签、数据时区、训练标签可用时间、重复信号、手续费、每笔现金、结算资金和归一收益等。
- 分钟桶保守延迟整分钟后才允许成为特征；所有resolution_seconds=0终局/特殊点排除，防止把结算价喂给模型。
- 训练标签必须早于当日测试截点，另设到期后至少1小时的标签可用缓冲；训练/测试不共享市场。
- 已离线独立重跑两遍，10个CSV文件逐个SHA256一致（后续report.py生成的日分组文件单独由固定逐笔CSV汇总）。
- 保存原始JSON、每次请求URL/抓取时间/响应hash、结算规则、清洗记录、折叠窗口、全部预测、逐笔信号、模拟成交及所有变体。
- 没有安装或登录交易应用，没有连接钱包、签名、转账或下单，也没有使用用户电脑。

## 最终判断

**这次跑出来的证据不支持“照着两个门槛就能复刻收益”的说法。** 合理补全版本中，原帖5%+87%条件在两个产品都亏；部分放宽变体出现正收益，但样本短、预测指标未胜市场价、执行压力会抹去优势。我们能否定的是“已经给出了可复制的盈利证明”，不能冒充已还原或已推翻Bonereaper的真实策略。

下一个真正有意义的验证不是继续在这3天上调参，而是取得经许可的历史盘口，冻结模型后再看新的独立时间段。本文没有替用户开通任何服务或设置定时任务。
'''
(R/'回测结果.md').write_text(s)
readme='''# CasaVerilla Polymarket 公开数据离线代理回测

先读 [回测结果.md](回测结果.md)。这是实际跑过的价格序列代理研究，不是可执行收益回测，不是Bonereaper源码复刻。

## 复现

已提供完整原始数据，收益运算不联网。需要Python3和requirements.txt所列numpy版本（本机已有，没有为此次任务安装依赖）。

```bash
cd /workspace/casa-verilla/backtest
python3 -m unittest discover -s src -p 'test_*.py' -v
python3 src/backtest.py
python3 src/audit.py
python3 src/report.py
```

重新获取原始数据的可选步骤：`python3 src/download.py`。它只访问公开GET接口，有缓存、限速和退避，不读取任何凭证、不访问钱包、不提交订单；已经下载的文件会直接复用，严谨复现应先使用交付快照而不是把新抓数据混入旧结果。

## 文件

- 研究协议_预先固定.md：首次结果前固定的样本、模型、变体和成本规则。
- src/download.py：公开数据下载，UTC请求区间固定。
- src/backtest.py：只有本地文件读写，无网络。
- src/test_core.py、src/audit.py：单元测试与真实数据审计。
- src/report.py：从结果CSV生成中文说明与按入场日分组账本。
- raw/markets.json：1440个真实市场及完整规则、结算标签。
- raw/events/：官方批量原始回复。
- raw/prices/：两边分钟价格原始回复。
- raw/reference/：288根Binance1小时K线，仅对应Binance结算市场；没有替换Chainlink结果。
- raw/trades/：20个市场的官方成交覆盖样本，不用它假装模拟订单成交。
- raw/*probe*、discovery*：探索与错误排查快照，不参与计算；有一份2025年同名slug探针，研究白名单仅由requested_markets.json和markets.json决定。
- docs/：官方分钟历史、费用、盘口接口文档。
- results/market_manifest.csv：每个合约的来源、规则、赢家、交叉核对、观察数与排除原因。
- results/exclusions.csv：本次无排除，只有列名。
- results/folds.csv：实际训练/测试市场数及最后可用标签时间。CSV时间为带时区UTC，中文报告已换台北时间。
- results/all_predictions.csv：每分钟特征及各模型预测，含原始时间和可用时间。
- results/signals.csv：每个变体首次入场信号。
- results/trades.csv：在明确成本假设下的模拟逐笔账本，不是真实fill。
- results/variant_results.csv：100行预先声明的策略/产品/场景组合。
- results/calibration.csv：Brier及校准分箱；一步概率版明确标为非终局概率。
- results/bootstrap_diagnostic.csv：描述性市场簇重采样，非严格显著性检验。
- results/daily_entry_cohorts.csv：按台北入场日分组的最终结算损益，不是当日盯市利润。
- logs/：抓取来源时间与hash、协议hash冻结、两次运行和审计、环境及重现一致性。

## 关键边界

没有历史bid/ask或深度，executable_net_pnl始终NA。quote0/fee_only/stress价格都是公开价格序列上的情景成本，绝不保证当时100份可成交。无交易时胜率和Brier空白表示没有样本，不是0胜率；有交易且全输时才是0。所有真实市场收益结算使用官方0/1结果，不生成虚假历史行情。单元测试中的手写数据仅用于函数测试，从不进入研究结果。

每市场每变体一笔，100份，初始模拟现金10000美元，不杠杆、不叠加同一市场。不把周转成交额当本金；最大回撤仅为已实现权益，不是盯市。

## 来源

- https://x.com/CasaVerilla/status/2122259548102656341
- https://gamma-api.polymarket.com/events
- https://docs.polymarket.com/api-reference/markets/get-a-tokens-price-history
- https://docs.polymarket.com/api-reference/feeds/list-account-activity.md
- https://docs.polymarket.com/trading/fees.md
- https://docs.polymarket.com/api-reference/market-data/get-order-book.md
- https://docs.polymarket.com/api-reference/geoblock
- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints

原始请求的完整查询URL与时间逐条见logs/download_manifest.jsonl，不在README列2880条URL。使用标准curl可读取官方公开历史；Python urllib探针曾收到Cloudflare1010，未伪造浏览器身份或导入cookies。官方公开网页下载方式成功后保持请求节流。
'''
(R/'README.md').write_text(readme)
print('report saved',len(s),'characters; CSV scenario rows',len(v))
