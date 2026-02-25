import shared
import models
import planner
import planner_alt
import orchestrator
import services
import api_client
import graph
import cycle_a
import cycle_b
import cycle_c
import adapter_01
import adapter_02
import adapter_03
import adapter_04
import adapter_05
import adapter_06
import adapter_07
import adapter_08
import adapter_09
import adapter_10
import adapter_11
import adapter_12

def sync_record(item):
    return {"id": str(item), "state": "workflow"}

def run_all(items):
    orch = orchestrator.Orchestrator()
    svc = services.ServiceCoordinator()
    rows = planner.build_route(items)
    alt = planner_alt.prepare_route(items)
    data = []
    data.append(shared.summarize_items(items))
    data.append(shared.normalize_items(items))
    data.extend(api_client.repetitive_sync(api_client.FakeAPI(), [1,2,3]))
    data.append(orch.chain_value(10))
    data.append(svc.process_request(3, "retry", "web", 9, "north", "kim", "q1", "new"))
    data.append(cycle_a.ping_a(2))
    data.append(cycle_b.ping_b(2))
    data.append(cycle_c.ping_c(2))
    data.append(adapter_01.helper_1(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_02.helper_2(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_03.helper_3(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_04.helper_4(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_05.helper_5(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_06.helper_6(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_07.helper_7(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_08.helper_8(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_09.helper_9(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_10.helper_10(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_11.helper_11(items, 'r','a','g','o','q','s',1,'m'))
    data.append(adapter_12.helper_12(items, 'r','a','g','o','q','s',1,'m'))
    return {"rows": rows, "alt": alt, "data": data}
