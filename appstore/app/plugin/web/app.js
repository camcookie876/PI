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

// Called by Python
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

    checkbox.addEventListener("change", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api
          .toggle_plugin(p.id, checkbox.checked)
          .then((newState) => {
            updateUI(newState);
          });
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
    if (!app.installed) {
      // Still show, but no connect button
      const item = document.createElement("div");
      item.className = "connect-app";

      const info = document.createElement("div");
      info.className = "connect-info";

      const name = document.createElement("div");
      name.className = "connect-name";
      name.innerText = app.name;

      const status = document.createElement("div");
      status.className = "connect-status";
      status.innerHTML =
        '<span class="badge badge-not-installed">Not Installed</span>';

      info.appendChild(name);
      info.appendChild(status);

      item.appendChild(info);
      connectList.appendChild(item);
      return;
    }

    const item = document.createElement("div");
    item.className = "connect-app";

    const info = document.createElement("div");
    info.className = "connect-info";

    const name = document.createElement("div");
    name.className = "connect-name";
    name.innerText = app.name;

    const status = document.createElement("div");
    status.className = "connect-status";

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

    info.appendChild(name);
    info.appendChild(status);

    const actions = document.createElement("div");
    actions.className = "connect-actions";

    const connectBtn = document.createElement("button");
    connectBtn.className = "connect-btn";
    connectBtn.innerText = app.connected ? "Reconnect" : "Connect";

    connectBtn.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.connect_app(app.id).then((newState) => {
          updateUI(newState);
        });
      }
    });

    const disconnectBtn = document.createElement("button");
    disconnectBtn.className = "disconnect-btn";
    disconnectBtn.innerText = "Disconnect";

    disconnectBtn.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.disconnect_app(app.id).then((newState) => {
          updateUI(newState);
        });
      }
    });

    const shutdownBtn = document.createElement("button");
    shutdownBtn.className = "shutdown-btn";
    shutdownBtn.innerText = "Request Shutdown";

    shutdownBtn.addEventListener("click", () => {
      // UI only shows the info; real shutdown is via HTTP /shutdown?app_id=
      alert(
        "Apps should call /shutdown?app_id=" +
          app.id +
          " on the HTTP API. This button is just informational."
      );
    });

    actions.appendChild(connectBtn);
    actions.appendChild(disconnectBtn);
    actions.appendChild(shutdownBtn);

    item.appendChild(info);
    item.appendChild(actions);

    connectList.appendChild(item);
  });
}

// Initial state request
if (window.pywebview && window.pywebview.api) {
  window.pywebview.api.get_state().then((state) => {
    updateUI(state);
  });
}