# Gartic Phone CLI + AI

Originally made for CSC 430 Assignment 2

## How to Run

### Prerequisites
Before running, ensure the following libraries are installed[cite: 1]:
* Pytorch
* nltk
* transformers

**Important Note:** On the first run, approximately 50 MB of additional data will be downloaded[cite: 2].

### Execution Steps
1.  **Launch the Server:** Run the server script first[cite: 3].
2.  **Select Chat Model:** Follow the on-screen prompts to select a chat model[cite: 3].
3.  **Select Number of Players:** Choose the number of players (minimum of 3)[cite: 3].
4.  **Launch Clients:** Launch all client instances that will participate[cite: 3].
5.  **Wait for Connection:** If the specified number of clients hasn't connected, the server will wait until all clients join before starting the game[cite: 4].

## Screenshots

* **1st Round:**
    ![Alt text for Image 1](./images/image1.png) [cite: 6]

* **Intermediate Rounds:**
    ![Alt text for Image 2](./images/image2.png) [cite: 7]

* **Final Round:**
    ![Alt text for Image 3](./images/image3.png) [cite: 8]

* **All Together (with Voting Phase):**
    ![Alt text for Image 4](./images/image4.png) [cite: 9]

## Explanation of Code

### Server Side
1.  **Initialization:**
    * Initialize the server[cite: 10].
    * Prompt the user to select a chatbot model[cite: 10].
    * Prompt the user for the number of players (minimum 3 required)[cite: 11, 12].
    * Initialize lists for threads, player tracking, and status Booleans[cite: 13].
2.  **Connection Handling (Loop):**
    * While the game hasn't started:
        * Accept incoming client connections[cite: 15].
        * Send the total player count to the connecting client[cite: 15].
        * Create and start a new thread for each client using the `clienthandler` function, passing the socket and a unique player index (0, 1, 2...)[cite: 15, 16].
        * Store the thread and increment the current player count[cite: 16].
    * Once `currentPlayerCount` equals `totalPlayercount`, set game status Booleans to true[cite: 17].
3.  **Game Start:**
    * Start all client handler threads[cite: 17].
    * Wait for all threads to complete[cite: 17].
    * End the main server loop[cite: 17].
4.  **Client Handler Function (`clienthandler`):**
    * Set a socket timeout to handle idle or disconnected players[cite: 18]. Chatbots substitute for disconnected players[cite: 18].
    * The game proceeds in rounds, up to `player count + 1`[cite: 20]. The last round involves printing the final stories[cite: 19].
    * **Round Logic (excluding the last round):**
        * Players wait until everyone completes the current round (`checkRoundOver` function)[cite: 20]. A round finishes when all players submit input or disconnect (triggering chatbot substitution)[cite: 21].
        * **Round 0:** Clients print "Start"[cite: 22].
        * **Subsequent Rounds:** Stories are passed circularly (e.g., player 1 gets player 0's story)[cite: 22].
        * **Disconnection/Timeout Handling:** If a socket fails, mark the player as offline, send a (potentially unreceived) timeout message, set their message to "---", and have a chatbot take over for future rounds[cite: 22, 23].
    * **Last Round:** Print all generated stories[cite: 23].
    * **Voting:** The Llama Chatbot determines the winner[cite: 24].

### Client Side
1.  **Connection:** Connect to the server[cite: 25].
2.  **Gameplay Loop:**
    * Each round: Send validated input to the server[cite: 25].
    * Next round: Receive input from another client or a chatbot[cite: 25].
3.  **Timeout:** Clients who take too long are timed out and disconnected[cite: 26].
