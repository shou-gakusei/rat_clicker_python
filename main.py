import math
import sys
import PyQt5
import numpy
import random


rat_png_path = "rat.png"
# id分三位：
# 第一位 0：特殊 1：常见 2：稀有 3：传奇 4：恶魔
# 第二位 0：药水 1：装备 2：材料 3：饰品 4：升级（合成后自动装备）
# 第三位 0：血药 1：蓝药
# 第三位 0：长剑 1：胸甲 2：头盔 3：魔杖 4：手套
# 第三位 0：水晶 1：煤炭 2：爪子 3：翅膀 4：眼睛 5：腿部 6：羽毛
# 第三位 0：红宝石项链 1：银项链 2：钻石项链 3：蓝宝石项链 4：恶魔项链
# 合成配方这里一共五种(序号对应ID)
# 1："magna potion"              对应原游戏中2常见手套+1常见法杖+20血药=20蓝药
# 2："legendary equipment"       对应原游戏中同等类型常见装备+稀有装备+水晶=传奇装备
# 3："devil equipment"           对应原游戏中常见装备+煤炭+对应材料=恶魔装备
# 4："enhanced devil equipment"  对应原游戏中稀有装备+煤炭+对应材料=恶魔装备（数值更高且有解锁条件）
# 5："upgrade accessories"       对应原游戏中那5个独特升级槽

class item:
    def __init__(self,type,id,value):
        self.type = type
        self.id = id
        self.value = value

class slot:
    def __init__(self):
        self.EquipmentSlot = [["sward", []],
                              ["armor", []],
                              ["helmet",[]],
                              ["wand",  []],
                              ["gloves",[]]]
        self.CrafterSlot = [[],[],[]]
        self.UpgradeSlot = [[],[],[],[],[]]

class recipe:
    def __init__(self,type,id):
        self.type = type
        self.id = id

    def craft(self, item_input, player):
        items = [item_input[0].id, item_input[1].id, item_input[2].id]
        items.sort()
        if self.type == "magna potion" and items == ['113', '113', '114']:
            # 直接用输入ID判断是不是合成蓝药配方
            if player.potions[0]>=20:
                player.potions[0] -=20
                return item(type="potion",id="001",value=20)
            else:
                return False
        elif self.type == "legendary equipment":
            if items[0]=="020" and items[1][2] == items[2][2]:
                item_id = "31"+items[1][2]
                item_value = 2*item_input[1].value + item_input[2].value
                return item(type="equipment",id=item_id,value=item_value)
            else:
                return False
        elif self.type == "devil equipment":
            if items[0] == "021" and int(items[1][2])-int(items[2][2]) == 2 and items[1][0] == "1":
                item_id = "41"+items[2][2]
                item_value = 8 * item_input[2].value
                return item(type="equipment",id=item_id,value=item_value)
            else:
                return False
        elif player.slot.UpgradeSlot[3] != [] and self.type=="enhanced devil equipment":
            if items[0] == "021" and int(items[1][2])-int(items[2][2]) == 2 and items[1][0] == "2":
                item_id = "41" + items[2][2]
                item_value = 8 * item_input[2].value
                return item(type="equipment", id=item_id, value=item_value)
            else:
                return False
        elif self.type=="upgrade accessories":
            if items[0] == "020" and items[1] == "020" and items[2][1] == "3":
                item_id = "04"+items[2][2]
                return item(type="accessories", id=item_id, value=1)
        else:
            return False

class logs:
    def __init__(self):
        self.LogList = []
        self.MaxLength = 20
    def NewLog(self,log):
        self.LogList.append(str(log))
        if self.LogList.__len__()>20:
            self.LogList.pop(0)

class player:
    def __init__(self,  prestige=0):
        # 重生时保留的声望
        self.ActivePrestige = prestige
        # 基础属性
        self.level = 1
        self.exp = 0
        self.CurrentHealthPercentage = 100
        self.CurrentMangaPercentage = 100
        self.gold = 0
        self.attack = 1
        self.defence = 0
        self.magic = 0
        self.luck = 0
        self.FreeAttributePoints = 0
        self.CurrentStorage = []
        self.MaxStorage = 8
        self.slot = slot()
        self.merc = [["skeleton",0],
                     ['goblin',0],
                     ['golem',0],
                     ['dragon',0]]
        self.CurrentPotions = [0,0] # 第一位是血药第二位是蓝药
        # 隐藏数据
        self.ExtraAttack = 0
        self.ExtraDefence = 0
        self.ExtraMagic = 0
        self.ExtraLuck = 0
        self.MaxPotions = 999
        self.MaxManga = 100 # 仅和魔法挂钩
        self.CurrentManga = 100
        self.MaxHealth = 100 # 仅和等级挂钩
        self.CurrentHealth = 100
        self.logs = logs()
        self.ExpRate = 1.1
        self.CurrentExpBarLength = 100
        self.InactivePrestige = 0
        self.ALLRecipies = [recipe(type="enhanced devil equipment",id=4),
                            recipe(type="upgrade accessories",id=5),
                            recipe(type="magna potion",id=1),
                            recipe(type="legendary equipment",id=2),
                            recipe(type="devil equipment",id=3)]
        self.UnlockedRecipies = []

    def GetExp(self,exp,rat):
        self.exp +=exp
        if self.exp >= self.CurrentExpBarLength:
            self.level += 1
            if int(self.level/10) -int((self.level-1)/10) != 0:
                rat.difficulty +=1
                rat.atk =self.level
                self.logs.NewLog("老鼠变得更强大了！")
                self.FreeAttributePoints += 1
            self.exp -= self.CurrentExpBarLength
            self.CurrentExpBarLength *= self.ExpRate
            self.CurrentExpBarLength = int(self.CurrentExpBarLength)
            self.MaxHealth += 100
        if self.level>=100 and self.UnlockedRecipies == []:
            self.UnlockedRecipies = [recipe(type="magna potion",id=1),
                                     recipe(type="legendary equipment",id=2),
                                     recipe(type="devil equipment",id=3)]

    def GetItem(self, GotItem):
        if len(self.CurrentStorage) >= self.MaxStorage:
            self.logs.NewLog("背包已满")
            return None

        if GotItem.type == "potion":
            idx = int(GotItem.id[2])
            if self.CurrentPotions[idx] < self.MaxPotions:
                self.CurrentPotions[idx] += 1
            else:
                self.logs.NewLog("药水已到达堆叠上限")

        elif GotItem.type == "materials":
            # 材料可堆叠
            for it in self.CurrentStorage:
                if it.id == GotItem.id and it.type == "materials":
                    it.value += GotItem.value
                    return
            self.CurrentStorage.append(GotItem)

        elif GotItem.type == "equipment":
            # 装备不可堆叠，直接添加
            self.CurrentStorage.append(GotItem)

        elif GotItem.type == "accessory":
            self.CurrentStorage.append(GotItem)

        else:
            self.CurrentStorage.append(GotItem)

    def GetPotion(self,GotPotion):
        if self.CurrentPotions[int(GotPotion.id[2])] >= self.MaxPotions:
            self.logs.NewLog(log="背包已满")
        else:
            self.CurrentPotions[int(GotPotion.id[2])] += 1

    def equip(self,index):
        equipment_to_equip = self.CurrentStorage[index]
        equip_slot = equipment_to_equip.id[2]
        if equipment_to_equip.type == "equipment":
            equipment_slot = str(equipment_to_equip.id[2])
            current_equipment = self.slot.EquipmentSlot[int(equipment_slot)][1]
            if current_equipment == []:
                self.CurrentStorage.pop(index)
                self.slot.EquipmentSlot[int(equip_slot)][1] = equipment_to_equip
                if equipment_slot == '0':
                    self.attack += equipment_to_equip.value
                elif equipment_slot == '1' or equipment_slot == '2':
                    self.defence += equipment_to_equip.value
                elif equipment_slot == '3':
                    self.magic += equipment_to_equip.value
                elif equipment_slot == '4':
                    self.luck += equipment_to_equip.value
                else:
                    print("未知装备类型")
            else:
                self.CurrentStorage[index] = current_equipment
                self.slot.EquipmentSlot[int(equip_slot)][1] = equipment_to_equip
                if equipment_slot == '0':
                    self.attack -= current_equipment.value
                    self.attack += equipment_to_equip.value
                elif equipment_slot == '1' or equipment_slot == '2':
                    self.defence -= current_equipment.value
                    self.defence += equipment_to_equip.value
                elif equipment_slot == '3':
                    self.magic -= current_equipment.value
                    self.magic += equipment_to_equip.value
                elif equipment_slot == '4':
                    self.luck -= current_equipment.value
                    self.luck += equipment_to_equip.value
                else:
                    print("未知装备类型")

    def ToCrafterSlot(self,index):
        crafter_empty_slot_count = [slot for slot in self.slot.CrafterSlot].__len__()
        if crafter_empty_slot_count !=0:
            if self.CurrentStorage[index].type == "materials":
                if self.CurrentStorage[index].value !=1:
                    self.CurrentStorage[index].value -= 1
                else:
                    self.CurrentStorage.pop(index)
                self.slot.CrafterSlot[3-crafter_empty_slot_count] = (
                    item(type="materials",id=self.CurrentStorage[index].id,value=1))
            else:
                self.CurrentStorage.pop(index)
                self.slot.CrafterSlot[3-crafter_empty_slot_count] = (
                    item(type=self.CurrentStorage[index].type,id=self.CurrentStorage[index].id,value=1))

    def ClearCrafterSlot(self):
        for item in self.slot.CrafterSlot:
            if item != []:
                self.GetItem(item)

    def CraftByRecipe(self):
        crafter_empty_slot_count = [slot for slot in self.slot.CrafterSlot].__len__()
        if crafter_empty_slot_count !=0:
            self.logs.NewLog("请填充所需要的材料")
        else:
            create_success = False
            for recipe in self.UnlockedRecipies:
                result = recipe.craft(item_input=self.slot.CrafterSlot,player=self)
                if result:
                    player.GetItem(result)
                    create_success = True
                    self.logs.NewLog("成功按照"+recipe.type+"配方制作了"+result.type)
            if not create_success:
                self.logs.NewLog("制作失败")

    def specialize(self,TargetStats):
        if self.FreeAttributePoints == 0:
            self.logs.NewLog("你没有可用的属性点！")
        else:
            if TargetStats == "attack":
                self.ExtraAttack += 1
                self.attack += 1
            elif TargetStats == "defend":
                self.ExtraDefence += 1
                self.defence += 1
            elif TargetStats == "magic":
                self.ExtraMagic += 1
                self.magic += 1
            else:
                self.ExtraLuck += 1
                self.luck += 1

    def respec(self):
        if self.gold >= 1*10**6:
            self.gold -=1*10**6
            self.attack -= self.ExtraAttack
            self.defence -= self.ExtraDefence
            self.magic -= self.ExtraMagic
            self.luck -= self.ExtraLuck
            self.ExtraAttack = 0
            self.ExtraDefence = 0
            self.ExtraMagic = 0
            self.ExtraLuck = 0
        else:
            self.logs.NewLog("你的金币不足！")


class rat:
    def __init__(self):
        self.difficulty = 1
        self.atk = 1
        self.BasePotionDrop = 0.085
        self.MagmaPotionPercentage = 0.05
        self.BaseGoldDrop = 0.8
        self.BaseLoc = 0
        self.BaseScale = 0.15
        self.BaseEquipmentDrop = 1/25
        self.RareEquipmentDrop = 1/6
        self.LegendaryEquipmentDrop = 1/6
        self.BaseEquipmentValueFactor = 10
        self.BaseEquipmentRandomFactor = 5
        self.BaseMaterialDrop = 1/1000
        self.CoalDrop = 1/20
        self.CrystalDrop = 1/10
        self.AccessoriesDrop = 1/100

    def click(self,player):
        if player.defence < self.atk:
            player.CurrentHealth -= self.atk-player.defence
        else:
            player.CurrentHealth -= 1
        player.GetExp(exp=player.attack,rat=self)
        player.gold += int(player.attack+self.BaseGoldDrop+numpy.random.normal(loc=self.BaseLoc,scale=self.BaseScale))
        if player.CurrentHealth <= 0:
            player.gold = 0
            player.CurrentHealth = 0
        # 用自带的RANDOM库做药水掉落和物品掉落
        potion_list_drop = ["no-drop","drop"]
        potion_drop_probability = [1-self.BasePotionDrop,self.BasePotionDrop]
        potion_drop_result = random.choices(potion_list_drop,potion_drop_probability)
        # 判断是否掉落药水并给出药水种类
        if potion_drop_result == ['drop']:
            potion_probability_list =  [1-self.MagmaPotionPercentage,self.MagmaPotionPercentage]
            potion_list = ["health_potion","magma_potion"]
            potion_result = random.choices(potion_list, potion_probability_list)
            if potion_result == "magma_potion":
                player.GetPotion(GotPotion=item(type="potion", id="001", value=1))
            else:
                player.GetPotion(GotPotion=item(type="potion", id="000", value=1))
        equipment_list_drop = ["no-drop", "drop"]
        e = math.e
        current_equipment_drop = self.BaseEquipmentDrop+((e**math.log(player.luck+1))-(e**(-math.log(player.luck+1)))/
                                      (e**math.log(player.luck+1)+e**(-math.log(player.luck+1))))
        equipment_drop_probability = [1-current_equipment_drop,current_equipment_drop]
        equipment_drop_result = random.choices(equipment_list_drop,equipment_drop_probability)
        # 判断是否掉落装备并按稀有度划分数值
        if equipment_drop_result == ['drop']:
            equipment_type_list = [0,1,2,3,4]
            equipment_probability = [0.2,0.2,0.2,0.2,0.2]
            equipment_type = random.choices(equipment_type_list,equipment_probability)
            equipment_base_value = int(self.difficulty*self.BaseEquipmentValueFactor+
                                    numpy.random.normal(self.difficulty*self.BaseEquipmentValueFactor,
                                                        self.difficulty*self.BaseEquipmentRandomFactor))
            if equipment_type == [0]:
                equipment_type_code = 0
            elif equipment_type == [1]:
                equipment_type_code = 1
                equipment_base_value *= 1.1
            elif equipment_type == [2]:
                equipment_type_code = 2
                equipment_base_value *= 0.65
                # 头盔防御力惩罚
            elif equipment_type == [3]:
                equipment_type_code = 3
            else:
                equipment_type_code = 4
            rare_list = ["common", "rare"]
            rare_probability = [1 - self.RareEquipmentDrop, self.RareEquipmentDrop]
            rare_result = random.choices(rare_list,rare_probability)
            if rare_result == "rare":
                legendary_list = ["rare","legendary"]
                legendary_probability = [1 - self.LegendaryEquipmentDrop, self.LegendaryEquipmentDrop]
                legendary_result = random.choices(legendary_list, legendary_probability)
                if legendary_result == "legendary":
                    equipment_id = "32"+str(equipment_type_code)
                    equipment_value = int(equipment_base_value * 4)
                else:
                    equipment_id = "22" + str(equipment_type_code)
                    equipment_value = int(equipment_base_value * 2)
            else:
                equipment_id = "12" + str(equipment_type_code)
                equipment_value = int(equipment_base_value)
            player.GetItem(item(type="equipment", id=equipment_id,value=equipment_value))
        material_list_drop = ["no-drop", "drop"]
        material_drop_probability = [1 - self.BaseMaterialDrop, self.BaseMaterialDrop]
        material_drop_result = random.choices(material_list_drop, material_drop_probability)
        if material_drop_result == "drop":
            # 判断是否掉落材料
            material_type = ["normal","crystal","coal"]
            material_probability = [1-self.CoalDrop-self.CrystalDrop,self.CrystalDrop,self.CoalDrop]
            material_type_result = random.choices(material_type,material_probability)
            if material_type_result == "normal":
                normal_material_type = ["claw","wing","eye","leg","feather"]
                normal_material_probability = [0.2,0.2,0.2,0.2,0.2]
                normal_material_result = random.choices(normal_material_type,normal_material_probability)
                if normal_material_result == "claw":
                    material_id = "022"
                if normal_material_result == "wing":
                    material_id = "023"
                if normal_material_result == "eye":
                    material_id = "024"
                if normal_material_result == "leg":
                    material_id = "025"
                if normal_material_result == "feather":
                    material_id = "026"
            elif material_type_result == "crystal":
                material_id = "020"
            else:
                material_id = "021"
            player.GetItem(item(type="materials",id=material_id,value=1))
        if any(recipe.id == 5 for recipe in player.UnlockedRecipies):
            # 先判断是不是开了护身符配方
            player_empty_upgrade_slot_count = [slot for slot in player.slot.UpgradeSlot if slot == []].__len__()
            # 查看玩家空着几个升级槽
            player_current_accessory = [item for item in player.CurrentStorage if item.type == "accessory"]
            # 检查仓库内的未合成护身符
            if player_empty_upgrade_slot_count != 0 and player_current_accessory == []:
                # 没未合成护身符+有空余升级槽
                accessory_list_drop = ["no-drop", "drop"]
                accessory_drop_probability = [1 - self.AccessoriesDrop, self.AccessoriesDrop]
                accessory_drop_result = random.choices(accessory_list_drop, accessory_drop_probability)
                if accessory_drop_result == "drop":
                    accessory_id = "03"+str(5-player_empty_upgrade_slot_count)
                    player.GetItem(type="accessory",id=accessory_id,value=1)




