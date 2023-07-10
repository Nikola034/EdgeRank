#autor: Nikola Bandulaja SV74/2022
#Projekat je izradjivan u periodu od 15. do 23. juna
import datetime
import os
import pickle
import re

from trie import Trie
import networkx as nx
from parse_files import load_friends, load_comments, load_reactions, load_shares, load_statuses
from heap import MaxHeap

G = nx.DiGraph()
friends = {}
comments = {}
reactions = {}
shares = {}
statuses = {}

def StartMenu():
    print("1 - Log in")
    print("2 - Exit")

def UserMenu():
    print("1 - Statuses")
    print("2 - Search")
    print("3 - Logout")

#DATA LOADING AND SERIALIZATION

def LoadData():
    global friends, comments, reactions, shares, statuses
    friends = load_friends("dataset/friends.csv")
    comments = load_comments("dataset/test_comments.csv")
    reactions = load_reactions("dataset/test_reactions.csv")
    shares = load_shares("dataset/test_shares.csv")
    statuses = load_statuses("dataset/test_statuses.csv")

def LoadOriginalData():
    global friends, comments, reactions, shares, statuses
    friends = load_friends("dataset/friends.csv")
    comments = load_comments("dataset/original_comments.csv")
    reactions = load_reactions("dataset/original_reactions.csv")
    shares = load_shares("dataset/original_shares.csv")
    statuses = load_statuses("dataset/original_statuses.csv")

def SerializeData():
    global comments, reactions, shares, statuses
    with open("serialized_data/serial_comments.csv", "wb") as file:
        pickle.dump(comments, file)
    with open("serialized_data/serial_reactions.csv", "wb") as file:
        pickle.dump(reactions, file)
    with open("serialized_data/serial_shares.csv", "wb") as file:
        pickle.dump(shares, file)
    with open("serialized_data/serial_statuses.csv", "wb") as file:
        pickle.dump(statuses, file)
    return comments, reactions, shares, statuses

def LoadSerializedData():
    global comments, reactions, shares, statuses
    with open("serialized_data/serial_comments.csv", "rb") as file:
        comments = pickle.load(file)
    with open("serialized_data/serial_reactions.csv", "rb") as file:
        reactions = pickle.load(file)
    with open("serialized_data/serial_shares.csv", "rb") as file:
        shares = pickle.load(file)
    with open("serialized_data/serial_statuses.csv", "rb") as file:
        statuses = pickle.load(file)
    return comments, reactions, shares, statuses

def MakeSerializedGraph():
    global G
    with open("serialized_data/serial_friends.csv", "wb") as file:
        pickle.dump(G, file)

def LoadSerializedGraph():
    with open("serialized_data/serial_friends.csv", "rb") as file:
        return pickle.load(file)
#END

def calculate_affinity(user, other):
    affinity = 0

    weights = {
        'reaction': {
            'likes': 0.5,
            'loves': 0.6,
            'wows': 0.6,
            'hahas': 0.5,
            'angrys': 0.1,
            'sads': 0.2,
            'special': 0.2
        },
        'comment': 1.0,
        'share': 1.5
    }

    if user in shares.keys():
        for share in shares[user]:
            if other == statuses[share["status_id"]]["author"]:
                time_elapsed = (datetime.datetime.now() - share["status_shared"]).total_seconds()
                time_weight = calculate_time_weight(time_elapsed)
                affinity += weights["share"] * time_weight

    if user in comments.keys():
        for comment in comments[user]:
            if other == statuses[comment["status_id"]]["author"]:
                time_elapsed = (datetime.datetime.now() - comment["comment_published"]).total_seconds()
                time_weight = calculate_time_weight(time_elapsed)
                affinity += weights["comment"] * time_weight

    if user in reactions.keys():
        for reaction in reactions[user]:
            if other == statuses[reaction["status_id"]]["author"]:
                time_elapsed = (datetime.datetime.now() - reaction["reacted"]).total_seconds()
                time_weight = calculate_time_weight(time_elapsed)
                affinity += weights["reaction"][reaction["type_of_reaction"]] * time_weight

    return affinity

def calculate_time_weight(time_elapsed):
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

def calculate_popularity(status):
    weights = {
        'shares': 1,
        'comments': 0.8,
        'likes': 0.3,
        'loves': 0.4,
        'wows': 0.4,
        'hahas': 0.3,
        'angrys': 0.1,
        'sads': 0.1
    }

    popularity = status["num_shares"] * weights["shares"] + status["num_comments"] * weights["comments"]\
                 + status["num_likes"] * weights["likes"] + status["num_loves"] * weights["loves"]\
                 + status["num_wows"] * weights["wows"] + status["num_hahas"] * weights["hahas"]\
                 + status["num_angrys"] * weights["angrys"] + status["num_sads"] * weights["sads"]

    return popularity

def generate_graph_from_friends(friends):
    graph = nx.DiGraph()

    graph.add_nodes_from(friends.keys())

    for user, friends_list in friends.items():
        for friend in friends_list:
            affinity = calculate_affinity(user, friend)
            graph.add_edge(user, friend, weight=affinity)

    for user, shares_list in comments.items():
        for share in shares_list:
            author = statuses[share["status_id"]]["author"]
            if (user, author) not in G.edges:
                affinity = calculate_affinity(user, author) * 0.9
                graph.add_edge(user, author, weight=affinity)

    for user, comments_list in comments.items():
        for comment in comments_list:
            author = statuses[comment["status_id"]]["author"]
            if (user, author) not in G.edges:
                affinity = calculate_affinity(user, author) * 0.8
                graph.add_edge(user, author, weight=affinity)

    for user, reactions_list in reactions.items():
        for reaction in reactions_list:
            author = statuses[reaction["status_id"]]["author"]
            if (user, author) not in G.edges:
                affinity = calculate_affinity(user, author) * 0.7
                graph.add_edge(user, author, weight=affinity)

    return graph

def generate_feed(user):
    relevant_statuses = []
    weights = {
        'affinity': 5,
        'popularity': 3,
    }

    for status_id, status in statuses.items():
        relevance = 0
        if (user, status["author"]) in G.edges:
            relevance += G[user][status["author"]]["weight"] * weights["affinity"]
            popularity = calculate_popularity(status)
            relevance += popularity * weights["popularity"]
            time_elapsed = (datetime.datetime.now() - status["status_published"]).total_seconds()
            time_weight = calculate_time_weight(time_elapsed)
            relevance *= time_weight
            relevant_statuses.append((relevance, status_id))

    return MaxHeap(relevant_statuses)

def search(user, parameter, search_string):
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
            popularity = calculate_popularity(status)
            relevance += popularity * weights["popularity"]
            time_elapsed = (datetime.datetime.now() - status["status_published"]).total_seconds()
            time_weight = calculate_time_weight(time_elapsed)
            relevance *= time_weight

            if status["status_id"] == "644891892279936_801054159997041":
                pass
            if words_weight == 1:
                relevance *= 1000000
            else:
                relevance *= words_weight
            relevant_statuses.append((relevance, status["status_id"]))

    return MaxHeap(relevant_statuses)

def display_feed(relevant_statuses):
    n = len(relevant_statuses)
    if n != 0:
        for i in range(0, n):
            if i < 10:
                print(statuses[relevant_statuses.pop()[1]])
            else:
                break
    else:
        print("No results")

#LoadOriginalData()

#G = generate_graph_from_friends(friends)
#MakeSerializedGraph()
#SerializeData()
#LoadSerializedData()

#display_feed(generate_feed("Sarina Hudgens"))
#display_feed(search("Sarina Hudgens", "status_message", "florida"))

print("Molim vas pokrenite GUI.PY ako se ne pokrene sam. To zavisi od vase RUN konfiguracije.")

"""
end = False

while not end:
    StartMenu()
    print("Choose an option: ")
    command = input()
    match command:
        case '1':
            end2 = False

            while not end2:
                print("Input your firstname and lastname: ")
                user = input()

                if user not in G.nodes:
                    print("The user named ", user, " does not exist in our database.")
                else:
                    end3 = False

                    while not end3:
                        UserMenu()
                        print("Choose an option: ")
                        command1 = input()
                        match command1:
                            case '1':
                                display_feed(generate_feed(user))
                            case '2':
                                print("1 - Search by author: ")
                                print("2 - Search by status text: ")
                                commands = input()
                                match commands:
                                    case '1':
                                        print("Search: ")
                                        search_string = input()
                                        display_feed(search(user, "author", search_string))
                                    case '2':
                                        print("Search: ")
                                        search_string = input()
                                        display_feed(search(user, "status_message", search_string))
                                    case other:
                                        print("Invalid input!")
                            case '3':
                                end2 = True
                                end3 = True
                            case other:
                                print("Invalid input!")

        case '2':
            end = True
        case other:
            print("Invalid input!")
"""
