from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.runnables import RunnableSequence, RunnableLambda
import json

llm_instance = None

def init_llm():
    global llm_instance
    if llm_instance is None:
        llm_instance = OllamaLLM(model="exaone3.5:7.8b", temperature=0.1, num_predict=300, format='json')
    return llm_instance

def get_log_response(user_input):
    # 로컬 Ollama 모델 설정 (예: 'llama3' 모델 사용)
    model = init_llm()
    system_message_prompt = SystemMessagePromptTemplate.from_template(
        '''
    당신은 사용자의 일기를 받아 조언을 해주는 동반자입니다.
    존댓말을 사용해서 한 문장으로 일기 내용을 평가한 후, 한 문장으로 조언을 해주세요.
    그 후 일기의 결과를 다음 세가지 분류에 따라 각각 점수를 매겨주세요.
    체력: 운동활동 미수행 = 0점 / 중간 강도 운동 수행 = 1점 / 강하고 힘든 강도 운동 수행 = 2점
    지식: 독서/학습활동 미수행 = 0점 / 중간 강도 학습활동 수행 = 1점 / 장시간 고강도 학습활동 수행 = 2점
    정신력: 정신적-육체적 에너지 미소모 = 0점 / 불편과 번거로움을 이겨냄 = 1점 / 가혹한 환경을 이겨냄 = 2점
    다음 출력 양식을 지켜주세요.
    ["격려" : 격려 내용, "조언" : 조언 내용, "체력" : 체력 점수, "지식" : 지식 점수, "정신력" : 정신력 점수]
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

def get_chat_response(user_input, prompt_input):

    # 로컬 Ollama 모델 설정 (예: 'llama3' 모델 사용)
    model = init_llm()

    first_prompt = PromptTemplate.from_template(
        ''' 
        다음은 사용자의 입력과 가장 관련도가 높은 기록들입니다.
        기록들: {input}
        이 기록은 사용자가 남긴 기록으로, 평소 특정 키워드에 대해 어떤 생각을 가졌었는지 드러납니다.
        또한 사용자의 평소 말투와 성격을 유추할 수 있습니다.
        사용자는 어떤 성격과 어떤 말투를 가졌는지, 핵심 키워드에 대해 어떻게 생각하는지지 요약해서 출력해주세요.
        '''
    )

    second_prompt = PromptTemplate.from_template(
        '''
            당신은 다음 정보를 통해 사용자의 말투와 성격, 핵심 키워드에 대한 생각을 알게됩니다.
            정보: {first_result}
            알게된 말투와 성격 및 핵심 키워드에 대한 생각을 모사하여 아래의 사용자의 대화에 답해주세요.
            대화: {user_input}

        '''
    )

    chain = RunnableSequence(
        first_prompt,
        model,
        RunnableLambda(lambda x: {"first_result": x, "user_input" : user_input}),
        second_prompt,
        model
    )

    result = chain.invoke({"input": prompt_input})
    return result