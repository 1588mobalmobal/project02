function show_result(){
    const result = JSON.parse(localStorage.getItem("result"))
    console.log(result.physical)
    const physical = document.getElementById("physical");
    physical.textContent = result.physical;
    document.getElementById("knowledge").innerHTML = `${result.knowledge}`
    document.getElementById("mental").innerHTML = `${result.mental}`
    document.getElementById("encouragement").innerHTML = `${result.encouragement}`
    document.getElementById("advice").innerHTML = `${result.advice}`
}

show_result()