import openai, os, time
openai.api_key =  os.getenv("OPENAI_API_KEY")

def create_message(role , content) : 
    return {"role" : role , "content" : content}

def send_message(intro , game_reports , token_limit , time_limit=0) : 
    time.sleep(time_limit)
    context = [create_message("system" , intro), create_message("system", game_reports[-(token_limit - len(intro) - 5):])]

    # log in console for debugging
    print("######################")
    for message in context : 
        print(f"{message['role'].capitalize()}: \n {message['content']}")
        print("-------------------")
    
    # connecting to Openai
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=context
    )
    return response.choices[0].message["content"]
