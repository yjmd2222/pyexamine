import shared
import models
import orchestrator
import graph

class ServiceCoordinator:
    def __init__(self):
        self.orch = orchestrator.Orchestrator()
        self.cache = {}
        self.records = []
        self.temp_flag = None
        self.temp_count = 0
        self.temp_result = None
    def load_items(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def save_items(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def export_report(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def send_notice(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def rebuild_index(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def audit_rows(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def reset_cache(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def assign_owner(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def update_schedule(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def calculate_totals(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def render_table(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def collect_metrics(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def archive_rows(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def restore_rows(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def publish_feed(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def close_day(self, rows, mode='normal'):
        total = 0
        out = []
        for row in rows:
            if row is None:
                continue
            text = str(row)
            total += len(text)
            out.append(text)
        if mode == 'x':
            total += 1
        elif mode == 'y':
            total += 2
        elif mode == 'z':
            total += 3
        elif mode == 'w':
            total += 4
        return {'total': total, 'rows': out}

    def delegate_route(self, rows):
        return self.orch.route(rows)

    def delegate_prepare(self, rows):
        return self.orch.prepare(rows)

    def delegate_add(self, key, value):
        return self.orch.add(key, value)

    def delegate_get(self, key):
        return self.orch.get(key)

    def delegate_chain(self, x):
        return self.orch.chain_value(x)

    def process_request(self, item, mode, channel, priority, region, owner, queue, status):
        result = {'steps': []}
        if mode == 'new':
            result['steps'].append('new')
        elif mode == 'retry':
            result['steps'].append('retry')
        elif mode == 'cancel':
            result['steps'].append('cancel')
        elif mode == 'hold':
            result['steps'].append('hold')
        elif mode == 'resume':
            result['steps'].append('resume')
        elif mode == 'night':
            result['steps'].append('night')
        elif mode == 'bulk':
            result['steps'].append('bulk')
        elif mode == 'fast':
            result['steps'].append('fast')
        elif mode == 'manual':
            result['steps'].append('manual')
        elif mode == 'audit':
            result['steps'].append('audit')
        elif mode == 'sync':
            result['steps'].append('sync')
        elif mode == 'preview':
            result['steps'].append('preview')
        elif mode == 'dryrun':
            result['steps'].append('dryrun')
        else:
            result['steps'].append('other')
        if channel:
            if priority > 5:
                if region:
                    if owner:
                        if queue:
                            result['steps'].append('deep')
        store = models.LedgerStore()
        view = models.LedgerView()
        store._items.append(item)
        store._items.append(mode)
        store._items.append(channel)
        store._secret['p'] = priority
        store._secret['r'] = region
        store._secret['o'] = owner
        value = len(store._items) + len(store._secret) + len(view._items) + len(view._secret)
        result['envy'] = value
        result['chain'] = graph.A(item).next().next().next().end()
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s0'] = 0
        else:
            result['s0'] = len(str(item)) + 0
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s1'] = 1
        else:
            result['s1'] = len(str(item)) + 1
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s2'] = 2
        else:
            result['s2'] = len(str(item)) + 2
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s3'] = 3
        else:
            result['s3'] = len(str(item)) + 3
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s4'] = 4
        else:
            result['s4'] = len(str(item)) + 4
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s5'] = 5
        else:
            result['s5'] = len(str(item)) + 5
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s6'] = 6
        else:
            result['s6'] = len(str(item)) + 6
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s7'] = 7
        else:
            result['s7'] = len(str(item)) + 7
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s8'] = 8
        else:
            result['s8'] = len(str(item)) + 8
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s9'] = 9
        else:
            result['s9'] = len(str(item)) + 9
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s10'] = 10
        else:
            result['s10'] = len(str(item)) + 10
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s11'] = 11
        else:
            result['s11'] = len(str(item)) + 11
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s12'] = 12
        else:
            result['s12'] = len(str(item)) + 12
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s13'] = 13
        else:
            result['s13'] = len(str(item)) + 13
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s14'] = 14
        else:
            result['s14'] = len(str(item)) + 14
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s15'] = 15
        else:
            result['s15'] = len(str(item)) + 15
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s16'] = 16
        else:
            result['s16'] = len(str(item)) + 16
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s17'] = 17
        else:
            result['s17'] = len(str(item)) + 17
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s18'] = 18
        else:
            result['s18'] = len(str(item)) + 18
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s19'] = 19
        else:
            result['s19'] = len(str(item)) + 19
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s20'] = 20
        else:
            result['s20'] = len(str(item)) + 20
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s21'] = 21
        else:
            result['s21'] = len(str(item)) + 21
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s22'] = 22
        else:
            result['s22'] = len(str(item)) + 22
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s23'] = 23
        else:
            result['s23'] = len(str(item)) + 23
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s24'] = 24
        else:
            result['s24'] = len(str(item)) + 24
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s25'] = 25
        else:
            result['s25'] = len(str(item)) + 25
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s26'] = 26
        else:
            result['s26'] = len(str(item)) + 26
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s27'] = 27
        else:
            result['s27'] = len(str(item)) + 27
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s28'] = 28
        else:
            result['s28'] = len(str(item)) + 28
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s29'] = 29
        else:
            result['s29'] = len(str(item)) + 29
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s30'] = 30
        else:
            result['s30'] = len(str(item)) + 30
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s31'] = 31
        else:
            result['s31'] = len(str(item)) + 31
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s32'] = 32
        else:
            result['s32'] = len(str(item)) + 32
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s33'] = 33
        else:
            result['s33'] = len(str(item)) + 33
        if isinstance(item, (int, float)) and item % 2 == 0:
            result['s34'] = 34
        else:
            result['s34'] = len(str(item)) + 34
        return result
