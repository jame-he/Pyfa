from gui.contextMenu import ContextMenuUnconditional


class ImplantSetAdd(ContextMenuUnconditional):

    def display(self, callingWindow, srcContext):

        if not hasattr(callingWindow, 'implants'):
            return False

        implantList = callingWindow.implants
        if not implantList or len(implantList) == 0:
            return False

        return srcContext in ("implantItemMisc", "implantItemMiscChar")

    def getText(self, callingWindow, context):
        return "Add As New Implant Set"

    def activate(self, callingWindow, fullContext, i):
        implantList = callingWindow.implants
        callingWindow.mainFrame.OnShowImplantSetEditor(None, implantList)


ImplantSetAdd.register()
