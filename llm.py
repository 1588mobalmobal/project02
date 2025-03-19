from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_ollama.llms import OllamaLLM

llm_instance = None

def init_llm():
    global llm_instance
    if llm_instance is None:
        llm_instance = OllamaLLM(model="gemma3:latest", temperature=0.1, num_predict=300, format='json')
    return llm_instance

def get_llm_response(user_input):
    # 로컬 Ollama 모델 설정 (예: 'llama3' 모델 사용)
    model = init_llm()
    system_message_prompt = SystemMessagePromptTemplate.from_template(
        '''
    당신은 사용자의 일기를 받아 조언을 해주는 동반자입니다.
    존댓말을 사용해서 한 문장으로 일기 내용을 평가한 후, 한 문장으로 조언을 해주세요.
    그 후 일기 내용을 다음 세가지 분류에 따라 각각 점수를 매겨주세요.
    체력: 운동활동 없음 = 0점 / 중간 강도 운동 = 1점 / 강하고 힘든 강도 운동 = 2점
    지식: 독서/학습활동 없음 = 0점 / 중간 강도 학습활동 = 1점 / 장시간 고강도 학습활동 = 2점
    정신력: 편안한 하루를 보냄 = 0점 / 불편을 극복 = 1점 / 어려운 환경을 극복 = 2점
    다음 출력 양식을 지켜주세요.
    ["격려" : 격려 내용, "조언" : 조언 내용, "체력" : 체력 점수, "지식" : 지식 점수 "정신력" : 정신력 점수]
    감사합니다.
    '''
    )
    human_message_prompt = HumanMessagePromptTemplate.from_template('{text}')

    chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt, human_message_prompt]
    )

    chain = chat_prompt | model

    response = chain.invoke(user_input)

    return response