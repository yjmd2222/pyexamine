import workflow
import bridge
import services
import orchestrator
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

def main():
    rows = [1, 2, 3, {"a": 1}, ["x", "y"]]
    a = workflow.run_all(rows)
    b = bridge.Bridge().execute(rows)
    c = services.ServiceCoordinator().process_request(7, "bulk", "api", 8, "east", "lee", "q2", "open")
    d = orchestrator.Orchestrator().process_batch(rows, "kr", "seoul", "grp", "kim", "main", "new", 1, "auto")
    _ = adapter_01.helper_1(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_02.helper_2(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_03.helper_3(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_04.helper_4(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_05.helper_5(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_06.helper_6(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_07.helper_7(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_08.helper_8(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_09.helper_9(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_10.helper_10(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_11.helper_11(rows, 'r','a','g','o','q','s',1,'m')
    _ = adapter_12.helper_12(rows, 'r','a','g','o','q','s',1,'m')
    return a, b, c, d
