#!/usr/bin/env python3

import npyscreen
from os import walk
import re
from collections import defaultdict
import curses

class MyTheme(npyscreen.npysThemeManagers.ThemeManager):
	#To use MyTheme, edit NSESelecta.onStart()
	default_colors = {
		'DEFAULT'     : 'BLACK_WHITE',
		'FORMDEFAULT' : 'BLACK_WHITE',
		'NO_EDIT'     : 'BLUE_BLACK',
		'STANDOUT'    : 'CYAN_BLACK',
		'CURSOR'      : 'CYAN_BLACK',
		'CURSOR_INVERSE': 'BLACK_CYAN',
		'LABEL'       : 'GREEN_WHITE',
		'LABELBOLD'   : 'BLACK_WHITE',
		'CONTROL'     : 'YELLOW_CYAN',
		'WARNING'     : 'RED_BLACK',
		'CRITICAL'    : 'BLACK_RED',
		'GOOD'        : 'GREEN_BLACK',
		'GOODHL'      : 'GREEN_BLACK',
		'VERYGOOD'    : 'BLACK_GREEN',
		'CAUTION'     : 'YELLOW_BLACK',
		'CAUTIONHL'   : 'BLACK_YELLOW',
	}
	
class NSESelecta(npyscreen.NPSAppManaged):
	selected_scripts =[]
	
	def onStart(self):
		#Set theme
		#npyscreen.setTheme(MyTheme)
		npyscreen.setTheme(npyscreen.Themes.DefaultTheme)
		
		self.registerForm("MAIN", MainForm())

	def setSelectedScripts(self, scripts):
		self.selected_scripts = scripts

	def getSelectedScripts(self):
		return self.selected_scripts
		
		
		

class CustomTitleMultiSelect(npyscreen.MultiSelect):
	def set_up_handlers(self):
		super(npyscreen.MultiSelect, self).set_up_handlers()
		self.handlers.update({
					ord("x"):    self.h_select_toggle,
					curses.ascii.SP: self.h_select_toggle,
					ord("X"):    self.h_select,
					"^U":        self.h_select_none,
					"^A":        self.h_select_all,
				})				
	def h_select_all(self, input):
		self.value = [x for x in range(0, len(self.values))]
	def h_select_none(self, input):
		self.value = []
	
	
	
	def when_value_edited(self):
		if self.name == 'Protocol':
			self.parent.update_available_scripts(self.get_selected_objects())
			itm = self.parent.available_scripts.values[0]
			if not itm == 'select at least one protocol':
				self.get_info(itm)
		if self.name == 'Scripts':
			self.parent.update_selected_scripts(self.get_selected_objects())
		if self.name == 'Categories':
			self.parent.filter_categories(self.get_selected_objects())
			
		
	def when_cursor_moved(self):
		if self.name == "Scripts":
			itm = self.values[self.cursor_line]
			if not itm == 'select at least one protocol':
				self.get_info(itm)
				
	
	def when_parent_changes_value(self):
		if self.name == "Scripts":
			itm = self.values[self.cursor_line]
			if not itm == 'select at least one protocol':
				self.get_info(itm)
				
			
	def get_info(self, selected_item):
		self.parent.update_info_and_categories(selected_item)




class MainForm(npyscreen.Form):

	nse_path = '/usr/share/nmap/scripts/'
	nse_files = defaultdict(dict)
	selected_scripts = []
	categories = ["auth", "broadcast", "brute", "default", "discovery", "dos", "exploit", "external", "fuzzer", "intrusive", "malware", "safe", "version", "vuln"]
	
	def make_datadict(self, x, path):
		for (pathname, dirs, files) in walk(path):
			for f in files:
				if f[-3:] == "nse":
					#get protocol & scripts
					protocol = re.search(r'(\w+)(-|\.)', f).group(1)
					scriptname = f[:-4]
					self.nse_files[protocol].update({scriptname:[]})					
					#get info and categories
					filename = path + f
					with open(filename) as f:
						content = re.sub(r'\r', '', " ".join(f.readlines()))
						if not content == "":
							info_result = re.search(r'(?i)(description\s*=\s*\[\[\s*|description\s*=\s*\")((.*\n?)*)', content)
							if info_result:
								if info_result.group(1)[-1] == '"':
									info_result = re.search(r'(.|\n)*?(?:\")', info_result.group(2))
								else:
									info_result = re.search(r'(.|\n)*?(?:\]\])', info_result.group(2))
							cats_result = re.search(r'(categories\s*=\s*\{)([^\}]+)(\})', content)
							if cats_result:
								cats = [re.sub(r'"', '', c.strip()) for c in cats_result.group(2).split(',')]
								self.nse_files[protocol][scriptname].append(cats)
							if info_result:
								self.nse_files[protocol][scriptname].append(info_result.group(0)[:-2])



	def update_available_scripts(self, protocols):
		av_scripts = []
		if protocols:
			for prtocl, scripts in self.nse_files.items():
				if prtocl in protocols:
					av_scripts.extend(scripts.keys())
			self.available_scripts.values=av_scripts
			self.available_scripts.update()
		else:
			self.available_scripts.values=['select at least one protocol']
			self.available_scripts.update()
	
	
	def split_len(self, string, length):
		words = [w for w in string.split(' ')]
		lines = []
		line = ""
		for w in words:
			if len(w) > length:
				if len(line)>0:
					linelength = len(line)
					line += w[:length - linelength-1]
					w = w[length-linelength-1:]					
				while len(w) > length:					
					line = w[:length-1]
					w = w[length:]
					lines.append(line)				 
			if len(line) + len(w) + 2 < length and not "\n" in w:
				line += w+" "
			elif len(line) + len(w) + 2 < length and "\n" in w:
				line += w
				lines.append(line)
				line=""
			else:
				line +='\n'
				lines.append(line)
				line = w+" "
		lines.append(line)		
		return lines
			
			
	def update_info_and_categories(self, selected_item):
		width = self.script_info.width
		protocol = re.search(r'^(\w+)(-|\.)?', selected_item).group(1)
		categories = self.nse_files[protocol][selected_item][0]		
		info = self.nse_files[protocol][selected_item][1]	
		infolist = self.split_len(info, width)		
		self.script_info.values = infolist
		self.script_info.reset_cursor()
		self.script_info.update()
		self.categories.values = categories
		self.categories.update()

	
	def update_selected_scripts(self, scripts):
		self.selected_scripts = scripts
	
	
	def filter_categories(self, selected_categories, exclude=True):
		self.make_datadict('x', self.myPath.value)
		filtered_nse_files = defaultdict(dict)
		for protocol, scripts in self.nse_files.items():
			for s, values in self.nse_files[protocol].items():
				checks=[]
				for c in values[0]:
					if c in selected_categories:
						checks.append(True)
					else:
						checks.append(False)				
				if exclude:
					if not False in checks:
						#all script categories are selected
						filtered_nse_files[protocol].update({s:values})
				else:
					if True in checks:	
						#at least one script category is selected	
						filtered_nse_files[protocol].update({s:values})
						
		self.nse_files = filtered_nse_files																
		self.reset_all()
		
		
	def reset_all(self):
		self.select_protocols.value = []
		protocols = [p for p,s in self.nse_files.items()]
		self.select_protocols.values = sorted(protocols)
		self.select_protocols.reset_cursor()
		self.select_protocols.update()
		self.available_scripts.value = []
		self.available_scripts.values = ['select at least one protocol']
		self.available_scripts.reset_cursor()
		self.available_scripts.update()
		self.categories.values = ["select a script"]
		self.categories.update()
		self.script_info.values = ["select a script"]
		self.script_info.reset_cursor()
		self.script_info.update()
		
		
	def create(self):
		#title
		self.ttext = self.add(npyscreen.FixedText, rely= 0, relx = 2, name='footer', value = '- NSE-Selecta 0.2 alpha -', editable = False)
		
		#Path of nse scripts
		self.myPath = self.add(npyscreen.TitleFilename, rely= 1, name = "Path to scripts:", value=self.nse_path )
		
		# self.excludecattitle = self.add(npyscreen.FixedText, rely = 4, max_width = 20, color = 'LABEL', name= "excludetitle", value="Exclude Scripts", editable = False)
		# self.excludecattitle2 = self.add(npyscreen.FixedText, rely = 5, max_width = 20, color = 'LABEL', name= "excludetitle2", value="with unselected", editable = False)
		# self.excludecattitle3 = self.add(npyscreen.FixedText, rely = 6, max_width = 20, color = 'LABEL', name= "excludetitle3", value="categories", editable = False)
		
		# self.exclude_cat = self.add(npyscreen.Checkbox, exit_right=True, scroll_exit=True,  rely = 7 , max_width = 20, name='enabled', value=True)
		
		#Category filter
		self.categoriestitle = self.add(npyscreen.FixedText, rely=4, max_width= 20, color='LABEL', name="ctitle", value="Categories", editable=False)		
		self.category_filter = self.add(CustomTitleMultiSelect, rely=5, exit_right=True, scroll_exit=True, max_width=20, name='Categories', values = self.categories, value=[0,1,2,3,4,5,6,7,8,9,10,11,12,13])
				
		#Protocol List
		if len(self.nse_files) > 0:
			protocols = [p for p,s in nse_files.items()]
		else:
			protocols =  ["check provided path"]	
		self.protocoltitle = self.add(npyscreen.FixedText, rely=4,relx=22, max_width= 25, color='LABEL', name="ptitle", value="Protocol", editable=False)		
		self.select_protocols = self.add(CustomTitleMultiSelect, rely=5,relx=22, exit_right=True, exit_left=True, max_width=25, name='Protocol', values = sorted(protocols))
		
		#Script List
		self.scripttitle = self.add(npyscreen.FixedText, rely=4,  relx=49, max_width= 45,  color='LABEL', name="stitle", value="Scripts", editable=False)
		self.available_scripts = self.add(CustomTitleMultiSelect,rely=5, relx=49, exit_right=True, exit_left=True, max_width=45, name='Scripts', values=['select at least one protocol'])
		
		#Categories and info
		self.categoriestitle = self.add(npyscreen.FixedText, rely=4,  relx=96, color='LABEL', name="catstitle", value="Categories", editable=False)
		self.categories = self.add(npyscreen.MultiLine, rely=5, max_height=5, relx= 96, name='Categories', editable=False, exit_left=True, values=["select a script"])
		self.scriptinfotitle = self.add(npyscreen.FixedText, rely=10,  relx=96, color='LABEL', name="scriptinfotitle", value="Script Info", editable=False)
		self.script_info = self.add(npyscreen.MultiLine, rely=11, relx= 96, name='Script info', exit_left=True, exit_right=True, scroll_exit=True, values=["select a script"])

		
				
		
	def while_editing(self, x):
		if x.name== "Path to scripts:":
			#make the datadict 
			self.make_datadict(self, self.myPath.value)
			# self.filter_categories(self.category_filter.get_selected_objects(), exclude=self.exclude_cat.value)
			#refresh protocols
			if len(self.nse_files) > 0:
				protocols = [p for p,s in self.nse_files.items()]
			else:
				protocols = ["check provided path"]	
			self.select_protocols.values = sorted(protocols)
		
		# if x.name == "enabled":
			# #the exclude checkbox was changed
			# self.reset_all()	
			# self.filter_categories(self.category_filter.get_selected_objects(), exclude=self.exclude_cat.value)	
				
	def afterEditing(self):	
		#pass the selected scripts to app and exit	
		self.parentApp.setSelectedScripts(self.selected_scripts)
		self.parentApp.setNextForm(None)




if __name__ == '__main__':
	testvar = "no"
	NSES = NSESelecta()
	
	NSES.run()
	print()
	selected_scripts = NSES.getSelectedScripts()
	if selected_scripts:
		print("--script="+",".join(NSES.getSelectedScripts()))
	else:
		print("No script selected!")
	print()
