# library_view.py
import datetime
import uuid
import os
import json 
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QGridLayout, QFrame, QInputDialog, QMessageBox, QMenu, QDialog, QLineEdit, QComboBox, QFileDialog, QColorDialog
)
from PySide6.QtGui import QColor, QFont, QCursor, QAction
from PySide6.QtCore import Qt, QSize, Signal

class PlanCardWidget(QFrame):
    """书页立体风格卡片部件 (支持本地封面背景图与隐式只读防护)"""
    clicked = Signal(str, str)
    delete_requested = Signal(str)
    rename_requested = Signal(str, str)  
    change_cover_color_requested = Signal(str, str)
    change_cover_image_requested = Signal(str)
    clear_cover_image_requested = Signal(str)
    toggle_protection_requested = Signal(str)  # 切换防护信号

    def __init__(self, plan_data, is_theme_dark, parent=None):
        super().__init__(parent)
        self.plan_id = plan_data["id"]
        self.file_path = plan_data["file_path"]
        self.plan_name = plan_data["name"]
        self.cover_color = plan_data.get("cover_color", "#2d3748")
        self.cover_image = plan_data.get("cover_image", "") 
        self.progress = plan_data.get("progress", 0)
        self.total_hours = plan_data.get("total_hours", 0.0)
        self.last_active = plan_data.get("last_active", "2023-10-01")
        self.is_protected_plan = plan_data.get("is_protected", False)  # 仅在后台维护防护状态，不在卡片表面展示
        self.is_theme_dark = is_theme_dark

        self.setFixedSize(190, 260)
        self.setObjectName("PlanCard")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. 精装书封面区
        self.cover_widget = QFrame()
        self.cover_widget.setObjectName("coverWidget")
        self.cover_widget.setFixedHeight(160)
        
        # 支持背景图
        if self.cover_image and os.path.exists(self.cover_image):
            clean_path = self.cover_image.replace("\\", "/")
            cover_style = f"""
                QFrame#coverWidget {{
                    border-image: url("{clean_path}") 0 0 0 0 stretch stretch;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    border-bottom: 2px solid rgba(0,0,0,0.2);
                    border-left: none; border-right: none; border-top: none;
                }}
            """
        else:
            cover_style = f"""
                QFrame#coverWidget {{
                    background-color: {self.cover_color};
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    border-bottom: 2px solid rgba(0,0,0,0.2);
                    border-left: none; border-right: none; border-top: none;
                }}
            """
        self.cover_widget.setStyleSheet(cover_style)
        
        cover_layout = QVBoxLayout(self.cover_widget)
        cover_layout.setContentsMargins(15, 15, 15, 15)
        
        # 书名区 (保持绝对的极简纯净外观，无额外标签干扰)
        self.lbl_cover_title = QLabel(self.plan_name, self.cover_widget)
        self.lbl_cover_title.setObjectName("coverTitle")
        self.lbl_cover_title.setWordWrap(True)
        self.lbl_cover_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # 若带有背景图片，添加柔和半透明黑色文字底阴影
        if self.cover_image and os.path.exists(self.cover_image):
            text_shadow_css = "background-color: rgba(0,0,0,0.35); border-radius: 4px; padding: 2px;"
        else:
            text_shadow_css = "background: transparent;"
            
        self.lbl_cover_title.setStyleSheet(f"""
            QLabel#coverTitle {{
                color: #ffffff; 
                font-family: 'Georgia', 'Microsoft YaHei'; 
                font-size: 14px; 
                font-weight: bold; 
                line-height: 18px;
                border: none;
                {text_shadow_css}
            }}
        """)
        cover_layout.addWidget(self.lbl_cover_title)
        
        # 底部栏布局
        badge_layout = QHBoxLayout()
        self.lbl_badge = QLabel("进度")
        self.lbl_badge.setObjectName("badgeStamp")
        self.lbl_badge.setStyleSheet("""
            QLabel#badgeStamp {
                color: rgba(255,255,255,0.7);
                font-size: 9px;
                font-weight: bold;
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 3px;
                padding: 1px 4px;
                background: rgba(0,0,0,0.2);
            }
        """)
        badge_layout.addWidget(self.lbl_badge)
        badge_layout.addStretch()
        
        self.btn_menu = QPushButton("•••")
        self.btn_menu.setObjectName("cardMenuBtn")
        self.btn_menu.setFixedSize(24, 18)
        self.btn_menu.setStyleSheet("""
            QPushButton#cardMenuBtn {
                background: rgba(0, 0, 0, 0.45);
                color: #ffffff;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 8px;
            }
            QPushButton#cardMenuBtn:hover { background: rgba(0, 0, 0, 0.7); }
        """)
        self.btn_menu.clicked.connect(self.show_context_menu)
        badge_layout.addWidget(self.btn_menu)
        cover_layout.addLayout(badge_layout)
        layout.addWidget(self.cover_widget)

        # 2. 底部信息反馈区
        self.info_widget = QFrame()
        self.info_widget.setObjectName("infoWidget")
        
        bg_color = "#1e1e1e" if self.is_theme_dark else "#f9f9f9"
        border_col = "#2d2d2d" if self.is_theme_dark else "#e5e5e5"
        self.info_widget.setStyleSheet(f"""
            QFrame#infoWidget {{
                background-color: {bg_color};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                border-top: 1px solid {border_col};
                border-left: none; border-right: none; border-bottom: none;
            }}
        """)
        info_layout = QVBoxLayout(self.info_widget)
        info_layout.setContentsMargins(12, 10, 12, 12)
        info_layout.setSpacing(5)

        self.lbl_title = QLabel(self.plan_name, self.info_widget)
        self.lbl_title.setObjectName("cardTitle")
        title_color = "#e0e0e0" if self.is_theme_dark else "#111111"
        self.lbl_title.setStyleSheet(f"""
            QLabel#cardTitle {{
                color: {title_color}; 
                font-weight: bold; 
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        info_layout.addWidget(self.lbl_title)

        self.lbl_stats = QLabel(f"累计学时: {self.total_hours}h  •  {self.last_active}", self.info_widget)
        self.lbl_stats.setObjectName("cardStats")
        stats_color = "#888888" if self.is_theme_dark else "#666666"
        self.lbl_stats.setStyleSheet(f"""
            QLabel#cardStats {{
                color: {stats_color}; 
                font-size: 10px;
                background: transparent;
                border: none;
            }}
        """)
        info_layout.addWidget(self.lbl_stats)

        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(6)
        
        self.bar_bg = QFrame(self.info_widget)
        self.bar_bg.setObjectName("barBg")
        self.bar_bg.setFixedHeight(4)
        self.bar_bg.setFixedWidth(125) 
        bar_bg_color = "#333333" if self.is_theme_dark else "#e5e5e5"
        self.bar_bg.setStyleSheet(f"QFrame#barBg {{ background-color: {bar_bg_color}; border-radius: 2px; border: none; }}")
        
        self.bar_fill = QFrame(self.bar_bg)
        self.bar_fill.setObjectName("barFill")
        self.bar_fill.setFixedHeight(4)
        fill_width = int(125 * (self.progress / 100.0))
        self.bar_fill.setFixedWidth(fill_width)
        fill_color = "#007acc" if self.is_theme_dark else "#002FA7"
        self.bar_fill.setStyleSheet(f"QFrame#barFill {{ background-color: {fill_color}; border-radius: 2px; border: none; }}")
        
        self.lbl_percent = QLabel(f"{self.progress}%", self.info_widget)
        self.lbl_percent.setObjectName("cardPercent")
        self.lbl_percent.setStyleSheet(f"QLabel#cardPercent {{ color: {fill_color}; font-size: 10px; font-weight: bold; border: none; background: transparent; }}")
        
        progress_layout.addWidget(self.bar_bg)
        progress_layout.addWidget(self.lbl_percent)
        info_layout.addLayout(progress_layout)

        layout.addWidget(self.info_widget)

        card_border = "#333333" if self.is_theme_dark else "#dcdcdc"
        self.setStyleSheet(f"""
            QFrame#PlanCard {{
                border: 1px solid {card_border};
                border-radius: 8px;
            }}
        """)

    def enterEvent(self, event):
        highlight = "#007acc" if self.is_theme_dark else "#002FA7"
        self.setStyleSheet(f"QFrame#PlanCard {{ border: 1.5px solid {highlight}; border-radius: 8px; }}")
        self.setCursor(Qt.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        card_border = "#333333" if self.is_theme_dark else "#dcdcdc"
        self.setStyleSheet(f"QFrame#PlanCard {{ border: 1px solid {card_border}; border-radius: 8px; }}")
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.childAt(event.pos()) != self.btn_menu:
                self.clicked.emit(self.plan_id, self.file_path)
        super().mousePressEvent(event)

    def show_context_menu(self):
        """弹出排版美化后的上下文菜单 (只读模式完全隐式化)"""
        menu = QMenu(self)
        
        # 现代扁平化菜单设计
        menu.setStyleSheet("""
            QMenu { 
                background-color: #1e1e1e; 
                color: #d4d4d4; 
                border: 1px solid #3c3c3c; 
                border-radius: 6px; 
                padding: 6px 0px;
            }
            QMenu::item { 
                padding: 6px 26px 6px 22px; 
                margin: 2px 5px;
                border-radius: 4px;
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 12px;
            }
            QMenu::item:selected { 
                background-color: #007acc; 
                color: #ffffff; 
            }
            QMenu::item:disabled {
                color: #5a5a5a;
            }
            QMenu::separator {
                height: 1px;
                background-color: #2e2e2e;
                margin: 6px 10px;
            }
        """)

        # 保护切换项
        protect_label = "切换至普通模式" if self.is_protected_plan else "切换至保护模式"
        protect_act = QAction(protect_label, self)
        protect_act.triggered.connect(lambda: self.toggle_protection_requested.emit(self.plan_id))
        menu.addAction(protect_act)

        menu.addSeparator()

        # 卡片常规修改功能
        rename_act = QAction("重命名路线", self)
        rename_act.triggered.connect(lambda: self.rename_requested.emit(self.plan_id, self.plan_name))
        menu.addAction(rename_act)

        color_act = QAction("修改封面颜色", self)
        color_act.triggered.connect(lambda: self.change_cover_color_requested.emit(self.plan_id, self.cover_color))
        menu.addAction(color_act)

        image_act = QAction("上传封面图片", self)
        image_act.triggered.connect(lambda: self.change_cover_image_requested.emit(self.plan_id))
        menu.addAction(image_act)

        clear_image_act = None
        if self.cover_image:
            clear_image_act = QAction("清除封面图片", self)
            clear_image_act.triggered.connect(lambda: self.clear_cover_image_requested.emit(self.plan_id))
            menu.addAction(clear_image_act)

        menu.addSeparator()

        del_action = QAction("删除此路线", self)
        del_action.triggered.connect(lambda: self.delete_requested.emit(self.plan_id))
        menu.addAction(del_action)

        # 处于保护状态下时，只读屏蔽相关的修改操作
        if self.is_protected_plan:
            rename_act.setEnabled(False)
            color_act.setEnabled(False)
            image_act.setEnabled(False)
            if clear_image_act:
                clear_image_act.setEnabled(False)
            del_action.setEnabled(False)

        menu.exec(QCursor.pos())


class AddCardWidget(QFrame):
    """新建计划占位虚线卡片"""
    clicked = Signal()

    def __init__(self, is_theme_dark, parent=None):
        super().__init__(parent)
        self.setFixedSize(190, 260)
        self.setObjectName("AddCard")
        
        border_col = "#454545" if is_theme_dark else "#cccccc"
        bg_col = "#1a1a1a" if is_theme_dark else "#fcfcfc"
        hover_bg = "#222222" if is_theme_dark else "#f3f3f3"
        hover_border = "#007acc" if is_theme_dark else "#002FA7"
        
        self.setStyleSheet(f"""
            QFrame#AddCard {{
                border: 2px dashed {border_col};
                border-radius: 8px;
                background-color: {bg_col};
            }}
            QFrame#AddCard:hover {{
                border: 2px dashed {hover_border};
                background-color: {hover_bg};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_plus = QLabel("＋", self)
        self.lbl_plus.setObjectName("addPlus")
        self.lbl_plus.setStyleSheet("QLabel#addPlus { color: #555555; font-size: 40px; font-weight: bold; border: none; background: transparent; }")
        self.lbl_plus.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_plus)

        self.lbl_text = QLabel("新建/导入", self)
        self.lbl_text.setObjectName("addText")
        self.lbl_text.setStyleSheet("QLabel#addText { color: #7f8c8d; font-size: 11px; font-weight: bold; border: none; background: transparent; }")
        self.lbl_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class LibraryView(QWidget):
    """主书架视图大厅"""
    plan_selected = Signal(str, str)

    def __init__(self, main_app, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.setObjectName("libraryView")
        self.is_dark_bg = True 
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(35, 30, 35, 30)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        
        self.lbl_main_title = QLabel("我的书架", self)
        self.lbl_main_title.setObjectName("mainTitle")
        
        self.lbl_sub_title = QLabel("", self)
        self.lbl_sub_title.setObjectName("subTitle")
        
        title_container.addWidget(self.lbl_main_title)
        title_container.addWidget(self.lbl_sub_title)
        header_layout.addLayout(title_container)
        header_layout.addStretch()

        self.btn_recycle_bin = QPushButton("回收站", self)
        self.btn_recycle_bin.setObjectName("btnRecycleBin")
        self.btn_new_plan = QPushButton("新建", self)
        self.btn_import_code = QPushButton("导入", self)
        self.btn_lib_settings = QPushButton("设置", self)
        
        self.btn_new_plan.setObjectName("btnNewPlan")
        self.btn_import_code.setObjectName("btnImport")
        self.btn_lib_settings.setObjectName("btnSettings")

        self.btn_recycle_bin.clicked.connect(self.show_recycle_bin_dialog)
        self.btn_new_plan.clicked.connect(self.show_new_plan_dialog)
        self.btn_import_code.clicked.connect(self.show_import_code_dialog)
        self.btn_lib_settings.clicked.connect(self.main_app.open_settings_dialog)

        header_layout.addWidget(self.btn_recycle_bin)
        header_layout.addWidget(self.btn_import_code)
        header_layout.addWidget(self.btn_lib_settings)
        header_layout.addWidget(self.btn_new_plan)
        main_layout.addLayout(header_layout)

        self.line = QFrame()
        self.line.setObjectName("midLine")
        main_layout.addWidget(self.line)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("gridScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea#gridScroll { background-color: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 8px; }
            QScrollBar::handle:vertical { background: #333333; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #555555; }
        """)
        
        self.grid_container = QWidget()
        self.grid_container.setObjectName("gridContainer")
        self.grid_container.setStyleSheet("QWidget#gridContainer { background-color: transparent; }")
        
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setHorizontalSpacing(25)
        self.grid_layout.setVerticalSpacing(30)
        self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(scroll_area, stretch=1)

    def adapt_to_theme(self, current_theme):
        """大厅文案与按钮自适应转换"""
        texts = getattr(current_theme, "desktop_texts", {
            "title": "我的书架",
            "subtitle": "",
            "new_btn": "新建",
            "import_btn": "导入",
            "settings_btn": "设置"
        })
        self.lbl_main_title.setText(texts.get("title", "我的书架"))
        self.lbl_sub_title.setText(texts.get("subtitle", ""))
        self.btn_new_plan.setText(texts.get("new_btn", "✚ 新建"))
        self.btn_import_code.setText(texts.get("import_btn", "导入"))
        self.btn_lib_settings.setText(texts.get("settings_btn", "设置"))
        self.btn_recycle_bin.setText("回收站")

        bg_hex = current_theme.canvas_bg
        self.is_dark_bg = True
        
        if bg_hex.startswith("#"):
            c = bg_hex.lstrip("#")
            if len(c) == 6:
                r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                brightness = (0.299 * r + 0.587 * g + 0.114 * b)
                self.is_dark_bg = brightness < 140

        text_color = "#ffffff" if self.is_dark_bg else "#111111"
        sub_color = "#888888" if self.is_dark_bg else "#555555"
        border_color = "#252526" if self.is_dark_bg else "#dddddd"

        self.setStyleSheet(f"QWidget#libraryView {{ background-color: {bg_hex}; border: none; }}")

        self.lbl_main_title.setStyleSheet(f"QLabel#mainTitle {{ color: {text_color}; font-size: 24px; font-weight: bold; border: none; background: transparent; font-family: '{current_theme.font_family}'; }}")
        self.lbl_sub_title.setStyleSheet(f"QLabel#subTitle {{ color: {sub_color}; font-size: 11px; border: none; background: transparent; font-family: '{current_theme.font_family}'; }}")
        self.line.setStyleSheet(f"QFrame#midLine {{ background-color: {border_color}; max-height: 1px; }}")

        btn_radius = "0px" if current_theme.__name__ in ["ConstructivistTheme", "SwissMinimalistTheme", "TerminalTheme"] else "5px"
        
        theme_main_color = "#007acc" if self.is_dark_bg else "#002FA7"
        theme_hover_color = "#0098ff" if self.is_dark_bg else "#001a80"
        if current_theme.__name__ == "ConstructivistTheme":
            theme_main_color = "#C0392B"
            theme_hover_color = "#e74c3c"
        
        self.btn_new_plan.setStyleSheet(f"""
            QPushButton#btnNewPlan {{
                background-color: {theme_main_color}; color: #ffffff; border: none;
                border-radius: {btn_radius}; padding: 8px 16px; font-weight: bold; font-size: 12px;
                font-family: '{current_theme.font_family}';
            }}
            QPushButton#btnNewPlan:hover {{ background-color: {theme_hover_color}; }}
        """)
        
        other_bg = "#2d2d2d" if self.is_dark_bg else "#f0f0f0"
        other_border = "#454545" if self.is_dark_bg else "#cccccc"
        other_text = "#cccccc" if self.is_dark_bg else "#111111"
        if current_theme.__name__ == "ConstructivistTheme":
            other_bg = "#2e3033"
            other_border = "#1a1a1a"
            other_text = "#EADEC9"

        self.btn_import_code.setStyleSheet(f"""
            QPushButton#btnImport {{
                background-color: {other_bg}; color: {other_text}; border: 1px solid {other_border};
                border-radius: {btn_radius}; padding: 8px 16px; font-weight: bold; font-size: 12px;
                font-family: '{current_theme.font_family}';
            }}
            QPushButton#btnImport:hover {{ background-color: {"#454545" if self.is_dark_bg else "#e0e0e0"}; }}
        """)
        self.btn_lib_settings.setStyleSheet(f"""
            QPushButton#btnSettings {{
                background-color: {other_bg}; color: {other_text}; border: 1px solid {other_border};
                border-radius: {btn_radius}; padding: 8px 16px; font-weight: bold; font-size: 12px;
                font-family: '{current_theme.font_family}';
            }}
            QPushButton#btnSettings:hover {{ background-color: {"#454545" if self.is_dark_bg else "#e0e0e0"}; }}
        """)
        self.btn_recycle_bin.setStyleSheet(f"""
            QPushButton#btnRecycleBin {{
                background-color: {other_bg}; color: {other_text}; border: 1px solid {other_border};
                border-radius: {btn_radius}; padding: 8px 16px; font-weight: bold; font-size: 12px;
                font-family: '{current_theme.font_family}';
            }}
            QPushButton#btnRecycleBin:hover {{ background-color: {"#454545" if self.is_dark_bg else "#e0e0e0"}; }}
        """)

    def refresh_shelf(self):
        """重新扫描并重新编排书架网格"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        plans = self.main_app.library_manifest.get("plans", [])
        col_count = 5  
        row = 0
        col = 0

        for plan in plans:
            card = PlanCardWidget(plan, self.is_dark_bg, self)
            card.clicked.connect(self.plan_selected.emit)
            card.delete_requested.connect(self.request_delete_plan)
            
            # 绑定重命名及其他信号槽
            card.rename_requested.connect(self.request_rename_plan)
            card.change_cover_color_requested.connect(self.request_change_cover_color)
            card.change_cover_image_requested.connect(self.request_change_cover_image)
            card.clear_cover_image_requested.connect(self.request_clear_cover_image)
            card.toggle_protection_requested.connect(self.request_toggle_plan_protection)

            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= col_count:
                col = 0
                row += 1

        add_card = AddCardWidget(self.is_dark_bg, self)
        add_card.clicked.connect(self.show_new_plan_dialog)
        self.grid_layout.addWidget(add_card, row, col)

    def request_toggle_plan_protection(self, plan_id):
        """切换特定路线的隐式只读防护状态"""
        for plan in self.main_app.library_manifest.get("plans", []):
            if plan["id"] == plan_id:
                plan["is_protected"] = not plan.get("is_protected", False)
                break
        self.main_app.save_library_manifest()
        self.refresh_shelf()

    def request_rename_plan(self, plan_id, current_name):
        """弹窗修改路线名称"""
        new_name, ok = QInputDialog.getText(
            self, "重命名路线", "请输入新的路线名称：", QLineEdit.Normal, current_name
        )
        if ok and new_name.strip():
            new_name = new_name.strip()
            target_plan = None
            
            for plan in self.main_app.library_manifest.get("plans", []):
                if plan["id"] == plan_id:
                    plan["name"] = new_name
                    target_plan = plan
                    break
            
            if target_plan:
                file_path = target_plan["file_path"]
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["name"] = new_name
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                    except Exception as e:
                        print(f"修改物理文件名称失败: {e}")

            self.main_app.save_library_manifest()
            self.refresh_shelf()

    def request_change_cover_color(self, plan_id, current_color):
        """修改卡片纯色封面背景"""
        color = QColorDialog.getColor(QColor(current_color), self, "选择封面背景色")
        if color.isValid():
            new_color = color.name()
            for plan in self.main_app.library_manifest.get("plans", []):
                if plan["id"] == plan_id:
                    plan["cover_color"] = new_color  
                    break
            self.main_app.save_library_manifest()
            self.refresh_shelf()

    def request_change_cover_image(self, plan_id):
        """上传本地封面图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择封面图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            _, ext = os.path.splitext(file_path)
            dest_filename = f"cover_{plan_id}{ext}"
            dest_path = os.path.join(self.main_app.plans_dir, dest_filename)
            try:
                shutil.copy(file_path, dest_path)
                relative_path = os.path.join(self.main_app.plans_dir, dest_filename)
                
                for plan in self.main_app.library_manifest.get("plans", []):
                    if plan["id"] == plan_id:
                        plan["cover_image"] = relative_path
                        break
                self.main_app.save_library_manifest()
                self.refresh_shelf()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"拷贝保存封面图失败: {e}")

    def request_clear_cover_image(self, plan_id):
        """清除封面背景底图并恢复纯色"""
        for plan in self.main_app.library_manifest.get("plans", []):
            if plan["id"] == plan_id:
                if "cover_image" in plan:
                    img_path = plan["cover_image"]
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except Exception as e:
                            print(f"清除物理图片失败: {e}")
                    plan.pop("cover_image", None)
                break
        self.main_app.save_library_manifest()
        self.refresh_shelf()

    def show_new_plan_dialog(self):
        """新建学习路线对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新建")
        dialog.setMinimumWidth(320)
        dialog.setStyleSheet("""
            QDialog { background-color: #1e1e1e; border: 1px solid #454545; }
            QLabel { color: #cccccc; font-size: 12px; }
            QLineEdit, QComboBox { 
                background-color: #2d2d2d; color: #ffffff; border: 1px solid #454545; 
                border-radius: 4px; padding: 6px; 
            }
        """)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("名称："))
        edit_name = QLineEdit()
        edit_name.setPlaceholderText("")
        layout.addWidget(edit_name)

        layout.addWidget(QLabel("主题选择："))
        combo_color = QComboBox()
        combo_color.addItem("VS-Code风格", "#2d3748")
        combo_color.addItem("构成主义", "#962d22")
        combo_color.addItem("洛可可风格", "#FFD1DC")
        combo_color.addItem("复古未来主义", "#020502")
        combo_color.addItem("现代包豪斯", "#002FA7")
        layout.addWidget(combo_color)

        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_ok = QPushButton("确认创建")
        
        btn_cancel.setStyleSheet("background-color: #2d2d2d; color: #ccc; border: none; padding: 6px; border-radius: 4px;")
        btn_ok.setStyleSheet("background-color: #007acc; color: #fff; border: none; padding: 6px; border-radius: 4px; font-weight: bold;")
        
        btn_cancel.clicked.connect(dialog.reject)
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            name = edit_name.text().strip()
            if not name:
                QMessageBox.warning(self, "限制", "科目名称不能为空！")
                return
            
            color_hex = combo_color.currentData() if combo_color.currentData() else "#2d3748"
            theme_map = {
                "#2d3748": 0,
                "#962d22": 1,
                "#FFD1DC": 2,
                "#020502": 3,
                "#002FA7": 4
            }
            theme_idx = theme_map.get(color_hex, 0)
            
            new_id = "plan_" + uuid.uuid4().hex[:8]
            file_path = os.path.join(self.main_app.plans_dir, f"{new_id}.json")
            
            base_data = {
                "node_id": "root",
                "name": name,
                "notes": "",
                "progress": 0,
                "color": color_hex,
                "node_type": "standard",
                "study_logs": [],
                "children": [],
                "is_protected": False,
                "layout_direction": 0  # 显式初始化默认的展示方向
            }
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(base_data, f, indent=4, ensure_ascii=False)
                
                new_plan = {
                    "id": new_id,
                    "name": name,
                    "file_path": file_path,
                    "cover_color": color_hex,
                    "theme_index": theme_idx,
                    "progress": 0,
                    "total_hours": 0.0,
                    "last_active": datetime.date.today().strftime("%Y-%m-%d"),
                    "is_protected": False
                }
                self.main_app.library_manifest["plans"].append(new_plan)
                self.main_app.save_library_manifest()
                self.refresh_shelf()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法生成初始计划：{e}")

    def show_import_code_dialog(self):
        """导入分享码"""
        code, ok = QInputDialog.getMultiLineText(self, "导入", "请在下方粘贴路线分享码：")
        if ok and code.strip():
            name, ok_name = QInputDialog.getText(self, "命名", "请为此导入的学习路径进行命名：")
            if ok_name and name.strip():
                try:
                    new_id, file_path = self.main_app.import_share_code_direct(code.strip(), name.strip())
                    
                    new_plan = {
                        "id": new_id,
                        "name": name.strip(),
                        "file_path": file_path,
                        "cover_color": "#2d3748",
                        "theme_index": 0,
                        "progress": 0,
                        "total_hours": 0.0,
                        "last_active": datetime.date.today().strftime("%Y-%m-%d"),
                        "is_protected": False
                    }
                    self.main_app.library_manifest["plans"].append(new_plan)
                    self.main_app.save_library_manifest()
                    self.refresh_shelf()
                    QMessageBox.information(self, "成功", f"路线【{name.strip()}】解析并导入成功！已加入书架。")
                except Exception as e:
                    QMessageBox.critical(self, "导入失败", f"该分享码无效！\n信息：{e}")

    def request_delete_plan(self, plan_id):
        """安全地将导图移动至回收站而不再直接执行物理删除"""
        target_plan = None
        for plan in self.main_app.library_manifest.get("plans", []):
            if plan["id"] == plan_id:
                target_plan = plan
                break

        if not target_plan:
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除路线【{target_plan['name']}】吗？\n删除后将被移至回收站，可随时还原。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.main_app.library_manifest["plans"].remove(target_plan)
            
            # 添加删除时间标签
            target_plan["deleted_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.main_app.library_manifest.setdefault("recycle_bin", []).append(target_plan)
            
            self.main_app.save_library_manifest()
            self.refresh_shelf()
            QMessageBox.information(self, "已移至回收站", f"已成功将【{target_plan['name']}】移至回收站。")

    def show_recycle_bin_dialog(self):
        """展示回收站对话框并重刷书架"""
        from dialogs import RecycleBinDialog
        dialog = RecycleBinDialog(self.main_app.library_manifest, self)
        dialog.setStyleSheet(self.main_app.get_current_theme_class().qss)
        dialog.exec()
        
        self.main_app.save_library_manifest()
        self.refresh_shelf()