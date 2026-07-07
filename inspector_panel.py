# inspector_panel.py
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QSlider, QColorDialog, QMessageBox, QComboBox, QDialog, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

class InspectorLineEdit(QLineEdit):
    """自定义文本单行框：Esc/Enter 键能释放焦点并将控制交还给画布"""
    def __init__(self, inspector, parent=None):
        super().__init__(parent)
        self.inspector = inspector

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            self.clearFocus()
            if self.inspector and self.inspector.main_app and self.inspector.main_app.view:
                self.inspector.main_app.view.setFocus()
            event.accept()
        else:
            super().keyPressEvent(event)

class InspectorTextEdit(QTextEdit):
    """自定义大文本框：Esc 键可释放焦点并将控制交还给画布"""
    def __init__(self, inspector, parent=None):
        super().__init__(parent)
        self.inspector = inspector

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clearFocus()
            if self.inspector and self.inspector.main_app and self.inspector.main_app.view:
                self.inspector.main_app.view.setFocus()
            event.accept()
        else:
            super().keyPressEvent(event)


class InspectorPanel(QWidget):
    """详情面板类，独立接管所有属性配置"""
    def __init__(self, main_app, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.setObjectName("inspectorPanel")
        self._build_ui()

    def _build_ui(self):
        self.inspector_main_layout = QVBoxLayout(self)
        self.inspector_main_layout.setContentsMargins(15, 15, 15, 15)
        self.inspector_main_layout.setSpacing(10)

        self.inspect_title = QLabel("节点详情配置")
        self.inspect_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #007acc;")
        self.inspector_main_layout.addWidget(self.inspect_title)

        self.inspect_placeholder = QLabel("请在画布中选择任意节点\n以查看和修改其详细信息。")
        self.inspect_placeholder.setStyleSheet("color: #7f8c8d; line-height: 18px;")
        self.inspect_placeholder.setAlignment(Qt.AlignCenter)
        self.inspector_main_layout.addWidget(self.inspect_placeholder)

        self.inspect_form = QWidget()
        
        # 1. 基础信息
        self.lbl_name_tag = QLabel("节点名称：")
        self.inspect_name = InspectorLineEdit(self)
        self.inspect_name.editingFinished.connect(self.save_inspector_changes)

        # 2. 节点模式
        self.lbl_type_tag = QLabel("管理模式：")
        self.combo_node_type = QComboBox()
        self.combo_node_type.addItems(["自由", "严格"])
        self.combo_node_type.currentIndexChanged.connect(self.on_node_type_changed)

        # 前置解锁依赖展示标签
        self.lbl_prereq_status = QLabel("解锁前置：无")
        self.lbl_prereq_status.setWordWrap(True)
        self.lbl_prereq_status.setStyleSheet("color: #d35400; font-size: 11px; font-weight: bold; background-color: rgba(211, 84, 0, 0.1); padding: 4px; border-radius: 4px;")

        # 3. 学习打卡与明细列表
        self.lbl_study_summary = QLabel("学习统计：暂无记录")
        self.btn_check_in = QPushButton("添加")
        self.btn_check_in.clicked.connect(self.open_check_in_dialog)
        
        self.lbl_history_tag = QLabel("历史记录 (双击移除)：")
        self.inspect_log_history = QListWidget()
        self.inspect_log_history.setMaximumHeight(95)
        self.inspect_log_history.itemDoubleClicked.connect(self.delete_selected_log)

        # 4. 进度滑杆
        self.inspect_prog_label = QLabel("学习进度：0%")
        self.inspect_prog_label.setMinimumWidth(160)
        self.inspect_slider = QSlider(Qt.Horizontal)
        self.inspect_slider.setRange(0, 100)
        self.inspect_slider.setSingleStep(5)
        self.inspect_slider.setPageStep(10)
        self.inspect_slider.valueChanged.connect(self.on_slider_value_changed)
        self.inspect_slider.sliderReleased.connect(self.on_slider_released)

        # 5. 配色
        self.lbl_color_tag = QLabel("卡片颜色：")
        self.color_buttons = []
        preset_colors = ["#2d3748", "#1b4d3e", "#5c3e16", "#511c1c", "#4a235a"]
        for hex_color in preset_colors:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #555555; border-radius: 11px;")
            btn.clicked.connect(lambda checked=False, col=hex_color: self.apply_preset_color(col))
            self.color_buttons.append(btn)

        self.btn_inspect_color = QPushButton("更多")
        self.btn_inspect_color.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.btn_inspect_color.clicked.connect(self.select_inspector_color)

        # 6. 备注
        self.lbl_notes_tag = QLabel("备注：")
        self.inspect_notes = InspectorTextEdit(self)
        self.inspect_notes.setPlaceholderText("点击此处输入...")
        self.inspect_notes.focusOutEvent = self.on_notes_focus_out

        self.inspector_main_layout.addWidget(self.inspect_form)
        self.inspect_form.setVisible(False)

    def _clear_layout_completely(self, layout):
        if not layout:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(self.inspect_form)
            elif item.layout():
                self._clear_layout_completely(item.layout())

    def setup_layout_by_mode(self, mode):
        """标准双形态自适应布局排版控制"""
        self._clear_layout_completely(self.inspect_form.layout())
        if self.inspect_form.layout():
            QWidget().setLayout(self.inspect_form.layout())

        color_layout = QHBoxLayout()
        color_layout.setSpacing(6)
        for btn in self.color_buttons:
            color_layout.addWidget(btn)
        color_layout.addWidget(self.btn_inspect_color)

        if mode == 0:
            form_layout = QVBoxLayout(self.inspect_form)
            form_layout.setContentsMargins(0, 0, 0, 0)
            form_layout.setSpacing(8)

            form_layout.addWidget(self.lbl_name_tag)
            form_layout.addWidget(self.inspect_name)
            
            form_layout.addWidget(self.lbl_type_tag)
            form_layout.addWidget(self.combo_node_type)
            
            form_layout.addWidget(self.lbl_prereq_status)

            form_layout.addWidget(self.inspect_prog_label)
            form_layout.addWidget(self.inspect_slider) 

            form_layout.addWidget(self.lbl_study_summary)
            form_layout.addWidget(self.btn_check_in)
            
            form_layout.addWidget(self.lbl_history_tag)
            form_layout.addWidget(self.inspect_log_history)
            
            form_layout.addWidget(self.lbl_color_tag)
            form_layout.addLayout(color_layout)
            
            form_layout.addWidget(self.lbl_notes_tag)
            form_layout.addWidget(self.inspect_notes)
            
            form_layout.addStretch()  
        else:
            form_layout = QHBoxLayout(self.inspect_form)
            form_layout.setContentsMargins(0, 0, 0, 0)
            form_layout.setSpacing(25)

            col1 = QVBoxLayout()
            col1.setSpacing(6)
            col1.addWidget(self.lbl_name_tag)
            col1.addWidget(self.inspect_name)
            col1.addWidget(self.lbl_type_tag)
            col1.addWidget(self.combo_node_type)
            col1.addWidget(self.lbl_prereq_status)
            form_layout.addLayout(col1)

            col2 = QVBoxLayout()
            col2.setSpacing(6)
            col2.addWidget(self.inspect_prog_label)
            col2.addWidget(self.inspect_slider) 
            col2.addWidget(self.lbl_study_summary)
            col2.addWidget(self.btn_check_in)
            col2.addWidget(self.lbl_history_tag)
            col2.addWidget(self.inspect_log_history)
            form_layout.addLayout(col2)

            col3 = QVBoxLayout()
            col3.setSpacing(6)
            col3.addWidget(self.lbl_color_tag)
            col3.addLayout(color_layout)
            col3.addWidget(self.lbl_notes_tag)
            col3.addWidget(self.inspect_notes)
            form_layout.addLayout(col3, stretch=1)

    def update_data(self, node):
        current_theme = self.main_app.get_current_theme_class()
        
        if node is None:
            show_mode = self.main_app.user_config.get("inspector_show_mode", 0)
            if show_mode == 1:
                self.setVisible(False)
            else:
                self.setVisible(True)
                self.inspect_form.setVisible(False)
                self.inspect_placeholder.setVisible(True)
                self.inspect_placeholder.setText(current_theme.inspector_placeholder) 
                self.inspect_title.setText(current_theme.inspector_title)
        else:
            self.setVisible(True)
            self.inspect_placeholder.setVisible(False)
            self.inspect_form.setVisible(True)
            self.inspect_title.setText(f"节点详情: {node.name}")

            # 获取防护状态
            is_protected = getattr(self.main_app.root_node, "is_protected", False) if self.main_app.root_node else False

            self.inspect_name.blockSignals(True)
            self.inspect_name.setText(node.name)
            self.inspect_name.setEnabled(not is_protected) # 防护时禁用重命名编辑框
            self.inspect_name.blockSignals(False)

            self.inspect_notes.setText(node.notes)
            
            self.combo_node_type.blockSignals(True)
            ntype = getattr(node, "node_type", "standard")
            self.combo_node_type.setCurrentIndex(1 if ntype == "strict" else 0)
            self.combo_node_type.setEnabled(not is_protected) # 防护时禁用模式切换框
            self.combo_node_type.blockSignals(False)

            prereq_texts = []
            for prereq_id in node.prerequisites:
                prereq_node = self.main_app.all_nodes.get(prereq_id)
                if prereq_node:
                    status_str = "✓ 已完成" if prereq_node.progress >= 100 else f"未完成 ({prereq_node.progress}%)"
                    prereq_texts.append(f"【{prereq_node.name}】 ({status_str})")

            if not prereq_texts and ntype == "strict":
                parent_node, _ = self.main_app._find_parent_and_siblings(self.main_app.root_node, node.node_id)
                if parent_node and parent_node.node_id != self.main_app.root_node.node_id:
                    status_str = "✓ 已完成" if parent_node.progress >= 100 else f"未完成 ({parent_node.progress}%)"
                    prereq_texts.append(f"父级【{parent_node.name}】 ({status_str})")

            if prereq_texts:
                self.lbl_prereq_status.setVisible(True)
                self.lbl_prereq_status.setText("解锁前置要求：\n" + "\n".join(prereq_texts))
            else:
                self.lbl_prereq_status.setVisible(False)

            logs = getattr(node, "study_logs", [])
            total_minutes = sum(log.get("minutes", 0) for log in logs)
            total_hours = round(total_minutes / 60.0, 1)
            
            unique_days = len(set(log.get("date") for log in logs if log.get("date")))
            count = len(logs)
            
            if count > 0:
                self.lbl_study_summary.setText(
                    f"累计: {total_hours} 小时 ({total_minutes}分) | 打卡: {unique_days} 天 ({count}次)"
                )
                
                self.inspect_log_history.clear()
                for idx, log in enumerate(reversed(logs), 1):
                    note_part = f" | {log['note']}" if log.get("note") else ""
                    item_text = f"#{count - idx + 1} {log['date']} | {log['minutes']}分{note_part}"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, count - idx)
                    self.inspect_log_history.addItem(item)
            else:
                self.lbl_study_summary.setText("学习统计：暂无")
                self.inspect_log_history.clear()

            self.inspect_slider.blockSignals(True)
            self.inspect_slider.setValue(node.progress)
            self.inspect_slider.blockSignals(False)

            is_locked = self.main_app.is_locked(node)
            if is_locked:
                self.inspect_prog_label.setText("学习进度：[已锁定] 前置依赖未完成")
                self.inspect_slider.setEnabled(False)
                self.btn_check_in.setEnabled(False)  
            else:
                self.inspect_prog_label.setText(f"学习进度：{node.progress}%")
                self.inspect_slider.setEnabled(True)
                self.btn_check_in.setEnabled(True)   

            self.btn_inspect_color.setStyleSheet(f"background-color: {node.color}; color: #ffffff;")

    def on_slider_value_changed(self, value):
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return
        self.inspect_prog_label.setText(f"学习进度：{value}%")

    def on_slider_released(self):
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return

        new_value = self.inspect_slider.value()
        old_value = node.progress

        if new_value == old_value:
            return

        threshold = 100
        crossed_down = (old_value >= threshold and new_value < threshold)

        if old_value == 100 and new_value < 100:
            reply = QMessageBox.question(
                self, 
                "确认降低进度", 
                "该节点已完成。降低进度会导致依赖它的所有后续节点重新被锁定并清空进度！\n确定要降低吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.main_app.push_undo_state()  # 状态变更前入栈备份
                node.progress = new_value
                self.main_app.relock_dependent_nodes(self.main_app.selected_node_id)
            else:
                self.inspect_slider.blockSignals(True)
                self.inspect_slider.setValue(100)
                self.inspect_slider.blockSignals(False)
                self.inspect_prog_label.setText("学习进度：100%")
                return
        else:
            self.main_app.push_undo_state()  # 状态变更前入栈备份
            node.progress = new_value
            if crossed_down:
                self.main_app.relock_dependent_nodes(self.main_app.selected_node_id)

        self.main_app.save_data()
        self.main_app.refresh_ui(force_select_id=self.main_app.selected_node_id)

    def on_node_type_changed(self, index):
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return

        target_type = "strict" if index == 1 else "standard"
        if getattr(node, "node_type", "standard") == target_type:
            return

        self.main_app.push_undo_state()  # 状态变更前入栈备份
        node.node_type = target_type
        self.main_app.save_data()
        self.main_app.refresh_ui(force_select_id=self.main_app.selected_node_id)

    def open_check_in_dialog(self):
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return

        if self.main_app.is_locked(node):
            QMessageBox.warning(self, "限制", "当前节点尚未解锁。")
            return

        from dialogs import CheckInDialog
        dialog = CheckInDialog(node.name, self)
        dialog.setStyleSheet(self.main_app.get_current_theme_class().qss)
        if dialog.exec() == QDialog.Accepted:
            self.main_app.push_undo_state()  # 状态变更前入栈备份
            log_data = dialog.get_log_data()
            if not hasattr(node, "study_logs") or node.study_logs is None:
                node.study_logs = []
            node.study_logs.append(log_data)
            
            self.main_app.save_data()
            self.update_data(node)
            QMessageBox.information(self, "打卡成功", f"成功登记：{log_data['minutes']} 分钟！")

    def delete_selected_log(self, item):
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return

        log_index = item.data(Qt.UserRole)
        logs = getattr(node, "study_logs", [])
        
        if log_index is None or log_index < 0 or log_index >= len(logs):
            return

        target_log = logs[log_index]
        reply = QMessageBox.question(
            self, 
            "确认删除打卡记录", 
            f"确定要删除此条打卡记录吗？\n\n"
            f"日期: {target_log.get('date')}\n"
            f"用时: {target_log.get('minutes')} 分钟\n"
            f"备注: {target_log.get('note') or '无'}\n\n"
            f"此操作不可逆。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.main_app.push_undo_state()  # 状态变更前入栈备份
            logs.pop(log_index)
            node.study_logs = logs
            self.main_app.save_data()
            self.update_data(node)
            QMessageBox.information(self, "删除成功", "该记录已成功移除。")

    def save_inspector_changes(self):
        # 验证防护状态：防护状态下不进行任何改名回调
        if self.main_app.root_node and getattr(self.main_app.root_node, "is_protected", False):
            return
            
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return

        new_name = self.inspect_name.text().strip()
        if new_name and new_name != node.name:
            self.main_app.push_undo_state()  # 状态变更前入栈备份
            node.name = new_name
            self.main_app.save_data()
            self.main_app.refresh_ui(force_select_id=self.main_app.selected_node_id)

    def on_notes_focus_out(self, event):
        QTextEdit.focusOutEvent(self.inspect_notes, event)
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return

        new_notes = self.inspect_notes.toPlainText().strip()
        if new_notes != node.notes:
            self.main_app.push_undo_state()  # 状态变更前入栈备份
            node.notes = new_notes
            self.main_app.save_data()
            # 修正 self.refresh_ui 逻辑问题为 self.main_app.refresh_ui
            self.main_app.refresh_ui(force_select_id=self.main_app.selected_node_id)

    def apply_preset_color(self, hex_color):
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return
        if node.color == hex_color: return
        
        self.main_app.push_undo_state()  # 状态变更前入栈备份
        node.color = hex_color
        self.main_app.save_data()
        self.main_app.refresh_ui(force_select_id=self.main_app.selected_node_id)

    def select_inspector_color(self):
        if not self.main_app.selected_node_id: return
        node = self.main_app.all_nodes.get(self.main_app.selected_node_id)
        if not node: return

        color = QColorDialog.getColor(QColor(node.color), self, "选择卡片颜色")
        if color.isValid():
            self.main_app.push_undo_state()  # 状态变更前入栈备份
            node.color = color.name()
            self.main_app.save_data()
            self.main_app.refresh_ui(force_select_id=self.main_app.selected_node_id)