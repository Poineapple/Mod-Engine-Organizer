import shutil
import re
import os
import toml
import sys
import subprocess
import json
#from collections import defaultdict
from pathlib import Path
from PyQt6.QtGui import QAction, QColor, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QListWidget, QListWidgetItem, QSplitter, QToolBar, QMessageBox, QInputDialog, QMenu, QTableWidget, QTableWidgetItem, QApplication, QMainWindow, QWidget, QCheckBox, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from datetime import datetime
from functools import partial
from fileViewer import DirTreeView
from dllOrganizer import dllOrganizer

# path to TOML config file that contains path to config_eldenring.toml
config_path = 'config.toml'

# Function to create a default TOML config file if it doesn't exist
def create_default_toml_file(config_path):
	# default_config = {
	# 	'path': ''  # Default path is an empty string
	# }
	with open(config_path, 'w') as file:
		# toml.dump(default_config, file)
		pass
	print(f"Created a default TOML file at {config_path}")

config_game_path = ''
# Load and parse TOML config file
try:
	config = toml.load(config_path)
	current_game = config['current_game']
	# Check if current_game is empty or doesn't match any game names
	if not current_game or current_game not in config:
		# Select the path of the first game found
		for game in config:
			if game != 'current_game' and 'path' in config[game]:
				current_game = game
				config_game_path = config[game]['path']
				# Update the current_game in the config dictionary
				config['current_game'] = current_game
				# Write the updated config back to the TOML file
				with open(config_path, 'w', encoding='utf-8') as toml_file:
					toml.dump(config, toml_file)
				break
	else:
		config_game_path = config[current_game]['path']
	if not os.path.exists(config_game_path):
		raise FileNotFoundError(f"File not found: {config_game_path}")
except Exception as e:
	print(f"{e} creating one...")
	create_default_toml_file(config_path)
	#config = {'path': ''}  # Use default config after creating the file

# If the path is empty, prompt the user to select the path to 'config_eldenring.toml'


class PathInputDialog(QDialog):
	pathValidated = pyqtSignal(bool)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle('Path')
		self.layout = QVBoxLayout(self)

		# Row for text box and browse button
		self.pathRowLayout = QHBoxLayout()
		self.pathLineEdit = QLineEdit(self)
		self.pathLineEdit.setFixedWidth(300)
		self.pathRowLayout.addWidget(self.pathLineEdit)
		self.browseButton = QPushButton('Browse', self)
		self.browseButton.clicked.connect(self.browsePath)
		self.pathRowLayout.addWidget(self.browseButton)
		self.layout.addLayout(self.pathRowLayout)

		# Row for Cancel and Next buttons
		self.buttonsRowLayout = QHBoxLayout()
		self.cancelButton = QPushButton('Cancel', self)
		self.cancelButton.clicked.connect(self.reject)
		self.buttonsRowLayout.addWidget(self.cancelButton)
		self.nextButton = QPushButton('Next', self)
		self.nextButton.setEnabled(False)
		self.nextButton.clicked.connect(self.accept)
		self.buttonsRowLayout.addWidget(self.nextButton)
		self.layout.addLayout(self.buttonsRowLayout)

		self.pathLineEdit.textChanged.connect(self.validatePath)

	def browsePath(self):
		# Open a file dialog and update the text box with the selected path
		path, _ = QFileDialog.getOpenFileName(
			self, 'Select File', '', 'TOML Files (*.toml)')
		if path:
			self.pathLineEdit.setText(path)

	def validatePath(self):
		# Check if the path is valid and points to config_<game_name>.toml
		path = self.pathLineEdit.text()
		pattern = r'config_[a-zA-Z0-9]+\.toml'
		if os.path.isfile(path) and re.match(pattern, os.path.basename(path)):
			global config_game_path
			config_game_path = path
			self.nextButton.setEnabled(True)
			self.pathValidated.emit(True)
		else:
			self.nextButton.setEnabled(False)
			self.pathValidated.emit(False)

class InitDialog(PathInputDialog):
	def __init__(self):
		super().__init__()
		self.setWindowTitle('Select Path to "config_<game_name>.toml"')

		# Row for game name
		self.gameRowLayout = QHBoxLayout()
		self.gameLabel = QLabel('Managed Game:', self)
		self.GameNameLineEdit = QLineEdit(self)
		self.GameNameLineEdit.setText('Elden Ring')
		self.gameRowLayout.addWidget(self.gameLabel)
		self.gameRowLayout.addWidget(self.GameNameLineEdit)
		self.layout.insertLayout(0, self.gameRowLayout)
		self.GameNameLineEdit.setFocus()
		self.GameNameLineEdit.selectAll()

class AddModDialog(QDialog):
	def __init__(self):
		super().__init__()
		self.setWindowTitle('Add Empty Mod')
		self.layout = QVBoxLayout(self)

		self.nameLineEdit = QLineEdit(self)
		self.nameLineEdit.setPlaceholderText('Enter Mod Name')
		self.layout.addWidget(self.nameLineEdit)

		self.ButtonLayout = QHBoxLayout()
		self.createButton = QPushButton('Create', self)
		self.cancelButton = QPushButton('Cancel', self)
		self.ButtonLayout.addWidget(self.createButton)
		self.ButtonLayout.addWidget(self.cancelButton)
		self.layout.addLayout(self.ButtonLayout)

		self.createButton.clicked.connect(self.accept)
		self.cancelButton.clicked.connect(self.reject)

class SwitchGameDialog(QDialog):
	def __init__(self):
		super().__init__()
		self.setWindowTitle('Select Game')
		layout = QVBoxLayout(self)
		self.setGeometry(200, 200, 800, 400)
		
		self.addNewGameLayout = QHBoxLayout()
		self.addNewGameButton = QPushButton('Add New Game', self)
		self.addNewGameButton.clicked.connect(self.addNewGame)
		self.addNewGameLayout.addWidget(self.addNewGameButton)
		layout.addLayout(self.addNewGameLayout)

		self.GamesListLayout = QHBoxLayout()

		self.detailsWidgetContainer = QWidget()
		self.detailsLayout = QVBoxLayout(self.detailsWidgetContainer)
		self.detailsLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
		
		self.NameLayout = QHBoxLayout()
		self.NameLabel = QLabel('Name:', self)
		self.Name = QLineEdit(self)
		self.Name.setReadOnly(True)
		self.RenameButton = QPushButton('Rename', self)
		self.RenameButton.clicked.connect(self.renameGame)
		self.NameLayout.addWidget(self.NameLabel)
		self.NameLayout.addWidget(self.Name)
		self.NameLayout.addWidget(self.RenameButton)


		self.pathLayout = QHBoxLayout()
		self.pathLabel = QLabel('Path:', self)
		self.path = QLineEdit(self)
		self.path.setReadOnly(True)
		self.pathLayout.addWidget(self.pathLabel)
		self.pathLayout.addWidget(self.path)

		self.buttonsLayout = QHBoxLayout()
		self.deleteGameButton = QPushButton('Remove Game', self)
		self.deleteGameButton.clicked.connect(self.removeGame)
		self.buttonsLayout.addWidget(self.deleteGameButton)
		self.ChangePathButton = QPushButton('Change Config Path', self)
		self.ChangePathButton.clicked.connect(self.changeConfigPath)
		self.buttonsLayout.addWidget(self.ChangePathButton)

		self.detailsLayout.addLayout(self.NameLayout)
		self.detailsLayout.addLayout(self.pathLayout)
		self.detailsLayout.addLayout(self.buttonsLayout)


		# Create a vertical splitter
		self.splitter = QSplitter()

		# Add widgets to the splitter
		self.gamesListWidget = QListWidget()
		self.gamesListWidget.setStyleSheet(""" QListWidget {margin: 10px;}""")
		

		self.splitter.addWidget(self.gamesListWidget)
		self.splitter.addWidget(self.detailsWidgetContainer)
		self.splitter.setSizes([150, 500])

		# Add the splitter to the GamesListLayout
		self.GamesListLayout.addWidget(self.splitter)
		layout.addLayout(self.GamesListLayout)

		self.switchGameLayout = QHBoxLayout()
		self.switchGameButton = QPushButton('Switch Game', self)
		self.switchGameButton.clicked.connect(self.switchGame)
		self.switchGameLayout.addWidget(self.switchGameButton)
		layout.addLayout(self.switchGameLayout)

		# Load the config and populate the games list
		self.populateGamesList()

		# Connect the item click event to a function
		self.gamesListWidget.itemClicked.connect(self.showGameDetails)

		self.setLayout(layout)

	def populateGamesList(self):
		self.config = toml.load(config_path)
		self.gamesListWidget.clear()
		for game in self.config:
			if game != 'current_game':
				item = QListWidgetItem(game)
				self.gamesListWidget.addItem(item)
				if current_game in game:
					item.setSelected(True)
					self.gamesListWidget.setCurrentItem(item)
		self.showGameDetails(self.gamesListWidget.currentItem())
				
	def showGameDetails(self, item):
		game_name = item.text()
		game_path = self.config[game_name]['path']
		self.Name.setText(f"{game_name}")
		self.path.setText(f"path: {game_path}")
		
	def addNewGame(self):
		dialog = InitDialog()
		if dialog.exec() == QDialog.DialogCode.Accepted:
			game_name = dialog.GameNameLineEdit.text()
			selected_path = dialog.pathLineEdit.text()
			print(f"Selected Path: {selected_path}")

			# Load the existing config, update the path, and write it back to the file
			try:
				config_data = toml.load('config.toml')
			except Exception as e:
				print(f"Failed to load 'config.toml': {e}")
				config_data = {}  # Create an empty config if loading fails

			# Ensure the game_name key exists in the config_data dictionary
			if game_name not in config_data:
				config_data[game_name] = {}

			# Update the path in the config
			config_data[game_name]['path'] = selected_path

			# Write the updated config back to 'config.toml'
			with open('config.toml', 'w', encoding='utf-8') as config_file:
				toml.dump(config_data, config_file)
			
			self.populateGamesList()

	def switchGame(self):
		selected_game = self.gamesListWidget.currentItem().text()
		self.config['current_game'] = selected_game
		with open('config.toml', 'w', encoding='utf-8') as toml_file:
			toml.dump(self.config, toml_file)
		# Restart the application
		QApplication.quit()
		subprocess.Popen([sys.executable, __file__])

	def removeGame(self):
		selected_game = self.gamesListWidget.currentItem().text()
		del self.config[selected_game]
		with open('config.toml', 'w', encoding='utf-8') as toml_file:
			toml.dump(self.config, toml_file)
		self.populateGamesList()

	def renameGame(self):
		dialog = AddModDialog()
		dialog.setWindowTitle('Rename Game')
		dialog.createButton.setText('Rename')
		dialog.nameLineEdit.setText(self.gamesListWidget.currentItem().text())
		if dialog.exec() == QDialog.DialogCode.Accepted:
			new_name = dialog.nameLineEdit.text()
			selected_game = self.gamesListWidget.currentItem().text()
			self.config[new_name] = self.config[selected_game]
			del self.config[selected_game]
			with open('config.toml', 'w', encoding='utf-8') as toml_file:
				toml.dump(self.config, toml_file)
			self.populateGamesList()

	def changeConfigPath(self):
		dialog = PathInputDialog()
		if dialog.exec() == QDialog.DialogCode.Accepted:
			new_path = dialog.pathLineEdit.text()
			selected_game = self.gamesListWidget.currentItem().text()
			self.config[selected_game]['path'] = new_path
			with open('config.toml', 'w', encoding='utf-8') as toml_file:
				toml.dump(self.config, toml_file)
			self.showGameDetails(self.gamesListWidget.currentItem())

def runBat():
	parent_dir = Path(config_game_path).parent
	batch_file_name = 'launchmod' + os.path.basename(config_game_path)[6:-5] + '.bat'
	print(batch_file_name)
	batch_file_path = parent_dir / batch_file_name
	subprocess.run(f'"{batch_file_path}"', shell=True, cwd=parent_dir)

def conflictDetector(config_game_path, disabled_mods):
	file_paths = {}  # Key: file name, Value: list of paths
	conflicts = {}
	# Convert list to set for faster lookup
	disabled_mods_set = set(disabled_mods)
# Extract the directory of the config_game_path
	directory = os.path.dirname(config_game_path)

	# Construct the path to the 'mod' folder
	mod_folder_path = os.path.join(directory, 'mod')

	# Walk through the directory
	for root, dirs, files in os.walk(mod_folder_path):
		if any(disabled_mod in root for disabled_mod in disabled_mods_set):
			continue
		for file in files:
			rel_dir = os.path.relpath(root, mod_folder_path)
			rel_file_path = os.path.join(rel_dir, file)
			if file in file_paths:
				file_paths[file].append(rel_file_path)
			else:
				file_paths[file] = [rel_file_path]

	# Identify duplicates
	duplicates = {file: paths for file,
				  paths in file_paths.items() if len(paths) > 1}

	# Store duplicates in the conflicts dictionary
	for paths in duplicates.values():
		for path in paths:
			level_1_folder = path.split(os.sep)[0]
			if level_1_folder in conflicts:
				conflicts[level_1_folder].append(path)
			else:
				conflicts[level_1_folder] = [path]

	return conflicts

def toggle_mod_status(checked, mod_name, config_game_path, mods):
	# Update the 'enabled' status of the corresponding mod
	for mod in mods:
		if mod['name'] == mod_name:
			mod['enabled'] = bool(checked)
			break

	# Write the updated mods list back to the TOML file
	try:
		with open(config_game_path, 'r') as toml_file:
			data = toml.load(toml_file)

		# Update the mods section
		data['extension']['mod_loader']['mods'] = mods

		with open(config_game_path, 'w') as toml_file:
			toml.dump(data, toml_file)
	except Exception as e:
		print(f"Failed to update the TOML file: {e}")

	refresh_ui()


def itemIDs():
	if hasattr(sys, '_MEIPASS'):
		# Running in a PyInstaller bundle
		base_path = sys._MEIPASS

	else:
		# Running in a normal Python environment
		base_path = os.path.abspath(".")

	dictPath = os.path.join(base_path, 'parts.json')

	# Load key-value pairs from the JSON file
	with open(dictPath, 'r') as file:
		IDs = json.load(file)

	return IDs

def displayTree(ModName):
	directory = os.path.dirname(config_game_path)
	IDs = itemIDs()
	# Construct the path to the 'mod' folder
	mod_path = os.path.join(root_mods_path, ModName)
	fileTree = DirTreeView(path=mod_path, itemIDs=IDs)
	fileTree.setStyleSheet("""QTreeView, QTreeView * {background-color: rgba(12, 12, 12, 0.75);
						color: white;
						font-size: 16px;}
						""")

	fileTree.tree_view.header().setStyleSheet("""
		QHeaderView::section {
			background-color: rgba(0, 0, 0, 0.8);
			color: white;
			font-size: 16px;
			border: 0.5px solid rgba(255, 255, 255, 0.4);
		}
										   
	""")
	fileTree.tree_view.expandAll()
	fileTree.path_label.setStyleSheet(
		"color: white; font-size: 16px; background-color: rgba(0, 0, 0, 0.8); padding: 8px;")
	splitter.replaceWidget(1, fileTree)
	splitter.addWidget(fileTree)


def refresh_ui():
	global folders, mods, table, root_mods_path
	root_mods_path = read_mod_folder_path(config_game_path)
	folders = read_mod_folders(root_mods_path)
	mods = read_mods(config_game_path)
	disabled_mods = [mod['name'] for mod in mods if not mod['enabled']]
	conflicts = conflictDetector(config_game_path, disabled_mods)
	game_folders = ['chr','parts','sfx','menu']
	# Clear the table first
	table.setRowCount(0)
	folders = [folder for folder in folders if folder[0] not in game_folders]
	table.setRowCount(len(folders))
	table.cellClicked.connect(lambda row, col: table.selectRow(row))
	table.cellClicked.connect(lambda row, col: displayTree(table.item(row, 1).text()))

	# Repopulate the table
	for i, (name, date) in enumerate(folders):
		chkBoxWidget = QWidget()
		chkBoxLayout = QHBoxLayout(chkBoxWidget)
		chkBoxLayout.setContentsMargins(8, 8, 8, 8)
		chkBoxLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
		chkBox = QCheckBox()
		chkBox.setChecked(
			any(mod['name'] == name and mod['enabled'] for mod in mods))
		# Ensure the partial function captures the current state of `mods`
		chkBox.stateChanged.connect(partial(
			toggle_mod_status, mod_name=name, config_game_path=config_game_path, mods=mods))
		chkBoxLayout.addWidget(chkBox)
		chkBoxWidget.setLayout(chkBoxLayout)
		table.setCellWidget(i, 0, chkBoxWidget)

		# Create QTableWidgetItem for name
		nameItem = QTableWidgetItem(name)
		# Create QTableWidgetItem for date
		dateItem = QTableWidgetItem(date)

		if name in conflicts:
			nameItem.setBackground(QColor(150, 0, 50, 120))
			dateItem.setBackground(QColor(150, 0, 50, 120))

		table.setItem(i, 1, nameItem)
		table.setItem(i, 2, dateItem)

def read_mod_folder_path(config_game_path):
	# Extract the directory of the config_game_path
	directory = os.path.dirname(config_game_path)
	try:
		with open(config_game_path, 'r') as toml_file:
			data = toml.load(toml_file)
			# Construct the path to the 'mod' folder
			return os.path.join(directory, data['extension']['mod_loader']['mods'][0]['path'])
	except Exception as e:
		print(f"Failed to read the mod path from the TOML file: {e}")
		return os.path.join(directory, 'mod')

def read_mod_folders(mod_folder_path):
	
	# Check if the 'mod' folder exists
	if not os.path.exists(mod_folder_path):
		print(f"The 'mod' folder does not exist at {mod_folder_path}")
		return []
	folders=[]
	# List all folders in the 'mod' folder
	for name in os.listdir(mod_folder_path):
		folder_path = os.path.join(mod_folder_path, name)
		if os.path.isdir(folder_path):
			# Get the 'date modified' timestamp 
			date_modified_timestamp = os.path.getmtime(folder_path)
			date_modified = datetime.fromtimestamp(
				date_modified_timestamp).strftime('%Y/%m/%d %H:%M')
			folders.append((name, date_modified))
	return folders

def read_mods(config_game_path):
	try:
		# Open and parse the TOML file
		with open(config_game_path, 'r') as toml_file:
			data = toml.load(toml_file)

		# Extract the 'mods' section
		mods = data['extension']['mod_loader']['mods']
		return mods
	except FileNotFoundError:
		print(f"File not found: {config_game_path}")
		return []
	except Exception as e:
		print(f"An error occurred: {e}")
		return []

def renameMod(root_mods_path):
	currentRow = table.currentRow()
	modName = table.item(currentRow, 1).text()
	newName, ok = QInputDialog.getText(
		None, 'Rename Mod', 'Enter new name for the mod:', QLineEdit.EchoMode.Normal, modName)
	if ok and newName:
		modPath = os.path.join(root_mods_path, modName)
		newModPath = os.path.join(root_mods_path, newName)
		try:
			os.rename(modPath, newModPath)
		except OSError as e:
			print(f"Error renaming mod folder: {e}")
			return
		
		configPath = config_game_path
		try:
			with open(configPath, 'r') as tomlFile:
				data = toml.load(tomlFile)

			mods = data['extension']['mod_loader']['mods']
			for mod in mods:
				if mod['name'] == modName:
					mod['name'] = newName
					mod['path'] = f"{data['extension']['mod_loader']['mods'][0]['path']}/{newName}"
					break

			data['extension']['mod_loader']['mods'] = mods

			with open(configPath, 'w') as tomlFile:
				toml.dump(data, tomlFile)
		except Exception as e:
			print(f"Error updating config file: {e}")
			return
		
		table.item(currentRow, 1).setText(newName)

def openModFolderInExplorer():
	currentRow = table.currentRow()
	modName = table.item(currentRow, 1).text()
	modPath = os.path.join(os.path.dirname(
		config_game_path), 'mod', modName)
	os.startfile(modPath)

def showContextMenu(position):
	contextMenu = QMenu()
	deleteAction = contextMenu.addAction("Delete")
	renameAction = contextMenu.addAction("Rename")
	openInExplorerAction = contextMenu.addAction("Open in Explorer")  # Add "Open in Explorer" action
	action = contextMenu.exec(table.mapToGlobal(position))
	if action == deleteAction:
		deleteMod(root_mods_path)
	elif action == openInExplorerAction:  # Check if "Open in Explorer" action was triggered
		openModFolderInExplorer()
	elif action == renameAction:
		renameMod(root_mods_path)

def deleteMod(root_mods_path):
	reply = QMessageBox.question(None, 'Confirm Delete', 'Are you sure you want to delete this mod?',
								 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
	if reply == QMessageBox.StandardButton.Yes:
		currentRow = table.currentRow()
		modName = table.item(currentRow, 1).text()
		modPath = os.path.join(root_mods_path, modName)
		try:
			shutil.rmtree(modPath)
		except OSError as e:
			print(f"Error deleting mod folder: {e}")
			return
		
		configPath = config_game_path
		try:
			with open(configPath, 'r') as tomlFile:
				data = toml.load(tomlFile)

			mods = data['extension']['mod_loader']['mods']
			for mod in mods:
				if mod['name'] == modName:
					mods.remove(mod)
					break

			data['extension']['mod_loader']['mods'] = mods

			with open(configPath, 'w') as tomlFile:
				toml.dump(data, tomlFile)
		except Exception as e:
			print(f"Error updating config file: {e}")
			return
		
		table.removeRow(currentRow)

app = QApplication([])
window = QMainWindow()

def showAddModDialog():
	dialog = AddModDialog()
	if dialog.exec() == QDialog.DialogCode.Accepted:
		modName = dialog.nameLineEdit.text()
		if modName:
			print('root '+root_mods_path)
			modPath = os.path.join(root_mods_path, modName)
			os.makedirs(modPath, exist_ok=True)
			# Load the existing configuration
			with open(config_game_path, 'r') as file:
				config = toml.load(file)

			extension = config.setdefault('extension', {})
			mod_loader = extension.setdefault('mod_loader', {})
			mods = mod_loader.setdefault('mods', [])
			# Update the configuration
			mods.append({
				'enabled': True,  # This will be serialized as 'true' in TOML, magic...
				'name': modName,
				'path': f"{os.path.basename(root_mods_path)}/{modName}"
			})

			# Write the updated configuration back to the file
			with open(config_game_path, 'w') as file:
				toml.dump(config, file)
			dialog.accept()
			refresh_ui()

if config_game_path:
	print(f"Found non-empty 'path': {config_game_path}")
else:
	print("The 'path' variable is empty.")
	dialog = InitDialog()
	if dialog.exec() == QDialog.DialogCode.Accepted:
		game_name = dialog.GameNameLineEdit.text()
		selected_path = dialog.pathLineEdit.text()
		print(f"Selected Path: {selected_path}")

		# Load the existing config, update the path, and write it back to the file
		try:
			config_data = toml.load('config.toml')
		except Exception as e:
			print(f"Failed to load 'config.toml': {e}")
			config_data = {}  # Create an empty config if loading fails

		 # Ensure the game_name key exists in the config_data dictionary
		if game_name not in config_data:
			config_data[game_name] = {}

		# Update the path in the config
		config_data['current_game'] = game_name
		config_data[game_name]['path'] = selected_path
		config_game_path = selected_path
		current_game = game_name

		# Write the updated config back to 'config.toml'
		with open('config.toml', 'w', encoding='utf-8') as config_file:
			toml.dump(config_data, config_file)
	else:
		print("bye")
		sys.exit(0)

if config_game_path:
	toolbar = QToolBar("Main Toolbar")
	window.addToolBar(toolbar)
	toolbar.setStyleSheet("""
	QToolBar {
		background-color: rgba(0, 0, 0, 0.7);
	}
	QToolBar * {
		color: white;
		font-size: 18px;
	}
	""")
	# Will replace plain text with icons later
	runGame = QAction("Run Game", window)
	toolbar.addAction(runGame)
	runGame.triggered.connect(runBat)
	changeGame = QAction("Change Game", window)
	toolbar.addAction(changeGame)
	changeGame.triggered.connect(lambda: SwitchGameDialog().exec())
	addModAction = QAction("Add Empty Mod", window)
	toolbar.addAction(addModAction)
	root_mods_path = read_mod_folder_path(config_game_path)
	addModAction.triggered.connect(showAddModDialog)

	window.setWindowTitle('Mod Engine Organizer')
	# some weird schenanigans to get the icon to work after building
	basePath = sys._MEIPASS if getattr(
		sys, 'frozen', False) else os.path.dirname(__file__)
	iconPath = os.path.join(basePath, 'icon.ico').replace('\\', '/')
	bgImagePath = os.path.join(basePath, 'bg.png').replace('\\', '/')
	window.setWindowIcon(QIcon(iconPath))
	window.setStyleSheet(f"""
	QMainWindow {{
		background-image: url("{bgImagePath}");
		background-repeat: no-repeat;
		background-position: center;
		color: white;
	}}
	""")

	window.setGeometry(100, 100, 1024, 600)
	root_mods_path = read_mod_folder_path(config_game_path)
	folders = read_mod_folders(root_mods_path)
	mods = read_mods(config_game_path)

	central_widget = QWidget()
	central_layout = QHBoxLayout(central_widget)

	# Create a scroll area
	# scroll_area = QScrollArea()
	# scroll_area.setWidgetResizable(True)  # Make the scroll area resizable
	# scroll_area.setStyleSheet(
	# 	"QScrollArea {background-color: rgba(0, 0, 0, 0.1);}")

	class CustomTableWidget(QTableWidget):
		def __init__(self, deleteModFunc, *args, **kwargs):
			super(CustomTableWidget, self).__init__(*args, **kwargs)
			self.deleteModFunc = deleteModFunc
			self.root_mods_path = root_mods_path

		def keyPressEvent(self, event):
			if event.key() == Qt.Key.Key_Delete:
				self.deleteModFunc(self.root_mods_path)
			else:
				super().keyPressEvent(event)

	table = CustomTableWidget(deleteMod, len(folders), 3)
	# Set column headers
	table.setHorizontalHeaderLabels(["", "Name", "Date Modified"])
	table.setStyleSheet("""QTableWidget, QTableWidget * {background-color: rgba(0, 0, 0, 0.65);
						color: white;
					 	padding: 4px;
						font-size: 16px;}
						QTableCornerButton::section {
						background-color: rgba(0, 0, 0, 0);
						border: none;
						}""")
	table.verticalHeader().setStyleSheet("""
		QHeaderView::section {
			background-color: rgba(0, 0, 0, 0.8);
			color: white;
			font-size: 16px;
			border: none;
		}
	""")
	table.horizontalHeader().setStyleSheet("""
		QHeaderView::section {
			background-color: rgba(0, 0, 0, 0.8);
			color: white;
			font-size: 16px;
			border: 0.5px solid rgba(255, 255, 255, 0.4);
		}
	""")

	# Populate the table for the first time
	refresh_ui()

	table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
	table.customContextMenuRequested.connect(showContextMenu)
	# Adjust table settings
	table.resizeColumnsToContents()
	# table.setColumnWidth(1, 400)  # Adjust the width of the 'Name' column
	table.setSortingEnabled(True)

	# Add the table to the scroll area
	# scroll_area.setWidget(table)

	

	splitter = QSplitter()
	splitter.addWidget(table)
	parent_splitter = QSplitter()
	parent_splitter.addWidget(splitter)
	
	parent_splitter.setStretchFactor(0, 4)
	parent_splitter.setStretchFactor(1, 1)
	central_layout.addWidget(parent_splitter)

	
	# Set the central widget as the main window's central widget
	window.setCentralWidget(central_widget)

	window.show()
	parent_splitter.addWidget(dllOrganizer(config_game_path, current_game))
	sys.exit(app.exec())
