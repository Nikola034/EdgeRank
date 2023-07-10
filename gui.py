#autor: Nikola Bandulaja SV74/2022
#Projekat je izradjivan u periodu od 15. do 23. juna
import functools
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, \
    QTextEdit, QPushButton, QScrollArea, QLineEdit, QCompleter, QSizePolicy, QMessageBox, QFrame
from PyQt5.QtGui import QFont, QTextCharFormat, QColor
from PyQt5.QtCore import QStringListModel, pyqtSignal
import datetime
import os
import pickle
import re

from trie import Trie
import networkx as nx
from parse_files import load_friends, load_comments, load_reactions, load_shares, load_statuses
from heap import MaxHeap
from main import LoadData, LoadSerializedData, LoadSerializedGraph

G = LoadSerializedGraph()
comments, reactions, shares, statuses = LoadSerializedData()
pass
class LoginWindow(QWidget):
    loginSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setGeometry(800, 300, 400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        username_label = QLabel("Username:")
        username_label.setFont(QFont("Arial", 16, QFont.Bold))
        username_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(username_label)

        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)
        self.username_input.setFont(QFont("Arial", 16, QFont.Bold))

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

    def login(self):
        username = self.username_input.text()

        if username in G.nodes:
            self.loginSignal.emit(username)
            self.close()
        else:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Error")
            msg_box.setText("The user named " + username + " does not exist in our database.")
            msg_box.exec_()

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()

        self._user = user
        self.setWindowTitle("Feed - " + user)
        self.setGeometry(340, 230, 1200, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        search_layout = QHBoxLayout()


        self.feed_button = QPushButton("Feed")
        self.feed_button.clicked.connect(functools.partial(self.show_feed, "feed"))
        search_layout.addWidget(self.feed_button)

        self.search_combobox = QComboBox()
        self.search_combobox.addItems(["Author", "Status_Message"])
        search_layout.addWidget(self.search_combobox)

        self.search_bar = QLineEdit()
        self.search_bar.textChanged.connect(self._handle_search)
        search_layout.addWidget(self.search_bar)


        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(functools.partial(self.show_feed, "search"))
        search_layout.addWidget(self.search_button)

        self.layout.addLayout(search_layout)

        self.posts_label = QLabel("Posts:")
        self.posts_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.layout.addWidget(self.posts_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.posts_widget = QWidget()
        scroll_area.setWidget(self.posts_widget)

        self.posts_layout = QVBoxLayout()
        self.posts_widget.setLayout(self.posts_layout)

        self.layout.addWidget(scroll_area)

        self._words = Trie()

        for status_id, status in statuses.items():
            words = re.split(r'[,\s.?!():\'"\`/\-\']', (status["author"] + status["status_message"]))
            for word in words:
                self._words.insert(word.lower().strip('.,?!-()/"`\-\''))

        self.show()

    def _handle_search(self):
        completer = QCompleter(self)
        self.search_bar.setCompleter(completer)

        sample_model = []

        prefix = self.search_bar.text()
        if len(prefix) != 0:
            for word in self._words.prefix(prefix.lower()):
                if prefix[0].isupper():
                    sample_model.append(word[0].capitalize())
                else:
                    sample_model.append(word[0])

        completer.setModel(QStringListModel(sample_model))
    def _generate_feed(self):
        user = self._user
        relevant_statuses = []
        weights = {
            'affinity': 5,
            'popularity': 3,
        }

        for status_id, status in statuses.items():
            relevance = 0
            if (user, status["author"]) in G.edges:
                relevance += G[user][status["author"]]["weight"] * weights["affinity"]
                popularity = self._calculate_popularity(status)
                relevance += popularity * weights["popularity"]
                time_elapsed = (datetime.datetime.now() - status["status_published"]).total_seconds()
                time_weight = self._calculate_time_weight(time_elapsed)
                relevance *= time_weight
                relevant_statuses.append((relevance, status_id))

        return MaxHeap(relevant_statuses)

    def _calculate_time_weight(self, time_elapsed):
        if time_elapsed <= 86400:
            return 5
        if time_elapsed > 86400 and time_elapsed <= 432000:
            return 3
        if time_elapsed > 432000 and time_elapsed <= 864000:
            return 1
        if time_elapsed > 864000 and time_elapsed <= 2592000:
            return 0.3
        if time_elapsed > 2592000 and time_elapsed <= 5184000:
            return 0.1
        if time_elapsed > 5184000 and time_elapsed <= 10184000:
            return 0.01
        return 0.001

    def _calculate_popularity(self, status):
        weights = {
            'shares': 1,
            'comments': 0.8,
            'likes': 0.3,
            'loves': 0.4,
            'wows': 0.4,
            'hahas': 0.3,
            'angrys': 0.1,
            'sads': 0.1,
            'special': 0.2
        }

        popularity = status["num_shares"] * weights["shares"] + status["num_comments"] * weights["comments"] \
                     + status["num_likes"] * weights["likes"] + status["num_loves"] * weights["loves"] \
                     + status["num_wows"] * weights["wows"] + status["num_hahas"] * weights["hahas"] \
                     + status["num_angrys"] * weights["angrys"] + status["num_sads"] * weights["sads"]

        return popularity

    def _search(self):
        user = self._user
        parameter = self.search_combobox.currentText().lower()
        search_string = self.search_bar.text()

        if search_string[0] == '"' and search_string[-1] == '"':
            pattern = self.search_bar.text().strip('"').lower()
            relevant_statuses = []
            containing_phrases = []
            weights = {
                'affinity': 5,
                'popularity': 3,
            }

            for status_id, status in statuses.items():
                if len(self.kmp(status["status_message"].lower(), pattern)) != 0:
                    containing_phrases.append(status)

            for item in containing_phrases:
                relevance = 0
                if (user, item["author"]) in G.edges:
                    relevance += G[user][item["author"]]["weight"] * weights["affinity"]
                    popularity = self._calculate_popularity(item)
                    relevance += popularity * weights["popularity"]
                    time_elapsed = (datetime.datetime.now() - item["status_published"]).total_seconds()
                    time_weight = self._calculate_time_weight(time_elapsed)
                    relevance *= time_weight

                    relevant_statuses.append((relevance, item["status_id"]))
        else:
            search_string = self.search_bar.text().lower()
            relevant_statuses = []
            containing_search_words = []
            weights = {
                'affinity': 5,
                'popularity': 3,
            }
            for status_id, status in statuses.items():
                if status_id == "644891892279936_801054159997041":
                    pass
                tr = Trie()
                words = re.split(r'[,\s.?!():\-\']', status[parameter])
                for word in words:
                    tr.insert(word.lower().strip('.,?!-()'))

                i = 0
                search_words = search_string.split()
                for word in search_words:
                    x = tr.search(word.lower())
                    if len(x) != 0:
                        i += 1

                if i != 0:
                    words_weight = i / len(search_words)
                    containing_search_words.append((status, words_weight))

            for item in containing_search_words:
                status = item[0]
                words_weight = item[1]
                relevance = 0
                if (user, status["author"]) in G.edges:
                    relevance += G[user][status["author"]]["weight"] * weights["affinity"]
                    popularity = self._calculate_popularity(status)
                    relevance += popularity * weights["popularity"]
                    time_elapsed = (datetime.datetime.now() - status["status_published"]).total_seconds()
                    time_weight = self._calculate_time_weight(time_elapsed)
                    relevance *= time_weight

                    if status["status_id"] == "644891892279936_801054159997041":
                        pass
                    if words_weight == 1:
                        relevance *= 1000000
                    else:
                        relevance *= words_weight
                    relevant_statuses.append((relevance, status["status_id"]))

        return MaxHeap(relevant_statuses)

    def _phrases(self):
        user = self._user
        pattern = self.search_bar.text()
        relevant_statuses = []
        containing_phrases = []
        weights = {
            'affinity': 5,
            'popularity': 3,
        }

        for status_id, status in statuses.items():
            if len(self.kmp(status["status_message"], pattern)) != 0:
                containing_phrases.append(status)

        for item in containing_phrases:
            relevance = 0
            if (user, item["author"]) in G.edges:
                relevance += G[user][item["author"]]["weight"] * weights["affinity"]
                popularity = self._calculate_popularity(item)
                relevance += popularity * weights["popularity"]
                time_elapsed = (datetime.datetime.now() - item["status_published"]).total_seconds()
                time_weight = self._calculate_time_weight(time_elapsed)
                relevance *= time_weight

                relevant_statuses.append((relevance, item))

        return MaxHeap(relevant_statuses)

    def show_feed(self, option):
        for i in reversed(range(self.posts_layout.count())):
            self.posts_layout.itemAt(i).widget().setParent(None)

        if option == "feed":
            relevant_statuses = self._generate_feed()
        elif option == "search":
            relevant_statuses = self._search()
        else:
            relevant_statuses = self._phrases()
        n = len(relevant_statuses)
        if n != 0:
            for i in range(0, n):
                if i < 10:
                    status = statuses[relevant_statuses.pop()[1]]
                    post_widget = QWidget()
                    post_layout = QVBoxLayout()
                    post_widget.setLayout(post_layout)

                    marked_text1 = status["author"]
                    if len(self.search_bar.text()) >= 2:
                        if self.search_bar.text()[0] == '"' and self.search_bar.text()[-1] == '"':
                            marked_text1 = self.highlight_text(self.search_bar.text().strip('"'), status["author"])
                    if option == "search" and marked_text1 == status["author"]:
                        marked_text1 = self.highlight_text(self.search_bar.text(), status["author"])

                    author_label = QLabel(f"Author: {marked_text1}")
                    author_label.setFont(QFont("Arial", 10))
                    post_layout.addWidget(author_label)

                    marked_text2 = status["status_message"]
                    if len(self.search_bar.text()) >= 2:
                        if self.search_bar.text()[0] == '"' and self.search_bar.text()[-1] == '"':
                            marked_text2 = self.highlight_text(self.search_bar.text().strip('"'), status["status_message"])
                    if option == "search" and marked_text2 == status["status_message"]:
                        marked_text2 = self.highlight_text(self.search_bar.text(), status["status_message"])

                    status_text_label = QLabel(f"Status Text: {marked_text2}")
                    status_text_label.setFont(QFont("Arial", 10))
                    post_layout.addWidget(status_text_label)

                    date_label = QLabel(f"Date: {status['status_published']}")
                    date_label.setFont(QFont("Arial", 10))
                    post_layout.addWidget(date_label)

                    comments_label = QLabel(f"Comments: {status['num_comments']}")
                    comments_label.setFont(QFont("Arial", 10))
                    post_layout.addWidget(comments_label)

                    reactions_label = QLabel(f"Reactions: {status['num_reactions']}")
                    reactions_label.setFont(QFont("Arial", 10))
                    post_layout.addWidget(reactions_label)

                    separator = QFrame()
                    separator.setFrameShape(QFrame.HLine)
                    separator.setFrameShadow(QFrame.Sunken)
                    post_layout.addWidget(separator)

                    self.posts_layout.addWidget(post_widget)

                else:
                    break
        else:
            pass

    def _generate_table(self, P):
        m = len(P)
        table = [0] * m

        k = 0
        i = 1

        while i < m:
            if P[i] == P[k]:
                table[i] = k + 1
                i = i + 1
                k = k + 1
            elif k > 0:
                k = table[k - 1]
            else:
                i = i + 1

        return table

    def kmp(self, T, P):
        n = len(T)
        m = len(P)

        if m == 0:
            return [0]

        table = self._generate_table(P)

        k = 0
        i = 0

        found = []

        while i < n:
            if T[i] == P[k]:
                if k == m - 1:
                    found.append(i - m + 1)
                    k = table[k - 1]
                else:
                    i = i + 1
                    k = k + 1
            elif k > 0:
                k = table[k - 1]
            else:
                i = i + 1

        return found

    def highlight_text(self, query, text): #stackowerflow
        pattern = re.compile(r'(\b|\#|\d+)' + re.escape(query.replace('-', r'\b-\b|\d+')) + r'(\b|\d+|\b\W)',
                             re.IGNORECASE)
        highlighted_text = pattern.sub(r'<span style="background-color: yellow;">\g<0></span>', text)
        return highlighted_text


if __name__ == "__main__":
    app = QApplication(sys.argv)

    login_window = LoginWindow()
    main_window = None


    def show_main_window(username):
        global main_window
        main_window = MainWindow(username)
        main_window.show()


    login_window.loginSignal.connect(show_main_window)
    login_window.show()
    sys.exit(app.exec())