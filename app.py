import streamlit as st
import requests
import uuid
from datetime import datetime


# Configuration
API_URL = "http://localhost:8000"

# Session state
if 'session_id' not in st.session_state:
    st.session_state.update({
        'session_id': str(uuid.uuid4()),
        'messages': [],
        'active': True,
        'start_time': datetime.now()
    })

# UI Setup
st.set_page_config(page_title="AI Bartender", page_icon="🍸")
st.title("🍹 AI Mixologist")
st.caption("Your personal cocktail consultant")

# Sidebar
with st.sidebar:
    st.header("Session Info")
    st.write(f"Started: {st.session_state.start_time.strftime('%H:%M:%S')}")
    st.write(f"Session ID: `{st.session_state.session_id[:8]}...`")
    
    if st.button("End Session", type="primary"):
        try:
            response = requests.post(
                f"{API_URL}/end_chat",
                json={"session_id": st.session_state.session_id},
                timeout=5
            )
            if response.status_code == 200:
                st.session_state.active = False
                st.success("Session ended successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.divider()
    st.markdown("""
    **How to use:**
    1. Chat naturally about your drink preferences
    2. Get personalized recommendations
    3. Our AI remembers your favorites!
    """)

# Chat display
for msg in st.session_state.messages:
    avatar = "🍸" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Chat input
if st.session_state.active:
    if prompt := st.chat_input("What would you like to drink?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get AI response
        with st.spinner("Mixing your drink..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "user_message": prompt
                    },
                    timeout=10
                ).json()
                
                st.session_state.messages.append(
                    {"role": "assistant", "content": response["response"]}
                )
                with st.chat_message("assistant", avatar="🍸"):
                    st.markdown(response["response"])
            
            except requests.exceptions.Timeout:
                st.error("Our bartender is busy. Please try again!")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
else:
    st.info("Session ended. Refresh page to start new chat.")

# Auto-scroll
st.markdown("""
<script>
window.addEventListener('load', function() {
    const chat = window.parent.document.querySelector('.stChatFloatingInputContainer');
    chat.scrollIntoView();
});
</script>
""", unsafe_allow_html=True)