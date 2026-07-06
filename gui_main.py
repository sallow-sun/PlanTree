# gui_main.py
import sys
import uuid
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QPushButton, QHBoxLayout, 
    QVBoxLayout, QWidget, QGraphicsScene, QSplitter, QDialog, QStackedWidget
)
from PySide6.QtGui import QColor, QPen, QPainterPath
from PySide6.QtCore import Qt, QPointF

# 引入子模块
from models import StudyNode
from dialogs import SettingsDialog, PrereqSelectDialog
from canvas_views import VisualNodeItem, InteractiveGraphicsView
from data_manager import DataManagerMixin  
from inspector_panel import InspectorPanel  
from library_view import LibraryView  
import themes


class KnowledgeTreeApp(QMainWindow, DataManagerMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D 知识图谱学习路线规划系统")
        self.resize(1150, 750)

        # 1. 数据环境与偏好初始化
        self.all_nodes = {}
        self.root_node = None
        self.selected_node_id = None
        self.node_positions = {}

        self.user_config = {
            "confirm_delete": True,
            "add_select_mode": 0,
            "delete_select_mode": 1,
            "inspector_position": 0,  
            "inspector_show_mode": 0,
            "layout_direction": 0,
            "auto_center_canvas": True,
            "nav_mode": 0,
            "new_node_color_policy": 0, # 新增 0: 默认颜色，1: 继承父节点颜色
            "theme": 0 
        }

        self.current_page_idx = 0  
        self.current_workspace_theme_idx = 0

        self.init_library_env()
        self.load_user_config()

        # 2. 引入 QStackedWidget 路由机制
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # ---------------- 路由页 0：书架大厅 ----------------
        self.library_page = LibraryView(self)
        self.library_page.plan_selected.connect(self.route_to_workspace)
        self.central_stack.addWidget(self.library_page)

        # ---------------- 路由页 1：图谱画布工作区 ----------------
        self.workspace_widget = QWidget()
        self.workspace_layout = QVBoxLayout(self.workspace_widget)
        self.workspace_layout.setContentsMargins(12, 12, 12, 12)
        self.workspace_layout.setSpacing(10)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(8) 

        self.btn_back_library = QPushButton()
        self.btn_back_library.clicked.connect(self.route_to_library)
        toolbar_layout.addWidget(self.btn_back_library)
        toolbar_layout.addSpacing(15)
        
        self.btn_export = QPushButton()
        self.btn_import = QPushButton()
        self.btn_add_child = QPushButton()
        self.btn_delete_node = QPushButton()
        self.btn_move_up = QPushButton()
        self.btn_move_down = QPushButton()
        self.btn_edit_prereq = QPushButton()
        self.btn_settings = QPushButton()
        
        self.btn_delete_node.setObjectName("dangerButton")
        
        self.btn_export.clicked.connect(self.export_share_code)
        self.btn_import.clicked.connect(self.import_share_code)
        self.btn_add_child.clicked.connect(self.add_child_node_fast)
        self.btn_delete_node.clicked.connect(self.delete_selected_node)
        self.btn_move_up.clicked.connect(lambda: self.move_sibling_order(-1))
        self.btn_move_down.clicked.connect(lambda: self.move_sibling_order(1))
        self.btn_edit_prereq.clicked.connect(self.edit_prerequisites)
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addWidget(self.btn_import)
        toolbar_layout.addSpacing(15) 
        toolbar_layout.addWidget(self.btn_add_child)
        toolbar_layout.addWidget(self.btn_delete_node)
        toolbar_layout.addWidget(self.btn_move_up)
        toolbar_layout.addWidget(self.btn_move_down)
        toolbar_layout.addWidget(self.btn_edit_prereq)
        toolbar_layout.addStretch() 
        toolbar_layout.addWidget(self.btn_settings)
        
        self.workspace_layout.addLayout(toolbar_layout)

        self.splitter = QSplitter(Qt.Horizontal)
        self.workspace_layout.addWidget(self.splitter, stretch=1)
        
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.view = InteractiveGraphicsView(self.scene, self)
        self.splitter.addWidget(self.view)

        self.inspector = InspectorPanel(self)
        self.splitter.addWidget(self.inspector)
        
        self.central_stack.addWidget(self.workspace_widget)

        self.scene.selectionChanged.connect(self.on_canvas_selection_changed)

        self.apply_inspector_layout_config()
        self.route_to_library()

    # ---- 路由跳转控制 ----

    def route_to_library(self):
        if self.current_plan_path:
            self.save_data()
            
        self.current_plan_id = None
        self.current_plan_path = ""
        self.root_node = None
        self.selected_node_id = None
        self.all_nodes.clear()

        self.current_page_idx = 0
        self.central_stack.setCurrentIndex(0)

        library_theme = self.get_current_theme_class()
        self.setStyleSheet(library_theme.qss)
        self.library_page.adapt_to_theme(library_theme)

        self.library_page.refresh_shelf()
        self.setWindowTitle("the tree")

    def route_to_workspace(self, plan_id, file_path):
        self.current_plan_id = plan_id
        self.current_plan_path = file_path

        self.load_data()
        
        for plan in self.library_manifest.get("plans", []):
            if plan["id"] == plan_id:
                self.current_workspace_theme_idx = plan.get("theme_index", 0)
                break
                
        self.current_page_idx = 1
        self.central_stack.setCurrentIndex(1)
        
        self.apply_theme_styles()
        self.refresh_ui()
        
        self.setWindowTitle(f"当前学习路径规划中 - {self.root_node.name}")
        
        if self.root_node and self.root_node.node_id in self.node_positions:
            pos = self.node_positions[self.root_node.node_id]
            self.view.centerOn(pos[0] + 90, pos[1] + 35)

        for plan in self.library_manifest.get("plans", []):
            if plan["id"] == self.current_plan_id:
                plan["last_active"] = datetime.date.today().strftime("%Y-%m-%d")
                break
        self.save_library_manifest()

    def get_current_theme_class(self):
        if getattr(self, "current_page_idx", 0) == 0:
            theme_index = self.user_config.get("theme", 0)  
        else:
            theme_index = getattr(self, "current_workspace_theme_idx", 0)  

        if theme_index == 1:
            return themes.ConstructivistTheme
        elif theme_index == 2:
            return themes.RococoTheme
        elif theme_index == 3:
            return themes.TerminalTheme
        elif theme_index == 4:
            return themes.SwissMinimalistTheme
        return themes.ModernDarkTheme

    def apply_theme_styles(self):
        current_theme = self.get_current_theme_class()
        self.setStyleSheet(current_theme.qss)
        
        txt_map = current_theme.button_texts
        self.btn_back_library.setText(txt_map.get("back", "⬅ 返回"))  
        self.btn_export.setText(txt_map.get("export", "导出路线"))
        self.btn_import.setText(txt_map.get("import", "导入路线"))
        self.btn_add_child.setText(txt_map.get("add", "添加子节点"))
        self.btn_delete_node.setText(txt_map.get("delete", "删除节点"))
        self.btn_move_up.setText(txt_map.get("move_up", "向上/前移"))
        self.btn_move_down.setText(txt_map.get("move_down", "向下/后移"))
        self.btn_edit_prereq.setText(txt_map.get("prereq", "前置依赖"))
        self.btn_settings.setText(txt_map.get("settings", "偏好设置"))

    def apply_inspector_layout_config(self):
        position = self.user_config.get("inspector_position", 0)
        
        self.inspector.setMinimumWidth(0)
        self.inspector.setMaximumWidth(16777215)
        self.inspector.setMinimumHeight(0)
        self.inspector.setMaximumHeight(16777215)
        
        if position == 0:
            self.splitter.setOrientation(Qt.Horizontal)
            self.inspector.setup_layout_by_mode(0)
            self.splitter.setSizes([850, 280])     
        else:
            self.splitter.setOrientation(Qt.Vertical)
            self.inspector.setup_layout_by_mode(1)
            self.splitter.setSizes([550, 200])     
        
        self.apply_theme_styles()
        self.splitter.updateGeometry()

    def open_settings_dialog(self):
        temp_config = self.user_config.copy()
        
        if self.current_plan_id:
            temp_config["theme"] = self.current_workspace_theme_idx
        else:
            temp_config["theme"] = self.user_config.get("theme", 0)

        dialog = SettingsDialog(temp_config, self)
        dialog.setStyleSheet(self.get_current_theme_class().qss) 
        if dialog.exec() == QDialog.Accepted:
            new_config = dialog.get_config()
            
            if self.current_plan_id:
                self.current_workspace_theme_idx = new_config.get("theme", 0)
                for k in self.user_config:
                    if k != "theme":
                        self.user_config[k] = new_config[k]
                self.save_user_config()
                self.save_data()
            else:
                self.user_config = new_config
                self.save_user_config()
                current_theme = self.get_current_theme_class()
                self.setStyleSheet(current_theme.qss)
                self.library_page.adapt_to_theme(current_theme)
                self.library_page.refresh_shelf()
            
            selected_items = self.scene.selectedItems()
            if selected_items and isinstance(selected_items[0], VisualNodeItem):
                self.selected_node_id = selected_items[0].node.node_id
            else:
                self.selected_node_id = None
            
            self.apply_inspector_layout_config()
            self.refresh_ui(force_select_id=self.selected_node_id)

    def on_canvas_selection_changed(self):
        selected_items = self.scene.selectedItems()
        if selected_items and isinstance(selected_items[0], VisualNodeItem):
            node_item = selected_items[0]
            self.selected_node_id = node_item.node.node_id
            self.inspector.update_data(node_item.node) 
        else:
            self.selected_node_id = None
            self.inspector.update_data(None)

    def add_child_node_fast(self):
        if not self.selected_node_id:
            QMessageBox.warning(self, "提示", "请先在画布上点击选中一个卡片作为父节点！")
            return
        parent_node = self.all_nodes.get(self.selected_node_id)
        if not parent_node: return

        parent_id = self.selected_node_id
        new_id = "node_" + uuid.uuid4().hex[:8]
        
        # 处理颜色遗传策略 (需求 3)
        policy = self.user_config.get("new_node_color_policy", 0)
        node_color = parent_node.color if policy == 1 else "#2d3748"

        new_node = StudyNode(node_id=new_id, name="双击修改名称", notes="", color=node_color)
        parent_node.children.append(new_node)

        self._rebuild_node_dict()
        self.save_data()
        
        add_mode = self.user_config.get("add_select_mode", 0)
        if add_mode == 0:
            self.selected_node_id = new_id
        else:
            self.selected_node_id = parent_id
            
        self.refresh_ui(force_select_id=self.selected_node_id)

    def delete_selected_node(self):
        if not self.selected_node_id:
            QMessageBox.warning(self, "提示", "请先选中一个要删除的节点！")
            return
        node = self.all_nodes.get(self.selected_node_id)
        if not node: 
            return
        if self.selected_node_id == self.root_node.node_id:
            QMessageBox.warning(self, "限制", "根节点是整棵树的起点，不允许删除！")
            return

        if self.user_config.get("confirm_delete", True):
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除【{node.name}】及其下属的所有子节点吗？此操作不可逆！",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        parent_node, siblings = self._find_parent_and_siblings(self.root_node, self.selected_node_id)
        
        next_select_id = None
        if parent_node:
            mode = self.user_config.get("delete_select_mode", 1)
            if mode == 1:
                next_select_id = parent_node.node_id
            elif mode == 2:
                idx = -1
                for i, sib in enumerate(siblings):
                    if sib.node_id == self.selected_node_id:
                        idx = i
                        break
                
                if len(siblings) > 1:
                    if idx > 0:
                        next_select_id = siblings[idx - 1].node_id
                    else:
                        next_select_id = siblings[idx + 1].node_id
                else:
                    next_select_id = parent_node.node_id

        self._remove_node_recursive(self.root_node, self.selected_node_id)
        self._rebuild_node_dict()
        
        self.save_data()
        self.refresh_ui(force_select_id=next_select_id)

    def edit_prerequisites(self):
        if not self.selected_node_id:
            QMessageBox.warning(self, "提示", "请先选择一个节点！")
            return
        node = self.all_nodes.get(self.selected_node_id)
        if not node: return
        if self.selected_node_id == self.root_node.node_id:
            QMessageBox.warning(self, "限制", "根节点无法设置前置依赖！")
            return

        dialog = PrereqSelectDialog(node, self.all_nodes, self)
        dialog.setStyleSheet(self.get_current_theme_class().qss) 
        if dialog.exec() == QDialog.Accepted:
            selected_ids = dialog.get_selected_prereqs()
            node.prerequisites = selected_ids
            self.save_data()
            self.refresh_ui(force_select_id=self.selected_node_id)
            QMessageBox.information(self, "成功", f"【{node.name}】的前置依赖更新成功！")

    def calculate_subtree_heights(self, node, spacing_y=110):
        if not node.children:
            return spacing_y
        total_height = 0
        for child in node.children:
            total_height += self.calculate_subtree_heights(child, spacing_y)
        return total_height

    def position_nodes_recursive(self, node, x, y_start, spacing_x=280, spacing_y=110):
        subtree_height = self.calculate_subtree_heights(node, spacing_y)
        my_y = y_start + subtree_height / 2 - 35
        self.node_positions[node.node_id] = (x, my_y)
        
        current_y = y_start
        for child in node.children:
            child_height = self.calculate_subtree_heights(child, spacing_y)
            self.position_nodes_recursive(child, x + spacing_x, current_y, spacing_x, spacing_y)
            current_y += child_height

    def calculate_subtree_widths(self, node, spacing_x=220):
        if not node.children:
            return spacing_x
        total_width = 0
        for child in node.children:
            total_width += self.calculate_subtree_widths(child, spacing_x)
        return total_width

    def position_nodes_vertical_recursive(self, node, y, x_start, spacing_x=220, spacing_y=180):
        subtree_width = self.calculate_subtree_widths(node, spacing_x)
        my_x = x_start + subtree_width / 2 - 90  
        self.node_positions[node.node_id] = (my_x, y)
        
        current_x = x_start
        for child in node.children:
            child_width = self.calculate_subtree_widths(child, spacing_x)
            self.position_nodes_vertical_recursive(child, y + spacing_y, current_x, spacing_x, spacing_y)
            current_x += child_width

    def refresh_ui(self, force_select_id=None):
        if force_select_id is not None:
            self.selected_node_id = force_select_id
        else:
            selected_items = self.scene.selectedItems()
            if selected_items and isinstance(selected_items[0], VisualNodeItem):
                self.selected_node_id = selected_items[0].node.node_id
            else:
                self.selected_node_id = None

        self.scene.blockSignals(True)
        self.scene.clear()
        self.node_positions.clear()

        if not self.root_node:
            self.scene.blockSignals(False)
            return

        layout_dir = self.user_config.get("layout_direction", 0)
        if layout_dir == 0:
            self.position_nodes_recursive(self.root_node, 50, -200)
        else:
            self.position_nodes_vertical_recursive(self.root_node, 50, -350)

        for node_id, node in self.all_nodes.items():
            x, y = self.node_positions[node_id]
            is_node_locked = self.is_locked(node)
            
            item = VisualNodeItem(node, is_node_locked, self)
            item.setPos(x, y)
            self.scene.addItem(item)

            if node_id == self.selected_node_id:
                item.setSelected(True)

        self.draw_tree_connections_recursive(self.root_node)
        self.scene.blockSignals(False)

        if self.selected_node_id:
            current_node = self.all_nodes.get(self.selected_node_id)
            self.inspector.update_data(current_node)
        else:
            self.inspector.update_data(None)

    def draw_tree_connections_recursive(self, node):
        layout_dir = self.user_config.get("layout_direction", 0)
        parent_id = node.node_id
        px, py = self.node_positions[parent_id]

        current_theme = self.get_current_theme_class()

        for child in node.children:
            child_id = child.node_id
            cx, cy = self.node_positions[child_id]

            if layout_dir == 0:
                start_pt = QPointF(px + 180, py + 35)
                end_pt = QPointF(cx, cy + 35)
            else:
                start_pt = QPointF(px + 90, py + 70) 
                end_pt = QPointF(cx + 90, cy)        

            path = current_theme.draw_connection_path(start_pt, end_pt, layout_dir)
            is_child_locked = self.is_locked(child)

            if isinstance(current_theme, themes.ConstructivistTheme) and not is_child_locked:
                pen_outer = QPen(QColor("#1a1a1a"), 5, Qt.SolidLine) 
                pen_inner = QPen(QColor("#EADEC9"), 2.0, Qt.SolidLine) 
                
                path_outer = self.scene.addPath(path, pen_outer)
                path_outer.setZValue(-2)
                path_inner = self.scene.addPath(path, pen_inner)
                path_inner.setZValue(-1)
            else:
                line_color = current_theme.get_line_color(is_child_locked)
                pen = QPen(line_color, current_theme.line_width, Qt.SolidLine)
                path_item = self.scene.addPath(path, pen)
                path_item.setZValue(-1)

            self.draw_tree_connections_recursive(child)

    def keyPressEvent(self, event):
        if self.inspector.inspect_name.hasFocus() or self.inspector.inspect_notes.hasFocus():
            super().keyPressEvent(event)
            return

        if not self.selected_node_id:
            super().keyPressEvent(event)
            return

        key = event.key()

        if key == Qt.Key_Delete:
            self.delete_selected_node()
        elif key in [Qt.Key_Return, Qt.Key_Enter]:
            self.add_child_node_fast()
        elif key == Qt.Key_M:
            self.toggle_selected_node_mode()
        elif key in [
            Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right,
            Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D
        ]:
            self.handle_navigation(key)
    
    def toggle_selected_node_mode(self):
        if not self.selected_node_id:
            return
        node = self.all_nodes.get(self.selected_node_id)
        if not node:
            return

        if node.node_id == self.root_node.node_id:
            self.statusBar().showMessage("系统提示：根节点不允许变更为严格约束模式", 2000)
            return

        current_type = getattr(node, "node_type", "standard")
        new_type = "strict" if current_type == "standard" else "standard"
        node.node_type = new_type

        if new_type == "strict" and self.is_locked(node):
            node.progress = 0
            self.relock_dependent_nodes(node.node_id)

        self.save_data()
        self.refresh_ui(force_select_id=self.selected_node_id)
        
        mode_text = "严格模式 (前置/父级需达到100%)" if new_type == "strict" else "自由模式"
        self.statusBar().showMessage(f"已将该节点变更为：{mode_text}", 2000)

    def find_nearest_spatial_node(self, current_id, direction):
        if not current_id or current_id not in self.node_positions:
            return None
        
        curr_pos = self.node_positions[current_id]
        curr_x, curr_y = curr_pos[0], curr_pos[1]
        
        best_node_id = None
        min_score = float('inf')
        
        ortho_penalty = 3.0
        
        for node_id, pos in self.node_positions.items():
            if node_id == current_id:
                continue
            
            ox, oy = pos[0], pos[1]
            dx = ox - curr_x
            dy = oy - curr_y
            
            if direction == 'up' and dy < 0:
                score = abs(dy) + ortho_penalty * abs(dx)
                if score < min_score:
                    min_score = score
                    best_node_id = node_id
            elif direction == 'down' and dy > 0:
                score = abs(dy) + ortho_penalty * abs(dx)
                if score < min_score:
                    min_score = score
                    best_node_id = node_id
            elif direction == 'left' and dx < 0:
                score = abs(dx) + ortho_penalty * abs(dy)
                if score < min_score:
                    min_score = score
                    best_node_id = node_id
            elif direction == 'right' and dx > 0:
                score = abs(dx) + ortho_penalty * abs(dy)
                if score < min_score:
                    min_score = score
                    best_node_id = node_id
                    
        return best_node_id

    def handle_navigation(self, key):
        dir_str = None
        if key in [Qt.Key_Up, Qt.Key_W]: dir_str = 'up'
        elif key in [Qt.Key_Down, Qt.Key_S]: dir_str = 'down'
        elif key in [Qt.Key_Left, Qt.Key_A]: dir_str = 'left'
        elif key in [Qt.Key_Right, Qt.Key_D]: dir_str = 'right'

        if not dir_str:
            return

        nav_mode = self.user_config.get("nav_mode", 0) 
        target_id = None

        if nav_mode == 0:
            target_id = self.find_nearest_spatial_node(self.selected_node_id, dir_str)
        else:
            mapped_key = None
            if dir_str == 'up': mapped_key = Qt.Key_Up
            elif dir_str == 'down': mapped_key = Qt.Key_Down
            elif dir_str == 'left': mapped_key = Qt.Key_Left
            elif dir_str == 'right': mapped_key = Qt.Key_Right
            target_id = self._get_logical_navigation_target(mapped_key)

        if target_id:
            self.selected_node_id = target_id
            self.refresh_ui(force_select_id=target_id)
            
            if self.user_config.get("auto_center_canvas", True):
                if target_id in self.node_positions:
                    pos = self.node_positions[target_id]
                    self.view.centerOn(pos[0] + 90, pos[1] + 35)

    def _get_logical_navigation_target(self, key):
        if not self.selected_node_id or not self.root_node:
            return None

        current_node = self.all_nodes.get(self.selected_node_id)
        if not current_node:
            return None

        layout_dir = self.user_config.get("layout_direction", 0)
        parent_node, siblings = self._find_parent_and_siblings(self.root_node, self.selected_node_id)

        if current_node.node_id == self.root_node.node_id:
            siblings = []
            parent_node = None

        current_idx = -1
        if siblings:
            for i, sibling in enumerate(siblings):
                if sibling.node_id == self.selected_node_id:
                    current_idx = i
                    break

        if layout_dir == 0: 
            if key == Qt.Key_Left:
                return parent_node.node_id if parent_node else None
            elif key == Qt.Key_Right:
                return current_node.children[0].node_id if current_node.children else None
            elif key == Qt.Key_Up:
                if current_idx > 0:
                    return siblings[current_idx - 1].node_id
                return None
            elif key == Qt.Key_Down:
                if siblings and current_idx < len(siblings) - 1:
                    return siblings[current_idx + 1].node_id
                return None
        else: 
            if key == Qt.Key_Up:
                return parent_node.node_id if parent_node else None
            elif key == Qt.Key_Down:
                return current_node.children[0].node_id if current_node.children else None
            elif key == Qt.Key_Left:
                if current_idx > 0:
                    return siblings[current_idx - 1].node_id
                return None
            elif key == Qt.Key_Right:
                if siblings and current_idx < len(siblings) - 1:
                    return siblings[current_idx + 1].node_id
                return None

        return None
    
    def move_sibling_order(self, direction):
        if not self.selected_node_id:
            QMessageBox.warning(self, "提示", "请先选中一个要调整顺序的节点！")
            return
        if self.selected_node_id == self.root_node.node_id:
            return 

        parent_node, siblings = self._find_parent_and_siblings(self.root_node, self.selected_node_id)
        if not parent_node or len(siblings) <= 1:
            return 

        idx = -1
        for i, child in enumerate(siblings):
            if child.node_id == self.selected_node_id:
                idx = i
                break

        if idx == -1:
            return

        new_idx = idx + direction
        if 0 <= new_idx < len(siblings):
            siblings[idx], siblings[new_idx] = siblings[new_idx], siblings[idx]
            self.save_data()
            self.refresh_ui(force_select_id=self.selected_node_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KnowledgeTreeApp()
    window.show()
    sys.exit(app.exec())