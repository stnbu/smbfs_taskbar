# -*- coding: utf-8 -*-
import wx
import wx.grid
import re
import os
from collections import namedtuple
from smbfs_taskbar.data import ApplicationData, USER_DB_FILE, APPLICATION_TITLE
from smbfs_taskbar import util
from smbfs_taskbar.icon import icon


CheckboxItem = namedtuple('CheckboxItem', ('attr_name','id', 'description'))
TextboxItem = namedtuple('TextboxItem', ('attr_name', 'id', 'size', 'description'))

class PreferencesDialog(wx.Dialog):

    _checkboxes = [
        CheckboxItem(attr_name='auto_mount', id=wx.NewId(), description="Automatically Mount"),
        CheckboxItem(attr_name='save_passwords', id=wx.NewId(), description="Save Passwords in Keychain"),
    ]

    _textboxes = [
        TextboxItem(attr_name='default_username', id=wx.NewId(), size=(140, -1), description="Default Username"),
        TextboxItem(attr_name='mount_command', id=wx.NewId(), size=(140, -1), description="mount Command"),
    ]

    def __init__(self, parent=None, id=-1, title=None, application_data=None, size=None, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent=parent, id=id, title=title, size=size, style=style)
        if application_data is None:
            self.application_data = ApplicationData(path=USER_DB_FILE)
        else:
            self.application_data = application_data
        self.mainPanel = wx.Panel(self)
        self.preferencesBox = wx.StaticBox(self.mainPanel, -1)

        for item in self._checkboxes:
            attr_name = item.attr_name
            id = item.id
            description = item.description
            _checkbox_widget = wx.CheckBox(self.mainPanel, id, description)
            setattr(self, attr_name, _checkbox_widget)

        for item in self._textboxes:
            attr_name = item.attr_name
            id = item.id
            size = item.size
            description = item.description
            _textbox_widget = wx.TextCtrl(self.mainPanel, id=id, size=size)
            setattr(self, attr_name, _textbox_widget)
            _textbox_widget.Bind(wx.EVT_KILL_FOCUS, self.onTextKillFocus)

        self.SetProperties()
        self.DoLayout()

        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def _last_resort_OnClose(self, event):
        self._get_grid(self.grid)
        # The checkboxes and stuff are updated pseudo-realtime, we'll skip them.

    def onTextKillFocus(self, event):
        obj = event.GetEventObject()
        item, = [i for i in self._textboxes if i.id == obj.Id]
        field_name = item.attr_name
        value = obj.GetValue()
        self.application_data.write(preferences={field_name: value})

    def OnClose(self, event):
        self._last_resort_OnClose(event)
        self.Destroy()

    def SetProperties(self):
        preferences = self.application_data.get_preferences()
        for item in self._checkboxes + self._textboxes:
            if not hasattr(self, item.attr_name):
                continue
            value = preferences[item.attr_name]
            _widget = getattr(self, item.attr_name)
            _widget.SetValue(value)

    def _set_grid(self, grid, mounts=None):
        """
        given a wxpython Grid object, and some number of "mounts", write the contents of "mounts" to the Grid object
        (thereby updating its view).

        If mounts is not passed to us, we'll go to the database and get all mounts.
        """
        if mounts is None:
            mounts = self.application_data.get_mounts()
        if len(mounts) <= 0:  # FIXME ????
            # nothing to do
            grid.AppendRows(numRows=1, updateLabels=False)
            return
        headers = mounts[0].keys()  # FIXME
        grid.CreateGrid(len(mounts), len(headers))
        for index, text in enumerate(headers):
            grid.SetColLabelValue(index, text)
        for row, mount in enumerate(mounts):
            for column, field_name in enumerate(headers):
                value = mount[field_name]
                value = str(value)
                grid.SetCellValue(row, column, value)

    def _get_grid(self, grid):
        """
        given a wxpython Grid objcect, gather all the data, write it out to the ApplicationData objcet and return it.
        """
        data = []
        num_rows = grid.GetNumberRows()
        num_columns = grid.GetNumberCols()
        for row_num in xrange(0, num_rows):
            row = {}
            for column_num in xrange(0, num_columns):
                field_name = grid.GetColLabelValue(column_num)
                value = grid.GetCellValue(row_num, column_num)
                row[field_name] = value
            data.append(row)
        self.application_data.write(mounts=data)
        return data

    def DoLayout(self):
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        preferencesSizer = wx.StaticBoxSizer(self.preferencesBox, wx.VERTICAL)
        for item in self._checkboxes:
            attr_name = item.attr_name
            id = item.id
            description = item.description
            _checkbox_widget = getattr(self, attr_name)
            preferencesSizer.Add(_checkbox_widget, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
            preferencesSizer.Add((0, 2), 0, 0, 0)
        for item in self._textboxes:
            attr_name = item.attr_name
            id = item.id
            size = item.size
            description = item.description
            _textbox_widget = getattr(self, attr_name)
            preferencesSizer.Add(wx.StaticText(self, -1, description), 0, wx.LEFT|wx.RIGHT, 5)
            preferencesSizer.Add((0, 2), 0, 0, 0)
            preferencesSizer.Add(_textbox_widget, 0, wx.LEFT|wx.RIGHT, 5)
            preferencesSizer.Add((0, 2), 0, 0, 0)
        mainSizer.Add(preferencesSizer, 0, wx.ALL, 5)

        mountsPanel = wx.Panel(self)
        mountsSizer = wx.BoxSizer(wx.VERTICAL)
        self.grid = wx.grid.Grid(mountsPanel)
        self._set_grid(self.grid)
        add_row_button = wx.Button(mountsPanel, -1, '+')
        self.Bind(wx.EVT_BUTTON, self.AppendMountsRow, add_row_button)
        mountsSizer.Add(self.grid, 1, wx.EXPAND, 5)
        mountsSizer.Add(add_row_button, 1, wx.EXPAND, 5)  # FIXME
        mountsPanel.SetSizer(mountsSizer)

        self.mainPanel.SetSizer(mainSizer)
        frameSizer.Add(self.mainPanel, 1, wx.EXPAND)
        frameSizer.Add(mountsPanel, 1, wx.EXPAND)
        self.SetSizer(frameSizer)
        frameSizer.Layout()

    def AppendMountsRow(self, event):
        self.grid.AppendRows(numRows=1, updateLabels=False)

    def OnCheckBox(self, event):
        obj = event.GetEventObject()
        item, = [i for i in self._checkboxes if i.id == obj.Id]
        field_name = item.attr_name
        value = event.IsChecked()
        value = int(value)
        self.application_data.write(preferences={field_name: value})

class SmbfsTaskBarIcon(wx.TaskBarIcon):

    OPEN_PROPERTIES_DIALOG = wx.NewId()
    CLOSE_APPLICATION = wx.NewId()
    PROPERTIES_DIALOG = wx.NewId()

    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.application_data = ApplicationData(path=USER_DB_FILE)
        self.frame = frame
        self.SetIcon(icon.GetIcon(), APPLICATION_TITLE)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.CLOSE_APPLICATION)
        self.Bind(wx.EVT_MENU, self.OpenPropertiesDialog, id=self.OPEN_PROPERTIES_DIALOG)
        self._mounts_menu_items = None

    @property
    def preferences_dialog(self):
        return PreferencesDialog(
            parent=self.frame,
            id=-1,
            title="Prefereces",
            application_data=self.application_data,
            style=wx.DEFAULT_DIALOG_STYLE,
        )

    @property
    def mounts_menu_items(self):
        if self._mounts_menu_items is None:
            self._mounts_menu_items = []
            mounts = self.application_data.get_mounts()
            mount_item_menu_template = r'//{host}/{share}/{path} {mountpoint}'
            for mount in mounts:
                mount_item_menu_text =  mount_item_menu_template.format(**mount)
                mount_item_menu_text = util.cleanup_smb_url(mount_item_menu_text)
                id = wx.NewId()
                state = True
                self._mounts_menu_items.append((id, mount_item_menu_text, state))
        return self._mounts_menu_items

    @mounts_menu_items.setter
    def mounts_menu_items(self, data):
        self._mounts_menu_items = data

    def CreatePopupMenu(self):
        menu = wx.Menu()
        for id, mount_item_menu_text, state in self.mounts_menu_items:
            menu.Append(id, mount_item_menu_text, kind=wx.ITEM_CHECK)
            menu.Check(id, state)
            self.Bind(wx.EVT_MENU, self.MountClick, id=id)
        menu.AppendSeparator()
        menu.Append(self.OPEN_PROPERTIES_DIALOG, "Properties...")
        menu.AppendSeparator()
        menu.Append(self.CLOSE_APPLICATION, "Quit")
        return menu

    def MountClick(self, event):
        new_mount_items = []
        for id, mount_item_menu_text, state in self.mounts_menu_items:
            if id == event.Id:
                state = not state
            #actual_state = is_mounted(date, blah, blah)
            #do_filesystem_mounting(data, desired_state=state, actual_state=actual_state)
            new_mount_items.append((id, mount_item_menu_text, state))
        self.mounts_menu_items = new_mount_items

    def OpenPropertiesDialog(self, event):
        self.preferences_dialog.Show()  # FIXME ShowModal

    def OnTaskBarClose(self, event):
        self.frame.Close()

class SmbfsTaskBarFrame(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, style=wx.FRAME_NO_TASKBAR)
        self.ico = SmbfsTaskBarIcon(self)
        wx.EVT_TASKBAR_LEFT_UP(self.ico, self.OnTaskBarLeftClick)

    def OnTaskBarLeftClick(self, event):
        self.ico.PopupMenu(self.ico.CreatePopupMenu())

class MacApp(wx.App):

    def MacReopenApp(self):
        "self.GetTopWindow().Raise()"
    def MacNewFile(self):
        ""
    def MacPrintFile(self, file_path):
        ""

def main(argv=None):
    app = MacApp(
        redirect=False,
        useBestVisual=True,
        clearSigInt=True,
    )
    SmbfsTaskBarFrame(parent=None, title=APPLICATION_TITLE)
    app.MainLoop()

if __name__ == '__main__':
    main()
