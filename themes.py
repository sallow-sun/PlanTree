# themes.py
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QPainterPath, QFont
from PySide6.QtCore import Qt, QRectF, QPointF

class BaseTheme:
    qss = ""                  
    canvas_bg = "#151515"     
    line_width = 2            
    font_family = "Microsoft YaHei" 
    button_texts = {}
    desktop_texts = {} # 新增书架大厅多态文案字典
    inspector_title = ""
    inspector_placeholder = ""

    @staticmethod
    def get_line_color(is_child_locked):
        raise NotImplementedError

    @staticmethod
    def paint_node(painter, node, is_locked, is_selected, width, height, incomplete_count=0):
        raise NotImplementedError

    @staticmethod
    def draw_connection_path(start_pt, end_pt, layout_dir):
        raise NotImplementedError

    @staticmethod
    def draw_background(painter, rect):
        raise NotImplementedError


class ModernDarkTheme(BaseTheme):
    canvas_bg = "#151515"
    line_width = 2
    font_family = "Microsoft YaHei"
    inspector_title = "节点属性"
    inspector_placeholder = "选择任意节点\n以配置。"

    button_texts = {
        "back": "返回",
        "export": "导出",
        "import": "导入",
        "add": "添加子节点",
        "delete": "删除节点",
        "move_up": "向上/前移",
        "move_down": "向下/后移",
        "prereq": "设置前置",
        "settings": "设置"
    }

    desktop_texts = {
        "title": "我的书架",
        "subtitle": "",
        "new_btn": "新建",
        "import_btn": "导入",
        "settings_btn": "设置"
    }

    qss = """
    QMainWindow { background-color: #1a1a1a; }
    QLabel { color: #e0e0e0; font-family: "Microsoft YaHei", sans-serif; font-size: 13px; }
    QPushButton {
        background-color: #2d2d2d; color: #cccccc; border: 1px solid #454545;
        border-radius: 4px; padding: 6px 12px; font-family: "Microsoft YaHei"; font-weight: bold;
    }
    QPushButton:hover { background-color: #454545; border-color: #007acc; color: #ffffff; }
    QPushButton#dangerButton { background-color: #511c1c; color: #e74c3c; border-color: #722727; }
    QPushButton#dangerButton:hover { background-color: #e74c3c; color: #ffffff; }
    QDialog { background-color: #1e1e1e; }
    QWidget#inspectorPanel { background-color: #202020; border-left: 1px solid #2d2d2d; }
    
    QLineEdit, QTextEdit { 
        background-color: #2d2d2d; color: #cccccc; border: 1px solid #3f3f46; border-radius: 4px; padding: 6px; 
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #007acc; }
    
    QListWidget {
        background-color: #252526; color: #cccccc; border: 1px solid #3f3f46; border-radius: 4px; padding: 4px;
    }
    QListWidget::item {
        padding: 4px; border-bottom: 1px solid #2d2d2d; color: #bbbbbb; font-size: 11px;
    }
    QListWidget::item:hover {
        background-color: #2d2d30; color: #ffffff;
    }
    QListWidget::item:selected {
        background-color: #094771; color: #ffffff;
    }

    QSplitter::handle { background-color: #2d2d2d; }
    QSplitter::handle:horizontal { width: 6px; }
    QSplitter::handle:vertical { height: 6px; }
    QSplitter::handle:hover { background-color: #007acc; }
    QCheckBox { color: #e0e0e0; font-family: "Microsoft YaHei"; font-size: 13px; }
    QCheckBox::indicator { width: 14px; height: 14px; background-color: #252526; border: 1px solid #454545; border-radius: 2px; }
    QCheckBox::indicator:checked { background-color: #007acc; border-color: #007acc; }
    QComboBox { background-color: #252526; color: #cccccc; border: 1px solid #454545; border-radius: 4px; padding: 6px 12px; min-width: 200px; }
    QComboBox QAbstractItemView { background-color: #252526; color: #cccccc; selection-background-color: #094771; }

    QSlider::groove:horizontal {
        border: 1px solid #3f3f46;
        height: 6px;
        background: #252526;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #007acc;
        width: 14px;
        margin-top: -4px;
        margin-bottom: -4px;
        border-radius: 7px;
    }
    QSlider::handle:horizontal:hover { background: #0098ff; }
    """

    @staticmethod
    def get_line_color(is_child_locked):
        return QColor("#444444") if is_child_locked else QColor("#ffffff")

    @staticmethod
    def paint_node(painter, node, is_locked, is_selected, width, height, incomplete_count=0):
        brightness = 0
        is_strict = getattr(node, 'node_type', 'standard') == 'strict'

        if is_locked:
            bg_color = QColor("#1e1e1e")
            text_color = QColor("#555555")
        else:
            bg_color = QColor(node.color)
            r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()
            brightness = (0.299 * r + 0.587 * g + 0.114 * b)
            text_color = QColor("#111111") if brightness > 140 else QColor("#ffffff")

        if not is_locked and node.progress == 100:
            glow_color = QColor(node.color)
            glow_color.setAlpha(120)
            glow_pen = QPen(glow_color, 5, Qt.SolidLine)
            painter.setPen(glow_pen)
            painter.setBrush(QBrush())
            painter.drawRoundedRect(-2, -2, width + 4, height + 4, 10, 10)

        painter.setBrush(QBrush(bg_color))
        pen = QPen(QColor("#007acc"), 3) if is_selected else QPen(QColor("#3a3a3a") if is_locked else QColor("#7f8c8d"), 1, Qt.DashLine if is_locked else Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRoundedRect(0, 0, width, height, 8, 8)

        if is_locked and incomplete_count > 0:
            painter.setBrush(QBrush(QColor("#2d1a1a")))
            painter.setPen(QPen(QColor("#e74c3c"), 1))
            painter.drawRoundedRect(QRectF(width - 34, 6, 26, 14), 4, 4)
            painter.setPen(QColor("#ff9999"))
            font_badge = QFont("Microsoft YaHei", 7)
            font_badge.setBold(True)
            painter.setFont(font_badge)
            painter.drawText(QRectF(width - 34, 6, 26, 14), Qt.AlignCenter, f"🔒{incomplete_count}")

        if is_strict and not is_locked and node.progress < 100:
            painter.setBrush(QBrush(QColor("#e74c3c")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(width - 16, 8, 8, 8)

        if not is_locked and node.progress == 100:
            painter.setBrush(QBrush(QColor("#2ecc71")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(width - 22, 6, 14, 14)
            painter.setPen(QColor("#111111"))
            
            font_check = QFont("Microsoft YaHei", 8)
            font_check.setBold(True)
            painter.setFont(font_check)
            painter.drawText(QRectF(width - 22, 6, 14, 14), Qt.AlignCenter, "✓")

        painter.setPen(text_color)
        
        font_name = QFont("Microsoft YaHei", 10)
        font_name.setBold(True)
        painter.setFont(font_name)
        
        display_name = f"[锁] {node.name}" if is_locked else node.name
        right_margin = 38 if is_locked else (25 if (node.progress == 100 or is_strict) else 10)
        text_rect = QRectF(10, 8, width - 10 - right_margin, 25)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_name)

        if not is_locked:
            bar_bg_color = QColor("#1e1e1e") if node.color != "#1e1e1e" else QColor("#333333")
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bar_bg_color))
            painter.drawRoundedRect(QRectF(10, 42, width - 20, 8), 4, 4)

            if node.progress > 0:
                progress_width = (width - 20) * (node.progress / 100.0)
                fill_color = QColor("#2ecc71") if node.progress == 100 else QColor("#f39c12")
                painter.setBrush(QBrush(fill_color))
                painter.drawRoundedRect(QRectF(10, 42, progress_width, 8), 4, 4)

            prog_text_color = QColor("#333333") if brightness > 140 else QColor("#cccccc")
            painter.setPen(prog_text_color)
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(QRectF(10, 52, width - 20, 15), Qt.AlignRight, f"{node.progress}%")
        else:
            painter.setPen(QColor("#555555"))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(QRectF(10, 42, width - 20, 18), Qt.AlignLeft, f"PENDING REQUIREMENTS ({incomplete_count})")

    @staticmethod
    def draw_connection_path(start_pt, end_pt, layout_dir):
        path = QPainterPath()
        path.moveTo(start_pt)
        if layout_dir == 0:
            ctrl1 = QPointF(start_pt.x() + 50, start_pt.y())
            ctrl2 = QPointF(end_pt.x() - 50, end_pt.y())
        else:
            ctrl1 = QPointF(start_pt.x(), start_pt.y() + 50)
            ctrl2 = QPointF(end_pt.x(), end_pt.y() - 50)
        path.cubicTo(ctrl1, ctrl2, end_pt)
        return path

    @staticmethod
    def draw_background(painter, rect):
        painter.fillRect(rect, QColor("#151515"))


class ConstructivistTheme(BaseTheme):
    canvas_bg = "#EADEC9"      
    line_width = 3             
    font_family = "Impact"     
    inspector_title = "节点属性"
    inspector_placeholder = "选择任意节点\n以配置。"

    button_texts = {
        "back": "返回",
        "export": "导出",
        "import": "导入",
        "add": "添加子节点",
        "delete": "删除节点",
        "move_up": "向上/前移",
        "move_down": "向下/后移",
        "prereq": "设置前置",
        "settings": "设置"
    }

    desktop_texts = {
        "title": "我的书架",
        "subtitle": "",
        "new_btn": "新建",
        "import_btn": "导入",
        "settings_btn": "设置"
    }

    qss = """
    QMainWindow { background-color: #DFD1B8; } 
    QLabel { color: #1a1a1a; font-family: "Impact", "Microsoft YaHei"; font-size: 13px; font-weight: bold; }
    QPushButton {
        background-color: #2e3033; color: #EADEC9; border: 2px solid #1a1a1a;
        border-radius: 0px; padding: 6px 12px; font-family: "Impact", "Microsoft YaHei"; font-size: 13px;
    }
    QPushButton:hover { background-color: #C0392B; border-color: #1a1a1a; color: #ffffff; }
    QPushButton#dangerButton { background-color: #511c1c; color: #e74c3c; border-color: #1a1a1a; border-radius: 0px; }
    QPushButton#dangerButton:hover { background-color: #e74c3c; color: #ffffff; }
    QDialog { background-color: #EADEC9; border: 2px solid #1a1a1a; }
    QWidget#inspectorPanel { background-color: #DFD1B8; border-left: 2px solid #1a1a1a; }
    
    QLineEdit, QTextEdit { 
        background-color: #EADEC9; color: #1a1a1a; border: 2px solid #1a1a1a; border-radius: 0px; padding: 6px; 
        font-family: "Microsoft YaHei"; font-weight: bold;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #C0392B; }
    
    QListWidget {
        background-color: #EADEC9; color: #1a1a1a; border: 2px solid #1a1a1a; border-radius: 0px; padding: 4px;
        font-family: "Microsoft YaHei"; font-weight: bold;
    }
    QListWidget::item {
        padding: 4px; border-bottom: 2px solid #1a1a1a; color: #1a1a1a; font-size: 11px;
    }
    QListWidget::item:hover {
        background-color: #DFD1B8; color: #C0392B;
    }
    QListWidget::item:selected {
        background-color: #C0392B; color: #ffffff;
    }

    QSplitter::handle { background-color: #1a1a1a; }
    QSplitter::handle:horizontal { width: 8px; }
    QSplitter::handle:vertical { height: 8px; }
    QSplitter::handle:hover { background-color: #C0392B; }
    QCheckBox { color: #1a1a1a; font-family: "Microsoft YaHei"; font-size: 13px; font-weight: bold; }
    QCheckBox::indicator { width: 14px; height: 14px; background-color: #EADEC9; border: 2px solid #1a1a1a; border-radius: 0px; }
    QCheckBox::indicator:checked { background-color: #C0392B; border-color: #1a1a1a; }
    QComboBox { background-color: #EADEC9; color: #1a1a1a; border: 2px solid #1a1a1a; border-radius: 0px; padding: 6px 12px; min-width: 200px; font-weight: bold; }
    QComboBox QAbstractItemView { background-color: #EADEC9; color: #1a1a1a; selection-background-color: #C0392B; selection-color: #ffffff; }

    QSlider::groove:horizontal {
        border: 2px solid #1a1a1a;
        height: 10px;
        background: #EADEC9;
        border-radius: 0px;
    }
    QSlider::handle:horizontal {
        background: #C0392B;
        border: 2px solid #1a1a1a;
        width: 14px;
        height: 20px;
        margin-top: -6px;
        margin-bottom: -6px;
        border-radius: 0px; 
    }
    QSlider::handle:horizontal:hover { background: #e74c3c; }
    """

    @staticmethod
    def get_line_color(is_child_locked):
        return QColor("#95a5a6") if is_child_locked else QColor("#1a1a1a") 

    @staticmethod
    def paint_node(painter, node, is_locked, is_selected, width, height, incomplete_count=0):
        brightness = 0
        is_strict = getattr(node, 'node_type', 'standard') == 'strict'

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#1a1a1a")))
        painter.drawRect(5, 5, width, height)

        if is_locked:
            bg_color = QColor("#DFD1B8") 
            text_color = QColor("#95a5a6")
        else:
            bg_color = QColor("#2e3033") if node.color == "#2d3748" else QColor(node.color)
            r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()
            brightness = (0.299 * r + 0.587 * g + 0.114 * b)
            text_color = QColor("#1a1a1a") if brightness > 140 else QColor("#EADEC9")

        painter.setBrush(QBrush(bg_color))
        if is_selected:
            border_pen = QPen(QColor("#C0392B"), 3, Qt.SolidLine)
        else:
            border_pen = QPen(QColor("#95a5a6") if is_locked else QColor("#1a1a1a"), 2, Qt.DashLine if is_locked else Qt.SolidLine)
        painter.setPen(border_pen)
        painter.drawRect(0, 0, width, height)

        if not is_locked:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#C0392B")))
            painter.drawRect(2, 2, 10, height - 4)

        if is_locked and incomplete_count > 0:
            painter.setBrush(QBrush(QColor("#C0392B")))
            painter.setPen(QPen(QColor("#1a1a1a"), 1.5))
            painter.drawRect(width - 48, 6, 40, 14)
            painter.setPen(QColor("#EADEC9"))
            font_req = QFont("Impact", 8)
            font_req.setBold(True)
            painter.setFont(font_req)
            painter.drawText(QRectF(width - 48, 6, 40, 14), Qt.AlignCenter, f"REQ-{incomplete_count}")

        if is_strict and not is_locked and node.progress < 100:
            painter.setBrush(QBrush(QColor("#C0392B")))
            painter.setPen(Qt.NoPen)
            painter.drawRect(width - 18, 6, 8, 8)

        if not is_locked and node.progress == 100:
            path = QPainterPath()
            path.moveTo(width - 32, 0)
            path.lineTo(width, 0)
            path.lineTo(width, 32)
            path.closeSubpath()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#C0392B")))
            painter.drawPath(path)
            
            painter.setPen(QColor("#EADEC9"))
            font_star = QFont("Impact", 10)
            font_star.setBold(True)
            painter.setFont(font_star)
            painter.drawText(QRectF(width - 20, 0, 20, 20), Qt.AlignCenter, "★")

        painter.setPen(text_color)
        
        font_display = QFont("Impact" if not is_locked else "Microsoft YaHei", 10)
        font_display.setBold(True)
        painter.setFont(font_display)
        
        display_name = node.name
        right_margin = 52 if is_locked else (35 if node.progress == 100 else (18 if is_strict else 10))
        text_rect = QRectF(18, 8, width - 18 - right_margin, 25) if not is_locked else QRectF(15, 8, width - 15 - right_margin, 25)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_name)

        if not is_locked and node.progress < 100:
            gauge_rect = QRectF(width - 20, 10, 10, 50)
            painter.setPen(QPen(text_color, 1))
            painter.setBrush(QBrush(QColor("#1a1a1a") if brightness > 140 else QColor("#111111")))
            painter.drawRect(gauge_rect)

            if node.progress > 0:
                fill_height = 48 * (node.progress / 100.0)
                fill_rect = QRectF(width - 19, 11 + (48 - fill_height), 8, fill_height)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#C0392B")))
                painter.drawRect(fill_rect)

            painter.setPen(QPen(text_color, 1))
            for tick_y in range(15, 65, 12):
                painter.drawLine(width - 24, tick_y, width - 21, tick_y)
        elif is_locked:
            painter.setPen(QPen(QColor("#962d22"), 1))
            font_lock = QFont("Impact", 8)
            font_lock.setBold(True)
            painter.setFont(font_lock)
            painter.drawText(QRectF(15, 42, width - 30, 18), Qt.AlignLeft | Qt.AlignVCenter, f"STATION LOCKED ({incomplete_count})")

    @staticmethod
    def draw_connection_path(start_pt, end_pt, layout_dir):
        path = QPainterPath()
        path.moveTo(start_pt)
        if layout_dir == 0:
            mid_x = start_pt.x() + (end_pt.x() - start_pt.x()) / 2
            path.lineTo(mid_x, start_pt.y())
            path.lineTo(mid_x, end_pt.y())
            path.lineTo(end_pt.x(), end_pt.y())
        else:
            mid_y = start_pt.y() + (end_pt.y() - start_pt.y()) / 2
            path.lineTo(start_pt.x(), mid_y)
            path.lineTo(end_pt.x(), mid_y)
            path.lineTo(end_pt.x(), end_pt.y())
        return path

    @staticmethod
    def draw_background(painter, rect):
        painter.fillRect(rect, QColor("#EADEC9"))
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen_grid = QPen(QColor("#DFD1B8"), 1.5, Qt.SolidLine)
        painter.setPen(pen_grid)
        
        painter.drawEllipse(QPointF(0, 0), 250, 250)
        painter.drawEllipse(QPointF(0, 0), 450, 450)
        painter.drawEllipse(QPointF(0, 0), 650, 650)
        
        painter.drawLine(-2500, -1800, 2500, 1800)
        painter.drawLine(-2500, 1800, 2500, -1800)
        painter.drawLine(-2500, 0, 2500, 0)
        painter.drawLine(0, -2500, 0, 2500)
        
        pen_dash = QPen(QColor("#D2C3AA"), 1.5, Qt.DashLine)
        painter.setPen(pen_dash)
        painter.drawEllipse(QPointF(0, 0), 550, 550)


class RococoTheme(BaseTheme):
    canvas_bg = "#FDFBF7" 
    line_width = 3
    font_family = "Georgia"
    inspector_title = "节点属性"
    inspector_placeholder = "选择任意节点\n以配置。"

    button_texts = {
        "back": "返回",
        "export": "导出",
        "import": "导入",
        "add": "添加子节点",
        "delete": "删除节点",
        "move_up": "向上/前移",
        "move_down": "向下/后移",
        "prereq": "设置前置",
        "settings": "设置"
    }

    desktop_texts = {
        "title": "我的书架",
        "subtitle": "",
        "new_btn": "新建",
        "import_btn": "导入",
        "settings_btn": "设置"
    }

    qss = """
    QMainWindow { background-color: #F5EFEB; }
    QLabel { color: #5C4033; font-family: "Georgia", "Microsoft YaHei"; font-size: 13px; font-weight: bold; }
    QPushButton {
        background-color: #FDFBF7; color: #5C4033; border: 1.5px solid #D4AF37;
        border-radius: 8px; padding: 6px 12px; font-family: "Georgia", "Microsoft YaHei"; font-weight: bold;
    }
    QPushButton:hover { background-color: #F5EFEB; border-color: #C5A028; color: #8B4513; }
    QPushButton#dangerButton { background-color: #FADBD8; color: #C0392B; border-color: #E6B0AA; border-radius: 8px; }
    QPushButton#dangerButton:hover { background-color: #E6B0AA; color: #78281F; }
    QDialog { background-color: #FDFBF7; border: 1.5px solid #D4AF37; border-radius: 10px; }
    QWidget#inspectorPanel { background-color: #F5EFEB; border-left: 2.5px solid #D4AF37; }
    
    QLineEdit, QTextEdit { 
        background-color: #FDFBF7; color: #5C4033; border: 1.5px solid #D4AF37; border-radius: 6px; padding: 6px; 
        font-family: "Georgia", "Microsoft YaHei";
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #C5A028; }
    
    QListWidget {
        background-color: #FDFBF7; color: #5C4033; border: 1.5px solid #D4AF37; border-radius: 6px; padding: 4px;
        font-family: "Georgia", "Microsoft YaHei";
    }
    QListWidget::item {
        padding: 4px; border-bottom: 1px dashed #E5D5C5; color: #8B7355; font-size: 11px;
    }
    QListWidget::item:hover {
        background-color: #F5EFEB; color: #5C4033;
    }
    QListWidget::item:selected {
        background-color: #E5D5C5; color: #5C4033;
    }

    QSplitter::handle { background-color: #E5D5C5; }
    QSplitter::handle:horizontal { width: 6px; }
    QSplitter::handle:vertical { height: 6px; }
    QSplitter::handle:hover { background-color: #D4AF37; }
    QCheckBox { color: #5C4033; font-family: "Georgia", "Microsoft YaHei"; font-size: 13px; }
    QCheckBox::indicator { width: 14px; height: 14px; background-color: #FDFBF7; border: 1.5px solid #D4AF37; border-radius: 4px; }
    QCheckBox::indicator:checked { background-color: #FFD1DC; border-color: #D4AF37; }
    QComboBox { background-color: #FDFBF7; color: #5C4033; border: 1.5px solid #D4AF37; border-radius: 6px; padding: 6px 12px; min-width: 200px; font-weight: bold; }
    QComboBox QAbstractItemView { background-color: #FDFBF7; color: #5C4033; selection-background-color: #E5D5C5; selection-color: #5C4033; }

    QSlider::groove:horizontal {
        border: 1.5px solid #D4AF37;
        height: 8px;
        background: #FDFBF7;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: #FFD1DC;
        border: 1.5px solid #D4AF37;
        width: 14px;
        height: 14px;
        margin-top: -3px;
        margin-bottom: -3px;
        border-radius: 7px;
    }
    QSlider::handle:horizontal:hover { background: #FFB7C5; }
    """

    @staticmethod
    def get_line_color(is_child_locked):
        return QColor("#D5D0C5") if is_child_locked else QColor("#D4AF37") 

    @staticmethod
    def paint_node(painter, node, is_locked, is_selected, width, height, incomplete_count=0):
        is_strict = getattr(node, 'node_type', 'standard') == 'strict'
        
        shadow_rect = QRectF(4, 4, width, height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#E5D5C5")))
        painter.drawRoundedRect(shadow_rect, 18, 18)

        if is_locked:
            bg_color = QColor("#EAE5DF")
            gold_pen = QPen(QColor("#C5B5A5"), 1.5, Qt.DashLine)
            text_color = QColor("#9E9285")
        else:
            bg_color = QColor("#FFD1DC") if node.color == "#2d3748" else QColor(node.color)
            gold_pen = QPen(QColor("#D4AF37"), 2.0 if is_selected else 1.2)
            text_color = QColor("#5C4033")

        painter.setBrush(QBrush(bg_color))
        painter.setPen(gold_pen)
        painter.drawRoundedRect(0, 0, width, height, 15, 15)

        inner_pen = QPen(QColor("#FAF6EE") if not is_locked else QColor("#D5D0C5"), 0.8)
        painter.setPen(inner_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(4, 4, width - 8, height - 8, 11, 11)

        if is_locked and incomplete_count > 0:
            painter.setBrush(QBrush(QColor("#FAF6EE")))
            painter.setPen(QPen(QColor("#D4AF37"), 1))
            painter.drawEllipse(width - 26, 6, 16, 16)
            painter.setPen(QColor("#8B7355"))
            font_req = QFont("Georgia", 8)
            font_req.setBold(True)
            painter.setFont(font_req)
            painter.drawText(QRectF(width - 26, 6, 16, 16), Qt.AlignCenter, str(incomplete_count))

        if is_strict and not is_locked and node.progress < 100:
            painter.setBrush(QBrush(QColor("#E1989A")))
            painter.setPen(QPen(QColor("#D4AF37"), 0.8))
            painter.drawEllipse(width - 15, 8, 6, 8)

        if not is_locked and node.progress == 100:
            bloom_x, bloom_y = width - 25, 18
            painter.setPen(QPen(QColor("#D4AF37"), 1.2))
            painter.setBrush(QBrush(QColor("#F5CBA7")))
            
            painter.drawEllipse(bloom_x - 6, bloom_y - 6, 12, 12)
            painter.drawEllipse(bloom_x - 2, bloom_y - 4, 8, 8)
            painter.setBrush(QBrush(QColor("#D4AF37")))
            painter.drawEllipse(bloom_x, bloom_y - 1, 4, 4)

        painter.setPen(text_color)
        
        font_name = QFont("Georgia", 9)
        font_name.setBold(True)
        painter.setFont(font_name)
        
        display_name = node.name
        right_margin = 32 if is_locked else (35 if (node.progress == 100 or is_strict) else 15)
        text_rect = QRectF(15, 10, width - 15 - right_margin, 25)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_name)

        if not is_locked:
            painter.setFont(QFont("Georgia", 8))
            painter.drawText(QRectF(15, 42, 80, 15), Qt.AlignLeft | Qt.AlignVCenter, f"Progress: {node.progress}%")
        else:
            font_locked = QFont("Georgia", 8)
            font_locked.setItalic(True)
            painter.setFont(font_locked)
            painter.drawText(QRectF(15, 42, width - 30, 15), Qt.AlignLeft | Qt.AlignVCenter, f"Blocked Salon ({incomplete_count})")

    @staticmethod
    def draw_connection_path(start_pt, end_pt, layout_dir):
        path = QPainterPath()
        path.moveTo(start_pt)
        if layout_dir == 0:
            ctrl1 = QPointF(start_pt.x() + 80, start_pt.y() - 30)
            ctrl2 = QPointF(end_pt.x() - 80, end_pt.y() + 30)
        else:
            ctrl1 = QPointF(start_pt.x() - 30, start_pt.y() + 80)
            ctrl2 = QPointF(end_pt.x() + 30, end_pt.y() - 80)
        path.cubicTo(ctrl1, ctrl2, end_pt)
        return path

    @staticmethod
    def draw_background(painter, rect):
        painter.fillRect(rect, QColor("#FDFBF7"))
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen_pattern = QPen(QColor("#F5EFEB"), 1.0, Qt.SolidLine)
        painter.setPen(pen_pattern)
        
        step = 100
        left = int(rect.left()) - (int(rect.left()) % step)
        right = int(rect.right())
        top = int(rect.top()) - (int(rect.top()) % step)
        bottom = int(rect.bottom())
        
        for x in range(left, right + step, step):
            for y in range(top, bottom + step, step):
                painter.drawArc(x, y, 60, 60, 0, 180 * 16)
                painter.drawArc(x + 30, y + 30, 60, 60, 180 * 16, 180 * 16)


class TerminalTheme(BaseTheme):
    canvas_bg = "#030704" 
    line_width = 2
    font_family = "Consolas"
    inspector_title = "节点属性"
    inspector_placeholder = "选择任意节点\n以配置。"

    button_texts = {
        "back": "返回",
        "export": "导出",
        "import": "导入",
        "add": "添加子节点",
        "delete": "删除节点",
        "move_up": "向上/前移",
        "move_down": "向下/后移",
        "prereq": "设置前置",
        "settings": "设置"
    }

    desktop_texts = {
        "title": "我的书架",
        "subtitle": "",
        "new_btn": "新建",
        "import_btn": "导入",
        "settings_btn": "设置"
    }

    qss = """
    QMainWindow { background-color: #050A05; }
    QLabel { color: #00FF66; font-family: "Consolas", monospace; font-size: 13px; font-weight: bold; }
    QPushButton {
        background-color: #030704; color: #00FF66; border: 1.5px solid #00FF66;
        border-radius: 0px; padding: 6px 12px; font-family: "Consolas", monospace; font-weight: bold;
    }
    QPushButton:hover { background-color: #00FF66; color: #030704; }
    QPushButton#dangerButton { background-color: #3a0808; color: #FF3333; border-color: #FF3333; }
    QPushButton#dangerButton:hover { background-color: #FF3333; color: #030704; }
    QDialog { background-color: #030704; border: 2px solid #00FF66; }
    QWidget#inspectorPanel { background-color: #050A05; border-left: 2px solid #00FF66; }
    
    QLineEdit, QTextEdit { 
        background-color: #030704; color: #00FF66; border: 1.5px solid #00FF66; border-radius: 0px; padding: 6px; 
        font-family: "Consolas", monospace;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #FFFFFF; }
    
    QListWidget {
        background-color: #030704; color: #00FF66; border: 1.5px solid #00FF66; border-radius: 0px; padding: 4px;
        font-family: "Consolas", monospace;
    }
    QListWidget::item {
        padding: 4px; border-bottom: 1px dashed #005522; color: #00CC55; font-size: 11px;
    }
    QListWidget::item:hover {
        background-color: #005522; color: #FFFFFF;
    }
    QListWidget::item:selected {
        background-color: #00FF66; color: #030704;
    }

    QSplitter::handle { background-color: #00FF66; }
    QSplitter::handle:horizontal { width: 6px; }
    QSplitter::handle:vertical { height: 6px; }
    QSplitter::handle:hover { background-color: #FFFFFF; }
    QCheckBox { color: #00FF66; font-family: "Consolas"; font-size: 13px; }
    QCheckBox::indicator { width: 14px; height: 14px; background-color: #030704; border: 1.5px solid #00FF66; border-radius: 0px; }
    QCheckBox::indicator:checked { background-color: #00FF66; border-color: #00FF66; }
    QComboBox { background-color: #030704; color: #00FF66; border: 1.5px solid #00FF66; border-radius: 0px; padding: 6px 12px; min-width: 200px; }
    QComboBox QAbstractItemView { background-color: #030704; color: #00FF66; selection-background-color: #005522; }

    QSlider::groove:horizontal {
        border: 1px solid #00FF66;
        height: 6px;
        background: #030704;
        border-radius: 0px;
    }
    QSlider::handle:horizontal {
        background: #00FF66;
        border: 1px solid #FFFFFF;
        width: 14px;
        margin-top: -4px;
        margin-bottom: -4px;
        border-radius: 0px;
    }
    QSlider::handle:horizontal:hover { background: #FFFFFF; }
    """

    @staticmethod
    def get_line_color(is_child_locked):
        return QColor("#551111") if is_child_locked else QColor("#00FF66")

    @staticmethod
    def paint_node(painter, node, is_locked, is_selected, width, height, incomplete_count=0):
        is_strict = getattr(node, 'node_type', 'standard') == 'strict'
        
        if is_locked:
            bg_color = QColor("#080202")      
            border_color = QColor("#772222")  
            text_color = QColor("#aa4444")    
        else:
            bg_color = QColor("#020502")      
            border_color = QColor("#00FF66")  
            text_color = QColor("#00FF66")    

        painter.fillRect(0, 0, width, height, bg_color)

        if is_selected:
            glow_color = QColor("#FF3333") if is_locked else QColor("#00FF66")
            glow_color.setAlpha(120)
            painter.setPen(QPen(glow_color, 4))
            painter.drawRect(-1, -1, width + 2, height + 2)
            border_pen = QPen(QColor("#FFFFFF"), 1.5)
        else:
            border_pen = QPen(border_color, 1.0, Qt.DashLine if is_locked else Qt.SolidLine)
        
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, width, height)

        raster_line_color = QColor(60, 10, 10, 30) if is_locked else QColor(0, 50, 20, 40)
        painter.setPen(QPen(raster_line_color, 1))
        for raster_y in range(3, height, 4):
            painter.drawLine(1, raster_y, width - 1, raster_y)

        if is_locked and incomplete_count > 0:
            painter.setPen(QPen(QColor("#FF3333"), 1))
            font_req = QFont("Consolas", 7)
            font_req.setBold(True)
            painter.setFont(font_req)
            painter.drawText(QRectF(width - 55, 5, 50, 12), Qt.AlignRight, f"LCK:{incomplete_count}")

        if is_strict and not is_locked and node.progress < 100:
            painter.setPen(QPen(QColor("#FF3333"), 1.0))
            font_strict = QFont("Consolas", 7)
            font_strict.setBold(True)
            painter.setFont(font_strict)
            painter.drawText(QRectF(width - 40, 5, 35, 12), Qt.AlignRight, "[STRICT]")

        if not is_locked and node.progress == 100:
            painter.setPen(QPen(QColor("#00FF66"), 1.0))
            font_secured = QFont("Consolas", 8)
            font_secured.setBold(True)
            painter.setFont(font_secured)
            painter.drawText(QRectF(width - 65, 5, 60, 15), Qt.AlignRight | Qt.AlignVCenter, "[SECURED]")

        painter.setPen(text_color)
        font_terminal = QFont("Consolas", 9)
        font_terminal.setBold(True)
        painter.setFont(font_terminal)
        
        display_name = f">> {node.name}"
        right_margin = 60 if is_locked else 15
        text_rect = QRectF(10, 8, width - 10 - right_margin, 20)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_name)

        if not is_locked:
            bar_w = width - 20
            painter.setPen(QPen(QColor("#005522"), 1))
            painter.drawRect(10, 32, bar_w, 10)
            
            filled_w = int(bar_w * (node.progress / 100.0))
            segment_step = 8
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#00FF66")))
            
            for seg_x in range(12, 12 + filled_w - segment_step, segment_step):
                painter.drawRect(seg_x, 34, 6, 6)

            painter.setPen(QPen(QColor("#00AA44"), 1))
            font_status = QFont("Consolas", 7)
            painter.setFont(font_status)
            status_hex = f"SYS_OK_0x{node.progress:02X}" if node.progress > 0 else "SYS_AWAIT"
            painter.drawText(QRectF(10, 48, bar_w, 15), Qt.AlignLeft | Qt.AlignVCenter, f"{status_hex}")
            painter.drawText(QRectF(10, 48, bar_w, 15), Qt.AlignRight | Qt.AlignVCenter, f"{node.progress}%")
        else:
            painter.setPen(QPen(QColor("#aa4444"), 1))
            font_locked = QFont("Consolas", 7)
            font_locked.setBold(True)
            painter.setFont(font_locked)
            painter.drawText(QRectF(10, 40, width - 20, 15), Qt.AlignLeft | Qt.AlignVCenter, f">> LINK_LOCKED (REQ:{incomplete_count:02d})")

    @staticmethod
    def draw_connection_path(start_pt, end_pt, layout_dir):
        path = QPainterPath()
        path.moveTo(start_pt)
        if layout_dir == 0:
            mid_x = start_pt.x() + (end_pt.x() - start_pt.x()) / 2
            path.lineTo(mid_x, start_pt.y())
            path.lineTo(mid_x, end_pt.y())
            path.lineTo(end_pt.x(), end_pt.y())
        else:
            mid_y = start_pt.y() + (end_pt.y() - start_pt.y()) / 2
            path.lineTo(start_pt.x(), mid_y)
            path.lineTo(end_pt.x(), mid_y)
            path.lineTo(end_pt.x(), end_pt.y())
        return path

    @staticmethod
    def draw_background(painter, rect):
        painter.fillRect(rect, QColor("#030704"))
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen_radar = QPen(QColor(0, 45, 15, 35), 1.0, Qt.SolidLine)
        painter.setPen(pen_radar)
        painter.drawEllipse(QPointF(0, 0), 200, 200)
        painter.drawEllipse(QPointF(0, 0), 400, 400)
        painter.drawEllipse(QPointF(0, 0), 600, 600)
        
        painter.drawLine(-2000, 0, 2000, 0)
        painter.drawLine(0, -2000, 0, 2000)
        
        pen_grid = QPen(QColor(0, 30, 10, 25), 0.5)
        painter.setPen(pen_grid)
        grid_size = 80
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        for x in range(left, int(rect.right()) + grid_size, grid_size):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()) + grid_size, grid_size):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)


class SwissMinimalistTheme(BaseTheme):
    canvas_bg = "#F2F2F2"
    line_width = 1
    font_family = "Helvetica"
    inspector_title = "节点属性"
    inspector_placeholder = "选择任意节点\n以配置。"

    button_texts = {
        "back": "返回",
        "export": "导出",
        "import": "导入",
        "add": "添加子节点",
        "delete": "删除节点",
        "move_up": "向上/前移",
        "move_down": "向下/后移",
        "prereq": "设置前置",
        "settings": "设置"
    }

    desktop_texts = {
        "title": "我的书架",
        "subtitle": "",
        "new_btn": "新建",
        "import_btn": "导入",
        "settings_btn": "设置"
    }

    qss = """
    QMainWindow { background-color: #E6E6E6; }
    QLabel { color: #111111; font-family: "Helvetica", "Arial", sans-serif; font-size: 13px; font-weight: bold; text-transform: uppercase; }
    QPushButton {
        background-color: #F2F2F2; color: #111111; border: 1px solid #111111;
        border-radius: 0px; padding: 6px 12px; font-family: "Helvetica", "Arial"; font-weight: bold;
    }
    QPushButton:hover { background-color: #002FA7; color: #FFFFFF; border-color: #002FA7; }
    QPushButton#dangerButton { background-color: #000000; color: #FF3333; border-color: #FF3333; }
    QPushButton#dangerButton:hover { background-color: #FF3333; color: #FFFFFF; }
    QDialog { background-color: #F2F2F2; border: 1px solid #111111; border-radius: 0px; }
    QWidget#inspectorPanel { background-color: #E6E6E6; border-left: 1px solid #CCCCCC; }
    
    QLineEdit, QTextEdit { 
        background-color: #F2F2F2; color: #111111; border: 1px solid #111111; border-radius: 0px; padding: 6px; 
        font-family: "Helvetica", "Arial";
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #002FA7; }
    
    QListWidget {
        background-color: #F2F2F2; color: #111111; border: 1px solid #CCCCCC; border-radius: 0px; padding: 4px;
        font-family: "Helvetica", "Arial";
    }
    QListWidget::item {
        padding: 4px; border-bottom: 1px solid #E6E6E6; color: #333333; font-size: 11px;
    }
    QListWidget::item:hover {
        background-color: #E6E6E6; color: #000000;
    }
    QListWidget::item:selected {
        background-color: #002FA7; color: #FFFFFF;
    }

    QSplitter::handle { background-color: #CCCCCC; }
    QSplitter::handle:horizontal { width: 5px; }
    QSplitter::handle:vertical { height: 5px; }
    QSplitter::handle:hover { background-color: #002FA7; }
    QCheckBox { color: #111111; font-family: "Helvetica"; font-size: 13px; }
    QCheckBox::indicator { width: 14px; height: 14px; background-color: #F2F2F2; border: 1px solid #111111; border-radius: 0px; }
    QCheckBox::indicator:checked { background-color: #002FA7; border-color: #002FA7; }
    QComboBox { background-color: #F2F2F2; color: #111111; border: 1px solid #111111; border-radius: 0px; padding: 6px 12px; min-width: 200px; font-weight: bold; }
    QComboBox QAbstractItemView { background-color: #F2F2F2; color: #111111; selection-background-color: #002FA7; selection-color: #FFFFFF; }

    QSlider::groove:horizontal {
        border: 1px solid #111111;
        height: 4px;
        background: #F2F2F2;
        border-radius: 0px;
    }
    QSlider::handle:horizontal {
        background: #002FA7;
        width: 12px;
        height: 12px;
        margin-top: -4px;
        margin-bottom: -4px;
        border-radius: 0px;
    }
    QSlider::handle:horizontal:hover { background: #000000; }
    """

    @staticmethod
    def get_line_color(is_child_locked):
        return QColor("#D1D1D1") if is_child_locked else QColor("#111111")

    @staticmethod
    def paint_node(painter, node, is_locked, is_selected, width, height, incomplete_count=0):
        is_strict = getattr(node, 'node_type', 'standard') == 'strict'
        
        if is_locked:
            bg_color = QColor("#EAEAEA")
            line_pen = QPen(QColor("#CCCCCC"), 1)
            text_color = QColor("#888888")
        else:
            bg_color = QColor("#FFFFFF") if node.color == "#2d3748" else QColor(node.color)
            line_pen = QPen(QColor("#002FA7") if is_selected else QColor("#111111"), 1.2 if is_selected else 0.8)
            text_color = QColor("#111111")

        painter.setBrush(QBrush(bg_color))
        painter.setPen(line_pen)
        painter.drawRect(0, 0, width, height)

        if is_locked and incomplete_count > 0:
            painter.setBrush(QBrush(QColor("#000000")))
            painter.setPen(Qt.NoPen)
            painter.drawRect(width - 32, 0, 32, 12)
            painter.setPen(QColor("#FFFFFF"))
            font_req = QFont("Arial", 7)
            font_req.setBold(True)
            painter.setFont(font_req)
            painter.drawText(QRectF(width - 32, 0, 32, 12), Qt.AlignCenter, f"L.{incomplete_count}")

        if is_strict and not is_locked and node.progress < 100:
            painter.setBrush(QBrush(QColor("#111111")))
            painter.setPen(Qt.NoPen)
            painter.drawRect(width - 15, 6, 6, 6)

        if not is_locked and node.progress == 100:
            painter.setBrush(QBrush(QColor("#002FA7")))
            painter.setPen(Qt.NoPen)
            painter.drawRect(width - 25, 0, 25, 10)
            
            painter.setPen(QColor("#FFFFFF"))
            font_ok = QFont("Arial", 7)
            font_ok.setBold(True)
            painter.setFont(font_ok)
            painter.drawText(QRectF(width - 25, 0, 25, 10), Qt.AlignCenter, "OK")

        painter.setPen(text_color)
        
        font_helvetica = QFont("Arial", 9)
        font_helvetica.setBold(True)
        painter.setFont(font_helvetica)
        
        display_name = node.name.upper()
        right_margin = 35 if is_locked else 15
        text_rect = QRectF(10, 8, width - 10 - right_margin, 22)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_name)

        if not is_locked:
            prog_w = (width - 20) * (node.progress / 100.0)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawRect(10, height - 12, width - 20, 2)

            if node.progress > 0:
                painter.setBrush(QBrush(QColor("#002FA7")))
                painter.drawRect(10, height - 12, prog_w, 2)

            painter.setPen(QColor("#666666"))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(QRectF(10, 36, width - 20, 15), Qt.AlignLeft | Qt.AlignVCenter, f"P. {node.progress}%")
        else:
            painter.setPen(QColor("#999999"))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(QRectF(10, 36, width - 20, 15), Qt.AlignLeft | Qt.AlignVCenter, f"BLOCKED BY {incomplete_count} UNITS")

    @staticmethod
    def draw_connection_path(start_pt, end_pt, layout_dir):
        path = QPainterPath()
        path.moveTo(start_pt)
        if layout_dir == 0:
            mid_x = start_pt.x() + (end_pt.x() - start_pt.x()) / 2
            path.lineTo(mid_x, start_pt.y())
            path.lineTo(mid_x, end_pt.y())
            path.lineTo(end_pt.x(), end_pt.y())
        else:
            mid_y = start_pt.y() + (end_pt.y() - start_pt.y()) / 2
            path.lineTo(start_pt.x(), mid_y)
            path.lineTo(end_pt.x(), mid_y)
            path.lineTo(end_pt.x(), end_pt.y())
        return path

    @staticmethod
    def draw_background(painter, rect):
        painter.fillRect(rect, QColor("#F2F2F2"))
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen_grid = QPen(QColor("#E1E1E1"), 0.5, Qt.SolidLine)
        painter.setPen(pen_grid)
        
        step = 100
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)
        
        for x in range(left, int(rect.right()) + step, step):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()) + step, step):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)