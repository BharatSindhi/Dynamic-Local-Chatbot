# app.py
import streamlit as st
from llm_chains import load_normal_chain
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
import yaml
import os
from streamlit_mic_recorder import mic_recorder
from audio_handler import transcribe_audio
import json
from utils import save_chat_history_json, load_chat_history_json, get_timestamp
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)
def load_chain(chat_history):
    return load_normal_chain(chat_history)

def clear_input_field():
    st.session_state.user_question = st.session_state.user_input
    st.session_state.user_input = ""

def set_send_input():
    st.session_state.send_input = True
    clear_input_field()


def save_chat_history():
    if st.session_state.history != []:
        if st.session_state.session_key == "new_session":
            st.session_state.new_session_key = get_timestamp() + ".json"
            save_chat_history_json(st.session_state.history, config["chat_history_path"] + st.session_state.new_session_key)
        else:
            save_chat_history_json(st.session_state.history, config["chat_history_path"] + st.session_state.session_key)

 

def main():
    st.title("Dynamic Local Chatbot")
    chat_container = st.container()
    
    st.sidebar.title("Chat Sessions")
    chat_sessions = ["new_session"] + os.listdir(config["chat_history_path"])


    if "send_input" not in st.session_state:
        st.session_state.session_key = "new_session"
        st.session_state.send_input = False
        st.session_state.user_question = ""
        st.session_state.new_session_key = None
        st.session_state.session_index_tracker = "new_session"
    if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None

# ✅ Safe indexing
    if st.session_state.session_index_tracker in chat_sessions:
            index = chat_sessions.index(st.session_state.session_index_tracker)
    else:
            index = 0  # fallback to "new_session"

    st.sidebar.selectbox("Select Chat Session", chat_sessions, key="session_key", index=index)


    if st.session_state.session_key != "new_session":
        st.session_state.history = load_chat_history_json(config["chat_history_path"] + st.session_state.session_key)
    else:
        st.session_state.history = []

    chat_history=StreamlitChatMessageHistory(key="history")
    llm_chain=load_chain(chat_history)

    user_input=st.text_input("Enter You Prompt Here",key="user_input",on_change=set_send_input)
    voice_recording_column, send_button_column = st.columns(2)
    chat_container = st.container()
    with voice_recording_column:
        voice_recording=mic_recorder(start_prompt="Start recording",stop_prompt="Stop recording", just_once=True)
    with send_button_column:
        send_button = st.button("Send", key="send_button", on_click=clear_input_field)
        
    if voice_recording:
        transcribed_audio = transcribe_audio(voice_recording["bytes"])
        print(transcribed_audio)
        llm_chain = load_chain(chat_history)
        llm_chain.run(transcribed_audio)

        
    if send_button or st.session_state.send_input:
        if st.session_state.user_question != "":
                llm_response=llm_chain.run(st.session_state.user_question)
                st.session_state.user_question = ""

        if chat_history.messages != []:
            with chat_container:
                st.write("Chat History:")
                for message in chat_history.messages:
                    st.chat_message(message.type).write(message.content)

    save_chat_history()
if __name__ == "__main__":
    main()

