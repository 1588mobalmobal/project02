async function sendMessage(){
    const input = document.getElementById("diaryContent");
    const message = input.value.trim()
    if (message == "") return;

    try {
        const response = await fetch("http://127.0.0.1:5252/api/log", {
            method: "POST",
            headers: {
                "Content-Type" : "application/json"
            },
        body: JSON.stringify({"input" : message})
        });

        if (!response.ok) throw new Error("서버 응답 오류");
        const data = await response.json()

        localStorage.setItem("result", JSON.stringify(data.response))
        
        window.location.href = data.redirect
    } catch (error) {
        console.log("에러")
    }


};


