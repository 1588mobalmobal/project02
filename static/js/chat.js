function sendMessage(){
    const input = document.getElementById("chat_input");
    const message = input.value.trim()
    // console.log(message)
    if (message == "") return;
    create_chat_div(message, 'end')
    get_response(message)
    input.value = "";
}

function create_chat_div(message, direction){
    let div_color = "bg-primary"
    let text_color = "text-white"
    if (direction == "start") {
        div_color = "bg-light"
        text_color = "text-black"
    }
    const chatContainer = document.querySelector(".chat-container");
    const messageDiv = document.createElement("div");
    messageDiv.className = `d-flex justify-content-${direction} mb2`;
    messageDiv.innerHTML = `
        <div class="${div_color} ${text_color} p-2 m-2 rounded" style="max-width: 70%; word-wrap: break-word;">
            ${message}
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return messageDiv
}

function get_response(user_input){
    const data = {
        chat: user_input
    };

    let temp_message = create_chat_div("생성 중...", "start")
    
    fetch("http://127.0.0.1:5252/api/chat", {
        method: "POST",
        headers: {
            "Content-Type" : "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) throw new Error("서버 응답 오류");
        temp_message.remove()
        return response.json();
    })
    .then(data => {
        const reply_message = JSON.parse(data).reply;
        create_chat_div(reply_message, 'start')
    })
    .catch(error => {
        console.error("POST 요청 실패:", error)
        temp_message.remove()
        error_message = create_chat_div("오류가 발생했습니다.", "start")
        
    });

}