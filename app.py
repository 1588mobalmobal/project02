from flask import Flask, request, jsonify, render_template
import json
import db
import llm

app = Flask(__name__)

# 데이터베이스 초기화
db.init_db()

@app.route('/', methods = ['GET'])
def home():
    user_id = request.args.get('user_id')
    score = db.get_score(user_id)
    return render_template('home.html', score=score)

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
    
    # LLM 모델 실행
    llm_output = llm.get_llm_response(user_input)
    print(llm_output)

    encouragement = json.loads(llm_output)['격려']
    advice = json.loads(llm_output)['조언']
    physical = json.loads(llm_output)['체력']
    knowledge = json.loads(llm_output)['지식']
    mental = json.loads(llm_output)['정신력']

    # DB에 저장
    db.save_logs(user_input, encouragement, advice, physical, knowledge, mental)
    
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5252, debug=True)