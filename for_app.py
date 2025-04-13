from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chains import get_bartender_chain, get_analysis_chain
from helpers import update_user_preferences
from data_loader import load_user_preferences
from langchain.memory import ConversationBufferWindowMemory

# Initialize FastAPI
app = FastAPI()

# Load user preferences
users_df = load_user_preferences()

# Initialize session information
session_info = {}

# Initialize chains
analysis_chain = get_analysis_chain()

class ChatRequest(BaseModel):
    session_id: str
    user_message: str

class EndChatRequest(BaseModel):
    session_id: str

@app.post("/chat")
async def chat(request: ChatRequest):
    print(f"Received message: {request.user_message}")
    session_id = request.session_id
    
    # Initialize new session if needed
    if session_id not in session_info:
        session_info[session_id] = {
            'name': None,
            'memory': ConversationBufferWindowMemory(k=6, memory_key="history"),
            'state': 'get_name'
        }
        return {"response": "Welcome to our bar! What's your name?"}
    
    session = session_info[session_id]
    memory = session['memory']
    
    # Handle name collection
    if session['state'] == 'get_name':
        session['name'] = request.user_message.strip()
        session['state'] = 'chatting'
        memory.save_context({"input": f"My name is {session['name']}"}, {"output": f"Nice to meet you, {session['name']}!"})
        
    # Main conversation
    name = session['name']
    prefs = users_df[users_df['name'] == name].iloc[0]['preferences'] if name in users_df['name'].values else ""
    
    # Get bartender response
    chain = get_bartender_chain(memory, prefs)
    response = chain(request.user_message)
    
    # Analyze preferences
    try:
        chat_history = memory.load_memory_variables({})['history']
        extracted = analysis_chain.run(chat_history=chat_history)
        update_user_preferences(name, extracted)
    except Exception as e:
        print(f"Preference analysis error: {str(e)}")
    
    return {"response": response}

@app.post("/end_chat")
async def end_chat(request: EndChatRequest):
    session_id = request.session_id
    if session_id not in session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Final analysis
    session = session_info[session_id]
    if session['name']:
        try:
            chat_history = session['memory'].load_memory_variables({})['history']
            extracted = analysis_chain.run(chat_history=chat_history)
            update_user_preferences(session['name'], extracted)
        except Exception as e:
            print(f"Final analysis error: {str(e)}")
    
    del session_info[session_id]
    return {"status": "success"}

@app.get("/preferences")
async def get_preferences():
    return users_df.to_dict(orient="records")
