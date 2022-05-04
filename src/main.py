import sys
from PyQt5 import QtWidgets

from mainwindow import MainWindow;

def main():
	app = QtWidgets.QApplication(sys.argv)
	
	w = MainWindow()
	w.show()
	
	app.exec_()
	
if __name__ == '__main__':
	main()