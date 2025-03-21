from flask import Flask, request, jsonify, render_template
import json
import db
import llm
import embed

app = Flask(__name__)

# 데이터베이스 초기화
db.init_db()

@app.route('/', methods = ['GET'])
def home():
    user_id = request.args.get('user_id')
    score = db.get_score(user_id)
    return render_template('home.html', score=score) # 튜플 아니면 리스트 

@app.route('/log', methods = ['GET'])
def log():
    return render_template('log.html')

@app.route('/browse', methods = ['GET'])
def browse():
    user_id = request.args.get('user_id')
    logs = db.get_logs(user_id)
    # print(logs)
    return render_template('browse.html', logs=logs)

@app.route('/api/llm', methods=['POST'])
def handle_llm_request():
    # 클라이언트로부터 JSON 데이터 받기
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({"error": "No input provided"}), 400
    
    user_input = data['input']

    # Embedding 모델 실행 및 벡터 받기
    embedding = embed.get_embedding(user_input)
    # Embedding 벡터 스토어에 저장 및 인덱스 받기
    v_index = embed.store_vector(embedding)
    
    # LLM 모델 실행
    llm_output = llm.get_log_response(user_input)

    encouragement = json.loads(llm_output)['격려']
    advice = json.loads(llm_output)['조언']
    physical = json.loads(llm_output)['체력']
    knowledge = json.loads(llm_output)['지식']
    mental = json.loads(llm_output)['정신력']

    # 출력과 vector index 결합하여 DB에 저장
    db.save_logs(user_input, encouragement, advice, physical, knowledge, mental, v_index)
    
    # 클라이언트에 JSON 응답 반환
    response = {
        "encouragement": encouragement,
        "advice": advice,
        "physical": physical,
        "knowledge": knowledge,
        "mental": mental,
        "timestamp": db.datetime.now().isoformat()
    }
    return jsonify(response), 200

@app.route('/chat', methods = ['POST'])
def chatting():
    data = request.get_json()
    if not data or 'chat' not in data:
        return jsonify({"error": "No chat provided"}), 400
    
    chat = data['chat']

    embedding = embed.get_embedding(chat)
    _, indices = embed.search_vector_store(embedding)
    
    logs = db.get_log_by_vector(indices)

    llm_output = llm.get_chat_response(user_input=chat, prompt_input=logs)

    return jsonify(llm_output), 200



@app.route('/delete')
def delete_log():
    user_id = request.args.get('user_id')
    log_id = request.args.get('log_id')
    db.delete_log(user_id=user_id, log_id=log_id)
    return 'delete'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5252, debug=True)