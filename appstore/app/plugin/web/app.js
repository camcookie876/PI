function updateUI(status, arduinoData) {
    document.getElementById("plugin-count").innerText =
        "You currently have 1 plugin running";

    document.getElementById("arduino-data").innerText = arduinoData;
}