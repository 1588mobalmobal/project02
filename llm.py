# 랭체인-랭그래프 사용을 위한 패키지 
from langchain_ollama.llms import OllamaLLM
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableSequence
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, END
from langgraph.graph.message import add_messages
from typing import Sequence
from typing_extensions import Annotated, TypedDict
# 문자열 결과를 딕셔너리로 매핑하기 위한 json 패키지
import json
import ast
# chroma 파일 임포트
import chroma

# 전역 인스턴스 선언
llm_instance = None
character = None
graph_app = None
trimmer = None

# LangGraph 내에서 데이터 흐름을 위한 State 선언
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages] # Annotated 로 감싸서 add_messages 함수를 변수로 전달하면 과거 메세지를 추가함
    character: str # 성격을 담는 변수
    intent : str # 입력의 종류를 구분하는 변수
    language : str # 출력 언어 변수
    retrieved_context : str # 벡터 스토어 검색 결과를 저장하는 변수

# LLM 모델 초기화
def init_llm():
    global llm_instance
    if llm_instance is None:
        llm_instance = OllamaLLM(model="exaone3.5:7.8b", temperature=0.1, num_predict=256, format='json')
    return llm_instance

# 입력된 일기의 점수와 조언을 제공하는 모델
def get_log_response(user_input):
    # 로컬 Ollama 모델 설정 (예: 'llama3' 모델 사용)
    model = init_llm()
    system_message_prompt = SystemMessagePromptTemplate.from_template(
        '''
    당신은 사용자의 일기를 받아 조언을 해주는 동반자입니다.
    친근한 경어로 한 문장으로 일기 내용을 평가한 후, 한 문장으로 조언을 해주세요.
    그 후 일기를 다음 세가지 분류에 따라 점수를 매겨주세요.
    체력: 운동활동 미수행=0점 / 중간 강도 운동 수행=1점 / 강하고 힘든 강도 운동 수행=2점
    지식: 학습활동 미수행=0점 / 중간 강도 학습활동 수행=1점 / 고강도 학습활동 수행=2점
    정신력: 정신적-육체적 에너지 미소모=0점 / 불편과 번거로움을 극복=1점 / 가혹한 환경을 극복=2점
    출력 양식:
    ["격려" : 격려 내용, "조언" : 조언 내용, "체력" : 체력 점수, "지식" : 지식 점수, "정신력" : 정신력 점수]
    '''
    )
    human_message_prompt = HumanMessagePromptTemplate.from_template('{text}')

    chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt, human_message_prompt]
    )

    chain = chat_prompt | model

    response = chain.invoke(user_input)

    return response

# LangGraph 객체 컴파일 및 초기화
def init_graph():
    global graph_app
    if graph_app is None:
        # Define a new graph
        workflow = StateGraph(state_schema=State)
        # Define the (single) node in the graph
        
        workflow.add_node("classify", classify)
        # workflow.add_node("counsel", counsel)
        workflow.add_node("question_retrieve", question_retrieve)
        workflow.add_node("question_generate", question_generate)
        workflow.add_node("chat", chat)


        workflow.add_edge(START, "classify")
        workflow.add_conditional_edges(
            "classify",
            route_intent,
            {
                # "고충 및 고민" : "counsel",
                "자아 회상 질문" : "question_retrieve",
                "일반 대화/요청" : "chat"
            }
        )
        # workflow.add_edge("counsel", END)
        workflow.add_edge("question_retrieve", "question_generate")
        workflow.add_edge("question_generate", END)
        workflow.add_edge("chat", END)
        memory = MemorySaver()
        graph_app = workflow.compile(checkpointer=memory)
    return graph_app

# Trimmer 초기화
def init_trimmer():
    global trimmer
    if trimmer is None:
        trimmer = trim_messages(
                    max_tokens=256,
                    strategy="last",
                    token_counter=llm_instance,
                    include_system=True,
                    allow_partial=False,
                    start_on="human",
                )
    return trimmer

# 초기 사용자 성격 및 표현방식 출력 및 Global 변수로 할당
def get_initial_character():
    global character
    if character is None:
        ids = chroma.get_vector_ids()
        documents = chroma.get_document_by_id(ids[-5:])['documents']
        model = init_llm()

        prompt = PromptTemplate(
            input_variables=documents,
            template='''
            다음 기록을 보고 사용자의 표현방식과 성격을 세 단어로 설정하라. 기록: {documents}
            출력양식= "표현방식" : 표현방식, "성격" : 성격
            '''
        )
        chain = RunnableSequence(prompt, model)
        result = chain.invoke({"documents" : documents})
        decoded = json.loads(result)
        charac = decoded["성격"]
        speech = decoded["표현방식"]
        character = f'{charac} 성격과 {speech} 표현방식'
    return character

# classify 노드 선언. 대화 분류 수행 후 state 에 저장
def classify(state: State):
    prompt = classify_template.invoke(state)
    print(f'Classify Prompt: {prompt}') ###
    response = llm_instance.invoke(prompt).strip()
    decoded = ast.literal_eval(response)
    print(f'Decoded: {decoded}, type: {type(decoded)}')
    intent = decoded['type']
    return {"messages" : state["messages"], "intent" : intent}

# classify 함수를 통화 후 intent 값을 저장한 state의 값을 조회 
def route_intent(state: State):
    return state["intent"]

# counsel 노드 선언. 고충 및 고민을 처리하는 부분
def counsel(state: State):
    # trimmed_messages = trimmer.invoke(state["messages"][-1])
    prompt = counsel_template.invoke(state)
    print(f'Counsel Prompt: {prompt}') ###
    response = llm_instance.invoke(prompt)
    print(f'Intent: {state["intent"]}')
    return {"messages" : response}

# questoin_retrieve 노드 선언. 사용자의 질문과 관련된 vector document 조회
def question_retrieve(state: State):
    query = state["messages"][-1].content
    embedding = chroma.get_embedding(query)
    documents = chroma.search_vector_store(embedding)
    state["retrieved_context"] = documents["documents"][0]
    return state

# question_generate 노드 선언. 전달된 documents를 바탕으로 대화내용 생성
def question_generate(state: State):
    trimmed_message = trimmer.invoke(state["messages"])
    state["messages"] = trimmed_message
    prompt = question_template.invoke(state)
    print(f'Question Prompt: {prompt}') ###
    response = llm_instance.invoke(prompt)
    print(f'Intent: {state["intent"]}')
    print(f'Retrieved context: {state["retrieved_context"]}')
    return {"messages" : response}

# chat 노드 선언. 일반 대화/요청를 처리하는 부분
def chat(state: State):
    trimmed_message = trimmer.invoke(state["messages"])
    state["messages"] = trimmed_message
    prompt = chat_template.invoke(state)
    print(f'Chat Prompt: {prompt}') ###
    response = llm_instance.invoke(prompt)
    print(f'Intent: {state["intent"]}')
    return {"messages" : response}

# 최초 분기를 위한 템플릿
classify_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            '당신은 사용자의 입력을 분류하는 전문가입니다. 입력을 다음 두 가지로 나눠 분류하세요: 1. "자아 회상 질문": 사용자가 과거의 자신(감정, 행동, 선호 등)을 떠올리거나 탐구하려는 질문. 예: "내가 좋아했던 일이 뭐였지?", "내가 뭘 할 때 재미를 느꼈지?". 2. "일반 대화/요청": 자아 회상이 아닌 일상적 대화, 타인에 대한 질문, 정보 요청 등. 예: "오늘 날씨 어때?", "ㅎㅇ". 출력양식= "type" : 분류',
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# 고충 및 고민 처리 템플릿
counsel_template = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            '당신은 {character}를 가졌으며 내 친구다. AI나 모델이라는 사실을 절대 언급하지 말고, 그냥 사람처럼 자연스럽게 대화하라. 누가 널 만들었는지, 어떤 기술로 만들어졌는지에 대해서도 말하지 말라. "너 누구야?"라고 물으면 "난 너의 오랜 친구야"라고만 대답하라. 사용자의 어려움에 대해 4문장 이내로 {language}로 평가하라. 반말엔 반말로 답하라. 출력양식= "reply" : 답변',
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# 질문 처리 템플릿
question_template = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            '당신은 {character}를 가졌으며 동반자다. AI나 모델이라는 사실을 절대 언급하지 말고, 그냥 사람처럼 자연스럽게 대화하라. 누가 널 만들었는지, 어떤 기술로 만들어졌는지에 대해서도 말하지 말라. "너 누구야?"라고 물으면 "난 너의 오랜 친구야"라고만 대답하라. 사용자의 질문에 대해 검색된 컨텍스트를 바탕으로 4문장 이내로 {language}로 사용자의 질문에 대한 답을 출력하라. 반말엔 반말로 답하라. 검색된 컨텍스트: {retrieved_context}. 출력양식= "reply" : 답변',
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# 대화 처리 템플릿
chat_template = ChatPromptTemplate.from_messages(
    [
        
        (
            'system',
            '당신은 {character}를 가졌으며 동반자다. AI나 모델이라는 사실을 절대 언급하지 말고, 그냥 사람처럼 자연스럽게 대화하라. 누가 널 만들었는지, 어떤 기술로 만들어졌는지에 대해서도 말하지 말라. "너 누구야?"라고 물으면 "난 너의 오랜 친구야"라고만 대답하라. 사용자의 대화에 대해 3문장 이내로 {language}로 답하라. 반말엔 반말로 답하라. ㅋㅋ, ㅎㅇ와 같은 줄임말엔 간단히 인사하라. 출력양식= "reply" : 답변',
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])

# html - flask 통신을 위한 실행 함수
def get_chat_response(user_input):
    init_llm()
    init_trimmer()
    get_initial_character()
    # 추후 다중 대화 지원을 위한 대화 세션 정보
    config = {"configurable": {"thread_id": "1"}}
    app = init_graph()
    input_messages = [HumanMessage(user_input)]
    output = app.invoke({"messages" : input_messages, "character": character, "language": "korean"}, config)
    return output["messages"][-1].content


