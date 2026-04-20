/* PEHero — chat client (SSE streaming, 3-pane interactions). */

(() => {
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => Array.from(document.querySelectorAll(sel));

    let currentSessionId = getSidFromURL();
    let currentAgentSlug = null;
    let streaming = false;

    // Agent-prompt lookup table — embedded by the server in a <script id="agent-prompts-data">.
    const AGENT_PROMPTS = readJsonScript("agent-prompts-data") || {};
    const AGENT_NAMES = readJsonScript("agent-names-data") || {};

    function readJsonScript(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try { return JSON.parse(el.textContent); }
        catch (e) { console.warn("bad JSON in #" + id, e); return null; }
    }

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
            const nice = AGENT_NAMES[agentSlug] || agentSlug;
            hdr.innerHTML = `<span class="msg-agent-icon">◆</span><span class="msg-agent-label">${nice}</span>`;
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

    // ── Thinking indicator (timer + rotating tool name) ────────────
    let thinker = null;
    function showThinking(bubble) {
        if (!bubble) return;
        thinker = {
            started: Date.now(),
            tool: null,
            el: document.createElement("div"),
            timerId: null,
        };
        thinker.el.className = "thinking-indicator";
        thinker.el.innerHTML = `<span class="dot"></span><span class="label">Thinking… <span class="secs">0s</span></span>`;
        bubble.parentElement.insertBefore(thinker.el, bubble);
        thinker.timerId = setInterval(updateThinking, 500);
    }
    function updateThinking() {
        if (!thinker) return;
        const secs = Math.floor((Date.now() - thinker.started) / 1000);
        const label = thinker.tool
            ? `Thinking… <span class="secs">${secs}s</span> · calling <code>${thinker.tool}</code>`
            : `Thinking… <span class="secs">${secs}s</span>`;
        thinker.el.querySelector(".label").innerHTML = label;
    }
    function setThinkingTool(name) {
        if (!thinker) return;
        thinker.tool = name;
        updateThinking();
    }
    function hideThinking() {
        if (!thinker) return;
        clearInterval(thinker.timerId);
        if (thinker.el && thinker.el.parentElement) thinker.el.parentElement.removeChild(thinker.el);
        thinker = null;
    }

    // ── Sample cards (Gemini-style) ──────────────────────────────
    window.updateSampleCards = (slug) => {
        const row = $("#sample-cards-row");
        const label = $("#sample-cards-label");
        if (!row) return;
        let prompts = (slug && AGENT_PROMPTS[slug]) || [];
        if (!prompts.length) {
            prompts = [
                "triage: vertical SaaS, €8M EBITDA, 20% growth, €85M ask",
                "lbo: 5-year model for Northwind at 12x entry, 12% growth",
                "comps: software precedent M&A 2022-2024 under €500M EV",
                "memo: draft the IC memo for Meridian Healthcare",
                "vdr: audit the data room for Meridian Healthcare",
                "crm: top 10 LPs to reach out to for Fund V",
            ];
        }
        row.innerHTML = "";
        prompts.slice(0, 6).forEach(p => {
            const b = document.createElement("button");
            b.className = "sample-card";
            b.title = p;
            b.innerHTML = `<span class="sample-card-text"></span>`;
            b.querySelector(".sample-card-text").textContent = p;
            b.onclick = () => { fillChat(p); sendMessage(null); };
            row.appendChild(b);
        });
        if (label) {
            label.innerHTML = slug && AGENT_NAMES[slug]
                ? `<span class="sample-cards-label">Try with ${AGENT_NAMES[slug]}</span>`
                : `<span class="sample-cards-label">Try a prompt</span>`;
        }
    };

    // Update sample cards when the user types a prefix like "lbo:"
    window.onInputChange = (ta) => {
        const v = (ta.value || "").trim().toLowerCase();
        const m = v.match(/^(\w{2,10}):/);
        if (!m) return;
        const prefix = m[1] + ":";
        // find slug with this prefix
        for (const slug of Object.keys(AGENT_PROMPTS)) {
            const first = (AGENT_PROMPTS[slug][0] || "").toLowerCase();
            if (first.startsWith(prefix)) { updateSampleCards(slug); return; }
        }
    };

    // ── Memo → PDF preview (IC Memo Writer + any markdown-heavy response) ──
    const MEMO_AGENTS = new Set(["investor_memo", "deal_teaser", "lp_update", "outreach_email", "loi_writer"]);
    let lastMemoFileId = null;

    async function renderMemoPdf(markdown, title) {
        const body = new URLSearchParams({ markdown, title: title || "IC memo" });
        const r = await fetch("/app/memo-pdf/render", { method: "POST", body });
        if (!r.ok) throw new Error("render failed " + r.status);
        const data = await r.json();
        if (data.error) throw new Error(data.error);
        lastMemoFileId = data.file_id;
        openPdfInPane(data.file_url, null, data.title);
        return data;
    }

    function openPdfInPane(fileUrl, searchText, title) {
        const src = fileUrl.startsWith("http") ? fileUrl : fileUrl;
        const body = $("#artifact-body");
        const empty = $("#artifact-empty");
        if (empty) empty.style.display = "none";
        body.style.display = "block";
        body.innerHTML = `
            <div class="pdf-wrap">
              <div class="pdf-caption">${title ? escapeHtml(title) : "Memo preview"}${searchText ? " · <i>highlighting \"" + escapeHtml(searchText.slice(0, 40)) + "\"</i>" : ""}</div>
              <iframe id="pdf-frame" class="pdf-iframe" src="${src}" allow="fullscreen"></iframe>
            </div>`;
        $("#artifact-subtitle").textContent = title || "PDF preview";
        document.querySelector(".app").classList.remove("pane-closed");
        $("#right-pane").classList.add("open");
        $("#artifact-btn").classList.add("active");
    }

    async function highlightInLastPdf(searchText) {
        if (!lastMemoFileId) return false;
        const frame = document.getElementById("pdf-frame");
        if (frame) frame.src = `/app/memo-pdf/file/${lastMemoFileId}`;
        const cap = document.querySelector(".pdf-caption");
        if (cap) cap.innerHTML = `Memo preview · <i>"${escapeHtml(searchText.slice(0, 40))}"</i>`;
        return true;
    }
    window.renderMemoPdf = renderMemoPdf;
    window.openPdfInPane = openPdfInPane;
    window.highlightInLastPdf = highlightInLastPdf;

    function maybeAppendMemoPreviewButton(bubble, text, agentSlug) {
        if (!bubble || !text) return;
        if (!MEMO_AGENTS.has(agentSlug)) return;
        // Heuristic: a memo needs at least a couple of markdown headers + some length
        const looksMemo = text.length > 400 && /(^|\n)##?\s+\w/.test(text);
        if (!looksMemo) return;
        const existing = bubble.parentElement.querySelector(".memo-preview-row");
        if (existing) return;
        const row = document.createElement("div");
        row.className = "memo-preview-row";
        row.innerHTML = `
            <button class="memo-preview-btn">📄 Preview PDF</button>
            <span class="memo-preview-hint">Renders this memo as a PDF in the right pane — then ask "show me the deal size" to jump to it.</span>`;
        bubble.parentElement.appendChild(row);
        const btn = row.querySelector(".memo-preview-btn");
        btn.onclick = async () => {
            btn.disabled = true; btn.textContent = "Rendering…";
            try {
                await renderMemoPdf(text, "IC memo");
                btn.textContent = "✓ PDF open in the right pane";
            } catch (e) {
                btn.textContent = "Render failed";
                console.error(e);
            }
        };
    }

    // If the user's last message looks like a PDF-highlight intent *and* we
    // have a memo PDF already rendered, intercept it client-side and
    // navigate the iframe to the highlighted match — no SSE roundtrip.
    function tryHighlightIntent(msg) {
        if (!lastMemoFileId) return false;
        const m = msg.match(/^\s*(?:show|find|highlight|jump to|where (?:is|does))\s+(?:me\s+)?(?:the\s+)?(.+?)[?.!]?\s*$/i);
        if (!m) return false;
        const term = m[1].trim();
        if (term.length < 3 || term.length > 60) return false;
        highlightInLastPdf(term);
        // Also echo as a tiny user-side message so the transcript shows the action
        const bubble = addBubble("user", msg);
        addBubble("assistant", `Highlighted "${term}" in the memo PDF →`, null);
        return true;
    }
    window.tryHighlightIntent = tryHighlightIntent;

    // ── "Should we do that?" follow-up button ─────────────────────
    function maybeAppendFollowUp(bubble, text) {
        if (!bubble || !text) return;
        // look for "Next step —" or "Next step:" pattern
        const m = text.match(/\*?\*?Next step\*?\*?[\s]*[—–:-][\s]*([^\n]+)/i);
        if (!m) return;
        const action = m[1].trim().replace(/\*+$/, "");
        const row = document.createElement("div");
        row.className = "followup-row";
        row.innerHTML = `
            <div class="followup-prompt">${escapeHtml(action)}</div>
            <button class="followup-btn followup-yes">Yes, do that</button>
            <button class="followup-btn followup-no">No thanks</button>
        `;
        bubble.parentElement.appendChild(row);
        row.querySelector(".followup-yes").onclick = () => {
            row.remove();
            fillChat("Yes — do that: " + action);
            sendMessage(null);
        };
        row.querySelector(".followup-no").onclick = () => row.remove();
    }

    function escapeHtml(s) {
        return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // ── SSE send ──────────────────────────────────────────────────
    async function sendMessage(evt) {
        if (evt) evt.preventDefault();
        if (streaming) return;
        const ta = $("#chat-input");
        const msg = ta.value.trim();
        if (!msg) return;

        // Client-side fast path: if a memo PDF is already open and the user
        // asks "show me the deal size", highlight directly in the iframe
        // and skip the round-trip.
        if (tryHighlightIntent(msg)) {
            ta.value = "";
            ta.style.height = "";
            return;
        }

        streaming = true;
        $("#send-btn").disabled = true;

        const wh = $("#welcome-hero");
        if (wh) wh.style.display = "none";

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
                        const nice = payload.agent || AGENT_NAMES[payload.slug] || payload.slug;
                        $("#current-agent-label").textContent = nice;
                        currentAgentSlug = payload.slug;
                        updateSampleCards(payload.slug);
                        bubble = addBubble("assistant", "", payload.slug);
                        bubble.classList.add("streaming");
                        showThinking(bubble);
                    } else if (type === "token") {
                        if (!bubble) bubble = addBubble("assistant", "", "");
                        if (accumulated === "") hideThinking();
                        accumulated += payload.text;
                        bubble.innerHTML = renderMarkdownLite(accumulated);
                        scrollMessagesBottom();
                    } else if (type === "tool_start") {
                        setThinkingTool(payload.name);
                        appendToolLog(bubble || addBubble("assistant", "", ""), payload.name, payload.args);
                    } else if (type === "tool_end") {
                        // update thinker with "(done)" flavor; leaving tool name as-is
                    } else if (type === "artifact_show") {
                        showArtifact(payload);
                    } else if (type === "error") {
                        hideThinking();
                        if (!bubble) bubble = addBubble("assistant", "", "");
                        bubble.textContent = "Error: " + (payload.message || "unknown");
                    } else if (type === "session") {
                        if (payload.sid) setSid(payload.sid);
                    } else if (type === "done") {
                        hideThinking();
                        if (bubble) bubble.classList.remove("streaming");
                        maybeAppendFollowUp(bubble, accumulated);
                        maybeAppendMemoPreviewButton(bubble, accumulated, payload.slug || currentAgentSlug);
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
                    <div style="color:var(--ink-dim); font-size:.68rem; font-family:'JetBrains Mono',monospace;">${it.doc_type || ""}${it.url ? ` · <a href="${it.url}" target="_blank">link</a>` : ""} · score ${(it.score||0).toFixed(2)}</div>
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
        onInputChange(ta);
    };
    window.newChat = () => { window.location.href = "/app"; };
    window.showSignIn = () => { $("#signin-overlay").classList.add("visible"); $("#signin-email").focus(); };
    window.doSignIn = async () => {
        const email = $("#signin-email").value.trim();
        if (!email) return;
        const r = await fetch("/app/auth/signin", { method: "POST", body: new URLSearchParams({ email }) });
        if (r.ok) window.location.reload();
    };
    window.setCurrency = async (code) => {
        const r = await fetch("/app/config", {
            method: "POST",
            body: new URLSearchParams({ currency: code }),
        });
        if (r.ok) {
            document.querySelectorAll(".cfg-chip").forEach(el => {
                el.classList.toggle("active", el.textContent.trim().endsWith(code));
            });
            // Page reloads next navigation; refresh pipeline/cards currency now.
            window.location.reload();
        }
    };
    window.signOut = async () => {
        await fetch("/app/auth/signout", { method: "POST" });
        window.location.reload();
    };

    window.sendMessage = sendMessage;
})();
