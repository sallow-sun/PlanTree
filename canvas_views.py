# canvas_views.py
from PySide6.QtWidgets import QGraphicsView, QGraphicsItem
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QFont
from PySide6.QtCore import Qt, QRectF

class VisualNodeItem(QGraphicsItem):
    def __init__(self, node, is_locked, main_app):
        super().__init__()
        self.node = node
        self.is_locked = is_locked
        self.main_app = main_app
        self.width = 180
        self.height = 70
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def boundingRect(self):
        return QRectF(-10, -10, self.width + 20, self.height + 20)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        current_theme = self.main_app.get_current_theme_class()
        
        # 动态计算未完成的前置依赖数量
        incomplete_count = 0
        if self.is_locked:
            # 1. 计算显式配置的前置依赖中未完成的数量
            for prereq_id in self.node.prerequisites:
                prereq_node = self.main_app.all_nodes.get(prereq_id)
                if not prereq_node or prereq_node.progress < 100:
                    incomplete_count += 1
            
            # 2. 如果是严格模式，且显式依赖已满足（但仍锁定），则说明受限于隐式父级节点约束
            if incomplete_count == 0 and getattr(self.node, "node_type", "standard") == "strict":
                parent_node, _ = self.main_app._find_parent_and_siblings(self.main_app.root_node, self.node.node_id)
                if parent_node and parent_node.node_id != self.main_app.root_node.node_id:
                    if parent_node.progress < 100:
                        incomplete_count = 1
                        
        current_theme.paint_node(
            painter, self.node, self.is_locked, self.isSelected(), self.width, self.height, incomplete_count
        )

    def mousePressEvent(self, event):
        self.main_app.selected_node_id = self.node.node_id
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.main_app.inspector.inspect_name.setFocus()
        self.main_app.inspector.inspect_name.selectAll()


class InteractiveGraphicsView(QGraphicsView):
    def __init__(self, scene, main_app, parent=None):
        super().__init__(scene, parent)
        self.main_app = main_app 
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def keyPressEvent(self, event):
        if event.key() in [
            Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right,
            Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D,
            Qt.Key_Return, Qt.Key_Enter, Qt.Key_Delete
        ]:
            # 直接委托给主窗口的键盘处理事件，避免被 QGraphicsView 的滚动条吞噬
            self.main_app.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def drawBackground(self, painter, rect):
        current_theme = self.main_app.get_current_theme_class()
        current_theme.draw_background(painter, rect)