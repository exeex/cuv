import os
import subprocess
from typing import Dict, Any, Union, List, Set
import json
from pathlib import Path
from collections import defaultdict, deque

std_modules = {
    "iostream","std"
}

class Node:
    def __init__(self, name: str, prefix=""):
        self.name = name
        self.hashable_name = prefix + name
    def __hash__(self):
        return hash(self.hashable_name)
    def __eq__(self, other):
        return self.hashable_name == other.hashable_name
    def __ne__(self, other):
        return self.hashable_name != other.hashable_name
    def __lt__(self, other):
        return self.hashable_name < other.hashable_name
    def __le__(self, other):
        return self.hashable_name <= other.hashable_name
    def __gt__(self, other):
        return self.hashable_name > other.hashable_name
    def __ge__(self, other):
        return self.hashable_name >= other.hashable_name
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

class FileNode(Node):
    def __init__(self, name: str):
        super().__init__(name, "file:")

class ModuleNode(Node):
    def __init__(self, name: str):
        super().__init__(name, "module:")

def resolve_dependencies(json_deps: Dict[str, Any], external_modules: Set[str] = None):

    if external_modules is None:
        external_modules = std_modules
    else:
        external_modules = set(external_modules).union(std_modules)

    graph = defaultdict(set)          # 正向圖：A -> B 意味著 A 依賴 B
    reverse_graph = defaultdict(set)  # 反向圖：B -> A 意味著 B 被誰依賴
    # 第一步：模組名稱 → 提供者檔案（即 module node → file node）
    for rule in json_deps["rules"]:
        output_file = rule["primary-output"]
        file_node = FileNode(output_file)
        for p in rule.get("provides", []):
            module_name = p["logical-name"]
            mod_node = ModuleNode(module_name)
            if file_node not in graph:
                graph[file_node] = set()
                
            graph[mod_node].add(file_node)
            reverse_graph[file_node].add(mod_node)

    # 第二步：檔案 → 所需模組名稱（即 file node → module node）
    for rule in json_deps["rules"]:
        source_file = rule["primary-output"]
        file_node = FileNode(source_file)
        for r in rule.get("requires", []):
            module_name = r["logical-name"]
            if module_name in std_modules:
                mod_node = ModuleNode(module_name)
                graph[mod_node] = set()
            elif module_name in external_modules:
                mod_node = ModuleNode(module_name)
                graph[mod_node] = set()
            else:
                mod_node = ModuleNode(module_name)

            graph[file_node].add(mod_node)
            reverse_graph[mod_node].add(file_node)

    # 第三步: 移除 module node，將其依賴轉移給所有依賴它的 file node
    module_nodes = [n for n in graph if isinstance(n, ModuleNode)]

    for mod_node in module_nodes:
        # 這個 module node 被哪些 file node 依賴（A → mod_node）
        file_users = reverse_graph[mod_node]
        
        # module node 依賴哪些 file（mod_node → B）
        file_providers = graph[mod_node]

        # 將所有 file_users 改成直接依賴 file_providers
        for user in file_users:
            for provider in file_providers:
                graph[user].add(provider)
                reverse_graph[provider].add(user)

            # 移除原本指向 module 的邊
            graph[user].discard(mod_node)

        # 刪除 module node 自身的邊
        for provider in file_providers:
            reverse_graph[provider].discard(mod_node)

        del graph[mod_node]
        del reverse_graph[mod_node]



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
        deps = graph[node]
        deps = [d.name for d in deps]
        task_list.append((node.name, deps))
    return task_list





if __name__ == "__main__":


    # test case from:
    # https://rocm.docs.amd.com/projects/llvm-project/en/latest/LLVM/clang/html/StandardCPlusPlusModules.html#id63
#     json_deps="""
# {
#   "revision": 0,
#   "rules": [
#     {
#       "primary-output": "Impl.o",
#       "requires": [
#         {
#           "logical-name": "M",
#           "source-path": "M.cppm"
#         }
#       ]
#     },
#     {
#       "primary-output": "M.o",
#       "provides": [
#         {
#           "is-interface": true,
#           "logical-name": "M",
#           "source-path": "M.cppm"
#         }
#       ],
#       "requires": [
#         {
#           "logical-name": "M:interface_part",
#           "source-path": "interface_part.cppm"
#         },
#         {
#           "logical-name": "M:impl_part",
#           "source-path": "impl_part.cppm"
#         }
#       ]
#     },
#     {
#       "primary-output": "User.o",
#       "requires": [
#         {
#           "logical-name": "M",
#           "source-path": "M.cppm"
#         }
#       ]
#     },
#     {
#       "primary-output": "impl_part.o",
#       "provides": [
#         {
#           "is-interface": false,
#           "logical-name": "M:impl_part",
#           "source-path": "impl_part.cppm"
#         }
#       ],
#       "requires": [
#         {
#           "logical-name": "M:interface_part",
#           "source-path": "interface_part.cppm"
#         }
#       ]
#     },
#     {
#       "primary-output": "interface_part.o",
#       "provides": [
#         {
#           "is-interface": true,
#           "logical-name": "M:interface_part",
#           "source-path": "interface_part.cppm"
#         }
#       ]
#     }
#   ],
#   "version": 1
# }

# """
#     json_deps = json.loads(json_deps)
#     task_list = resolve_dependencies(json_deps)

#     for task in task_list:
#         print(task)


    from pathlib import Path
    project_root = Path(os.path.abspath(__file__)).parent.parent.parent
    config_path = project_root / "tests" / "myproject" / "build" / "deps.json"
    with open(config_path, "r") as f:
        json_deps = json.load(f)

    task_list = resolve_dependencies(json_deps)

    for task in task_list:
        print(task)