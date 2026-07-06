import json
from models import StudyNode

# 1. 手动构建一个简单的 C++ 知识树
# 根节点
root = StudyNode("cpp_root", "C++ 学习路线")

# 第一层节点
syntax = StudyNode("syntax", "基础语法", prerequisites=[])
stl = StudyNode("stl", "STL 容器", prerequisites=["syntax"]) # 依赖于 基础语法

root.children.append(syntax)
root.children.append(stl)

# 2. 将这棵树保存为 JSON 文件
tree_data = root.to_dict()
with open("my_learning_plan.json", "w", encoding="utf-8") as f:
    json.dump(tree_data, f, indent=4, ensure_ascii=False)
print("保存成功！已生成 my_learning_plan.json 文件。")

# 3. 尝试读取刚才保存的文件并打印
with open("my_learning_plan.json", "r", encoding="utf-8") as f:
    loaded_data = json.load(f)

loaded_root = StudyNode.from_dict(loaded_data)
print(f"读取成功！根节点名称: {loaded_root.name}")
print(f"子节点1: {loaded_root.children[0].name}，状态: {loaded_root.children[0].status}")
print(f"子节点2: {loaded_root.children[1].name}，前置依赖: {loaded_root.children[1].prerequisites}")