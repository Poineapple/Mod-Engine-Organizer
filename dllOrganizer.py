import sys
import toml
import os
from PyQt6.QtWidgets import QLabel, QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QCheckBox, QListWidgetItem
from PyQt6.QtCore import Qt

class DragDropListWidget(QListWidget):
	def __init__(self, config_game_path, current_game, parent=None):
		super().__init__(parent)
		self.config_game_path = config_game_path
		self.current_game = current_game
		self.enabled_dlls = self.read_dlls()
		print('enabled dlls ',self.enabled_dlls)
		self.save_dict(self.enabled_dlls)
		self.dlls_dict = self.read_dict()
		print('dlls dict ',self.dlls_dict)
		self.save_dlls()
		self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
		self.populate()
		self.itemChanged.connect(self.toggle_dll)

	def populate(self):
		for dll in self.dlls_dict.keys():
			item = QListWidgetItem(dll)
			item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
			item.setCheckState(Qt.CheckState.Checked if self.dlls_dict[dll] else Qt.CheckState.Unchecked)
			self.addItem(item)

	def dropEvent(self, event):
		super().dropEvent(event)
		self.update_items()

	def update_items(self):
		new_order = []
		for index in range(self.count()):
			new_order.append(self.item(index).text())
		self.dlls_dict = {key: self.dlls_dict[key] for key in new_order}
		print('moved',self.dlls_dict)
		self.save_dict(self.dlls_dict)
		self.save_dlls()

	def toggle_dll(self, item):
		self.dlls_dict[item.text()] = True if item.checkState() == Qt.CheckState.Checked else False
		print('toggled',self.dlls_dict)
		self.save_dict(self.dlls_dict)
		self.save_dlls()

	def read_dict(self):
		try:
			with open('config.toml', 'r', encoding='utf-8' ) as toml_file:
				config = toml.load(toml_file)
			dll_list = config[self.current_game]['external_dlls']
			dll_paths = self.get_dll_paths()
			print('paths',dll_paths)
			print('list',dll_list)

			# creating a copy because according to copilot: 
			# "The issue of skipping elements during iteration is likely due to 
			# modifying the list (dll_list) while iterating over it"
			dll_list_copy = dll_list[:]
			for i in dll_list_copy:
				# print('working on', i)
				if i not in dll_paths:
					# print('removing', i)
					dll_list.remove(i)
			
			for i in dll_paths:
				if i not in dll_list:
					dll_list.append(i)

			dll_dict = {}
			for i in dll_list:
				if i in self.enabled_dlls:
					dll_dict[i] = True
				else:
					dll_dict[i] = False

			
			
			return dll_dict

		except Exception as e:
			print(f"Failed to read the TOML file: {e}")
			return {}

	def save_dict(self, dict=None):

		config = toml.load('config.toml')
		config[self.current_game]['external_dlls'] = [key for key in dict.keys()]
		with open('config.toml', 'w', encoding='utf-8') as toml_file:
			toml.dump(config, toml_file)

	def get_dll_paths(self):
		dll_paths = []
		dir = os.path.dirname(self.config_game_path)
		for root, dirs, files in os.walk(dir):
			dirs[:] = [d for d in dirs if d != 'modengine2']
			for file in files:
				if file.endswith('.dll'):
					relative_path = os.path.relpath(os.path.join(root, file), dir)
					relative_path = relative_path.replace('\\', '/')
					dll_paths.append(relative_path)
		return dll_paths

	def read_dlls(self):
		try:
			with open(self.config_game_path, 'r') as toml_file:
				data = toml.load(toml_file)
				dll_list = data['modengine']['external_dlls']
				dll_dict = {dll: True for dll in dll_list}
				return dll_dict

		except Exception as e:
			print(f"Failed to read the TOML file: {e}")

	def save_dlls(self):
		config_ME2 = toml.load(self.config_game_path)
		config_ME2['modengine']['external_dlls'] = [key for key in self.dlls_dict.keys() if self.dlls_dict[key]]
		with open(self.config_game_path, 'w') as toml_file:
			toml.dump(config_ME2, toml_file)

class dllOrganizer(QWidget):
	def __init__(self, config_game_path, current_game):
		super().__init__()
		
		self.layout = QVBoxLayout()
		self.label = QLabel('Installed DLLs')
		self.layout.addWidget(self.label)
		self.list_widget = DragDropListWidget(config_game_path, current_game)
		self.layout.addWidget(self.list_widget)
		self.setLayout(self.layout)
		self.list_widget.setStyleSheet("""QListWidget, QListWidget * {background-color: rgba(12, 12, 12, 0.75);
						color: white;
						font-size: 16px;}
						""")
		self.label.setStyleSheet(
                    "color: white; font-size: 16px; background-color: rgba(0, 0, 0, 0.8); padding: 8px;")


if __name__ == "__main__":
	app = QApplication(sys.argv)
	config_game_path = 'a.toml'
	window = dllOrganizer(config_game_path)
	window.show()
	sys.exit(app.exec())