async function delete_log(button){
    const log_id = button.dataset.id
    const modal = document.getElementById("cardModal")
    const modal_instance = bootstrap.Modal.getInstance(modal)

    try {
        const response = await fetch("http://127.0.0.1:5252/delete", {
            method: "POST",
            headers: {
                "Content-Type" : "application/json"
            },
        body: JSON.stringify({"id" : log_id})
        });

        if (!response.ok) throw new Error("서버 응답 오류");
        
        modal_instance.hide()
        window.location.href = "/browse"
    } catch (error) {
        console.log("Error!")
    }
}

function take_over_id(button){
    const log_id = button.dataset.id;
    const delete_btn = document.getElementById("delete-btn")
    delete_btn.dataset.id = log_id
}