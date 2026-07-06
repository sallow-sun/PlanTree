# data_manager.py
import os
import json
import zlib
import base64
import datetime
from PySide6.QtWidgets import QMessageBox, QInputDialog, QApplication
from models import StudyNode

class DataManagerMixin:
    """数据管理混入类，升级支持多档案管理与全局书架索引联动"""

    def init_library_env(self):
        """初始化书架环境，创建 plans 目录、默认索引文件，并自动迁移旧导图"""
        self.plans_dir = "plans"
        self.manifest_path = "library_manifest.json"
        self.current_plan_id = None
        self.current_plan_path = ""
        self.library_manifest = {"last_opened_id": "", "plans": []}

        # 创建存储文件夹
        if not os.path.exists(self.plans_dir):
            os.makedirs(self.plans_dir)

        # 加载或创建全局索引
        self.load_library_manifest()

        # 自动无缝迁移旧版单文件数据 my_learning_plan.json
        old_plan_path = "my_learning_plan.json"
        if os.path.exists(old_plan_path) and not self.library_manifest["plans"]:
            try:
                with open(old_plan_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                
                # 迁移至新书架管理目录下
                migrated_id = "plan_migrated_default"
                new_path = os.path.join(self.plans_dir, f"{migrated_id}.json")
                with open(new_path, "w", encoding="utf-8") as f:
                    json.dump(old_data, f, indent=4, ensure_ascii=False)
                
                # 自动解析旧导图的节点名作为书本名称
                old_name = old_data.get("name", "已迁移的历史计划")
                old_color = old_data.get("color", "#2d3748")

                # 在索引中注册
                self.library_manifest["plans"].append({
                    "id": migrated_id,
                    "name": old_name,
                    "file_path": new_path,
                    "cover_color": old_color,
                    "theme_index": 0,
                    "progress": 0,  # 首次打开会自动重算
                    "total_hours": 0.0,
                    "last_active": datetime.date.today().strftime("%Y-%m-%d")
                })
                self.save_library_manifest()
                print(f"检测到历史数据，已自动迁移：{old_name}")
            except Exception as e:
                print(f"自动迁移失败: {e}")

    def load_library_manifest(self):
        """加载书架索引文件"""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self.library_manifest = json.load(f)
            except Exception as e:
                print(f"读取书架索引失败: {e}")
        else:
            self.save_library_manifest()

    def save_library_manifest(self):
        """保存书架索引文件"""
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.library_manifest, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存书架索引失败: {e}")

    def load_user_config(self):
        """从本地加载用户偏好设置"""
        try:
            with open("user_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            self.user_config.update(config)
        except FileNotFoundError:
            pass

    def save_user_config(self):
        """保存用户偏好设置"""
        try:
            with open("user_config.json", "w", encoding="utf-8") as f:
                json.dump(self.user_config, f, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def load_data(self):
        """从当前选择的路径加载特定知识树 JSON 数据"""
        if not self.current_plan_path or not os.path.exists(self.current_plan_path):
            self.root_node = StudyNode(node_id="root", name="新空白路线", notes="")
            self.save_data()
        else:
            try:
                with open(self.current_plan_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.root_node = StudyNode.from_dict(data)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法解析数据文件：{e}")
                self.root_node = StudyNode(node_id="root", name="损坏的数据备份", notes="")
        
        self._rebuild_node_dict()

    def save_data(self):
        """保存当前打开的知识树到其特定路径"""
        if self.root_node and self.current_plan_path:
            try:
                with open(self.current_plan_path, "w", encoding="utf-8") as f:
                    json.dump(self.root_node.to_dict(), f, indent=4, ensure_ascii=False)
                self.update_manifest_stats_for_current()
            except Exception as e:
                print(f"保存路线失败: {e}")

    def update_manifest_stats_for_current(self):
        """计算统计数据并更新书架，建立主题索引与代表色的映射回写"""
        if not self.current_plan_id:
            return
            
        total_nodes = len(self.all_nodes)
        completed_nodes = sum(1 for n in self.all_nodes.values() if n.progress >= 100)
        progress_val = int((completed_nodes / total_nodes) * 100) if total_nodes > 0 else 0

        total_minutes = 0
        for node in self.all_nodes.values():
            logs = getattr(node, "study_logs", [])
            total_minutes += sum(log.get("minutes", 0) for log in logs)
        total_hours = round(total_minutes / 60.0, 1)

        # 获取具体的路线工作区当前绑定的运行期主题
        theme_idx = getattr(self, "current_workspace_theme_idx", 0)
        
        # 将主题索引无缝折射映射到书架封面代表色上，使书架封面色与画布主题深度同步
        color_map = {
            0: "#2d3748",  # 现代钢青
            1: "#962d22",  # 复古朱砂
            2: "#FFD1DC",  # 蔷薇柔粉
            3: "#020502",  # 荧光暗绿
            4: "#002FA7"   # 克莱因蓝
        }
        new_color = color_map.get(theme_idx, "#2d3748")

        for plan in self.library_manifest.get("plans", []):
            if plan["id"] == self.current_plan_id:
                plan["progress"] = progress_val
                plan["total_hours"] = total_hours
                plan["theme_index"] = theme_idx
                plan["cover_color"] = new_color # 彻底更新卡片封面的显示色彩
                break
        self.save_library_manifest()

    def _rebuild_node_dict(self):
        """重建节点 ID 字典"""
        self.all_nodes.clear()
        if self.root_node:
            self._build_node_dict(self.root_node)

    def _build_node_dict(self, node):
        self.all_nodes[node.node_id] = node
        for child in node.children:
            self._build_node_dict(child)

    def _remove_node_recursive(self, parent_node, target_id):
        """递归寻找并删除节点"""
        for child in parent_node.children:
            if child.node_id == target_id:
                parent_node.children.remove(child)
                return True
            if self._remove_node_recursive(child, target_id):
                return True
        return False

    def _find_parent_and_siblings(self, current_parent, target_id):
        """递归检索父节点与兄弟节点"""
        for child in current_parent.children:
            if child.node_id == target_id:
                return current_parent, current_parent.children
                
        for child in current_parent.children:
            p, siblings = self._find_parent_and_siblings(child, target_id)
            if p is not None:
                return p, siblings
        return None, []

    def is_locked(self, node):
        """递归判定当前节点的锁定状态"""
        if node.node_id == self.root_node.node_id:
            return False
            
        if getattr(node, "node_type", "standard") == "strict":
            if node.prerequisites:
                for prereq_id in node.prerequisites:
                    prereq_node = self.all_nodes.get(prereq_id)
                    if not prereq_node or prereq_node.progress < 100:
                        return True
            else:
                parent_node, _ = self._find_parent_and_siblings(self.root_node, node.node_id)
                if parent_node and parent_node.node_id != self.root_node.node_id:
                    if parent_node.progress < 100:
                        return True
        else:
            for prereq_id in node.prerequisites:
                prereq_node = self.all_nodes.get(prereq_id)
                if not prereq_node or prereq_node.progress < 100:
                    return True
                    
        return False

    def relock_dependent_nodes(self, completed_node_id):
        """级联判定后续节点锁定状态"""
        changed = True
        while changed:
            changed = False
            for node in self.all_nodes.values():
                if node.node_id == self.root_node.node_id:
                    continue
                if self.is_locked(node) and node.progress > 0:
                    node.progress = 0
                    changed = True

    def export_share_code(self):
        """生成脱敏分享码"""
        if not self.root_node:
            QMessageBox.warning(self, "提示", "当前无学习路线可供导出！")
            return
        try:
            def sanitize_node(node):
                return {
                    "node_id": node.node_id,
                    "name": node.name,
                    "prerequisites": node.prerequisites,
                    "notes": node.notes,
                    "progress": 0,
                    "color": node.color,
                    "node_type": getattr(node, "node_type", "standard"),
                    "study_logs": [],
                    "children": [sanitize_node(child) for child in node.children]
                }

            sanitized_tree_dict = sanitize_node(self.root_node)
            json_str = json.dumps(sanitized_tree_dict, indent=4, ensure_ascii=False)
            compressed_data = zlib.compress(json_str.encode("utf-8"))
            share_code = base64.b64encode(compressed_data).decode("utf-8")
            
            QApplication.clipboard().setText(share_code)
            QMessageBox.information(
                self, 
                "分享成功", 
                "您的路线分享码已复制到剪贴板！\n\n"
                "[安全保护说明]：已自动清除您的个人完成进度与打卡记录，他人导入后将作为全新的空白计划开始学习。"
            )
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"生成分享码时出错: {e}")

    def import_share_code_direct(self, code_str, plan_name):
        """将分享码直接解析并写入指定的新计划文件中"""
        try:
            compressed_data = base64.b64decode(code_str.strip().encode("utf-8"))
            json_str = zlib.decompress(compressed_data).decode("utf-8")
            imported_data = json.loads(json_str)
            imported_data["name"] = plan_name
            
            import uuid
            new_id = "plan_" + uuid.uuid4().hex[:8]
            file_path = os.path.join(self.plans_dir, f"{new_id}.json")
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(imported_data, f, indent=4, ensure_ascii=False)
                
            return new_id, file_path
        except Exception as e:
            raise Exception(f"解析分享码时出错: {e}")
        
    def import_share_code(self):
        """[工作区端] 解析粘贴的分享码，覆盖写入当前正在编辑的计划"""
        if not self.current_plan_path:
            QMessageBox.warning(self, "提示", "当前未打开任何学习计划，请返回书架选择。")
            return
            
        code, ok = QInputDialog.getMultiLineText(
            self, 
            "覆盖导入计划", 
            "警告：覆盖导入将会完全抹去当前路线的所有进度和备注！\n\n请在下方粘贴您收到的分享码："
        )
        if ok and code.strip():
            try:
                compressed_data = base64.b64decode(code.strip().encode("utf-8"))
                json_str = zlib.decompress(compressed_data).decode("utf-8")
                imported_data = json.loads(json_str)
                
                with open(self.current_plan_path, "w", encoding="utf-8") as f:
                    json.dump(imported_data, f, indent=4, ensure_ascii=False)
                
                self.load_data()
                self.refresh_ui()
                QMessageBox.information(self, "导入成功", "已成功将分享码覆盖写入到当前计划中！")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"无效的分享码，无法解析！\n错误信息: {e}")