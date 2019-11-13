# noinspection PyPackageRequirements
import wx

import gui.mainFrame
from gui.auxFrame import AuxiliaryFrame
from gui.contextMenu import ContextMenuSingle
from service.ammo import Ammo
from service.market import Market


class GraphFitAmmoPicker(ContextMenuSingle):

    def __init__(self):
        self.mainFrame = gui.mainFrame.MainFrame.getInstance()

    def display(self, callingWindow, srcContext, mainItem):
        if srcContext != 'graphFitList':
            return False
        if mainItem is None or not mainItem.isFit:
            return False
        if callingWindow.graphFrame.getView().internalName != 'dmgStatsGraph':
            return False
        return True

    def getText(self, callingWindow, itmContext, mainItem):
        return 'Plot with Different Ammo...'

    def activate(self, callingWindow, fullContext, mainItem, i):
        window = AmmoPicker(callingWindow, mainItem.item)
        window.Show()


GraphFitAmmoPicker.register()


class AmmoPicker(AuxiliaryFrame):

    def __init__(self, parent, fit):
        super().__init__(parent, title='Choose Different Ammo', style=wx.DEFAULT_DIALOG_STYLE)

        indent = 15
        mods = self.getMods(fit)
        drones = self.getDrones(fit)
        fighters = self.getFighters(fit)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        firstRadio = True

        def addRadioButton(text):
            nonlocal firstRadio
            if not firstRadio:
                rb = wx.RadioButton(self, wx.ID_ANY, text, style=wx.RB_GROUP)
                rb.SetValue(True)
                firstRadio = True
            else:
                rb = wx.RadioButton(self, wx.ID_ANY, text)
                rb.SetValue(False)
            mainSizer.Add(rb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        def addCheckbox(text, indentLvl=0):
            cb = wx.CheckBox(self, -1, text)
            mainSizer.Add(cb, 0, wx.EXPAND | wx.LEFT, 5 + indent * indentLvl)

        def addLabel(text, indentLvl=0):
            label = wx.StaticText(self, wx.ID_ANY, text)
            mainSizer.Add(label, 0, wx.EXPAND | wx.LEFT, 5 + indent * indentLvl)

        for modInfo, ammo in mods:
            text = '\n'.join('{}x {}'.format(amount, item.name) for item, amount in modInfo)
            addRadioButton(text)
            # Get actual module, as ammo getters need it
            mod = next((m for m in fit.modules if m.itemID == next(iter(modInfo))[0].ID), None)
            modType, ammoTree = Ammo.getInstance().getModuleStructuredAmmo(mod)
            if modType in ('ddTurret', 'ddMissile'):
                for ammoCatName, ammos in ammoTree.items():
                    addLabel('{}:'.format(ammoCatName.capitalize()), indentLvl=1)
                    for ammo in ammos:
                        addCheckbox(ammo.name, indentLvl=2)
            else:
                for ammoCatName, ammos in ammoTree.items():
                    for ammo in ammos:
                        addCheckbox(ammo.name, indentLvl=1)
        if drones:
            addRadioButton('Drones')
        if fighters:
            addRadioButton('Fighters')

        self.SetSizer(mainSizer)
        self.SetMinSize((346, 156))
        self.Bind(wx.EVT_CHAR_HOOK, self.kbEvent)

    def kbEvent(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE and event.GetModifiers() == wx.MOD_NONE:
            self.Close()
            return
        event.Skip()

    def getMods(self, fit):
        sMkt = Market.getInstance()
        sAmmo = Ammo.getInstance()
        loadableChargesCache = {}
        # Modules, format: {frozenset(ammo): {item: count}}
        modsPrelim = {}
        if fit is not None:
            for mod in fit.modules:
                if not mod.canDealDamage():
                    continue
                typeID = mod.item.ID
                if typeID not in loadableChargesCache:
                    loadableChargesCache[typeID] = sAmmo.getModuleFlatAmmo(mod)
                charges = loadableChargesCache[typeID]
                # We're not interested in modules which contain no charges
                if charges:
                    data = modsPrelim.setdefault(frozenset(charges), {})
                    if mod.item not in data:
                        data[mod.item] = 0
                    data[mod.item] += 1
        # Format: [([(item, count), ...], frozenset(ammo)), ...]
        modsFinal = []
        for charges, itemCounts in modsPrelim.items():
            modsFinal.append((
                # Sort items within group
                sorted(itemCounts.items(), key=lambda i: sMkt.itemSort(i[0], reverseMktGrp=True), reverse=True),
                charges))
        # Sort item groups
        modsFinal.sort(key=lambda i: sMkt.itemSort(i[0][0][0], reverseMktGrp=True), reverse=True)
        return modsFinal

    def getDrones(self, fit):
        drones = set()
        if fit is not None:
            for drone in fit.drones:
                if drone.item is None:
                    continue
                # Drones are our "ammo", so we want to pick even those which are inactive
                if drone.canDealDamage(ignoreState=True):
                    drones.add(drone)
                    continue
                if {'remoteWebifierEntity', 'remoteTargetPaintEntity'}.intersection(drone.item.effects):
                    drones.add(drone)
                    continue
        return drones

    def getFighters(self, fit):
        fighters = set()
        if fit is not None:
            for fighter in fit.fighters:
                if fighter.item is None:
                    continue
                # Fighters are our "ammo" as well
                if fighter.canDealDamage(ignoreState=True):
                    fighters.add(fighter)
                    continue
                for ability in fighter.abilities:
                    if not ability.active:
                        continue
                    if ability.effect.name == 'fighterAbilityStasisWebifier':
                        fighters.add(fighter)
                        break
        return fighters
