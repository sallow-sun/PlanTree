# dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QDialogButtonBox, QColorDialog, QListWidget, QListWidgetItem, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(420, 560) 

        layout = QVBoxLayout(self)

        self.cb_confirm_delete = QCheckBox("删除节点二次确认")
        self.cb_confirm_delete.setChecked(config.get("confirm_delete", True))
        layout.addWidget(self.cb_confirm_delete)

        self.cb_auto_center = QCheckBox("画布自动居中")
        self.cb_auto_center.setChecked(config.get("auto_center_canvas", True))
        layout.addWidget(self.cb_auto_center)

        layout.addSpacing(10)

        layout.addWidget(QLabel("添加节点默认选中："))
        self.combo_add_mode = QComboBox()
        self.combo_add_mode.addItems(["新节点", "原节点"])
        self.combo_add_mode.setCurrentIndex(config.get("add_select_mode", 0))
        layout.addWidget(self.combo_add_mode)

        layout.addSpacing(10)

        layout.addWidget(QLabel("删除节点默认选中："))
        self.combo_delete_mode = QComboBox()
        self.combo_delete_mode.addItems([
            "不选中任何节点",
            "原节点",
            "同级相邻节点"
        ])
        self.combo_delete_mode.setCurrentIndex(config.get("delete_select_mode", 1))
        layout.addWidget(self.combo_delete_mode)

        layout.addSpacing(10)

        layout.addWidget(QLabel("键盘换点模式："))
        self.combo_nav_mode = QComboBox()
        self.combo_nav_mode.addItems(["物理跳转", "逻辑跳转"])
        self.combo_nav_mode.setCurrentIndex(config.get("nav_mode", 0))
        layout.addWidget(self.combo_nav_mode)

        layout.addSpacing(10)

        layout.addWidget(QLabel("详情面板位置："))
        self.combo_inspect_pos = QComboBox()
        self.combo_inspect_pos.addItems(["右侧", "底部"])
        self.combo_inspect_pos.setCurrentIndex(config.get("inspector_position", 0))
        layout.addWidget(self.combo_inspect_pos)

        layout.addSpacing(10)

        layout.addWidget(QLabel("详情面板显示："))
        self.combo_inspect_show = QComboBox()
        self.combo_inspect_show.addItems(["始终", "智能"])
        self.combo_inspect_show.setCurrentIndex(config.get("inspector_show_mode", 0))
        layout.addWidget(self.combo_inspect_show)

        layout.addSpacing(10)

        layout.addWidget(QLabel("知识树展开方向："))
        self.combo_layout_dir = QComboBox()
        self.combo_layout_dir.addItems(["水平", "垂直"])
        self.combo_layout_dir.setCurrentIndex(config.get("layout_direction", 0))
        layout.addWidget(self.combo_layout_dir)

        layout.addSpacing(10)

        # 新增子节点颜色继承策略设置
        layout.addWidget(QLabel("新建子节点颜色："))
        self.combo_color_policy = QComboBox()
        self.combo_color_policy.addItems(["使用默认颜色 (#2d3748)", "继承父节点颜色"])
        self.combo_color_policy.setCurrentIndex(config.get("new_node_color_policy", 0))
        layout.addWidget(self.combo_color_policy)

        layout.addSpacing(10)

        layout.addWidget(QLabel("视觉主题："))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems([
            "VS-Code风格", 
            "构成主义",
            "洛可可风格",
            "复古未来主义",
            "现代包豪斯"
        ])
        self.combo_theme.setCurrentIndex(config.get("theme", 0))
        layout.addWidget(self.combo_theme)

        layout.addSpacing(15)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self):
        return {
            "confirm_delete": self.cb_confirm_delete.isChecked(),
            "auto_center_canvas": self.cb_auto_center.isChecked(),
            "add_select_mode": self.combo_add_mode.currentIndex(),
            "delete_select_mode": self.combo_delete_mode.currentIndex(),
            "nav_mode": self.combo_nav_mode.currentIndex(),
            "inspector_position": self.combo_inspect_pos.currentIndex(),
            "inspector_show_mode": self.combo_inspect_show.currentIndex(),
            "layout_direction": self.combo_layout_dir.currentIndex(),
            "new_node_color_policy": self.combo_color_policy.currentIndex(), # 保存颜色继承偏好
            "theme": self.combo_theme.currentIndex() 
        }


class PrereqSelectDialog(QDialog):
    def __init__(self, current_node, all_nodes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"设置【{current_node.name}】的前置")
        self.resize(400, 350)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("请勾选该节点依赖的前置任务："))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        invalid_ids = set()
        self._collect_descendant_ids(current_node, invalid_ids)

        for node_id, node in all_nodes.items():
            if node_id in invalid_ids:
                continue

            item = QListWidgetItem(node.name)
            item.setData(Qt.UserRole, node_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            if node_id in current_node.prerequisites:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            self.list_widget.addItem(item)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _collect_descendant_ids(self, node, ids_set):
        ids_set.add(node.node_id)
        for child in node.children:
            self._collect_descendant_ids(child, ids_set)

    def get_selected_prereqs(self):
        selected_ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_ids.append(item.data(Qt.UserRole))
        return selected_ids


from PySide6.QtWidgets import QSpinBox, QDateEdit
from PySide6.QtCore import QDate

class CheckInDialog(QDialog):
    def __init__(self, node_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"打卡 - {node_name}")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("日期："))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        layout.addWidget(self.date_edit)

        layout.addWidget(QLabel("用时（分钟）："))
        self.spin_minutes = QSpinBox()
        self.spin_minutes.setRange(1, 1440)
        self.spin_minutes.setValue(30)
        layout.addWidget(self.spin_minutes)

        layout.addWidget(QLabel("备注："))
        self.edit_note = QLineEdit()
        self.edit_note.setPlaceholderText("")
        layout.addWidget(self.edit_note)

        layout.addSpacing(15)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_log_data(self):
        return {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "minutes": self.spin_minutes.value(),
            "note": self.edit_note.text().strip()
        }