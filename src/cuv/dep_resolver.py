import os
import subprocess
from typing import Dict, Any, Union, List, Set
import json
from pathlib import Path
from collections import defaultdict, deque


def resolve_dependencies(json_deps: Dict[str, Any]):


    file_provide_module = {}          # file -> module
    module_from_file = {}          # module -> file
    file_require_module = defaultdict(set)  # file -> set of modules

    graph = defaultdict(set)          # 正向圖：A -> B 意味著 A 依賴 B
    reverse_graph = defaultdict(set)  # 反向圖：B -> A 意味著 B 被誰依賴
    # 第一步：模組名稱 → 提供者檔案（即 module node → file node）
    for rule in json_deps["rules"]:
        output_file = rule["primary-output"]
        for p in rule.get("provides", []):
            module_name = p["logical-name"]
            mod_node = f"module:{module_name}"

            file_provide_module[output_file] = mod_node
            module_from_file[mod_node] = output_file

            if output_file not in graph:
                graph[output_file] = set()
            graph[mod_node].add(output_file)
            reverse_graph[output_file].add(mod_node)

    # 第二步：檔案 → 所需模組名稱（即 file node → module node）
    for rule in json_deps["rules"]:
        source_file = rule["primary-output"]
        for r in rule.get("requires", []):
            module_name = r["logical-name"]
            mod_node = f"module:{module_name}"

            file_require_module[source_file].add(mod_node)
            graph[source_file].add(mod_node)
            reverse_graph[mod_node].add(source_file)

    in_degree = defaultdict(int)
    for node, deps in graph.items():
        in_degree[node] += len(deps)

    # topological sort
    queue = deque([node for node in in_degree if in_degree[node] == 0])
    topo_order = []

    while queue:
        node = queue.popleft()
        topo_order.append(node)

        for neighbor in reverse_graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(topo_order) != len(in_degree):
        raise RuntimeError("Detected cycle in module dependency graph!")

    # generate task list
    task_list = []
    for node in topo_order:
        if not node.startswith("module:"):
            deps = graph[node]
            deps = [module_from_file[d] for d in deps]
            task_list.append((node, deps))
    return task_list





if __name__ == "__main__":
    # from pathlib import Path
    # project_root = Path(os.path.abspath(__file__)).parent.parent.parent
    # config_path = project_root / "tests" / "cuv-test-project" / "build_test" / "deps.json"
    # with open(config_path, "r") as f:
    #     json_deps = json.load(f)

    # test case from:
    # https://rocm.docs.amd.com/projects/llvm-project/en/latest/LLVM/clang/html/StandardCPlusPlusModules.html#id63
    json_deps="""
{
  "revision": 0,
  "rules": [
    {
      "primary-output": "Impl.o",
      "requires": [
        {
          "logical-name": "M",
          "source-path": "M.cppm"
        }
      ]
    },
    {
      "primary-output": "M.o",
      "provides": [
        {
          "is-interface": true,
          "logical-name": "M",
          "source-path": "M.cppm"
        }
      ],
      "requires": [
        {
          "logical-name": "M:interface_part",
          "source-path": "interface_part.cppm"
        },
        {
          "logical-name": "M:impl_part",
          "source-path": "impl_part.cppm"
        }
      ]
    },
    {
      "primary-output": "User.o",
      "requires": [
        {
          "logical-name": "M",
          "source-path": "M.cppm"
        }
      ]
    },
    {
      "primary-output": "impl_part.o",
      "provides": [
        {
          "is-interface": false,
          "logical-name": "M:impl_part",
          "source-path": "impl_part.cppm"
        }
      ],
      "requires": [
        {
          "logical-name": "M:interface_part",
          "source-path": "interface_part.cppm"
        }
      ]
    },
    {
      "primary-output": "interface_part.o",
      "provides": [
        {
          "is-interface": true,
          "logical-name": "M:interface_part",
          "source-path": "interface_part.cppm"
        }
      ]
    }
  ],
  "version": 1
}

"""
    json_deps = json.loads(json_deps)
    task_list = resolve_dependencies(json_deps)

    for task in task_list:
        print(task)