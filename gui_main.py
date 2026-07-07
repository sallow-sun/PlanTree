# gui_main.py
import sys
import uuid
import datetime
import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QPushButton, QHBoxLayout, 
    QVBoxLayout, QWidget, QGraphicsScene, QSplitter, QDialog, QStackedWidget,
    QMenu, QFileDialog
)
from PySide6.QtGui import QColor, QPen, QPainterPath, QAction, QCursor
from PySide6.QtCore import Qt, QPointF, QTimer  
from PySide6.QtCore import QRectF

# 引入子模块
from models import StudyNode
from dialogs import SettingsDialog, PrereqSelectDialog, HelpDialog  
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
            "new_node_color_policy": 0, 
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
        
        # 撤销与重做按钮
        self.btn_undo = QPushButton()
        self.btn_redo = QPushButton()
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo.clicked.connect(self.redo)
        
        self.btn_protect_toggle = QPushButton()  # 一键防护（只读）开关
        self.btn_add_child = QPushButton()
        self.btn_delete_node = QPushButton()
        self.btn_move_up = QPushButton()
        self.btn_move_down = QPushButton()
        self.btn_edit_prereq = QPushButton()
        
        self.btn_canvas_bg = QPushButton()
        self.btn_canvas_bg.clicked.connect(self.set_custom_canvas_background)
        
        self.btn_help = QPushButton()
        self.btn_help.clicked.connect(self.show_help_dialog)
        
        self.btn_settings = QPushButton()
        self.btn_delete_node.setObjectName("dangerButton")
        
        self.btn_export.clicked.connect(self.export_share_code)
        self.btn_import.clicked.connect(self.import_share_code)
        self.btn_protect_toggle.clicked.connect(self.toggle_workspace_protection)
        self.btn_add_child.clicked.connect(self.add_child_node_fast)
        self.btn_delete_node.clicked.connect(self.delete_selected_node)
        self.btn_move_up.clicked.connect(lambda: self.move_sibling_order(-1))
        self.btn_move_down.clicked.connect(lambda: self.move_sibling_order(1))
        self.btn_edit_prereq.clicked.connect(self.edit_prerequisites)
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addWidget(self.btn_import)
        toolbar_layout.addWidget(self.btn_undo)
        toolbar_layout.addWidget(self.btn_redo)
        toolbar_layout.addSpacing(15) 
        toolbar_layout.addWidget(self.btn_protect_toggle)
        toolbar_layout.addWidget(self.btn_add_child)
        toolbar_layout.addWidget(self.btn_delete_node)
        toolbar_layout.addWidget(self.btn_move_up)
        toolbar_layout.addWidget(self.btn_move_down)
        toolbar_layout.addWidget(self.btn_edit_prereq)
        toolbar_layout.addWidget(self.btn_canvas_bg)  
        toolbar_layout.addStretch() 
        toolbar_layout.addWidget(self.btn_help)      
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

    @property
    def current_layout_direction(self):
        """动态获取当前使用的布局方向，实现各导图的完全解耦"""
        if self.root_node:
            return getattr(self.root_node, "layout_direction", 0)
        return self.user_config.get("layout_direction", 0)

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
        """进入图谱画布工作区"""
        self.current_plan_id = plan_id
        self.current_plan_path = file_path

        self.load_data()
        
        for plan in self.library_manifest.get("plans", []):
            if plan["id"] == plan_id:
                self.current_workspace_theme_idx = plan.get("theme_index", 0)
                break

        # 进入画布时清空历史快照
        self.undo_stack.clear()
        self.redo_stack.clear()

        self.current_page_idx = 1
        self.central_stack.setCurrentIndex(1)
        
        self.apply_theme_styles()
        self.refresh_ui()
        self.update_undo_redo_buttons()
        
        self.setWindowTitle(f"当前学习路径规划中 - {self.root_node.name}")
        
        if self.root_node:
            QTimer.singleShot(50, lambda: self.center_on_node(self.root_node.node_id))

        for plan in self.library_manifest.get("plans", []):
            if plan["id"] == self.current_plan_id:
                plan["last_active"] = datetime.date.today().strftime("%Y-%m-%d")
                break
        self.save_library_manifest()

    def center_on_node(self, node_id):
        """安全居中定位到指定节点"""
        if not node_id or self.current_page_idx != 1:
            return
        if node_id in self.node_positions:
            pos = self.node_positions[node_id]
            self.view.centerOn(pos[0] + 90, pos[1] + 35)

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
        self.btn_undo.setText(txt_map.get("undo", "撤销"))
        self.btn_redo.setText(txt_map.get("redo", "恢复"))
        self.btn_add_child.setText(txt_map.get("add", "添加子节点"))
        self.btn_delete_node.setText(txt_map.get("delete", "删除节点"))
        self.btn_move_up.setText(txt_map.get("move_up", "向上/前移"))
        self.btn_move_down.setText(txt_map.get("move_down", "向下/后移"))
        self.btn_edit_prereq.setText(txt_map.get("prereq", "前置依赖"))
        self.btn_canvas_bg.setText(txt_map.get("canvas_bg", "画布背景")) 
        self.btn_help.setText(txt_map.get("help", "使用帮助"))       
        self.btn_settings.setText(txt_map.get("settings", "偏好设置"))

        # 动态刷新一键防护按钮文案和外观状态
        if self.root_node and getattr(self.root_node, "is_protected", False):
            self.btn_protect_toggle.setText("切换至普通模式")
            self.btn_protect_toggle.setStyleSheet("background-color: #511c1c; color: #ff9999; border-color: #722727;")
        else:
            self.btn_protect_toggle.setText("切换至保护模式")
            self.btn_protect_toggle.setStyleSheet("")

    def update_undo_redo_buttons(self):
        """根据快照栈数据量状态，激活或禁用工具栏按钮"""
        if hasattr(self, "btn_undo") and hasattr(self, "btn_redo"):
            self.btn_undo.setEnabled(bool(self.undo_stack))
            self.btn_redo.setEnabled(bool(self.redo_stack))

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
            if self.root_node:
                temp_config["layout_direction"] = getattr(self.root_node, "layout_direction", 0)
        else:
            temp_config["theme"] = self.user_config.get("theme", 0)
            temp_config["layout_direction"] = self.user_config.get("layout_direction", 0)

        dialog = SettingsDialog(temp_config, self)
        dialog.setStyleSheet(self.get_current_theme_class().qss) 
        if dialog.exec() == QDialog.Accepted:
            new_config = dialog.get_config()
            
            if self.current_plan_id:
                self.current_workspace_theme_idx = new_config.get("theme", 0)
                if self.root_node:
                    self.root_node.layout_direction = new_config.get("layout_direction", 0)
                for k in self.user_config:
                    if k not in ["theme", "layout_direction"]:
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

    def check_protection_and_warn(self):
        """防护状态验证辅助函数：开启防护时拒绝操作并弹出提示"""
        if self.root_node and getattr(self.root_node, "is_protected", False):
            QMessageBox.warning(self, "一键防护中", "当前导图已开启一键防护（只读），禁止增加、删除或修改节点属性！")
            return True
        return False

    def toggle_workspace_protection(self):
        """开启或解除导图内部一键防护"""
        if not self.root_node:
            return
        self.root_node.is_protected = not getattr(self.root_node, "is_protected", False)
        self.save_data()
        self.apply_theme_styles()
        self.refresh_ui(force_select_id=self.selected_node_id)
        
        status = "已开启更改防护" if self.root_node.is_protected else "已解除防护"
        self.statusBar().showMessage(f"系统提示：当前导图{status}", 2500)

    def add_child_node_fast(self):
        # 验证防护状态
        if self.check_protection_and_warn():
            return
            
        if not self.selected_node_id:
            QMessageBox.warning(self, "提示", "请先在画布上点击选中一个卡片作为父节点！")
            return
        parent_node = self.all_nodes.get(self.selected_node_id)
        if not parent_node: return

        # 变更前推入撤销栈
        self.push_undo_state()

        parent_id = self.selected_node_id
        new_id = "node_" + uuid.uuid4().hex[:8]
        
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

        if self.user_config.get("auto_center_canvas", True):
            QTimer.singleShot(50, lambda: self.center_on_node(self.selected_node_id))

    def delete_selected_node(self):
        # 验证防护状态
        if self.check_protection_and_warn():
            return

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

        # 变更前推入撤销栈
        self.push_undo_state()

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

        if self.user_config.get("auto_center_canvas", True) and next_select_id:
            QTimer.singleShot(50, lambda: self.center_on_node(next_select_id))

    def edit_prerequisites(self):
        # 验证防护状态
        if self.check_protection_and_warn():
            return

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
            # 变更前推入撤销栈
            self.push_undo_state()
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

        layout_dir = self.current_layout_direction
        if layout_dir == 0:
            self.position_nodes_recursive(self.root_node, 50, -200)
        else:
            self.position_nodes_vertical_recursive(self.root_node, 50, -350)

        if self.node_positions:
            xs = [pos[0] for pos in self.node_positions.values()]
            ys = [pos[1] for pos in self.node_positions.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            margin = 4000 
            rect = QRectF(
                min_x - margin,
                min_y - margin,
                (max_x - min_x) + 2 * margin + 180,
                (max_y - min_y) + 2 * margin + 70
            )
            self.scene.setSceneRect(rect)
            self.view.setSceneRect(rect)  
        else:
            default_rect = QRectF(-2000, -2000, 4000, 4000)
            self.scene.setSceneRect(default_rect)
            self.view.setSceneRect(default_rect)

        for node_id, node in self.all_nodes.items():
            x, y = self.node_positions[node_id]
            is_node_locked = self.is_locked(node)
            
            item = VisualNodeItem(node, is_node_locked, self)
            item.setPos(x, y)
            self.scene.addItem(item)

            if node_id == self.selected_node_id:
                item.setSelected(True)

        self.draw_all_connections()
        self.scene.blockSignals(False)

        if self.selected_node_id:
            current_node = self.all_nodes.get(self.selected_node_id)
            self.inspector.update_data(current_node)
        else:
            self.inspector.update_data(None)

        # 刷新撤销、重做工具栏按钮可用性
        self.update_undo_redo_buttons()

    def draw_all_connections(self):
        """一体化绘制连线：包含树状主干与前置依赖的多父级连接"""
        if not self.root_node:
            return

        self.draw_tree_connections_recursive(self.root_node)

        layout_dir = self.current_layout_direction
        current_theme = self.get_current_theme_class()

        for node_id, node in self.all_nodes.items():
            if node_id == self.root_node.node_id:
                continue

            cx, cy = self.node_positions[node_id]
            parent_node, _ = self._find_parent_and_siblings(self.root_node, node_id)
            parent_id = parent_node.node_id if parent_node else None

            for prereq_id in node.prerequisites:
                if prereq_id == parent_id:
                    continue

                if prereq_id in self.node_positions:
                    px, py = self.node_positions[prereq_id]

                    if layout_dir == 0:
                        start_pt = QPointF(px + 180, py + 35)
                        end_pt = QPointF(cx, cy + 35)
                    else:
                        start_pt = QPointF(px + 90, py + 70) 
                        end_pt = QPointF(cx + 90, cy)        

                    path = current_theme.draw_connection_path(start_pt, end_pt, layout_dir)
                    is_child_locked = self.is_locked(child_node := node)

                    if isinstance(current_theme, themes.ConstructivistTheme) and not is_child_locked:
                        pen_outer = QPen(QColor("#1a1a1a"), 3, Qt.DashLine) 
                        pen_inner = QPen(QColor("#EADEC9"), 1.5, Qt.DashLine) 
                        
                        path_outer = self.scene.addPath(path, pen_outer)
                        path_outer.setZValue(-2)
                        path_inner = self.scene.addPath(path, pen_inner)
                        path_inner.setZValue(-1)
                    else:
                        line_color = current_theme.get_line_color(is_child_locked)
                        pen = QPen(line_color, current_theme.line_width, Qt.DashLine)
                        path_item = self.scene.addPath(path, pen)
                        path_item.setZValue(-1)

    def draw_tree_connections_recursive(self, node):
        layout_dir = self.current_layout_direction
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

    def set_custom_canvas_background(self):
        if not self.root_node:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #252526; color: #cccccc; border: 1px solid #454545; }
            QMenu::item:selected { background-color: #094771; color: #ffffff; }
        """)
        
        select_act = QAction("选择画布背景图", self)
        select_act.triggered.connect(self.import_canvas_bg_image)
        menu.addAction(select_act)
        
        if getattr(self.root_node, "canvas_bg_image", ""):
            clear_act = QAction("恢复默认主题画布", self)
            clear_act.triggered.connect(self.clear_canvas_bg_image)
            menu.addAction(clear_act)
            
        menu.exec(QCursor.pos())

    def import_canvas_bg_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择画布背景图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            _, ext = os.path.splitext(file_path)
            dest_filename = f"canvas_bg_{self.current_plan_id}{ext}"
            dest_path = os.path.join(self.plans_dir, dest_filename)
            try:
                shutil.copy(file_path, dest_path)
                relative_path = os.path.join(self.plans_dir, dest_filename)
                
                self.root_node.canvas_bg_image = relative_path
                self.save_data()
                self.view.viewport().update()  
                QMessageBox.information(self, "成功", "专属画布背景应用成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"应用画布背景失败: {e}")

    def clear_canvas_bg_image(self):
        img_path = getattr(self.root_node, "canvas_bg_image", "")
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"删除专属物理背景图异常: {e}")
        self.root_node.canvas_bg_image = ""
        self.save_data()
        self.view.viewport().update()
        QMessageBox.information(self, "成功", "已恢复默认主题画布背景！")

    def show_help_dialog(self):
        dialog = HelpDialog(self)
        dialog.setStyleSheet(self.get_current_theme_class().qss)
        dialog.exec()

    def keyPressEvent(self, event):
        if self.inspector.inspect_name.hasFocus() or self.inspector.inspect_notes.hasFocus():
            super().keyPressEvent(event)
            return

        key = event.key()

        # 支持 Ctrl+Z 和 Ctrl+Y 键盘热键撤销/重做
        if event.modifiers() & Qt.ControlModifier:
            if key == Qt.Key_Z:
                self.undo()
                event.accept()
                return
            elif key == Qt.Key_Y:
                self.redo()
                event.accept()
                return

        if not self.selected_node_id:
            super().keyPressEvent(event)
            return

        # F2 改名
        if key == Qt.Key_F2:
            if self.check_protection_and_warn():
                event.accept()
                return
            if self.selected_node_id and self.inspector.isVisible() and self.inspector.inspect_form.isVisible():
                self.inspector.inspect_name.setFocus()
                self.inspector.inspect_name.selectAll()
                event.accept()
                return

        # 键盘热键执行修改
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
        # 验证防护状态
        if self.check_protection_and_warn():
            return

        if not self.selected_node_id:
            return
        node = self.all_nodes.get(self.selected_node_id)
        if not node:
            return

        if node.node_id == self.root_node.node_id:
            self.statusBar().showMessage("系统提示：根节点不允许变更为严格约束模式", 2000)
            return

        # 变更前推入撤销栈
        self.push_undo_state()

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
                QTimer.singleShot(50, lambda: self.center_on_node(target_id))

    def _get_logical_navigation_target(self, key):
        if not self.selected_node_id or not self.root_node:
            return None

        current_node = self.all_nodes.get(self.selected_node_id)
        if not current_node:
            return None

        layout_dir = self.current_layout_direction
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
        # 验证防护状态
        if self.check_protection_and_warn():
            return

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
            # 变更前推入撤销栈
            self.push_undo_state()
            siblings[idx], siblings[new_idx] = siblings[new_idx], siblings[idx]
            self.save_data()
            self.refresh_ui(force_select_id=self.selected_node_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KnowledgeTreeApp()
    window.show()
    sys.exit(app.exec())