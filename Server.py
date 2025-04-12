import random
import socket
import time
from socket import *
import threading
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import requests
import json

serverPort = 13000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(5)
bot = input("Which bot do you wish to use to replace disconnected players? "
            "\n'GPT-2'(Offline) or 'oLama'(Recommended/Online)?"
            "\nChoice : ")
print('The server is ready to receive')
API_KEY = "YOUR_API_KEY_HERE"
if API_KEY == "YOUR_API_KEY_HERE":
    print("--- WARNING - OLama API KEY NOT SPECIFIED, FALLING BACK TO DistilGPT-2 ---")
    bot = "GPT-2"
print("📥 Downloading DistilGPT-2 model (this may take a few minutes)...")
AutoModelForCausalLM.from_pretrained("distilgpt2")  # Downloads model weights (~50MB)
AutoTokenizer.from_pretrained("distilgpt2")  # Downloads tokenizer
print("✅ Model download complete!")
print("⏳ Initializing DistilGPT-2 model on CPU...")
generator = pipeline("text-generation", model="distilgpt2", device=-1)  # Force CPU usage
print("✅ Model loaded and ready!")
time.sleep(3)

'''
---START OF VARIABLE DECLARATION
'''

totalPlayerCount = 0
while totalPlayerCount < 3:
    totalPlayerCount = int(input("How many players will be in the game : "))
stories = ["" for x in range(totalPlayerCount)]
previousStory = ["" for x in range(totalPlayerCount)]
roundCompletion = [0 for x in range(totalPlayerCount)]
playerOnline = [True for x in range(totalPlayerCount)]
playerThreads = []
currentPlayerCount = 0
gameStarted = False
entered = False
lamaRanks = ""

'''
---END OF VARIABLE DECLARATION
'''

'''
---START OF HELPER FUNCTIONS
'''


def checkRoundOver(completion, currentRound):
    for i in range(len(completion)):
        if completion[i] < currentRound and playerOnline[i]:
            return False
    return True


def lastRound(clientSocket, player_index, currentRound):
    global lamaRanks

    if playerOnline[player_index]:
        print(player_index + 1, " is Waiting for the rest of the players...")
        while not checkRoundOver(roundCompletion, currentRound):
            continue
        result = ''
        for i in range(totalPlayerCount):
            result += f'---------\nStory {i + 1}: {stories[i]}\n----------'

        # We will let the AI Vote instead of players
        if lamaRanks == "":
            lamaRanks = oLamaCompletor(result, "RANK THE FOLLOWING STORIES AND TAKE TOP 3. DO NOT SEND ANYTHING BEYOND RANKING, ONLYYY RANKING, use the following format, RANK 1: Story X\nRANK 2: Story X\nRANK 3: Story X\n", 200)
        result += "\n" + lamaRanks

        clientSocket.send(result.encode())


def oLamaCompletor(previous_sentence, segment, token=35):
    """Generates a short sentence continuation using OpenRouter's Free LLaMA model."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {"role": "system", "content": segment},
            {"role": "user", "content": f"{previous_sentence} ..."}
        ],
        "max_tokens": token
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)

    if response.status_code == 200:
        try:
            json_response = response.json()
            message = json_response.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "").strip()

            if content:
                return content
            return "Error: No valid response"
        except json.JSONDecodeError:
            return "Error: Failed to parse API response"
    else:
        return f"API Error {response.status_code}: {response.text}"


def generate_placeholder(previous_sentence, segment):
    if bot != 'GPT-2':
        """Generates a small sentence continuation using GPT-2 (CPU only)."""
        print(f"📝 Generating text for: '{previous_sentence}'...")
        response = generator(previous_sentence, max_length=25, num_return_sequences=1)
        result = " ".join(response[0]["generated_text"].split()[-3:])  # Get only 2-3 words
        print(f"✅ Generated: {result}")
        return result
    else:
        if len(previous_sentence) > 20:
            previous_sentence = previous_sentence[-20:]

        character = random.choice(["Be very cheesy and joke a lot, ",
                                   "Be Mystical, ", "Be Funny",
                                   "Be jokingly offensive such as pineapple on pizza etc and "])
        if segment == 'start':
            return oLamaCompletor("", character + " Start a random new mystical sentence regardless of input")
        elif segment == 'mid':
            return oLamaCompletor(previous_sentence, character + " Continue this sentence naturally : ")
        else:
            return oLamaCompletor(previous_sentence, character + " End this sentence naturally : ")


'''
---END OF HELPER FUNCTIONS
'''

'''
---START OF GAME LOOP
'''


def clientHandler(clientSocket, player_index):
    clientSocket.settimeout(45)
    currentRound = 0
    try:
        while currentRound <= totalPlayerCount:
            if not playerOnline[player_index]:
                break  # Skip player if they are offline

            if currentRound == totalPlayerCount:
                lastRound(clientSocket, player_index, currentRound)
            else:
                if checkRoundOver(roundCompletion, currentRound):
                    message = previousStory[player_index - 1]
                    if currentRound == 0:
                        message = "start"
                    clientSocket.send(message.encode())

                    try:
                        receive = clientSocket.recv(1024).decode()
                        if not receive:
                            print(f"Player {player_index + 1} disconnected!")
                            clientSocket.send("DISCONNECT".encode())
                            playerOnline[player_index] = False
                            receive = "--- "
                    except TimeoutError:
                        print(f"Player {player_index + 1} timed out! Disconnecting...")
                        clientSocket.send("TIMEOUT".encode())
                        playerOnline[player_index] = False
                        receive = "--- "
                    except (ConnectionResetError, BrokenPipeError, socket.error) as e:
                        print(f"Player {player_index + 1} crashed: {e}")
                        clientSocket.send("DISCONNECT".encode())
                        playerOnline[player_index] = False
                        receive = "--- "

                    previousStory[player_index] = receive
                    stories[player_index - currentRound] += receive + " "
                    print("-------------------------------------------------------")
                    print("Round progress ", roundCompletion)
                    print("Player ", player_index + 1, " Increased their completion")
                    roundCompletion[player_index] += 1
                    print("story : ", stories)
                    print("Round progress ", roundCompletion)
                else:
                    currentRound -= 1
            currentRound += 1
    finally:
        clientSocket.close()
        print(f"🔴 Player {player_index + 1} removed from the game.")

        while currentRound <= totalPlayerCount:
            if currentRound != totalPlayerCount-1:
                segment = 'mid'
            else:
                segment = 'end'
            if checkRoundOver(roundCompletion, currentRound):
                bot_message = generate_placeholder(previousStory[player_index - 1], segment)
                previousStory[player_index] = bot_message
                stories[player_index - currentRound] += bot_message
                print("-------------------------------------------------------")
                print("Round progress ", roundCompletion)
                print("Player ", player_index + 1, " Increased their completion")
                roundCompletion[player_index] += 1
                print("story : ", stories)
                print("Round progress ", roundCompletion)
            else:
                currentRound -= 1
            currentRound += 1


'''
---END OF GAME LOOP
'''

'''
---START OF GAME BOOT
'''
while True:
    if not gameStarted:
        clientSocket, addr = serverSocket.accept()
        clientSocket.send(str(totalPlayerCount).encode())

        thread = threading.Thread(target=clientHandler, args=(clientSocket, currentPlayerCount))
        currentPlayerCount += 1
        playerThreads.append(thread)

    elif gameStarted and entered:
        for thread in playerThreads:
            thread.start()
        for thread in playerThreads:
            thread.join()
        entered = False

    if currentPlayerCount == totalPlayerCount:
        gameStarted = True
        entered = True
        currentPlayerCount += 1

    if gameStarted and not entered:
        break
'''
---END OF GAME BOOT
'''
