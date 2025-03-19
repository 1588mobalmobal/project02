from flask import Flask, request, jsonify
import json
import db
import llm

app = Flask(__name__)

# 데이터베이스 초기화
db.init_db()

@app.route('/api/llm', methods=['POST'])
def handle_llm_request():
    # 클라이언트로부터 JSON 데이터 받기
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({"error": "No input provided"}), 400
    
    user_input = data['input']
    
    # LLM 모델 실행
    llm_output = llm.get_llm_response(user_input)
    
    # DB에 저장
    db.save_interaction(user_input, llm_output)
    
    # 클라이언트에 JSON 응답 반환
    response = {
        "input": user_input,
        "output": llm_output,
        "timestamp": db.datetime.now().isoformat()
    }
    return jsonify(json.loads(response['output'])), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5252, debug=True)