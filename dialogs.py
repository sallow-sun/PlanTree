# dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QDialogButtonBox, QColorDialog, QListWidget, QListWidgetItem, QCheckBox, QComboBox,
    QFrame, QHBoxLayout, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, QSize  # 引入 QSize 确保布局尺寸精准
import os

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


# dialogs.py 底部 HelpDialog 类的餐馆清单样式更新

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键帮助")
        self.setFixedSize(380, 420)  # 固定大小确保清单排版不变形

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        help_text = QTextEdit(self)
        help_text.setReadOnly(True)
        help_text.setFrameShape(QFrame.NoFrame)
        
        # 饭店菜单/极简对齐清单式布局
        help_html = """
        <div style="font-family: 'Microsoft YaHei', sans-serif; line-height: 24px;">
            <p align="center" style="font-size: 14px; font-weight: bold; margin-bottom: 15px;">
                快捷操作清单 / KEYBOARD SHORTCUTS
            </p>
            
            <p style="font-weight: bold; margin-bottom: 5px;">一、 节点编辑</p>
            <table width="100%" cellspacing="0" cellpadding="2">
                <tr><td>F2 键</td><td>············································</td><td align="right">重命名节点</td></tr>
                <tr><td>Enter 键</td><td>············································</td><td align="right">新增子节点</td></tr>
                <tr><td>Delete 键</td><td>············································</td><td align="right">删除整条分支</td></tr>
                <tr><td>M 键</td><td>············································</td><td align="right">切换模式</td></tr>
            </table>
            
            <br/>
            <p style="font-weight: bold; margin-bottom: 5px;">二、 视图控制</p>
            <table width="100%" cellspacing="0" cellpadding="2">
                <tr><td>方向键 / WASD</td><td>············································</td><td align="right">选择节点</td></tr>
                <tr><td>Esc 键</td><td>············································</td><td align="right">释放文本焦点</td></tr>
                <tr><td>鼠标滚轮</td><td>············································</td><td align="right">缩放画布</td></tr>
                <tr><td>右键拖拽</td><td>············································</td><td align="right">平移视野</td></tr>
            </table>
        </div>
        """
        help_text.setHtml(help_html)
        layout.addWidget(help_text)

        btn_close = QPushButton("关闭", self)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class RecycleBinDialog(QDialog):
    """回收站管理对话框，支持数据恢复与物理文件彻底删除"""
    def __init__(self, manifest, parent=None):
        super().__init__(parent)
        self.setWindowTitle("回收站")
        self.resize(540, 420)  # 提供合理的视口空间
        self.manifest = manifest

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.lbl_info = QLabel("已删除的导图列表（可在下方直接还原或彻底销毁）：")
        layout.addWidget(self.lbl_info)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # 1. 先初始化底部控件，确保 btn_empty 被正确创建
        bottom_layout = QHBoxLayout()
        self.btn_empty = QPushButton("清空回收站")
        self.btn_empty.setObjectName("dangerButton")
        self.btn_empty.clicked.connect(self.empty_bin)
        bottom_layout.addWidget(self.btn_empty)

        bottom_layout.addStretch()

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(self.btn_close)

        layout.addLayout(bottom_layout)

        # 2. 控件创建完毕后再进行列表加载与按钮状态更新
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        bin_list = self.manifest.get("recycle_bin", [])
        
        if not bin_list:
            item = QListWidgetItem("回收站空空如也")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            self.btn_empty.setEnabled(False)
            return

        self.btn_empty.setEnabled(True)
        for plan in bin_list:
            item = QListWidgetItem()
            self.list_widget.addItem(item)

            row_widget = QWidget()
            row_widget.setFixedHeight(40)  # 使用固定行高保证内容区域不缩水

            row_layout = QHBoxLayout(row_widget)
            # 核心调整：通过顶部 1px、底部 5px 的非对称边距，把按钮和文字往上提拉 2 像素，抵消视觉偏差
            row_layout.setContentsMargins(12, 0, 12, 7)  
            row_layout.setSpacing(10)

            deleted_time = plan.get("deleted_at", "未知时间")
            info_text = f"【{plan['name']}】  (删除于: {deleted_time})"
            lbl_name = QLabel(info_text)
            lbl_name.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")
            
            # 对文本进行显式垂直居中
            row_layout.addWidget(lbl_name, alignment=Qt.AlignVCenter)
            row_layout.addStretch()

            btn_restore = QPushButton("还原")
            btn_restore.setFixedSize(60, 24)
            btn_restore.setStyleSheet("font-size: 11px; padding: 0px; margin: 0px;")
            btn_restore.clicked.connect(lambda checked=False, p=plan: self.restore_plan(p))
            # 对“还原”按钮进行显式垂直居中
            row_layout.addWidget(btn_restore, alignment=Qt.AlignVCenter)

            btn_pure_del = QPushButton("彻底删除")
            btn_pure_del.setObjectName("dangerButton")
            btn_pure_del.setFixedSize(80, 24)
            btn_pure_del.setStyleSheet("font-size: 11px; padding: 0px; margin: 0px;")
            btn_pure_del.clicked.connect(lambda checked=False, p=plan: self.purge_plan(p))
            # 对“彻底删除”按钮进行显式垂直居中
            row_layout.addWidget(btn_pure_del, alignment=Qt.AlignVCenter)

            # 显式强制 QListWidgetItem 的尺寸，防止容器大小与实际渲染产生偏差
            item.setSizeHint(QSize(100, 42))
            self.list_widget.setItemWidget(item, row_widget)
            
    def restore_plan(self, plan):
        if plan in self.manifest.get("recycle_bin", []):
            self.manifest["recycle_bin"].remove(plan)
            plan.pop("deleted_at", None)
            self.manifest["plans"].append(plan)
            self.refresh_list()

    def purge_plan(self, plan):
        reply = QMessageBox.question(
            self, "确认彻底删除", f"此操作将永久抹除导图【{plan['name']}】，物理数据文件将被直接销毁。是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if plan in self.manifest.get("recycle_bin", []):
                self.manifest["recycle_bin"].remove(plan)
                self._physical_delete(plan)
                self.refresh_list()

    def empty_bin(self):
        reply = QMessageBox.question(
            self, "确认清空回收站", "确定要永久清除回收站中的所有路线图吗？此物理删除操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            bin_list = list(self.manifest.get("recycle_bin", []))
            for plan in bin_list:
                self._physical_delete(plan)
            self.manifest["recycle_bin"] = []
            self.refresh_list()

    def _physical_delete(self, plan):
        """执行彻底的物理删除"""
        try:
            if os.path.exists(plan["file_path"]):
                os.remove(plan["file_path"])
            if "cover_image" in plan:
                img_p = plan["cover_image"]
                if os.path.exists(img_p):
                    os.remove(img_p)
        except Exception as e:
            print(f"清空回收站物理文件异常: {e}")