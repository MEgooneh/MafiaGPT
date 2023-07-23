import openai, os, time
openai.api_key =  os.getenv("OPENAI_API_KEY")

def create_message(role , content) : 
    return {"role" : role , "content" : content}

def send_message(intro , game_report , command , token_limit=4000 , time_limit_rate=20) : 
    time.sleep(time_limit_rate)
    context = [create_message("system" , intro), create_message("user", game_report[-(token_limit - len(intro) - 70):]) , create_message("system" , command)]

    # connecting to Openai
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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
