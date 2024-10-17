## Importing libraries required 

import redis
import json
import random

## Creating the class chatbot

class Chatbot:
    
    def __init__(self, host='redis', port=6379):
        
        ## Initializing the different attributes 
        
        self.client = redis.StrictRedis(host=host, port=port)
        self.pubsub = self.client.pubsub()
        self.username = None        ## username is empty because there is no 
        self.has_introduced = False ## Flag to track if introduction has been shown as in the pictures given the introduction is not always shown - 
                                    ## just that the options to use. 

    def introduce(self):
        ## Provide an introduction and list of commands 
        intro = """
        This is your super friendly chatbot 
        Here are the commands this bot supports:
        !help: List of commands
        !weather <city>: Weather update
        !fact: Random fun fact
        !whoami: Your user information\n
        """
        print(intro)
        
    def display_options(self):
        ## Display options to the user 
        print("Options:\n")
        print("1: Identify yourself\n")
        print("2: Join a channel\n")
        print("3: Leave a channel\n")
        print("4: Send a message to a channel\n")
        print("5: Get info about a user\n")
        print("6: Read messages from a channel\n")
        print("7: Exit\n")

    def identify(self, username, age, gender, location):
        ## method to register and store the value within the redis database 
        user_key = f"user:{username}"
        self.client.hset(user_key, mapping={
            "name": username, 
            "age": age,
            "gender": gender,
            "location": location
        })
        self.username = username  
        ## printing statement to comfirm information has been stored 
        print('The username has been stored!')

    def join_channel(self, channel):
        ## method to make the user subscribe to the channel 
        self.pubsub.subscribe(channel)
        ## printing statement to comfirm user has subscribed to the channel 
        print("The user has subscribed to the channel :) ")

    def leave_channel(self, channel):
        ## method to make the user unsubscribe from the channel
        self.pubsub.unsubscribe(channel)
        ## printing statement to comfirm user has unsubscribed from the channel 
        print("The user has unsubscribed from the channel :( ")

    def send_message(self, channel, message):
        ## method to send a message to the channel
        self.client.publish(channel, f"{self.username}: {message}")

    def read_message(self, channel):
        ## method to allow the user to subscribe to channel and see all the messages for that channel 
        print(f"Listening for messages on {channel}...")
        
        self.pubsub.subscribe(channel) 
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                print(f"New message on {message['channel']}: {message['data'].decode('utf-8')}")

    def process_commands(self, message):
        ## method to process the special commands that the user inputs which are not part of pubsub like '!fact', '!weather', '!help'
        
        ##condition to see if user asks for help
        if message.startswith("!help"):
            print("Use the following commands to interact with the chatbot:")
            self.introduce()
            
        ##condition to see if user asks for weather based on city 
        ## This will give facts based on the preloaded information  
        elif message.startswith("!weather"):
            parts = message.split(" ")
            if len(parts) > 1:
                city = parts[1]
                self.get_weather(city)
            else:
                city = input("Please enter a city name: ")
                self.get_weather(city) 
         
        ## preset facts will be returned here  
        elif message.startswith("!fact"):
            fact = self.get_fact()
            print(f"Fact: {fact}")
            
        ## user information will be returned here     
        elif message.startswith("!whoami"):
            self.whoami()

    def get_weather(self, city):
        ## method to get the preset weather information about city 
        weather_data = self.client.hget("weather", city)
        if weather_data:
            print(f"Weather in {city}: {weather_data.decode('utf-8')}")
        else:
            print(f"No weather data for {city}.")
    
    def get_fact(self):
        ## method to get the preset facts
        
        ## preset facts 
        facts = [
            "Real honey doesn't burn apparently.",
            "Humans are not capable of everything.",
            "Dentists are not real doctors.",
            "Some types of doctor professions are just downright weird."
        ]
        return random.choice(facts)
            
    def whoami(self):
        ## method to get the user information 
        ## method first checks if the user has been registered or not 
        ## if user is registered then it returns values, if not it asks to first register the user 
        if self.username:
            user_info = self.client.hgetall(f"user:{self.username}")
            # Decode keys and values to strings
            user_info = {k.decode('utf-8'): v.decode('utf-8') for k, v in user_info.items()}
            print(f"User Info for {self.username}: {json.dumps(user_info, indent=2)}")
        else:
            print("You need to identify yourself first using the identify command.")
    
    def menu(self):
        
        while True:
            if not self.has_introduced:  ## Check if introduction has been shown
                self.introduce()
                self.has_introduced = True  ## Set flag to True if introduction has been shown so that the big introducory text is not shown. 
            
            self.display_options()  ## Show options after the introduction
            
            choice = input("Enter your choice: ") ## asks for input for user commands 

            ## interaction with the user for registering value 
            if choice == '1':
                username = input("Enter username: ")
                age = input("Enter age: ")
                gender = input("Enter gender: ")
                location = input("Enter location: ")
                self.identify(username, age, gender, location)
            
            ## interaction with the user for joining channel   
            elif choice == '2':
                channelname = input("Which channel would you like to join?: ")
                self.join_channel(channelname)
                
            ## interaction with the user for leaving channel
            elif choice == '3':
                channelname = input("Which channel would you like to leave?: ")
                self.leave_channel(channelname)
            
            ## interaction with the user for sending message to channel    
            elif choice == '4':
                channelname = input("Which channel would you like to send a message to?: ")
                message = input("Enter your message: ")
                self.send_message(channelname, message)
            
            ## interaction with the user for getting information about a user    
            elif choice == '5': 
                username = input("Enter username to get info about: ")
                self.get_user_info(username)
                
            ## interaction with the user for reading messages from a channel
            elif choice == '6':
                channelname = input("Which channel would you like to read messages from?: ")
                self.read_message(channelname)
                
            ## interaction with the user for exiting the chatbot - the break clause allows user to exit from the chatbot 

            elif choice == '7':
                print("Goodbye!")
                break
            
            ## interaction for special commands 
            elif choice.startswith('!'):
                self.process_commands(choice)
            
            ## error clause     
            else:
                print("Invalid option. Please try again.") 
            
    def get_user_info(self, username):
        ## method to retreive information from database 
        ## first checks if there is a username which is specified 
        ## else throws error 
        user_data = self.client.hgetall(f"user:{username}")
        if user_data:
            print(f"Info for {username}: Username: {username}, Age: {user_data.get(b'age').decode('utf-8')}, Gender: {user_data.get(b'gender').decode('utf-8')}, Location: {user_data.get(b'location').decode('utf-8')}")
        else:
            print(f"No information found for {username}.")           

def add_mock_weather_data():
    ## mock weather data to get information for the weather 
    client = redis.StrictRedis(host='redis', port=6379)
    client.hset("weather", "nashville", "Sunny, 75°F")
    client.hset("weather", "new_york", "Cloudy, 60°F")
    client.hset("weather", "los_angeles", "Clear, 85°F")
    print("Mock weather data added.")

if __name__ == "__main__":
    add_mock_weather_data()
    
    bot = Chatbot()
    bot.menu()
