from flask import Flask, request, jsonify, render_template, make_response
import json
import db
import llm
import embed

app = Flask(__name__)

user_id = 1

db.init_db()

@app.route('/', methods=['GET'])
def home():
    score = db.get_score(user_id)
    if score is None:
        score = (0, 0, 0)
    
    # 가장 최근 로그의 추가 점수
    change = db.get_score_change(user_id) or (0, 0, 0)
    
    sign_physical = '+' if change[0] >= 0 else ''
    sign_knowledge = '+' if change[1] >= 0 else ''
    sign_mental = '+' if change[2] >= 0 else ''
    
    response = make_response(render_template('index.html', 
                                             physical=score[0], 
                                             knowledge=score[1], 
                                             mental=score[2], 
                                             change_physical=change[0], 
                                             change_knowledge=change[1], 
                                             change_mental=change[2], 
                                             sign_physical=sign_physical, 
                                             sign_knowledge=sign_knowledge, 
                                             sign_mental=sign_mental, 
                                             user_id=user_id))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/write', methods=['GET'])
def log():
    return render_template('write.html')

@app.route('/browse', methods=['GET'])
def browse():
    logs = db.get_logs(user_id)
    return render_template('browse.html', logs=logs)

@app.route('/history', methods=['GET'])
def history():
    return render_template('history.html')

@app.route('/api/log', methods=['POST'])
def handle_llm_request():
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({"error": "No input provided"}), 400
    
    user_input = data['input']
    embedding = embed.get_embedding(user_input)
    v_index = embed.store_vector(embedding)
    llm_output = llm.get_log_response(user_input)

    encouragement = json.loads(llm_output)['격려']
    advice = json.loads(llm_output)['조언']
    physical = json.loads(llm_output)['체력']
    knowledge = json.loads(llm_output)['지식']
    mental = json.loads(llm_output)['정신력']

    print(f"LLM Output: physical={physical}, knowledge={knowledge}, mental={mental}, types: {type(physical)}, {type(knowledge)}, {type(mental)}")

    physical = int(physical)
    knowledge = int(knowledge)
    mental = int(mental)

    db.save_logs(user_input, encouragement, advice, physical, knowledge, mental, v_index)
    
    response = {
        "encouragement": encouragement,
        "advice": advice,
        "physical": physical,
        "knowledge": knowledge,
        "mental": mental,
        "timestamp": db.datetime.now().isoformat()
    }
    return jsonify(response), 200

@app.route('/chat', methods=['GET'])
def chat():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
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
    user_id = int(request.args.get('user_id', 1))
    log_id = int(request.args.get('log_id', 0))
    db.delete_log(user_id=user_id, log_id=log_id)
    return 'delete'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5252, debug=True)