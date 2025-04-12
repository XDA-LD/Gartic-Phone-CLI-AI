from socket import *
import nltk
from nltk.corpus import words

'''
---START OF VALID SENTENCE CHECKING
'''
# Ensure the words dataset is downloaded
try:
    nltk.data.find("corpora/words.zip")
except LookupError:
    print("Downloading 'words' dataset...\n Please wait, this will take a few seconds")
    nltk.download("words")

english_words = set(words.words())


def is_real_word_sentence(text):
    """
    this method checks sentence validity.
    For a sentence to be valid, half of its words must be real.
    We want this to allow the player some comical flexibility

    'tHiS is TekHniKaLy wrong' will still be allowed
    but 'afbafbf' or 'Yes iwsa will asdss yau' is not allowed
    """

    words_in_text = text.split()
    valid_words = [word.lower() for word in words_in_text if word.lower() in english_words]

    return len(valid_words) / max(1, len(words_in_text)) > 0.5  # Requires 50% real words


def validated_sentence(potential_segment_sentence):
    """
    :param potential_segment_sentence: Sentence to evaluate

    Checks if user has inputted a valid sentence,
    and verifies if the uses wishes to send it regardless.
    """
    if is_real_word_sentence(potential_segment_sentence):
        return potential_segment_sentence
    else:
        response = input("Your sentence doesn't seem right,\nDo you still wish to proceed? (y/n) : ")
        if response.lower() == "y":
            return potential_segment_sentence
        else:
            return validated_sentence(input("Enter your new sentence: "))


'''
---END OF VALID SENTENCE CHECKING
'''

'''
---START OF CONNECTION ESTABLISHING
'''

serverName = '127.0.0.1'
serverPort = 13000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
connected = True

totalPlayerCount = int(clientSocket.recv(1024).decode())
print("You are playing with ", totalPlayerCount, "players.")

'''
---END OF CONNECTION ESTABLISHING
'''


'''
---START OF MAIN GAME LOOP
'''
for i in range(totalPlayerCount):
    print("---------------------------")
    print("Round ", i + 1)
    print("Waiting for other players...")

    try:
        prevStory = clientSocket.recv(1024).decode()

        if prevStory in ["DISCONNECT", "TIMEOUT"]:
            print(f"❌ Server says: {prevStory}. You have been removed from the game.")
            break

        if i == 0:
            message = input("Start Your Story: ")
        else:
            print("You have 30 seconds.\nContinue the story: ")
            message = input(prevStory + "...")

        message = validated_sentence(message)
        clientSocket.send(message.encode())

    except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError, OSError):
        print("--- Connection lost! The server removed you. ---")
        connected = False
        break

if connected:
    print("------------------------------------------------")
    print("Waiting for the rest of the players to finish...")
    try:
        print(clientSocket.recv(1024).decode())
    except:
        print("The game ended unexpectedly.")
    clientSocket.close()
'''
---END OF MAIN GAME LOOP
'''