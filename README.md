# EdgeRank
This application represents usage of EdgeRank algorithm used for finding relevant posts to be shown on user's feed. The application is made using Python, and its module PyQt for making GUI.

## Implementation
I used various data structures and algorithms like Trie, Graph and Tree. Because of the large size of the data, i used serialization.
Once the main graph for affinity between users is made, it won't be changed anymore. 
The users can see their feed, which includes top 10 relevant posts.
Also, they can search all posts by an author or by post message. This type of search is implemented using Trye Prefix search.
An extra feature is searching phrases, implemented using KMP algorithm for searching.
