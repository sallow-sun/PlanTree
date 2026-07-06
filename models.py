# models.py
import json

class StudyNode:
    def __init__(self, node_id, name, prerequisites=None, notes="", color="#2d3748", node_type="standard", study_logs=None):
        self.node_id = node_id          
        self.name = name                
        self.prerequisites = prerequisites if prerequisites else []  
        self.notes = notes              
        self.progress = 0               
        self.color = color              
        self.children = []              
        self.node_type = node_type  # "standard" (普通自由) 或 "strict" (严格关卡)
        self.study_logs = study_logs if study_logs else []  # 学习打卡记录列表: [{"date": "YYYY-MM-DD", "minutes": 30, "note": "..."}]

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
            study_logs=data.get("study_logs", [])
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