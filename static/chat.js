/* PEHero — chat client (SSE streaming, 3-pane interactions). */

(() => {
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => Array.from(document.querySelectorAll(sel));

    let currentSessionId = getSidFromURL();
    let streaming = false;

    // ── URL session id ─────────────────────────────────────────────
    function getSidFromURL() {
        const p = new URLSearchParams(window.location.search);
        return p.get("sid") || "";
    }
    function setSid(sid) {
        currentSessionId = sid;
        const u = new URL(window.location);
        u.searchParams.set("sid", sid);
        history.replaceState(null, "", u);
    }

    // ── Message rendering ─────────────────────────────────────────
    function addBubble(role, text, agentSlug) {
        const wrap = document.createElement("div");
        wrap.className = `msg msg-${role}`;
        if (role === "assistant" && agentSlug) {
            const hdr = document.createElement("div");
            hdr.className = "msg-agent";
            hdr.innerHTML = `<span class="msg-agent-icon">◆</span><span class="msg-agent-label">${agentSlug}</span>`;
            wrap.appendChild(hdr);
        }
        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.textContent = text;
        wrap.appendChild(bubble);
        $("#messages").appendChild(wrap);
        scrollMessagesBottom();
        return bubble;
    }

    function appendToolLog(bubble, name, args) {
        let log = bubble.parentElement.querySelector(".tool-log");
        if (!log) {
            log = document.createElement("div");
            log.className = "tool-log";
            bubble.parentElement.appendChild(log);
        }
        const step = document.createElement("div");
        step.className = "tool-step";
        const argStr = args ? JSON.stringify(args).slice(0, 140) : "";
        step.innerHTML = `→ <span class="tool-name">${name}</span> <span class="tool-args">${argStr}</span>`;
        log.appendChild(step);
    }

    function scrollMessagesBottom() {
        const m = $("#messages");
        m.scrollTop = m.scrollHeight;
    }

    function renderMarkdownLite(text) {
        // Tiny inline renderer — bold, bullets, fences
        let out = text
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/```([\s\S]*?)```/g, "<pre>$1</pre>")
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        const lines = out.split("\n");
        const html = [];
        let inList = false;
        for (const l of lines) {
            if (l.match(/^- /)) {
                if (!inList) { html.push("<ul>"); inList = true; }
                html.push(`<li>${l.slice(2)}</li>`);
            } else {
                if (inList) { html.push("</ul>"); inList = false; }
                html.push(l || "<br>");
            }
        }
        if (inList) html.push("</ul>");
        return html.join("\n");
    }

    // ── SSE send ──────────────────────────────────────────────────
    async function sendMessage(evt) {
        if (evt) evt.preventDefault();
        if (streaming) return;
        const ta = $("#chat-input");
        const msg = ta.value.trim();
        if (!msg) return;

        streaming = true;
        $("#send-btn").disabled = true;

        // Hide welcome hero
        const wh = $("#welcome-hero");
        if (wh) wh.style.display = "none";

        // user bubble
        addBubble("user", msg);
        ta.value = "";
        ta.style.height = "";

        const body = new URLSearchParams({ msg, sid: currentSessionId || "" });

        const resp = await fetch("/app/chat", { method: "POST", body });
        if (!resp.ok) {
            addBubble("assistant", "Error: " + resp.status);
            streaming = false; $("#send-btn").disabled = false;
            return;
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let bubble = null;
        let accumulated = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            let idx;
            while ((idx = buffer.indexOf("\n\n")) !== -1) {
                const raw = buffer.slice(0, idx);
                buffer = buffer.slice(idx + 2);
                handleEvent(raw, (type, payload) => {
                    if (type === "agent_route") {
                        $("#current-agent-label").textContent = payload.agent || payload.slug;
                        bubble = addBubble("assistant", "", payload.slug);
                        bubble.classList.add("streaming");
                    } else if (type === "token") {
                        if (!bubble) bubble = addBubble("assistant", "", "");
                        accumulated += payload.text;
                        bubble.innerHTML = renderMarkdownLite(accumulated);
                        scrollMessagesBottom();
                    } else if (type === "tool_start") {
                        appendToolLog(bubble || addBubble("assistant", "", ""), payload.name, payload.args);
                    } else if (type === "tool_end") {
                        // optional: append result preview
                    } else if (type === "artifact_show") {
                        showArtifact(payload);
                    } else if (type === "error") {
                        if (!bubble) bubble = addBubble("assistant", "", "");
                        bubble.textContent = "Error: " + (payload.message || "unknown");
                    } else if (type === "session") {
                        if (payload.sid) setSid(payload.sid);
                    } else if (type === "done") {
                        if (bubble) bubble.classList.remove("streaming");
                    }
                });
            }
        }
        streaming = false; $("#send-btn").disabled = false;
    }

    function handleEvent(raw, cb) {
        let type = null; let data = "";
        for (const line of raw.split("\n")) {
            if (line.startsWith("event: ")) type = line.slice(7).trim();
            else if (line.startsWith("data: ")) data += line.slice(6);
        }
        if (!type) return;
        try { cb(type, data ? JSON.parse(data) : {}); }
        catch (e) { console.error("bad sse line", raw, e); }
    }

    // ── Artifacts ─────────────────────────────────────────────────
    function showArtifact(payload) {
        const body = $("#artifact-body");
        const empty = $("#artifact-empty");
        empty.style.display = "none";
        body.style.display = "block";

        $("#artifact-subtitle").textContent = payload.subtitle || "";
        const card = document.createElement("div");
        card.className = "artifact-card";
        const title = payload.title || "Artifact";
        const kind = payload.kind || "note";
        card.innerHTML = `
            <div class="meta">${kind}</div>
            <h4>${title}</h4>
            <div class="body">${renderArtifactHTML(payload)}</div>
        `;
        body.prepend(card);

        // Auto-open the pane
        document.querySelector(".app").classList.remove("pane-closed");
        $("#right-pane").classList.add("open");
        $("#artifact-btn").classList.add("active");
    }

    function renderArtifactHTML(p) {
        if (p.kind === "table" && Array.isArray(p.rows)) {
            if (!p.rows.length) return "<p><em>No rows.</em></p>";
            const cols = p.columns || Object.keys(p.rows[0]);
            const head = "<tr>" + cols.map(c => `<th>${c}</th>`).join("") + "</tr>";
            const body = p.rows.map(r => "<tr>" + cols.map(c => `<td>${formatCell(r[c])}</td>`).join("") + "</tr>").join("");
            return `<table class="artifact-table">${head}${body}</table>`;
        }
        if (p.kind === "citations" && Array.isArray(p.items)) {
            return p.items.map(it => `
                <div style="margin-bottom:.6rem;">
                    <div style="color:var(--ink); font-size:.8rem; font-weight:500;">${it.title || ""}</div>
                    <div style="color:var(--ink-dim); font-size:.68rem; font-family:'JetBrains Mono',monospace;">${it.doc_type || ""} · score ${(it.score||0).toFixed(2)}</div>
                    <div style="color:var(--ink-muted); font-size:.75rem; margin-top:.25rem;">${(it.snippet || "").replace(/\n/g,"<br>")}</div>
                </div>
            `).join("");
        }
        if (p.body_md) {
            return renderMarkdownLite(p.body_md);
        }
        return `<pre>${JSON.stringify(p, null, 2)}</pre>`;
    }

    function formatCell(v) {
        if (v === null || v === undefined) return "—";
        if (typeof v === "number") return v.toLocaleString();
        if (typeof v === "object") return JSON.stringify(v);
        return String(v);
    }

    // ── UI helpers ────────────────────────────────────────────────
    window.toggleLeftPane = () => {
        $(".left-pane").classList.toggle("open");
        $(".left-overlay").classList.toggle("visible");
    };
    window.toggleArtifactPane = () => {
        const r = $("#right-pane");
        const app = $(".app");
        if (r.classList.contains("open")) {
            r.classList.remove("open");
            app.classList.add("pane-closed");
            $("#artifact-btn").classList.remove("active");
        } else {
            r.classList.add("open");
            app.classList.remove("pane-closed");
            $("#artifact-btn").classList.add("active");
        }
    };
    window.toggleGroup = (id) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.toggle("open");
        const btn = document.getElementById("btn-" + id);
        if (btn) btn.classList.toggle("open");
    };
    window.handleKey = (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); sendMessage(ev); }
    };
    window.autoResize = (el) => {
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 240) + "px";
    };
    window.fillChat = (text) => {
        const ta = $("#chat-input");
        ta.value = text;
        ta.focus();
        autoResize(ta);
    };
    window.newChat = () => { window.location.href = "/app"; };
    window.showSignIn = () => { $("#signin-overlay").classList.add("visible"); $("#signin-email").focus(); };
    window.doSignIn = async () => {
        const email = $("#signin-email").value.trim();
        if (!email) return;
        const r = await fetch("/app/auth/signin", { method: "POST", body: new URLSearchParams({ email }) });
        if (r.ok) window.location.reload();
    };
    window.signOut = async () => {
        await fetch("/app/auth/signout", { method: "POST" });
        window.location.reload();
    };

    window.sendMessage = sendMessage;
})();
