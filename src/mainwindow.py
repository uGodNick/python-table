# Подключаем необходимые библиотеки
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import *
from PyQt5.QtSql import *
import mainwindow_ui as ui

# Класс главного окна
# Наследуется от базового класса QMainWindow
class MainWindow(QMainWindow):
	# Конструктор
	def __init__(self):
		# Вызываем конструктор базового класса
		super(MainWindow, self).__init__()
		# Создаем экземпляр класса окна из ui файла
		self.ui = ui.Ui_MainWindow()
		# Устанавливаем окно на текущую форму
		self.ui.setupUi(self)
		# Задаём переменную для работы с БД по умолчанию пустой
		self.db = None
		# Создаем лист для Id удаленных элементов
		self.remove = []
		# Создаем лист для Id пользователей
		self.userId = []

	
	# Инициализируем подключение БД в локальную переменную
	# dbName - Путь к БД
	# Если всё корректно - возвращает True
	def prepareDatabase(self, dbName):
		self.db = QSqlDatabase.addDatabase('QSQLITE', 'db')
		self.db.setDatabaseName(dbName)
		
		if not self.db.open():
			QMessageBox.critical(self, 'Ошибка', 'Не удалось подключиться к БД:\n' + self.db.lastError().text())
			return False
		return True
	
	# Задание списка таблиц из БД вручную
	def showTables(self):
		for i in range(3):
			self.ui.tableWidget.removeRow(i)
			self.ui.tableWidget.insertRow(i)
		users = QTableWidgetItem('Пользователи')
		users.setData(Qt.UserRole, ['users', True])
		self.ui.tableWidget.setItem(0,0,users)
		users.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
		
		groups = QTableWidgetItem('Группы')
		groups.setData(Qt.UserRole, ['groups', True])
		self.ui.tableWidget.setItem(1,0,groups)
		groups.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
		
		userGroups = QTableWidgetItem('Пользователи-группы')
		userGroups.setData(Qt.UserRole, ['user_groups', False])
		self.ui.tableWidget.setItem(2,0,userGroups)
		userGroups.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
		
	# Обработчик кнопки создания БД
	@pyqtSlot()
	def on_actionCreateDB_triggered(self):
		name = QFileDialog.getSaveFileName(self, 'Выберите файл БД для создания','', 'SQLite database (*.sqlite)')[0]
		if not name:
			return
		if not self.prepareDatabase(name):
			return
		
		query = QSqlQuery(self.db)
		
		qStr = ['''CREATE TABLE users(
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name VARCHAR,
			password VARCHAR
		)''',
		
		'''CREATE TABLE groups (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name VARCHAR
		);''',
		
		'''CREATE TABLE user_groups(
			user_id INTEGER CONSTRAINT user_id_fk REFERENCES users(id) ON DELETE CASCADE,
			group_id INTEGER CONSTRAINT group_id_fk REFERENCES groups(id) ON DELETE CASCADE
		);
		''']
		
		for str in qStr:
			if not query.exec(str):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось создать БД:\n' + query.lastError().text())
				return
			
		self.showTables()
		
	# Обработчик кнопки открытия БД
	@pyqtSlot()
	def on_actionOpenDB_triggered(self):
		name = QFileDialog.getOpenFileName(self, 'Выберите файл БД','', 'SQLite database (*.sqlite)')[0]
		if not name:
			return
		if not self.prepareDatabase(name):
			return
		self.showTables()
		
	# Обработчик кнопки добавления записи
	@pyqtSlot()
	def on_actionAdd_triggered(self):	
		lastStr = self.ui.twSimple.rowCount()
		self.ui.twSimple.insertRow(lastStr)
		self.ui.twSimple.setItem(lastStr, 0, QTableWidgetItem(''))
		self.ui.twSimple.item(lastStr, 0).setData(Qt.UserRole, 0)

		
	# Обработчик кнопки удаления записи
	@pyqtSlot()
	def on_actionDelete_triggered(self):
		if self.ui.twSimple.currentRow() >= 0:
			item = self.ui.twSimple.currentRow()
			idC = self.ui.twSimple.item(item, 0).data(Qt.UserRole)
			if idC != 0:
				self.remove.append(idC)
			self.ui.twSimple.removeRow(item)

	# Обработчик кнопки сохранения
	@pyqtSlot()
	def on_actionSave_triggered(self):
		if self.ui.tableWidget.currentRow() == 0 or self.ui.tableWidget.currentRow() == 1:
			if self.ui.tableWidget.currentRow() == 0:
				self.deleteFromTable("users")
			if self.ui.tableWidget.currentRow() == 1:
				self.deleteFromTable("groups")
			self.updateTable()
		if self.ui.tableWidget.currentRow() == 2:
			self.removeFromTable()
			self.insertToTableUserGroups()
		QMessageBox.information(self, 'Успешно', 'Сохранено')
	# Удаление элементов из таблицы пользователи-группы
	def removeFromTable(self):
		query = QSqlQuery(self.db)
		for c in self.remove:
			if not query.exec(f'DELETE FROM user_groups WHERE group_id = {self.ui.twMain.item(self.ui.twMain.currentRow(), 0).data(Qt.UserRole)} AND user_id = {c}'):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить строку:\n' + query.lastError().text())
				return

	# Проверка элементов на добавление в таблицу пользователи-группы
	def insertToTableUserGroups(self):
		for i in range(self.ui.twListInMain.rowCount()):
			if self.ui.twListInMain.item(i, 0).data(Qt.UserRole) == 0:
				self.insertToTableUserGroupsProcess(i)

	# Добавление элементов в список пользователи-группы
	def insertToTableUserGroupsProcess(self, i):
		query = QSqlQuery(self.db)
		group = self.ui.twMain.item(self.ui.twMain.currentRow(),0).data(Qt.UserRole)
		userName = self.ui.twListInMain.item(i,0).text()
		qStr = f'INSERT INTO user_groups(user_id, group_id) VALUES((SELECT id FROM users WHERE name="{userName}"),{group})'
		if not query.exec(qStr):
			QMessageBox.critical(self, 'Ошибка', 'Не удалось добавить строку:\n' + query.lastError().text())
			return
		self.getLastIdUserGroups(i)

	# Удаление элементов из таблицы
	def deleteFromTable (self, table):
		query = QSqlQuery(self.db)
		for c in self.remove:
			if not query.exec(f'DELETE FROM {table} WHERE id = {c}'):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить строку:\n' + query.lastError().text())
				return
	
	# Добавление в таблицу пользователи
	def insertToTableUsers (self, i):
		query = QSqlQuery(self.db)
		if self.ui.twSimple.item(i ,0).text() and self.ui.twSimple.item(i ,1).text():
			name = self.ui.twSimple.item(i ,0).text()
			password = self.ui.twSimple.item(i ,1).text()
			qStr = f"INSERT INTO users(name, password) VALUES('{name}','{password}')"
			if not query.exec(qStr):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось добавить строку:\n' + query.lastError().text())
				return
			self.getLastId(i)

	# Добавление в таблицу группы
	def insertToTableGroups (self, i):
		query = QSqlQuery(self.db)
		if self.ui.twSimple.item(i ,0).text():
			name = self.ui.twSimple.item(i ,0).text()
			qStr = f"INSERT INTO groups(name) VALUES('{name}')"
			if not query.exec(qStr):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось добавить строку:\n' + query.lastError().text())
				return
			self.getLastId(i)

	# Получение последнего добавленного id таблицы пользователи-группы
	def getLastIdUserGroups(self, i):
		query = QSqlQuery(self.db)
		qStr = f"SELECT last_insert_rowid()"
		if not query.exec(qStr) or not query.next():
			QMessageBox.critical(self, 'Ошибка', 'Не удалось выбрать последнюю строку:\n' + query.lastError().text())
			return
		self.ui.twListInMain.item(i ,0).setData(Qt.UserRole, query.value(0))

	# Получение последнего добавленного id
	def getLastId (self, i):
		query = QSqlQuery(self.db)
		qStr = f"SELECT last_insert_rowid()"
		if not query.exec(qStr) or not query.next():
			QMessageBox.critical(self, 'Ошибка', 'Не удалось выбрать последнюю строку:\n' + query.lastError().text())
			return
		self.ui.twSimple.item(i ,0).setData(Qt.UserRole, query.value(0))

	# Обновление таблицы пользователи
	def updateTableUsers(self, i):
		query = QSqlQuery(self.db)
		if self.ui.twSimple.item(i ,0).text() and self.ui.twSimple.item(i ,1).text():
			name = self.ui.twSimple.item(i ,0).text()
			password = self.ui.twSimple.item(i ,1).text()
			idC = self.ui.twSimple.item(i, 0).data(Qt.UserRole)
			qStr = f"UPDATE users SET name = '{name}', password = '{password}' WHERE id = {idC}"
			if not query.exec(qStr):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось обновить строку:\n' + query.lastError().text())
				return

	# Обновление таблицы группы
	def updateTableGroups(self, i):
		query = QSqlQuery(self.db)
		if self.ui.twSimple.item(i ,0).text():
			name = self.ui.twSimple.item(i ,0).text()
			idC = self.ui.twSimple.item(i, 0).data(Qt.UserRole)
			qStr = f"UPDATE groups SET name = '{name}' WHERE id = {idC}"
			if not query.exec(qStr):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось обновить строку:\n' + query.lastError().text())
				return
		
	# Проверка на действие с элементом (добавить/обновить)	
	def updateTable(self):
		for i in range(self.ui.twSimple.rowCount()):
			if self.ui.twSimple.item(i, 0).data(Qt.UserRole) == 0:
				if self.ui.tableWidget.currentRow() == 0:
					self.insertToTableUsers(i)
				if self.ui.tableWidget.currentRow() == 1:
					self.insertToTableGroups(i)
			else:
				if self.ui.tableWidget.currentRow() == 0:
					self.updateTableUsers(i)
				if self.ui.tableWidget.currentRow() == 1:
					self.updateTableGroups(i)
					
	# Обработчик смены элемента в таблице с именами таблиц из БД
	@pyqtSlot()
	def on_tableWidget_itemSelectionChanged(self):
		if not len(self.ui.tableWidget.selectedItems()):
			return
		item = self.ui.tableWidget.selectedItems()[0]
		self.prepareTables(item.data(Qt.UserRole))
		self.remove.clear()

	# Подготовка таблиц редактирования
	def prepareTables(self, dataList):
		if dataList[1]:
			self.prepareSimple(dataList[0])
		else:
			self.prepareConnection(dataList[0])

	# Обработчик смены элемента в таблице с ролями
	@pyqtSlot()
	def on_twMain_itemSelectionChanged(self):
		if not len(self.ui.twMain.selectedItems()):
			return
		item = self.ui.twMain.selectedItems()[0]
		self.prepareUserGroupsСompliance(item.data(Qt.UserRole))
		self.remove.clear()
		self.userId.clear()

	# Подготовка таблиц редактирования
	def prepareTables(self, dataList):
		if dataList[1]:
			self.prepareSimple(dataList[0])
		else:
			self.prepareConnection(dataList[0])

	# Обработчик стрелочки добавления
	@pyqtSlot()
	def on_tbtnAddTo_clicked(self):
		if self.ui.twAll.currentRow() >= 0:
			user = self.ui.twAll.item(self.ui.twAll.currentRow(),0).text()
			lastStr = self.ui.twListInMain.rowCount()
			self.ui.twListInMain.insertRow(lastStr)
			self.ui.twListInMain.setItem(lastStr, 0, QTableWidgetItem(user))
			self.ui.twListInMain.item(lastStr, 0).setData(Qt.UserRole, 0)

	# Обработчик стрелочки удаления
	@pyqtSlot()
	def on_tbtnRemoveFrom_clicked(self):
		if self.ui.twListInMain.currentRow() >= 0:
			item = self.ui.twListInMain.currentRow()
			idC = self.ui.twListInMain.item(item, 0).data(Qt.UserRole)
			if idC != 0:
				self.remove.append(idC)
			self.ui.twListInMain.removeRow(item)

	# Подготовка таблиц типа "Связка"
	def prepareConnection(self, name):
		self.ui.stackedWidget.setCurrentIndex(1)
		if name == 'user_groups':
			res = self.prepareUserGroups()
		else:
			res = False
		if res:
			self.ui.actionAdd.setEnabled(False)
			self.ui.actionDelete.setEnabled(False)
			self.ui.actionSave.setEnabled(True)
		else:
			self.ui.actionAdd.setEnabled(False)
			self.ui.actionDelete.setEnabled(False)
			self.ui.actionSave.setEnabled(False)
		
	# Подготовка простых таблиц
	def prepareSimple(self, name):
		self.ui.stackedWidget.setCurrentIndex(0)
		self.tableName = name
		
		if name == 'users':
			res = self.prepareUsers()
		elif name == 'groups':
			res = self.prepareGroups()
		else:
			res = False
		if res:
			self.ui.actionAdd.setEnabled(True)
			self.ui.actionDelete.setEnabled(True)
			self.ui.actionSave.setEnabled(True)
		else:
			self.ui.actionAdd.setEnabled(False)
			self.ui.actionDelete.setEnabled(False)
			self.ui.actionSave.setEnabled(False)
		
	# Подготовка таблицы пользователей
	def prepareUsers(self):
		self.ui.twSimple.setRowCount(0)
		self.ui.twSimple.setColumnCount(2)
		self.ui.twSimple.setHorizontalHeaderItem(0, QTableWidgetItem('Имя пользователя'))
		self.ui.twSimple.setHorizontalHeaderItem(1, QTableWidgetItem('Пароль'))
		
		query = QSqlQuery(self.db)
		str = 'SELECT id, name, password FROM users'
		
		if not query.exec(str):
			QMessageBox.critical(self, 'Ошибка', 'Не удалось получить список пользователей:\n' + query.lastError().text())
			return False
		
		i = 0
		while query.next():
			self.ui.twSimple.insertRow(i)
			self.ui.twSimple.setItem(i, 0, QTableWidgetItem(query.value(1)))
			self.ui.twSimple.setItem(i, 1, QTableWidgetItem(query.value(2)))
			self.ui.twSimple.item(i, 0).setData(Qt.UserRole, query.value(0))
			i += 1
		self.ui.twSimple.resizeColumnsToContents()
		return True
	
	# Подготовка таблицы групп
	def prepareGroups(self):
		self.ui.twSimple.setRowCount(0)
		self.ui.twSimple.setColumnCount(1)
		self.ui.twSimple.setHorizontalHeaderItem(0, QTableWidgetItem('Наименование группы'))
		
		query = QSqlQuery(self.db)
		str = 'SELECT id, name FROM groups'
		
		if not query.exec(str):
			QMessageBox.critical(self, 'Ошибка', 'Не удалось получить список групп:\n' + query.lastError().text())
			return False
		
		i = 0
		while query.next():
			self.ui.twSimple.insertRow(i)
			self.ui.twSimple.setItem(i, 0, QTableWidgetItem(query.value(1)))
			self.ui.twSimple.item(i, 0).setData(Qt.UserRole, query.value(0))
			i += 1
		self.ui.twSimple.resizeColumnsToContents()
		return True
	
	# Подготовка таблицы пользователи-группы
	def prepareUserGroups(self):
		self.ui.twMain.clear()
		self.ui.twMain.setColumnCount(1)
		self.ui.twMain.setRowCount(0)
		self.ui.twMain.setHorizontalHeaderItem(0, QTableWidgetItem('Роли'))
		self.ui.twMain.horizontalHeader().setStretchLastSection(True)
		
		query = QSqlQuery(self.db)
		str = 'SELECT id, name FROM groups'
		
		if not query.exec(str):
			QMessageBox.critical(self, 'Ошибка', 'Не удалось получить список групп:\n' + query.lastError().text())
			return False
		
		i = 0
		while query.next():
			self.ui.twMain.insertRow(i)
			self.ui.twMain.setItem(i, 0, QTableWidgetItem(query.value(1)))
			self.ui.twMain.item(i, 0).setData(Qt.UserRole, query.value(0))
			self.ui.twMain.item(i, 0).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
			i += 1
		self.ui.twMain.resizeColumnsToContents()
		self.ui.twAll.clear()
		self.ui.twAll.setColumnCount(1)
		self.ui.twAll.setRowCount(0)
		self.ui.twAll.setHorizontalHeaderItem(0, QTableWidgetItem('Пользователи'))
		self.ui.twAll.horizontalHeader().setStretchLastSection(True)
		
		
		query = QSqlQuery(self.db)
		str = 'SELECT id, name FROM users'
		
		if not query.exec(str):
			QMessageBox.critical(self, 'Ошибка', 'Не удалось получить список пользователей:\n' + query.lastError().text())
			return False
		
		i = 0
		while query.next():
			self.ui.twAll.insertRow(i)
			self.ui.twAll.setItem(i, 0, QTableWidgetItem(query.value(1)))
			self.ui.twAll.item(i, 0).setData(Qt.UserRole, query.value(0))
			self.ui.twAll.item(i, 0).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
			i += 1
		self.ui.twAll.resizeColumnsToContents()
		return True

	# Подготовка таблицы пользователей в определенной группе
	def prepareUserGroupsСompliance(self, data):
		self.ui.twListInMain.clear()
		self.ui.twListInMain.setRowCount(0)
		self.ui.twListInMain.setColumnCount(1)
		self.ui.twListInMain.setHorizontalHeaderItem(0, QTableWidgetItem('Назначенные на роль'))
		self.ui.twListInMain.horizontalHeader().setStretchLastSection(True)
		
		query = QSqlQuery(self.db)
		str = f'SELECT user_id FROM user_groups WHERE group_id = {data}'
		
		if not query.exec(str):
			QMessageBox.critical(self, 'Ошибка', 'Не удалось получить список пользователей в этой группе:\n' + query.lastError().text())
			return False

		while query.next():
			self.userId.append(query.value(0))

		for i in range(0, len(self.userId)):
			userId = self.userId[i]
			str = f'SELECT name FROM users WHERE id = {userId}'
			if not query.exec(str):
				QMessageBox.critical(self, 'Ошибка', 'Не удалось получить имя пользователя:\n' + query.lastError().text())
				return False
			while query.next():
				self.ui.twListInMain.insertRow(i)
				self.ui.twListInMain.setItem(i, 0, QTableWidgetItem(query.value(0)))
				self.ui.twListInMain.item(i, 0).setData(Qt.UserRole, self.userId[i])
				self.ui.twListInMain.item(i, 0).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
			self.ui.twListInMain.resizeColumnsToContents()
		return True