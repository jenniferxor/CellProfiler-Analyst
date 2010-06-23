import wx
import re
from filter import Filter
from properties import Properties
from dbconnect import DBConnect
from wx.combo import OwnerDrawnComboBox as ComboBox

p = Properties.getInstance()
db = DBConnect.getInstance()

class ColumnFilterPanel(wx.Panel):
    '''
    Creates a UI that allows the user to create WHERE clauses by selecting 
    1) a DB column name, 2) a comparator, and 3) a value
    '''
    def __init__(self, parent, tables, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.fieldSets = []
        self.tables = tables
        self.types = {}
        self.types[p.image_table] = db.GetColumnTypes(p.image_table)
        self.tableChoice = ComboBox(self, choices=self.tables, size=(150,-1))
        self.tableChoice.Select(0)
        self.colChoice = ComboBox(self, choices=db.GetColumnNames(p.image_table), size=(150,-1), style=wx.CB_READONLY)
        self.colChoice.Select(0)
        self.comparatorChoice = ComboBox(self, size=(80,-1))
        self.update_comparator_choice()
        self.valueField = wx.ComboBox(self, -1, value='')
        self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))
        
        colSizer = wx.BoxSizer(wx.HORIZONTAL)
        colSizer.Add(self.tableChoice, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.colChoice, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.comparatorChoice, 0.5, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.valueField, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.x_btn, 0, wx.EXPAND)
        
        self.SetSizer(colSizer)
        self.tableChoice.Bind(wx.EVT_COMBOBOX, self.on_select_table)
        self.colChoice.Bind(wx.EVT_COMBOBOX, self.on_select_col)
        self.x_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        
    def on_remove(self, evt):
        self.Parent.remove(self)
        self.Destroy()
        
    def on_select_col(self, evt):
        self.update_comparator_choice()
        self.update_value_choice()
        
    def on_select_table(self, evt):
        self.update_col_choice()
        self.update_comparator_choice()
        self.update_value_choice()
        
    def update_col_choice(self):
        table = self.tableChoice.GetStringSelection()
        self.colChoice.SetItems(db.GetColumnNames(table))
        self.colChoice.Select(0)
        
    def update_comparator_choice(self):
        table = self.tableChoice.GetStringSelection()
        colidx = self.colChoice.GetSelection()
        coltype = db.GetColumnTypes(table)[colidx]
        comparators = []
        if coltype in [str, unicode]:
            comparators = ['=', '!=', 'REGEXP']
        if coltype in [int, float, long]:
            comparators = ['=', '!=', '<', '>', '<=', '>=']
        self.comparatorChoice.SetItems(comparators)
        self.comparatorChoice.Select(0)
        
    def update_value_choice(self):
        table = self.tableChoice.GetStringSelection()
        column = self.colChoice.GetStringSelection()
        colidx = self.colChoice.GetSelection()
        coltype = db.GetColumnTypes(table)[colidx]
        vals = []
        if coltype == str:# or coltype == int or coltype == long:
            res = db.execute('SELECT DISTINCT %s FROM %s ORDER BY %s'%(column, table, column))
            vals = [str(row[0]) for row in res]
        self.valueField.SetItems(vals)
    
    def get_filter(self):
        table = self.tableChoice.GetStringSelection()
        column = self.colChoice.GetStringSelection()
        comparator = self.comparatorChoice.GetValue()
        value = self.valueField.GetValue()
        return Filter(table, column, comparator, value)
    
                
class ColumnFilterDialog(wx.Dialog):
    '''
    Dialog for building Filters on the fly.
    '''
    def __init__(self, parent, tables, **kwargs):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, **kwargs)
        self.tables = tables
        self.panels = [ColumnFilterPanel(self, tables)]
        self.filter_name = wx.TextCtrl(self, -1, 'My_Filter')
        self.addbtn = wx.Button(self, -1, 'Add Column')
        self.ok = wx.Button(self, -1, 'OK')
        self.cancel = wx.Button(self, -1, 'Cancel')
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Name your filter: '), 0, wx.CENTER)
        sz.Add(self.filter_name, 1, wx.EXPAND)
        sizer.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
        sizer.AddSpacer((-1,5))
        
        sizer.Add(wx.StaticText(self, -1, 'Choose constraints for your filter: '), 0, wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        sizer.AddSpacer((-1,5))
        sizer.Add(self.panels[0], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        sizer.AddSpacer((-1,5))
        
        sizer.AddStretchSpacer()
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(self.addbtn, 0)
        sz.AddStretchSpacer()
        sz.Add(self.ok, 0)
        sz.Add(self.cancel, 0)
        sizer.Add(sz, 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        
        self.SetSizer(sizer)
        
        self.validate_filter_name()
        
        self.addbtn.Bind(wx.EVT_BUTTON, self.add_column)
        self.ok.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.filter_name.Bind(wx.EVT_TEXT, self.validate_filter_name)
        
    def on_ok(self, evt):
        self.EndModal(wx.OK)
    
    def on_cancel(self, evt):
        self.EndModal(wx.CANCEL)
        
    def validate_filter_name(self, evt=None):
        name = self.get_filter_name()
        self.ok.Enable()
        self.filter_name.SetForegroundColour('black')
        if (name in p._filters_ordered 
            or not re.match('^[A-Za-z0-9_]+$',name)):
            self.ok.Disable() 
            self.filter_name.SetForegroundColour('red')
        
    def get_filter(self):
        filter = Filter()
        for panel in self.panels:
            filter += panel.get_filter()
        return filter
    
    def get_filter_name(self):
        return str(self.filter_name.Value) # do NOT return unicode
    
    def remove(self, panel):
        self.panels.remove(panel)
        self.Sizer.Remove(panel)
        self.Layout()
    
    def add_column(self, evt):
        self.panels += [ColumnFilterPanel(self, self.tables)]
        self.GetSizer().Insert(len(self.panels)+3, self.panels[-1], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.Layout()

    
if __name__ == "__main__":
    import sys
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    app = wx.PySimpleApp()
    
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        p.LoadFile('/Users/afraser/Desktop/cpa_example/example.properties')
#        p.LoadFile('/Users/afraser/CPA/properties/nirht.properties')
#        p.LoadFile('../properties/Gilliland_LeukemiaScreens_Validation.properties')


    cff = ColumnFilterDialog(None, tables=[p.image_table], size=(600,150))
    if cff.ShowModal()==wx.OK:
        print cff.get_filter()
        print cff.get_filter_name()
        
    cff.Destroy()
    app.MainLoop()