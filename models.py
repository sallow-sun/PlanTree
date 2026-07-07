# models.py
import json

class StudyNode:
    def __init__(self, node_id, name, prerequisites=None, notes="", color="#2d3748", node_type="standard", study_logs=None, canvas_bg_image="", is_protected=False, layout_direction=0):
        self.node_id = node_id          
        self.name = name                
        self.prerequisites = prerequisites if prerequisites else []  
        self.notes = notes              
        self.progress = 0               
        self.color = color              
        self.children = []              
        self.node_type = node_type  # "standard" (普通自由) 或 "strict" (严格关卡)
        self.study_logs = study_logs if study_logs else []  # 学习打卡记录列表
        self.canvas_bg_image = canvas_bg_image  # 地图画布独立背景图路径
        self.is_protected = is_protected  # 是否开启一键防护（只读）
        self.layout_direction = layout_direction  # 展开方向：0代表水平，1代表垂直

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "name": self.name,
            "prerequisites": self.prerequisites,
            "notes": self.notes,
            "progress": self.progress,
            "color": self.color,
            "node_type": self.node_type,
            "study_logs": self.study_logs,
            "canvas_bg_image": getattr(self, "canvas_bg_image", ""),  
            "is_protected": getattr(self, "is_protected", False),  # 序列化防护属性
            "layout_direction": getattr(self, "layout_direction", 0),  # 序列化展示方向
            "children": [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data):
        node = cls(
            node_id=data["node_id"],
            name=data["name"],
            prerequisites=data.get("prerequisites", []),
            notes=data.get("notes", ""),
            color=data.get("color", "#2d3748"),
            node_type=data.get("node_type", "standard"),
            study_logs=data.get("study_logs", []),
            canvas_bg_image=data.get("canvas_bg_image", ""),  
            is_protected=data.get("is_protected", False),  # 反序列化防护属性
            layout_direction=data.get("layout_direction", 0)  # 反序列化展示方向
        )
        if "progress" in data:
            node.progress = data["progress"]
        elif "status" in data:
            node.progress = 100 if data["status"] == "completed" else 0
        else:
            node.progress = 0

        for child_data in data.get("children", []):
            node.children.append(cls.from_dict(child_data))
        return node