"""Observed request results, independent of fault attribution. Never rewrites history."""
from collections import Counter, defaultdict

LABELS = {
    'SUCCESS': '目标请求成功',
    'TIMEOUT': '内核探测超时',
    'PROBE_FAILED': '内核明确探测失败',
    'INTERRUPTED': '采集进程中断，结局未保存',
    'MEASUREMENT_UNAVAILABLE': '控制接口或库存不可测',
    'RESPONSE_UNCONFIRMED': '目标成功响应未确认',
    'UNRESOLVED': '其他结局未确认',
    'IN_PROGRESS': '请求或测量在途',
    'NOT_STARTED': '未发起的计划槽',
}
KNOWN = ('SUCCESS', 'TIMEOUT', 'PROBE_FAILED')


def outcome(status, raw, started, completed, positive_delay=False):
    """A shared-path timeout remains an observed timeout, even when no node is to blame."""
    if not started:
        return 'NOT_STARTED'
    if raw == 'crash-after-admission':
        return 'INTERRUPTED'
    if not completed:
        return 'IN_PROGRESS' if status in ('PENDING', 'ADJUDICATE') else 'UNRESOLVED'
    if raw == 'SUCCESS/200/204' and positive_delay:
        return 'SUCCESS'
    if raw == 'NODE_TIMEOUT/504':
        return 'TIMEOUT'
    if raw == 'NODE_TEST_FAILED/503':
        return 'PROBE_FAILED'
    if raw == 'UNKNOWN_ERROR/204-not-confirmed':
        return 'RESPONSE_UNCONFIRMED'
    if status in ('API_UNAVAILABLE', 'CONFIG_CHANGED') or str(raw).startswith(
            ('API_UNAVAILABLE/', 'CONFIG_CHANGED/')):
        return 'MEASUREMENT_UNAVAILABLE'
    return 'UNRESOLVED'


def summarize(db, run):
    """Explicit report only: one grouped read, not a new collector or a per-refresh raw scan."""
    counts = defaultdict(Counter)
    seconds = defaultdict(float)
    attributed_uncertain = Counter()
    rows = db.execute('''select node,status,raw,start is not null started,
        end is not null and elapsed is not null completed,coalesce(delay>0,0) positive_delay,
        count(*) n,coalesce(sum(interval),0) seconds from st_sample where run=?
        group by node,status,raw,started,completed,positive_delay''', (run,))
    for node,status,raw,started,completed,positive,n,sec in rows:
        result = outcome(status,raw,started,completed,positive)
        for key in (node, None):
            counts[key][result] += n
            if result in KNOWN:
                seconds[key] += sec
            if result in ('TIMEOUT','PROBE_FAILED') and status == 'UNKNOWN_ERROR':
                attributed_uncertain[key] += n
    out = {}
    for node,values in counts.items():
        known = sum(values[k] for k in KNOWN)
        unknown = sum(v for k,v in values.items() if k not in KNOWN + ('NOT_STARTED','IN_PROGRESS'))
        out[node] = dict(counts=dict(values),known=known,success=values['SUCCESS'],
            request_success_pct=100*values['SUCCESS']/known if known else None,
            outcome_unknown=unknown,known_failure_with_uncertain_cause=attributed_uncertain[node],
            measured_seconds=seconds[node])
    return out
