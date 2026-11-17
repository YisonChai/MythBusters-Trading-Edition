"""Insert the plain-language ticket explainer into an existing REPORT.html.

The inserted examples are hypothetical. This script does not read results,
refit a model, or change audit-copy HTML files.
"""
from pathlib import Path

NAV_OLD = '<div class="nav"><a href="#overview">'
NAV_NEW = '<div class="nav"><a href="#ticket">用买票理解</a><a href="#overview">'
FILTERS = '<div class="filters">'

LIMITS = {
    "v1": (
        "醒目限制：报价代理模拟，不是可执行收益。没有历史盘口和深度，不能把显示价说成保证能成交100份。"
        "费用是抓取时的元数据快照情景，不是完整不可变历史费用审计。"
        "本版字面一步概率是诊断变体，概率事件与到期结果并不一致，不是正确的到期概率模型。"
        "15分钟用实际Chainlink规则，1小时用实际Binance规则，二者不是同一产品。"
    ),
    "v2": (
        "醒目限制：报价代理模拟，不是可执行收益。没有历史盘口和深度，不能把显示价说成保证能成交100份。"
        "费用是抓取时的元数据快照情景，不是完整不可变历史费用审计。"
        "本版没有完成账户5分钟产品复刻。原版一分钟、本版五分钟采样，持续率不能直接跨采样频率比较。"
    ),
    "v3": (
        "醒目限制：报价代理模拟，不是可执行收益。没有历史盘口和深度，不能把显示价说成保证能成交100份。"
        "费用是抓取时的元数据快照情景，不是完整不可变历史费用审计。"
        "本版没有一年训练，实际是30日训练和30日测试。"
        "测试市场中33.05%此前已评估，86.61%此前已下载，不是全新盲测。"
    ),
}


def ticket_html(version: str) -> str:
    if version not in LIMITS:
        raise SystemExit(f"unknown version {version}")
    limit = LIMITS[version]
    return f'''<section id="ticket" class="section card method">
<div class="sectionhead"><h2>用买票理解策略</h2><span class="badge">教学数字均为假设，不是回测交易</span></div>
<div class="warning" style="border:2px solid #ce5260;background:#fff5f5;color:#7a2430"><b>{limit}</b></div>
<p>下面四小节的价格、概率、次数和门槛全部是为了说明规则而设的假设，不是本页任何一笔回测交易，也不能拿来代替资金曲线。</p>
<h3>1. 买一张结果票</h3>
<p>Polymarket的一张“Up结果票”现在卖0.90美元。买100份花90美元。如果到期按该市场真实规则判为Up，100份共兑回100美元，毛赚10美元；判为Down则兑回0，亏90美元。这里暂不含手续费。赢不赢取决于合约写明的参考源和起止比较，不是看这张票本身涨没涨。</p>
<h3>2. 第一关：市场有没有卖便宜</h3>
<p>假设模型估计到期Up概率p=0.96，市场报价q=0.90，差值是0.06，超过0.05，所以通过第一关。这不代表模型一定正确；如果真实概率被高估，期望优势就会消失。不能把模型说出的96%当成已经证实的胜率。</p>
<h3>3. 第二关：下一次检查还像不像现在</h3>
<p>为了方便理解，假设把“票价高、近期波动小”叫一种状态。历史上100次类似状态中，90次在下一个采样时刻仍属同一类，可以说这种教学状态的一步持续率约90%，超过87%，通过第二关。</p>
<p>它不是说价格一分钱不动，更不是到期90%会赢。例如把0.85至0.95作为教学价格桶，0.90变成0.88仍在同桶，最后也完全可能输钱。87%这道过滤能不能改善收益必须回测验证，数值没有神奇保证。</p>
<p><b>“票价高、波动小”和0.85至0.95的宽桶只是教学假设，原帖没有披露真实状态定义。我们的实际研究使用另行声明的模型，不是Bonereaper内部算法。第二、三版到期概率大模型是6600个理论状态的稀疏/分层吸收马尔可夫链，不是CRF。共同的持续率过滤单独使用20档价格的一步转移矩阵，先取 j*=argmax_j P[i,j]，再看 P[j*,j*]，并不直接等同教学例子的P[i,i]，也不是完整6600状态的对角线。原版一分钟、后两版五分钟采样，持续率不能直接跨采样频率比较。</b></p>
<p>实际20档每桶0.05，教学宽桶0.85至0.95不是实际分桶；0.90到0.88的例子只解释教学宽桶，不得声称两者在真实0.05分桶中一定同桶。</p>
<h3>4. 到底在赌什么</h3>
<p>两个条件都通过才产生研究信号。关键不是“状态稳就稳赢”，而是模型的到期概率估计能否比市场更准，并覆盖费用、价差、滑点和延迟。原帖状态持续率不是交易胜率，高胜率也不等于高利润。没有历史盘口和深度，三版都只能称报价代理模拟，不能把显示价说成保证能成交100份。</p>
</section>
'''


def insert_ticket(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    if 'id="ticket"' in text:
        raise SystemExit(f"{path} already contains the ticket section")
    if text.count(NAV_OLD) != 1:
        raise SystemExit(f"{path} nav anchor count {text.count(NAV_OLD)}")
    if text.count(FILTERS) != 1:
        raise SystemExit(f"{path} filters anchor count {text.count(FILTERS)}")
    text = text.replace(NAV_OLD, NAV_NEW, 1)
    text = text.replace(FILTERS, ticket_html(version) + FILTERS, 1)
    if text.count('id="ticket"') != 1:
        raise SystemExit("ticket section was not inserted once")
    path.write_text(text, encoding="utf-8")
    print(f"inserted {version} explainer into {path} ({path.stat().st_size} bytes)")
