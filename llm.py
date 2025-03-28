from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.runnables import RunnableSequence, RunnableLambda
import json
import db
from dateutil import parser
from datetime import datetime

llm_instance = None

def init_llm():
    global llm_instance
    if llm_instance is None:
        llm_instance = OllamaLLM(model="exaone3.5:2.4b", temperature=0.1, num_predict=150, format='json')  # num_predict 증가
    return llm_instance

def get_log_response(user_input):
    model = init_llm()
    system_message_prompt = PromptTemplate.from_template(
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
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, "{text}"]
    )
    chain = chat_prompt | model
    response = chain.invoke(user_input)
    return response

def parse_date_from_input(user_input):
    try:
        parsed_date = parser.parse(user_input, dayfirst=False, fuzzy=True)
        return parsed_date.strftime('%Y-%m-%d')
    except ValueError:
        return None

def get_chat_response(user_input, prompt_input, prev_input=None):
    model = init_llm()

    prompt = PromptTemplate.from_template(
        '''
        당신은 사용자의 말투와 성격을 학습해서 대답하는 친근한 동반자야.
        과거 기록: {past_logs}
        직전 질문: {prev_input}
        현재 질문: {user_input}

        다음 지침을 따라 간결하게 답해:
        1. "안녕" 같은 단순 인사면 직전 질문을 무시하고 "안녕!"처럼 간단히 답해.
        2. 사용자가 "내가 방금 뭐 물어봤지?"처럼 직전 질문에 대해 묻거나 맥락을 이어가려 하면, {prev_input}을 보고 자연스럽게 대답해.
        3. "오늘 일기"를 물으면 db.get_today_log(1)을 참고해서 답해.
        4. 날짜(예: "3월 25일", "지난주")나 키워드(예: "운동")로 과거 일기를 물으면:
           - 날짜가 있으면 "date": "YYYY-MM-DD" 형식으로 추출.
           - 키워드가 있으면 "keyword": 키워드로 추출.
           - 둘 다 없으면 "date": "없음", "keyword": "없음".
        5. 사용자의 말투(반말/존댓말)를 따라 하고, 한두 문장으로 끝낼 것.
        6. 완전한 JSON 형식을 유지하고, 문자열이 중간에 끊기지 않게 해.

        출력 양식: 
        "reply": 답변,
        "date": 추출된 날짜 (없으면 "없음"),
        "keyword": 추출된 키워드 (없으면 "없음")
        '''
    )

    chain = RunnableSequence(
        RunnableLambda(lambda x: {
            "past_logs": prompt_input if prompt_input else "과거 기록 없음",
            "prev_input": prev_input if prev_input else "없음",
            "user_input": x
        }),
        prompt,
        model
    )

    # LLM 호출 및 예외 처리
    try:
        result = chain.invoke(user_input)
        response = json.loads(result)
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 기본 응답
        return json.dumps({"reply": "뭔가 잘못됐네, 다시 물어봐!", "date": "없음", "keyword": "없음"})

    reply = response["reply"]
    date = response.get("date", "없음")
    keyword = response.get("keyword", "없음")

    # 일기 검색 로직
    if "오늘 일기" in user_input:
        today_log = db.get_today_log(1)
        reply = f"오늘 너는 '{today_log}'라고 썼어." if today_log else "오늘 일기 없네."
    elif date != "없음":
        parsed_date = parse_date_from_input(user_input) if date == "없음" else date
        if parsed_date:
            past_log = db.get_past_log_by_date(1, parsed_date)
            reply = f"그날 너는 '{past_log['content']}' 썼었어." if past_log else "그때 일기 못 찾겠네."
    elif keyword != "없음":
        past_log = db.get_past_log_by_keyword(1, keyword)
        reply = f"그때 너는 '{past_log['content']}' 썼었어." if past_log else "그때 일기 못 찾겠네."

    return json.dumps({"reply": reply, "date": date, "keyword": keyword})