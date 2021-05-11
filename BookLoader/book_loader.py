'''Gui''' # pylint: disable=(invalid-name)
import ast  # Use to read list from config file.
import configparser  # Read config file.
import csv
import io
import json
import logging  # Logging errors.
import os
import pathlib
import re
import shutil
import sys
import time
import traceback
import webbrowser
from distutils import util
from queue import Queue  # Report result from threads
from threading import Thread

from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets

from book import find_html
from book import main as book_mode
from image_downloader import get_image
from private.gui_book_updater import Ui_MainWindow
from settings import Ui_Settings
from woo import get_product as woo_get
from woo import main as woo

current_dir = (os.path.dirname(os.path.realpath(__file__)))
logging_path = os.path.join(current_dir, "logs", "gui.log")

logging.basicConfig(filename=logging_path, level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

class WorkerSignals(QtCore.QObject): # pylint: disable=(c-extension-no-member)
    ''' Workers signals '''
    finished = QtCore.pyqtSignal() # pylint: disable=(c-extension-no-member)
    error = QtCore.pyqtSignal(tuple) # pylint: disable=(c-extension-no-member)
    result = QtCore.pyqtSignal(object) # pylint: disable=(c-extension-no-member)
    progress = QtCore.pyqtSignal() # pylint: disable=(c-extension-no-member)

class Worker(QtCore.QRunnable): # pylint: disable=(c-extension-no-member)
    ''' Thread Worker '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @QtCore.pyqtSlot() # pylint: disable=(c-extension-no-member)
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as error:  # pylint: disable=broad-except
            logger.info(error)
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class Completer(QtWidgets.QCompleter): # pylint: disable=(c-extension-no-member)
    '''Category Completer'''
    def __init__(self, *args, **kwargs):
        super(Completer, self).__init__(*args, **kwargs)

        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive) # pylint: disable=(c-extension-no-member)
        self.setCompletionMode(QtWidgets.QCompleter.PopupCompletion) # pylint: disable=(c-extension-no-member)
        self.setWrapAround(False)

    # Add texts instead of replace
    def pathFromIndex(self, index):
        ''' ? '''
        path = QtWidgets.QCompleter.pathFromIndex(self, index) # pylint: disable=(c-extension-no-member)
        lst = str(self.widget().text()).split(',')
        if len(lst) > 1:
            path = '%s, %s' % (','.join(lst[:-1]), path)
        return path

    def splitPath(self, path):
        ''' ? '''
        path = str(path.split(',')[-1]).lstrip(' ')
        return [path]


class MyMainWindow(QtWidgets.QMainWindow, Ui_MainWindow): # pylint: disable=(c-extension-no-member)
    ''' Initialize Gui '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.screen = app.primaryScreen()
        print('Screen: %s' % self.screen.name())
        self.size = self.screen.size()
        print('Size: %d x %d' % (self.size.width(), self.size.height()))
        self.rect = self.screen.availableGeometry()
        print('Available: %d x %d' % ((self.rect.width()), (self.rect.height())))
        self.setupUi(self)
        # self.setMaximumSize(QtCore.QSize(self.rect.width(),self.rect.height()))
        self.threadpool = QtCore.QThreadPool() # pylint: disable=(c-extension-no-member)
        self.percent_size_line = 0.035
        self.percent_size_label = 0.027

        if self.rect.width() > 1700 and self.rect.height() > 900:
            self.percent_size_line = 0.043
            self.percent_size_label = 0.03

        ### RESIZING ### 
        self.cover_image_label.setMaximumSize(int(self.rect.width()*0.33) ,int(self.rect.height()*0.33)) # pylint: disable=(line-too-long)

        self.isbn_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.name_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.title_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.author_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.publisher_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.category_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.year_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.amount_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.price_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.sale_price_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.description_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.binding_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.id_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.image_size_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.cover_label.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.next_desc_button.setMaximumHeight(int(self.rect.height()*self.percent_size_label))
        self.previous_desc_button.setMaximumHeight(int(self.rect.height()*self.percent_size_label))

        self.name_line.setMaximumHeight(int(self.rect.height()*0.08))
        self.isbn_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.title_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.author_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.publisher_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.category_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.year_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.amount_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.price_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.sale_price_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        
        self.check_button.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.binding_box.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.gift_check_box.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.release_check_box.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.sale_check_box.setMaximumHeight(int(self.rect.height()*self.percent_size_line))

        self.id_line.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.clear_button.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.load_button.setMaximumHeight(int(self.rect.height()*self.percent_size_line))

        self.source_label.setMaximumHeight(int(self.rect.height()*self.percent_size_line))

        self.description_text_edit.setMaximumHeight(int(self.rect.height()*0.6))

        self.next_image_buttom.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.previous_image_buttom.setMaximumHeight(int(self.rect.height()*self.percent_size_line))
        self.image_change_button.setMaximumHeight(int(self.rect.height()*0.04))
        self.save_to_file_button.setMaximumHeight(int(self.rect.height()*0.08))
        self.settings_button.setMaximumHeight(int(self.rect.height()*0.08))
        self.word_press_button.setMaximumHeight(int(self.rect.height()*0.12))
        self.update_info_label.setMaximumHeight(int(self.rect.height()*self.percent_size_line))

        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(os.path.dirname(__file__),'config', 'conf.ini'))

        self.gui = {
            'google'            :util.strtobool(self.config.get('Source', 'google')),
            'isbndb'            :util.strtobool(self.config.get('Source', 'isbndb')),
            'amazon'            :util.strtobool(self.config.get('Source', 'amazon')),
            'goodreads'         :util.strtobool(self.config.get('Source', 'goodreads')),
            'title_box'         :True,
            'authors_box'       :True,
            'description_box'   :True,
            'binding_box'       :True,
            'publisher_box'     :True,
            'publish_date_box'  :True,
            'categories_box'    :True,
            'image_box'         :True
        }

        self.image_iterator = 0
        self.image_list = []
        self.current_dir = pathlib.Path(__file__).parent # Setting curret ABS path
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.current_dir, "private", "image", "bookloader.png"))) # pylint: disable=(c-extension-no-member, line-too-long)
        self.setWindowTitle("Book Loader")

        self.progress_bar = QtWidgets.QProgressBar() # pylint: disable=(c-extension-no-member)
        self.statusbar.addWidget(self.progress_bar)
        self.isbn_line.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{13}"))) # pylint: disable=(c-extension-no-member)

        self.isbn_line.textChanged.connect(self.isbn_run)

        self.year_line.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{4}"))) # pylint: disable=(c-extension-no-member)
        self.amount_line.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{5}"))) # pylint: disable=(c-extension-no-member)
        self.price_line.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{5}"))) # pylint: disable=(c-extension-no-member)
        self.sale_price_line.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{5}"))) # pylint: disable=(c-extension-no-member)


        self._completer = Completer(self.categories_main_list())
        self.category_line.setCompleter(self._completer)

        self.image_change_button.clicked.connect(self.change_image)
        self.check_button.clicked.connect(self.category_exist)

        self.load_button.clicked.connect(self.update_item)
        self.load_button.setDisabled(True)
        self.clear_button.clicked.connect(self.clear_line_edit)

        self.word_press_button.setDisabled(True)
        self.word_press_button.clicked.connect(self.send_to_wordpress)

        self.save_to_file_button.setDisabled(True)
        self.save_to_file_button.clicked.connect(self.save_item)
        self.settings_button.clicked.connect(self.open_settings)
        self.actionConfig.triggered.connect(self.open_settings)

        self.actionSave.triggered.connect(self.save_item)
        self.actionExit_program.triggered.connect(self.close)
        self.actionOpen_Config_folder.triggered.connect(lambda: os.startfile(self.current_dir))
        self.actionGIt_Hub.triggered.connect(lambda: webbrowser.open('https://github.com/PytongMasters')) # pylint: disable=(line-too-long)
        self.actionOpen_Help.triggered.connect(lambda: webbrowser.open('https://github.com/PytongMasters')) # pylint: disable=(line-too-long)
        self.actionContact_Us.triggered.connect(lambda: webbrowser.open('https://github.com/PytongMasters')) # pylint: disable=(line-too-long)
        self.msg_box = QtWidgets.QMessageBox() # pylint: disable=(c-extension-no-member)
        self.msg_to_send = QtWidgets.QMessageBox() # pylint: disable=(c-extension-no-member)
        self.options = QtWidgets.QFileDialog.Options() # pylint: disable=(c-extension-no-member)
        self.screen_size = QtWidgets.QDesktopWidget().screenGeometry(-1) # pylint: disable=(c-extension-no-member)
        self.word_press_button.setShortcut("Ctrl+Return")
        self.setTabOrder(self.title_line,self.author_line)
        self.setTabOrder(self.publisher_line,self.category_line)
        self.setTabOrder(self.category_line,self.year_line)
        self.setTabOrder(self.year_line,self.amount_line)
        self.setTabOrder(self.amount_line,self.price_line)
        self.setTabOrder(self.price_line,self.sale_price_line)
        self.setTabOrder(self.sale_price_line,self.description_text_edit)
        self.shortcut_full_screen = QtWidgets.QShortcut(QtGui.QKeySequence("F11"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_full_screen.activated.connect(self.full_screen)

        self.shortcut_colon = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+;"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_colon.activated.connect(self.get_shortname_colon)
        self.shortcut_comma = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+,"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_comma.activated.connect(self.get_shortname_comma)
        self.shortcut_parenthesis = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+9"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_parenthesis.activated.connect(self.get_shortname_parenthesis)
        self.shortcut_title_parenthesis = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+9"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_title_parenthesis.activated.connect(self.get_short_title_parenthesis)
        self.shortcut_gift = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+g"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_gift.activated.connect(lambda: self.gift_check_box.setChecked(False)
                                             if self.gift_check_box.isChecked() else self.gift_check_box.setChecked(True)) # pylint: disable=(line-too-long)
        self.shortcut_release = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+n"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_release.activated.connect(lambda: self.release_check_box.setChecked(False)
                                             if self.release_check_box.isChecked() else self.release_check_box.setChecked(True)) # pylint: disable=(line-too-long)
        self.shortcut_sale = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+s"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_sale.activated.connect(lambda: self.sale_check_box.setChecked(False)
                                             if self.sale_check_box.isChecked() else self.sale_check_box.setChecked(True)) # pylint: disable=(line-too-long)
        self.shortcut_next_image = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+right"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_next_image.activated.connect(self.next_image)
        self.shortcut_previous_image = QtWidgets.QShortcut(QtGui.QKeySequence("Alt+left"), self) # pylint: disable=(c-extension-no-member)
        self.shortcut_previous_image.activated.connect(self.previous_image)
        self.next_image_buttom.clicked.connect(self.next_image)
        self.previous_image_buttom.clicked.connect(self.previous_image)
        self.desc_iterator = 0
        self.next_desc_button.clicked.connect(self.next_description)
        self.previous_desc_button.clicked.connect(self.previous_description)
        self.next_desc_button.setDisabled(True)
        self.previous_desc_button.setDisabled(True)

    #     self.load_button2.clicked.connect(self.search_in_book)

    # def search_in_book(self):
        # ''' Download afresh book details '''
    #     self.clear_line_edit()

    def full_screen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


    def next_description(self):
        """ Next description from list """
        try:
            if len(self.dictionary['description']) > 1:
                self.desc_iterator += 1
                if len(self.dictionary['description']) == self.desc_iterator:
                    self.desc_iterator = 0

                self.description_text_edit.setPlainText(self.dictionary['description'][self.desc_iterator]) # pylint: disable=(c-extension-no-member,line-too-long)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def previous_description(self):
        """ Previous description from list """
        try:
            if len(self.dictionary['description']) > 1:
                self.desc_iterator -= 1
                if self.desc_iterator == -1:
                    self.desc_iterator = len(self.dictionary['description']) -1

                self.description_text_edit.setPlainText(self.dictionary['description'][self.desc_iterator]) # pylint: disable=(c-extension-no-member,line-too-long)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def get_short_title_parenthesis(self):
        ''' Remove subtitle between parenthesis and parenthesis '''
        try:
            parenthesis = re.compile("\((.*?)\)") # pylint: disable=(anomalous-backslash-in-string)
            short = re.sub(parenthesis,'' ,self.title_line.text())
            self.title_line.setText(short)
            self.title_line.setToolTip('<html><head/><body><p><b><span style=\" font-size:12pt;\">{}</span></b></p></body></html>'.format(self.title_line.text())) # pylint: disable=(line-too-long)
            self.amount_line.setFocus()
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def get_shortname_colon(self):
        ''' Remove subtitle between colon and dash '''
        try:
            colon = re.compile(':(.*?)-')
            short = re.sub(colon, " -", self.name_line.toPlainText())
            self.name_line.setText(short)
            self.name_line.setToolTip('<html><head/><body><p><b><span style=\" font-size:16pt;\">{}</span></b></p></body></html>'.format(self.name_line.toPlainText())) # pylint: disable=(line-too-long)
            self.amount_line.setFocus()
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def get_shortname_comma(self):
        ''' Remove subtitle between comma and dash '''
        try:
            comma = re.compile(',(.*?)-')
            short = re.sub(comma, " -", self.name_line.toPlainText())
            self.name_line.setText(short)
            self.name_line.setToolTip('<html><head/><body><p><b><span style=\" font-size:16pt;\">{}</span></b></p></body></html>'.format(self.name_line.toPlainText())) # pylint: disable=(line-too-long)
            self.amount_line.setFocus()
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def get_shortname_parenthesis(self):
        ''' Remove subtitle between parenthesis and dash '''
        try:
            parenthesis = re.compile("\((.*?)-") # pylint: disable=(anomalous-backslash-in-string)
            short = re.sub(parenthesis, "-", self.name_line.toPlainText())
            self.name_line.setText(short)
            self.name_line.setToolTip('<html><head/><body><p><b><span style=\" font-size:16pt;\">{}</span></b></p></body></html>'.format(self.name_line.toPlainText())) # pylint: disable=(line-too-long)
            self.amount_line.setFocus()
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def progress_fn(self):
        ''' Progress bar method'''
        try:
            self.progress_bar.setValue(0)
            QtCore.QCoreApplication.processEvents() # pylint: disable=(c-extension-no-member)
            self.msg_box.setWindowTitle('Pobieranie danych')
            self.msg_box.setWindowIcon(QtGui.QIcon(os.path.join(self.current_dir, "private", "image", "bookloader.png"))) # pylint: disable=(c-extension-no-member),(line-too-long)
            self.msg_box.setText('Pobieranie danych')
            self.msg_box.show()
            QtCore.QCoreApplication.processEvents() # pylint: disable=(c-extension-no-member)
            for i in range(101):
                if self.name_line.toPlainText() == '':
                    QtCore.QCoreApplication.processEvents() # pylint: disable=(c-extension-no-member)
                    time.sleep(0.05)
                    self.progress_bar.setValue(i)
                else:
                    i = 100
                    self.progress_bar.setValue(i)
        except Exception as error:  # pylint: disable=broad-except
            print("Progress fn: ",error)
            logger.info(error)

    def isbn_run(self):
        ''' Automatic run for ISBN edit line '''
        try:
            self.load_button.setDisabled(False)
            if len(self.isbn_line.text()) == 13:
                self.update_item()
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def update_item(self):
        ''' Update button method '''
        try:
            self.update_info_label.clear()
            self.item = self.isbn_line.text() # pylint: disable=(attribute-defined-outside-init)
            worker = Worker(self.search_item)

            worker.signals.finished.connect(self.get_source)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        except Exception as error:  # pylint: disable=broad-except
            print("Update item: ",error)
            logger.info(error)

    def search_item(self, progress_callback):
        ''' Search item, Mutli ThreadPool '''
        try:
            progress_callback.emit()
            que = Queue()
            thread_woo = Thread(target=lambda q, arg1: q.put(self.search_item_woo(arg1)),args=(que,self.item)) # pylint: disable=(line-too-long)
            thread_book = Thread(target=lambda q, arg1: q.put(self.search_item_book(arg1)),args=(que,self.item)) # pylint: disable=(line-too-long)
            thread_woo.start()
            thread_book.start()
            result = que.get()
            if result is None:
                thread_woo.join()
                thread_book.join()
            else:
                thread_woo.join()
        except Exception as error:  # pylint: disable=broad-except
            print("Search item: ",error)
            logger.info(error)

    def search_item_book(self, item): # pylint: disable=(unused-argument)
        ''' Search item in book '''
        book_start = time.time()
        try:
            self.dictionary_book = book_mode(self.item, self.gui) # pylint: disable=(attribute-defined-outside-init)
        except Exception as error:  # pylint: disable=broad-except
            print("Search item book: ",error)
            logger.info(error)
            self.dictionary_book = None # pylint: disable=(attribute-defined-outside-init)
        print("book  ",(time.time()) - book_start)
        return self.dictionary_book

    def search_item_woo(self, item): # pylint: disable=(unused-argument)
        ''' Search item in woocommerce '''
        woo_start = time.time()

        self.gui['name'] = True
        try:
            self.dictionary_woo = woo_get(self.item, self.gui) # pylint: disable=(attribute-defined-outside-init)
            if not self.dictionary_woo :
                self.dictionary_woo = None # pylint: disable=(attribute-defined-outside-init)
        except Exception as error:  # pylint: disable=broad-except
            print("Search item woo: ",error)
            logger.info(error)
            self.dictionary_woo = None # pylint: disable=(attribute-defined-outside-init)
        print("woo  ",(time.time()) - woo_start)

        return self.dictionary_woo

    def get_source(self):
        ''' Compere lists from Book and Woocommerce '''
        try:
            if self.dictionary_woo is None:
                self.dictionary = self.dictionary_book # pylint: disable=(attribute-defined-outside-init)
                self.dictionary['source'] = False
                self.next_desc_button.setDisabled(False)
                self.previous_desc_button.setDisabled(False)
            else:
                self.dictionary = self.dictionary_woo # pylint: disable=(attribute-defined-outside-init)
                self.dictionary['source'] = True

            if self.dictionary is None:
                self.update_info_label.setText("Produkt nie znaleziony")
            else:
                self.put_dict()
        except Exception as error:  # pylint: disable=broad-except
            print("Get source:",error)
            logger.info(error)

    def put_dict(self):
        ''' Put dictionary to editlines '''
        try:
            self.msg_box.close()
            self.image_list = []
            self.update_info_label.clear()

            if self.dictionary['source'] is False:
                self.get_image_list()
            else:
                self.image_list.append(self.dictionary_woo['image'])
            self.image_iterator = 0
            self.desc_iterator = 0
        except Exception as error:  # pylint: disable=broad-except
            print("Put Dict 1:",error)
            logger.info(error)

        try:
            self.dictionary["image"] = get_image(self.image_list[0], self.item)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            print("Put Dict image list :",error)
            self.dictionary["image"] = None

        # Convert binding to Polish names
        try:
            if ((self.dictionary['binding']).lower() == 'hardcover') or ((self.dictionary['binding']).lower() == 'twarda'): # pylint: disable=(line-too-long)
                self.dictionary['binding'] = 'twarda'
            elif ((self.dictionary['binding']).lower() == 'paperback') or ((self.dictionary['binding']).lower() == 'miękka'): # pylint: disable=(line-too-long)
                self.dictionary['binding'] = 'miękka'
            else:
                self.dictionary['binding'] = 'inna'
        except Exception as error:  # pylint: disable=broad-except
            print("Put Dict cover check: ",error)
            logger.info(error)
            self.dictionary['binding'] = 'inna'

        # Set dictionary to edit lines
        try:
            self.isbn_line.setText(self.item)
            if self.dictionary['source'] is False:
                self.name_line.setText(str(self.dictionary['title']) + ' - ' + str(self.dictionary['authors'])) # pylint: disable=(line-too-long)
            else:
                self.name_line.setText(str(self.dictionary['name']))


            if self.dictionary['description']:
                desc_with_html = [has_html for has_html in self.dictionary['description'] if find_html(has_html)] # pylint: disable=(line-too-long)

            if desc_with_html:
                if type(desc_with_html) is list:
                    self.description_text_edit.setPlainText(str(max(desc_with_html, key=len)))
                else:
                    self.description_text_edit.setPlainText(str(desc_with_html))
            elif type(self.dictionary['description']) is list:
                self.description_text_edit.setPlainText(str(max(self.dictionary['description'], key=len))) # pylint: disable=(line-too-long)
            else:
                self.description_text_edit.setPlainText(str(self.dictionary['description']))
            if self.dictionary['title']:
                self.title_line.setText(self.dictionary['title'])
            if self.dictionary['authors']:
                self.author_line.setText(self.dictionary['authors'])
            if self.dictionary['binding']:
                self.binding_box.setCurrentIndex(self.binding_box.findText(self.dictionary['binding']))
            if self.dictionary['publisher']:
                self.publisher_line.setText(self.dictionary['publisher'])
            if self.dictionary['categories']:
                self.category_line.setText(",".join(list(self.dictionary['categories'])))
            if self.dictionary['publish_date']:
                self.year_line.setText(self.dictionary['publish_date'])

        except Exception as error:  # pylint: disable=broad-except
            print("Put Dict to edit lines : ",error)
            logger.info(error)

        # Show image
        try:
            if self.dictionary['image']:
                self.cover_image_label.setPixmap(QtGui.QPixmap(self.dictionary['image'])) # pylint: disable=(c-extension-no-member)
                im = Image.open(self.dictionary["image"])
                self.image_size_label.setText(str(im.size))
        except Exception as error: # pylint: disable=broad-except
            print("Put Dict - show image: ",error)
            logger.info(error)

        # Show source and specific edit lines
        try:
            if self.dictionary['source'] is False:
                self.source_label.setText("Stwórz nowy produkt")
                self.amount_line.setText('1')
            else:
                self.source_label.setText("Zaktualizuj istniejący produkt")
                self.id_line.setText(str(self.dictionary['id']))
                if self.dictionary['tags']:
                    if 'Sale' in self.dictionary['tags']:
                        self.sale_check_box.setChecked(True)
                    if 'New Release' in self.dictionary['tags']:
                        self.release_check_box.setChecked(True)
                    if 'Perfect Gift' in self.dictionary['tags']:
                        self.release_check_box.setChecked(True)
                try:
                    self.sale_price_line.setText(str(self.dictionary['sale_price']))
                    self.amount_line.setText(str(self.dictionary['amount']))
                    self.price_line.setText(str(self.dictionary['price']))
                except Exception as error: # pylint: disable=broad-except
                    print("Put Dict - show price/amount: ",error)
                    logger.info(error)
        except Exception as error: # pylint: disable=broad-except
            print("Put Dict - source and other: ",error)
            logger.info(error)

        # Disable / Undisable buttons
        try:
            self.save_to_file_button.setDisabled(False)
            self.word_press_button.setDisabled(False)
            self.load_button.setDisabled(True)
            self.name_line.setToolTip('<html><head/><body><p><b><span style=\" font-size:16pt;\">{}</span></b></p></body></html>'.format(self.name_line.toPlainText())) # pylint: disable=(line-too-long)
            self.title_line.setToolTip('<html><head/><body><p><b><span style=\" font-size:16pt;\">{}</span></b></p></body></html>'.format(self.title_line.text())) # pylint: disable=(line-too-long)
            self.amount_line.setFocus()
        except Exception as error: # pylint: disable=broad-except
            print("Put Dict 3:",error)
            logger.info(error)

    def get_dictionary(self):
        ''' Getting dictionary from edit lines '''
        tags = []
        if self.sale_check_box.isChecked():
            tags.append('Sale')
        if self.release_check_box.isChecked():
            tags.append('New Release')
        if self.gift_check_box.isChecked():
            tags.append('Perfect Gift')

        try:
            self.dictionary_to_save = { # pylint: disable=(attribute-defined-outside-init)
                'isbn' : self.isbn_line.text(),
                'name' : self.name_line.toPlainText(),
                'title' : self.title_line.text(),
                'authors' : self.author_line.text(),
                'description' : self.description_text_edit.toPlainText(),
                'binding' : self.binding_box.currentText(),
                'publisher' : self.publisher_line.text(),
                'publish_date' : self.year_line.text(),
                'image': self.dictionary['image'],
                'categories' : self.category_to_save,
                'price' : self.price_line.text(),
                'amount' : self.amount_line.text(),
                'source' : self.dictionary['source'],
                'tags' : tags
            }

            if self.dictionary["source"]:
                self.dictionary_to_save['id'] = self.dictionary["id"]
            if self.sale_price_line.text():
                self.dictionary_to_save['sale_price'] = self.sale_price_line.text()

        except Exception as error:  # pylint: disable=broad-except
            print("Get dictionary method:\n",error)
            logger.info(error)
        return self.dictionary_to_save

    def send_to_wordpress(self):
        ''' Method to send product / Check line edit if not empty '''
        try:
            self.category_exist()
            self.woocommerce_dict = self.get_dictionary() # pylint: disable=(attribute-defined-outside-init)

            if (self.price_line.text() == '') or (self.amount_line.text() == '')or (self.description_text_edit.toPlainText() == '') or (self.name_line.toPlainText() == '') or (self.title_line.text() == '') or (self.author_line.text() == '') or (self.publisher_line.text() == '') or (self.year_line.text() == '') or (self.category_line.text() == ''): # pylint: disable=(line-too-long)
                self.msg_to_send.setWindowTitle('Uwaga!')
                self.msg_to_send.setWindowIcon(QtGui.QIcon(os.path.join(self.current_dir, "private", "image", "bookloader.png"))) # pylint: disable=(c-extension-no-member),(line-too-long)
                self.msg_to_send.setIcon(QtWidgets.QMessageBox.Warning) # pylint: disable=(c-extension-no-member)
                self.msg_to_send.setText('Podaj resztę danych')
                self.msg_to_send.show()
            else:
                worker = Worker(self.word)
                self.threadpool.start(worker)
                worker.signals.finished.connect(lambda: self.update_info_label.setText(self.message)) # pylint: disable=(line-too-long)
                self.clear_line_edit()
                self.load_button.setDisabled(True)
                self.next_desc_button.setDisabled(True)
                self.previous_desc_button.setDisabled(True)
        except Exception as error:  # pylint: disable=broad-except
            print("\nSend to wordpress method: \n",error)
            logger.info(error)

    def word(self,progress_callback):
        ''' Worker to send product to Woocommerce '''
        progress_callback.emit()
        try:
            self.post_product = woo(self.woocommerce_dict) # pylint: disable=(attribute-defined-outside-init)
            print(self.post_product)
            if self.post_product['source']:
                self.message = "Produkt został zaktualizowany" # pylint: disable=(attribute-defined-outside-init)
            else:
                self.message = "Dodano nowy produkt" # pylint: disable=(attribute-defined-outside-init)
        except Exception as error:  # pylint: disable=broad-except
            print("\nWord method:\n",error)
            logger.info(error)

    def get_image_list(self):
        """ Merge image list """
        try:
            for dictionary in self.dictionary['image']:
                for links in dictionary.values():
                    self.image_list += links

            for link in self.image_list:
                if link is None:
                    self.image_list.remove(link)

            self.image_list = list(set(self.image_list))
            print(self.image_list)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def next_image(self):
        """ Next image from list """
        try:
            if len(self.image_list) > 1:
                self.image_iterator += 1
                if len(self.image_list) == self.image_iterator:
                    self.image_iterator = 0

                self.dictionary["image"] = get_image(self.image_list[self.image_iterator], self.item) # pylint: disable=(line-too-long)
                im = Image.open(self.dictionary["image"])
                self.image_size_label.setText(str(im.size))
                self.cover_image_label.setPixmap(QtGui.QPixmap(self.dictionary['image'])) # pylint: disable=(c-extension-no-member)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def previous_image(self):
        """ Previous image from list """
        try:
            if len(self.image_list) > 1:
                self.image_iterator -= 1
                if self.image_iterator == -1:
                    self.image_iterator = len(self.image_list) -1

                self.dictionary["image"] = get_image(self.image_list[self.image_iterator], self.item) # pylint: disable=(line-too-long)
                im = Image.open(self.dictionary["image"])
                self.image_size_label.setText(str(im.size))
                self.cover_image_label.setPixmap(QtGui.QPixmap(self.dictionary['image'])) # pylint: disable=(c-extension-no-member)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def change_image(self):
        ''' Change image button method '''
        try:
            image_folder = self.config.get("General", "image_folder")
            image_path = os.path.join(self.current_dir, image_folder)
            image = os.path.join(image_path, str(self.item)+".jpg")

            self.fileName, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Open File", "",'Images (*.png *.xpm *.jpg)', options=self.options) # pylint: disable=(c-extension-no-member),(attribute-defined-outside-init),(line-too-long)
            print(str(self.fileName))

            try:
                shutil.copy2(self.fileName, image)
            except Exception as error:  # pylint: disable=broad-except
                print(error)
                logger.info(error)
            self.dictionary['image'] = image
            im = Image.open(self.dictionary["image"])
            self.image_size_label.setText(str(im.size))
            self.cover_image_label.setPixmap(QtGui.QPixmap(self.dictionary['image'])) # pylint: disable=(c-extension-no-member)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def clear_line_edit(self):
        ''' Clear edit lines method'''
        try:
            self.isbn_line.clear()
            self.title_line.clear()
            self.author_line.clear()
            self.publisher_line.clear()
            self.year_line.clear()
            self.amount_line.clear()
            self.price_line.clear()
            self.description_text_edit.clear()
            self.name_line.clear()
            self.category_line.clear()
            self.cover_image_label.clear()
            self.source_label.clear()
            self.progress_bar.setValue(0)
            self.id_line.clear()
            self.sale_price_line.clear()
            self.image_size_label.clear()
            self.save_to_file_button.setDisabled(True)
            self.word_press_button.setDisabled(True)
            self.isbn_line.setFocus()
            self.sale_check_box.setChecked(False)
            self.release_check_box.setChecked(False)
            self.gift_check_box.setChecked(False)
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    def save_item(self):
        ''' Save to file method '''
        self.category_exist() # Start function to check category from header list
        self.get_dictionary()
        self.dictionary_to_save['image'] = (self.isbn_line.text())
        try:
            self.fileNameSave, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Open File", "","All Files (*)", options=self.options) # pylint: disable=(attribute-defined-outside-init),(c-extension-no-member)(line-too-long)
            self.fileNameSave, self.fileNameSave_extension = os.path.splitext(self.fileNameSave) # pylint: disable=(attribute-defined-outside-init)

            if self.fileNameSave_extension == '.txt': # pylint: disable=(attribute-defined-outside-init)
                self.save_item_txt()
            else:
                self.fileNameSave_extension = ".csv" # pylint: disable=(attribute-defined-outside-init)
                self.save_item_csv()
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

        self.isbn_line.setFocus()

    # Save to csv method
    def save_item_csv(self):
        ''' Save to .csv '''
        try:
            with open(self.fileNameSave + self.fileNameSave_extension, 'w',encoding=None) as f:
                w = csv.DictWriter(f, self.dictionary_to_save.keys())
                w.writeheader()
                w.writerow(self.dictionary_to_save)
            if not len(self.fileNameSave) == 0:
                self.clear_line_edit()
                self.update_info_label.setText("File saved")
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    # Save to txt method
    def save_item_txt(self):
        ''' Save to .txt '''
        try:
            with io.open(self.fileNameSave + self.fileNameSave_extension, 'w',encoding=None) as f:
                f.write(json.dumps(self.dictionary_to_save))
            self.clear_line_edit()
            self.update_info_label.setText("File saved")
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

    # Open settings button method
    def open_settings(self):
        ''' Open settings method '''
        self.settings_window = QtWidgets.QDialog() # pylint: disable=(attribute-defined-outside-init),(c-extension-no-member)
        self.settings_window.setWindowIcon(QtGui.QIcon(os.path.join(self.current_dir, "private", "image", "bookloader.png"))) # pylint: disable=(c-extension-no-member, line-too-long)
        self.settings_ui = Ui_Settings() # pylint: disable=(attribute-defined-outside-init)
        self.settings_ui.setupUi(self.settings_window)

        # Set Parser for config.ini
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config', 'conf.ini'))
        self.settings_ui.isbndb_check_box.setChecked(util.strtobool(config.get('Source', 'isbndb')))
        self.settings_ui.google_check_box.setChecked(util.strtobool(config.get('Source', 'google')))
        self.settings_ui.amazon_check_box.setChecked(util.strtobool(config.get('Source', 'amazon')))
        self.settings_ui.goodreads_check_box.setChecked(util.strtobool(config.get('Source', 'goodreads'))) # pylint: disable=(line-too-long)
        for radio in self.settings_ui.list_of_radio:
            if config.get('Validator', 'priority') in radio.text().lower():
                radio.setChecked(True)
        self.settings_window.show()

    # Get header category list from .ini file
    def categories_main_list(self):
        ''' Category list '''
        try:
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(__file__), 'config', 'conf.ini'))
            self.category_completer_list = ast.literal_eval(config.get("Category", "categories"))
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)
        return self.category_completer_list

    # Check category button method
    def category_exist(self):
        ''' Compare category list '''
        self.category_to_save = [] # pylint:disable=(attribute-defined-outside-init)
        try:
            self.cat = self.category_line.text().split(',') # pylint: disable=(attribute-defined-outside-init)
            for i in self.cat:
                if i[0] == ' ':
                    i = i[1:]
                if i in self.category_completer_list:
                    self.category_to_save.append(i)

            self.category_line.setText(",".join(self.category_to_save))
        except Exception as error:  # pylint: disable=broad-except
            print(error)
            logger.info(error)

        return self.category_to_save

    def closeEvent(self, event):
        ''' Close event method '''
        reply = QtWidgets.QMessageBox.question(self, 'Close window', # pylint: disable=(c-extension-no-member)
            'Are you sure you want to close the window?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No) # pylint: disable=(c-extension-no-member)

        if reply == QtWidgets.QMessageBox.Yes: # pylint: disable=(c-extension-no-member)
            event.accept()
            print('Window closed')
            cache = pathlib.Path(os.path.join(self.current_dir, "cache"))
            if cache.exists() and cache.is_dir():
                shutil.rmtree(cache)
        else:
            event.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv) # pylint: disable=(c-extension-no-member)
    MyMainWindow = MyMainWindow()
    MyMainWindow.show()
    sys.exit(app.exec_())
