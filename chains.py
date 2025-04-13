from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from config import OPENAI_API_KEY
from data_loader import load_cocktail_documents


embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)


docs = load_cocktail_documents()
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever()


def get_bartender_chain(memory, preferences=""):
    prompt = PromptTemplate(
        template="""
            You are a professional bartender with 20 years experience. Follow this flow:
            1. Welcome if it's a new customer, warm greetings if it's a returning customer.
            2. Reference known preferences: {preferences}
            3. Using the context, suggest 2-3 perfectly matched cocktails
            4. Provide expert preparation tips, but try to keep it short and natural. 
            5. If you have provided a recipe for a drink, DO NOT repeat it in your answers anymore unless the user asks for it again. 
            6. Continue conversation naturally

            Context: {context}

            Current conversation:
            {history}
            Customer: {input}
            Bartender:""", 
        input_variables=["history", "input", "preferences", "context"]
    )
    
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True
    )
    
    def wrapped_chain(input_text):
        history = memory.load_memory_variables({})['history']
        relevant_docs = retriever.get_relevant_documents(input_text)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        result = chain.run(input=input_text, preferences=preferences, history=history, context=context)
        memory.save_context({"input": input_text}, {"output": result})
        return result
    
    return wrapped_chain

def get_analysis_chain():
    prompt = PromptTemplate(
        template="""
            Extract ALL drink preferences from this conversation as a comma-separated list.
            Be extremely precise - only include clear customer statements.

            Conversation:
            {chat_history}

            Extracted preferences:""", 
        input_variables=["chat_history"]
    )
    
    return LLMChain(
        llm=ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=OPENAI_API_KEY
        ),
        prompt=prompt,
        verbose=True
    )
