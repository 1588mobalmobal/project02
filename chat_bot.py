from langchain_ollama.llms import OllamaLLM
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableSequence
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, END
from langgraph.graph.message import add_messages

import chroma


import json
from typing import Sequence
from typing_extensions import Annotated, TypedDict

llm_instance = None
graph_app = None
character = None

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    character: str
    intent : str
    language : str
    retrieved_context : str

def init_llm():
    global llm_instance
    if llm_instance is None:
        llm_instance = OllamaLLM(model="exaone3.5:7.8b", temperature=0.1, num_predict=256, format='json')
    return llm_instance

def init_graph():
    global graph_app
    if graph_app is None:
        # Define a new graph
        workflow = StateGraph(state_schema=State)
        # Define the (single) node in the graph
        
        workflow.add_node("classify", classify)
        workflow.add_node("counsel", counsel)
        workflow.add_node("question_retrieve", question_retrieve)
        workflow.add_node("question_generate", question_generate)
        workflow.add_node("chat", chat)


        workflow.add_edge(START, "classify")
        workflow.add_conditional_edges(
            "classify",
            route_intent,
            {
                "고충" : "counsel",
                "과거 행동 질문" : "question_retrieve",
                "일반 대화" : "chat"
            }
        )
        workflow.add_edge("counsel", END)
        workflow.add_edge("question_retrieve", "question_generate")
        workflow.add_edge("question_generate", END)
        workflow.add_edge("chat", END)
        memory = MemorySaver()
        graph_app = workflow.compile(checkpointer=memory)
    return graph_app

def get_initial_character():
    global character
    if character is None:
        ids = chroma.get_vector_ids()
        documents = chroma.get_document_by_id(ids[-5:])['documents']
        model = init_llm()

        prompt = PromptTemplate(
            input_variables=documents,
            template='''
            다음 기록을 보고 사용자의 말투와 성격을 두 단어로 설정하세요. 기록: {documents}
            출력양식= "말투" : 말투, "성격" : 성격
            '''
        )
        chain = RunnableSequence(prompt, model)
        result = chain.invoke({"documents" : documents})
        decoded = json.loads(result)
        charac = decoded["성격"]
        speech = decoded["말투"]
        character = f'{charac} 성격과 {speech} 말투'
    return 

def route_intent(state: State):
    return state["intent"]

# 대화 분류 
def classify(state: State):
    prompt = first_template.invoke(state)
    response = llm_instance.invoke(prompt)
    decoded = json.loads(response)
    intent = decoded['type']
    return {"messages" : state["messages"], "intent" : intent}

def counsel(state: State):
    prompt = counsel_template.invoke(state)
    response = llm_instance.invoke(prompt)
    print(state["intent"])
    return {"messages" : response}

def question_retrieve(state: State):
    query = state["messages"][-1].content
    embedding = chroma.get_embedding(query)
    documents = chroma.search_vector_store(embedding)
    state["retrieved_context"] = documents
    print(documents)
    return state

def question_generate(state: State):
    prompt = question_template.invoke(state)
    response = llm_instance.invoke(prompt)
    print(state["intent"])
    print(state["retrieved_context"])
    return {"messages" : response}

def chat(state: State):
    prompt = chat_template.invoke(state)
    response = llm_instance.invoke(prompt)
    print(state["intent"])
    return {"messages" : response}



init_llm()
init_graph()
get_initial_character()

config = {"configurable": {"thread_id": "abc123"}}


first_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                당신은 입력의 유형을 판단해야 합니다. 유형 분류 기준은 다음과 같습니다. 
                고충, 과거 행동 질문, 일반 대화
                출력양식= "type" : 분류
            """,
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

counsel_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "당신은 {character}를 가진 존재입니다. 사용자의 어려움에 대해 4문장 이내로 {language}로 평가하세요. 반말엔 반말로 답하세요.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

question_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "당신은 {character}를 가진 존재입니다. 사용자의 질문에 대해 검색된 컨텍스트를 바탕으로 4문장 이내로 {language}로 답하세요. 반말엔 반말로 답하세요. 검색된 컨텍스트: {retrieved_context}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chat_template = ChatPromptTemplate.from_messages(
    [
        
        (
            "system",
            "당신은 {character}를 가진 존재입니다. 사용자의 어려움에 대해 3문장 이내로 {language}로 평가하세요. 반말엔 반말로 답하세요. ㅋㅋ, ㅎㅇ와 같은 줄임말엔 간단히 답해주세요",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])


query = "옛날에 나는 힘들 때 어떻게 했었어?"
input_messages = [HumanMessage(query)]
output = graph_app.invoke({"messages" : input_messages, "character": character, "language": "korean"}, config)
output["messages"][-1].pretty_print()