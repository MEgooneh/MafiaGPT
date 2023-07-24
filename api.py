# CONFIG YOUR API HERE : 
RATE_LIMIT = 20 # sleeping time for openai per minute limitation
TOKEN_LIMIT = 4000 # token limit per message
MODEL = 'gpt-3.5-turbo'

import openai, os, time
openai.api_key =  os.getenv("OPENAI_API_KEY")

def create_message(role , content) : 
    return {"role" : role , "content" : content}

def send_message(intro , game_report , command , token_limit=TOKEN_LIMIT , time_limit_rate=RATE_LIMIT) : 
    time.sleep(time_limit_rate)
    context = [create_message("system" , intro), create_message("user", game_report[-(token_limit - len(intro) - 70):]) , create_message("system" , command)]

    # connecting to Openai
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=context
    )
    print(f"""
          #######################
          {intro}
          #######################
          {game_report}
          #######################
          {command}
          #######################
          -----------------------------
          {response.choices[0].message["content"]}
    """)
    return response.choices[0].message["content"]
