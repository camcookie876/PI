const API_BASE = "http://127.0.0.1:8765";

// Tab handling
document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const tabId = link.getAttribute("data-tab");

    document.querySelectorAll(".nav-link").forEach((l) =>
      l.classList.remove("active")
    );
    link.classList.add("active");

    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.remove("active")
    );
    document.getElementById("tab-" + tabId).classList.add("active");
  });
});

async function fetchStatus() {
  try:
    const res = await fetch(API_BASE + "/status");
    const data = await res.json();
    updateUI(data);
  } catch (e) {
    console.error("Failed to fetch status", e);
  }
}

// Called with data from /status or /plugin/toggle
function updateUI(state) {
  const plugins = state.plugins || [];
  const arduinoData = state.arduino_data || "None";
  const connectableApps = state.connectable_apps || [];

  // Home tab
  const running = plugins.filter((p) => p.enabled).length;
  document.getElementById("plugin-count").innerText =
    "You currently have " +
    running +
    " plugin" +
    (running === 1 ? "" : "s") +
    " running";

  document.getElementById("arduino-data").innerText = arduinoData;

  // Plugins tab
  const list = document.getElementById("plugin-list");
  list.innerHTML = "";
  plugins.forEach((p) => {
    const item = document.createElement("div");
    item.className = "plugin-item";

    const info = document.createElement("div");
    info.className = "plugin-info";

    const name = document.createElement("div");
    name.className = "plugin-name";
    name.innerText = p.name;

    const status = document.createElement("div");
    status.className = "plugin-status";
    status.innerText = p.status;

    info.appendChild(name);
    info.appendChild(status);

    const toggleDiv = document.createElement("div");
    toggleDiv.className = "plugin-toggle";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = p.enabled;

    checkbox.addEventListener("change", async () => {
      try {
        const res = await fetch(
          API_BASE +
            "/plugin/toggle?id=" +
            encodeURIComponent(p.id) +
            "&enabled=" +
            (checkbox.checked ? "1" : "0")
        );
        const data = await res.json();
        if (data.ok && data.state) {
          updateUI(data.state);
        }
      } catch (e) {
        console.error("Failed to toggle plugin", e);
      }
    });

    toggleDiv.appendChild(checkbox);

    item.appendChild(info);
    item.appendChild(toggleDiv);

    list.appendChild(item);
  });

  // Connect tab
  const connectList = document.getElementById("connect-app-list");
  connectList.innerHTML = "";

  connectableApps.forEach((app) => {
    const item = document.createElement("div");
    item.className = "connect-app";

    const info = document.createElement("div");
    info.className = "connect-info";

    const name = document.createElement("div");
    name.className = "connect-name";
    name.innerText = app.name;

    const status = document.createElement("div");
    status.className = "connect-status";

    if (!app.installed) {
      const notInstalled = document.createElement("span");
      notInstalled.className = "badge badge-not-installed";
      notInstalled.innerText = "Not Installed";
      status.appendChild(notInstalled);
    } else {
      const installedBadge = document.createElement("span");
      installedBadge.className = "badge badge-installed";
      installedBadge.innerText = "Installed";

      const connectedBadge = document.createElement("span");
      connectedBadge.className =
        "badge " + (app.connected ? "badge-connected" : "badge-disconnected");
      connectedBadge.innerText = app.connected ? "Connected" : "Not Connected";

      status.appendChild(installedBadge);
      status.appendChild(document.createTextNode(" "));
      status.appendChild(connectedBadge);
    }

    info.appendChild(name);
    info.appendChild(status);

    item.appendChild(info);

    const actions = document.createElement("div");
    actions.className = "connect-actions";

    if (app.installed) {
      const connectBtn = document.createElement("button");
      connectBtn.className = "connect-btn";
      connectBtn.innerText = app.connected ? "Reconnect" : "Connect";

      connectBtn.addEventListener("click", async () => {
        try {
          const res = await fetch(
            API_BASE + "/connect?app_id=" + encodeURIComponent(app.id)
          );
          const data = await res.json();
          if (data.ok) {
            fetchStatus();
          }
        } catch (e) {
          console.error("Failed to connect app", e);
        }
      });

      const disconnectBtn = document.createElement("button");
      disconnectBtn.className = "disconnect-btn";
      disconnectBtn.innerText = "Disconnect";

      disconnectBtn.addEventListener("click", async () => {
        try {
          const res = await fetch(
            API_BASE + "/disconnect?app_id=" + encodeURIComponent(app.id)
          );
          const data = await res.json();
          if (data.ok) {
            fetchStatus();
          }
        } catch (e) {
          console.error("Failed to disconnect app", e);
        }
      });

      const shutdownBtn = document.createElement("button");
      shutdownBtn.className = "shutdown-btn";
      shutdownBtn.innerText = "Request Shutdown";

      shutdownBtn.addEventListener("click", async () => {
        try {
          const res = await fetch(
            API_BASE + "/shutdown?app_id=" + encodeURIComponent(app.id)
          );
          const data = await res.json();
          if (data.ok && data.shutting_down) {
            alert("Plugin engine will shut down soon (no other apps connected).");
          } else if (data.ok && !data.shutting_down) {
            alert("Engine stayed alive: " + (data.reason || ""));
          }
        } catch (e) {
          console.error("Failed to request shutdown", e);
        }
      });

      actions.appendChild(connectBtn);
      actions.appendChild(disconnectBtn);
      actions.appendChild(shutdownBtn);
    }

    item.appendChild(actions);

    connectList.appendChild(item);
  });
}

// Initial load
fetchStatus();
setInterval(fetchStatus, 2000);