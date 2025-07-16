import sys, random, math
from PyQt5.QtCore    import Qt, QTimer
from PyQt5.QtGui     import QPixmap, QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QListWidget,
                             QListWidgetItem, QMessageBox, QProgressBar,
                             QGroupBox, QGridLayout, QMenu, QAction)

import main  # 我们写好的后端

##############################################################################
# 一些工具
##############################################################################
def fmt(num):         # 大数字友好显示
    if num < 1e4: return str(num)
    if num < 1e6: return f"{num/1e3:.1f}K"
    if num < 1e9: return f"{num/1e6:.1f}M"
    return f"{num/1e9:.1f}B"

##############################################################################
# 主窗口
##############################################################################
class RatClickerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rat Clicker – PyQt5 前端")
        self.resize(600, 700)

        # 后端对象
        self.player = main.player()
        self.rat    = main.rat()

        # 主部件
        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)

        # 1. 状态栏
        self.init_status_bar(vbox)

        # 2. 点击区
        self.rat_btn = QPushButton()
        self.rat_btn.setFixedSize(120, 120)
        self.rat_btn.setStyleSheet("""
            QPushButton{
                border-image: url(rat.png);   /* 根目录下的 rat.png */
                border: none;
            }
            QPushButton:hover{
                border-image: url(rat.png);   /* 如需悬停图再换路径 */
            }
            QPushButton:pressed{
                border-image: url(rat.png);   /* 如需点击态再换路径 */
            }
        """)
        self.rat_btn.clicked.connect(self.on_rat_click)
        vbox.addWidget(self.rat_btn, alignment=Qt.AlignCenter)

        # 3. 装备栏
        self.init_equipment_box(vbox)

        # 4. 物品栏
        self.init_inventory_box(vbox)

        # 5. 日志
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(80)
        vbox.addWidget(QLabel("日志"))
        vbox.addWidget(self.log_list)

        # 定时把后端的 logs 搬到 GUI
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.sync_logs)
        self.log_timer.start(200)

        self.refresh_ui()

        # 生命值恢复
        self.regen_timer = QTimer(self)
        self.regen_timer.timeout.connect(self.regenerate_health)
        self.regen_timer.start(2000)  # 2000 ms

    ##########################################################################
    # 初始化子区块
    ##########################################################################
    def init_status_bar(self, parent_layout):
        self.lbl_lvl  = QLabel()
        self.lbl_exp  = QLabel()
        self.lbl_gold = QLabel()
        self.lbl_hp   = QLabel()
        self.exp_bar  = QProgressBar()
        self.exp_bar.setMaximumHeight(6)
        for w in (self.lbl_lvl, self.lbl_exp, self.lbl_gold, self.lbl_hp, self.exp_bar):
            w.setAlignment(Qt.AlignCenter)

        box = QGroupBox("状态")
        grid = QGridLayout(box)
        grid.addWidget(self.lbl_lvl,  0, 0)
        grid.addWidget(self.lbl_exp,  0, 1)
        grid.addWidget(self.lbl_gold, 1, 0)
        grid.addWidget(self.lbl_hp,   1, 1)
        grid.addWidget(self.exp_bar,  2, 0, 1, 2)
        parent_layout.addWidget(box)

    def init_equipment_box(self, parent_layout):
        self.equip_labels = []
        box = QGroupBox("装备")
        h = QHBoxLayout(box)
        for slot_name, _ in self.player.slot.EquipmentSlot:
            lbl = QLabel(slot_name.title())
            lbl.setFixedSize(64, 64)
            lbl.setFrameShape(QLabel.Box)
            lbl.setAlignment(Qt.AlignCenter)
            h.addWidget(lbl)
            self.equip_labels.append(lbl)
        parent_layout.addWidget(box)

    def init_inventory_box(self, parent_layout):
        box = QGroupBox("背包")
        v = QVBoxLayout(box)
        self.inv_list = QListWidget()
        self.inv_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.inv_list.customContextMenuRequested.connect(self.inventory_context_menu)
        v.addWidget(self.inv_list)
        parent_layout.addWidget(box)

    ##########################################################################
    # 事件
    ##########################################################################
    def on_rat_click(self):
        self.rat.click(self.player)
        self.refresh_ui()

    def sync_logs(self):
        logs = self.player.logs.LogList.copy()
        for text in logs:
            self.log_list.addItem(text)
            self.log_list.scrollToBottom()
            self.player.logs.LogList.remove(text)

    def refresh_ui(self):
        self.inv_list.clear()
        p = self.player
        rarity_map = {"1": "Common", "2": "Rare", "3": "Legendary", "4": "Demonic"}
        for it in p.CurrentStorage:
            if it.type == "equipment":
                slot_idx = int(it.id[2])
                slot_name = p.slot.EquipmentSlot[slot_idx][0]
                rarity_code = it.id[0]
                rarity = rarity_map.get(rarity_code, "Unknown")
                txt = f"[{rarity}] {slot_name.title()} +{it.value}"
            else:
                txt = f"{it.id} x{it.value}"
            QListWidgetItem(txt, self.inv_list).setData(Qt.UserRole, it)

        # 装备
        for idx, (slot_name, item_obj) in enumerate(p.slot.EquipmentSlot):
            if item_obj:                 # 已装备
                self.equip_labels[idx].setText(f"{slot_name.title()}\n{item_obj.value}")
            else:
                self.equip_labels[idx].setText(slot_name.title())

        # 状态栏
        self.lbl_lvl.setText(f"等级: {p.level}")
        self.lbl_exp.setText(f"经验值: {p.exp}/{int(p.CurrentExpBarLength)}")
        self.lbl_gold.setText(f"金币: {fmt(p.gold)}")
        self.lbl_hp.setText(f"生命值: {p.CurrentHealth}/{p.MaxHealth}")
        self.exp_bar.setValue(int(p.exp / p.CurrentExpBarLength * 100))

    ##########################################################################
    # 背包右键菜单：装备 / 使用 / 出售（示例实现“装备”）
    ##########################################################################
    def inventory_context_menu(self, pos):
        item = self.inv_list.itemAt(pos)
        if not item:
            return
        it_obj = item.data(Qt.UserRole)

        menu = QMenu(self)
        if it_obj.type == "equipment":
            menu.addAction("装备")
            menu.addAction("出售")
            menu.addAction("加入合成区")
        elif it_obj.type == "materials":
            menu.addAction("出售")
            menu.addAction("加入合成区")
        elif it_obj.type == "accessory":
            menu.addAction("出售")
            menu.addAction("加入合成区")
        else:
            menu.addAction("出售")

        action = menu.exec_(self.inv_list.mapToGlobal(pos))
        if action:
            self.handle_inv_action(action.text(), it_obj)

    def handle_inv_action(self, action, it_obj):
        p = self.player
        if action == "装备":
            # 找下标
            try:
                idx = p.CurrentStorage.index(it_obj)
            except ValueError:
                return
            p.equip(idx)
        elif action == "出售":
            if it_obj in p.CurrentStorage:
                if it_obj.type != "materials":
                    sell_price = max(1, int(it_obj.value * 0.3))  # 30% 价值
                    p.gold += sell_price
                    p.CurrentStorage.remove(it_obj)
                else:
                    p.gold += 1000
                self.refresh_ui()
        elif action == "加入合成区":
            if  not [] in p.slot.CrafterSlot:
                for sl in p.slot.CrafterSlot:
                    if sl == []:
                        sl = it_obj
                    p.CurrentStorage.remove(it_obj)
            else:
                p.logs.NewLog("合成区已满")


    def regenerate_health(self):
        p = self.player
        if p.CurrentHealth >= p.MaxHealth:
            return
        regen = max(1, int(p.MaxHealth * 0.01))  # 每跳 1%，至少 1 点
        p.CurrentHealth = min(p.MaxHealth, p.CurrentHealth + regen)
        self.refresh_ui()

##############################################################################
# 运行
##############################################################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RatClickerWindow()
    win.show()
    sys.exit(app.exec_())