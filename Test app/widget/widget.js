/**
 * RAG Widget — demo bundle
 *
 * This is the "one script tag" a host site adds. It defines a custom
 * element <rag-widget> that:
 *   - attaches a Shadow DOM (style isolation from the host page)
 *   - renders either an inline search box or a floating chat launcher,
 *     depending on the `mode` attribute
 *   - calls your FastAPI gateway directly (fetch), same as any frontend
 *
 * No React, no build tool — deliberately, so you can open host.html
 * straight in a browser and see it work. Swap the render logic for
 * React later if you want; the mounting/isolation pattern stays the same.
 */

(function () {
  const STYLES = `
    :host {
      all: initial;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color-scheme: light;
    }
    * { box-sizing: border-box; }

    .panel {
      background: #ffffff;
      border: 1px solid #e2e2e7;
      border-radius: 14px;
      box-shadow: 0 8px 24px rgba(20, 20, 40, 0.08);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* --- inline mode --- */
    .inline .panel { width: 100%; max-width: 480px; }
    .inline .header {
      padding: 14px 16px;
      border-bottom: 1px solid #eee;
      font-weight: 600;
      font-size: 14px;
      color: #1a1a2e;
    }

    /* --- floating mode --- */
    .launcher {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #4338ca;
      color: white;
      border: none;
      cursor: pointer;
      font-size: 22px;
      box-shadow: 0 6px 20px rgba(67, 56, 202, 0.4);
      z-index: 999999;
    }
    .launcher:hover { background: #372fa3; }

    .floating-panel {
      position: fixed;
      bottom: 92px;
      right: 24px;
      width: 340px;
      height: 460px;
      z-index: 999999;
      display: none;
    }
    .floating-panel.open { display: flex; }
    .floating-panel .header {
      background: #4338ca;
      color: white;
      padding: 14px 16px;
      font-weight: 600;
      font-size: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .floating-panel .close {
      background: none; border: none; color: white; cursor: pointer;
      font-size: 18px; line-height: 1; opacity: 0.85;
    }
    .floating-panel .close:hover { opacity: 1; }

    /* --- shared body --- */
    .body {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      font-size: 13px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .msg { max-width: 90%; line-height: 1.5; }
    .msg.user {
      align-self: flex-end;
      background: #4338ca;
      color: white;
      padding: 8px 12px;
      border-radius: 12px 12px 2px 12px;
    }
    .msg.bot {
      align-self: flex-start;
      background: #f4f4f8;
      color: #1a1a2e;
      padding: 8px 12px;
      border-radius: 12px 12px 12px 2px;
    }
    .msg.bot.loading { color: #888; font-style: italic; }

    .citations { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
    .citation {
      background: white;
      border: 1px solid #e2e2e7;
      border-radius: 8px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 12px;
    }
    .citation:hover { border-color: #4338ca; }
    .citation .title { font-weight: 600; color: #4338ca; }
    .citation .snippet {
      display: none;
      margin-top: 4px;
      color: #555;
      font-size: 12px;
      line-height: 1.4;
    }
    .citation.expanded .snippet { display: block; }

    .composer {
      border-top: 1px solid #eee;
      padding: 10px;
      display: flex;
      gap: 8px;
    }
    .composer input {
      flex: 1;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 13px;
      outline: none;
      font-family: inherit;
    }
    .composer input:focus { border-color: #4338ca; }
    .composer button {
      background: #4338ca;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 8px 14px;
      font-size: 13px;
      cursor: pointer;
    }
    .composer button:disabled { opacity: 0.5; cursor: default; }

    .meta {
      font-size: 10px;
      color: #999;
      padding: 4px 12px 8px;
      border-top: 1px solid #f4f4f4;
    }

    .citation .open-doc {
      display: inline-block;
      margin-top: 6px;
      font-size: 11px;
      color: #4338ca;
      cursor: pointer;
      text-decoration: underline;
    }

    /* --- document viewer modal (overlay, same page, session untouched) --- */
    .doc-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(20, 20, 40, 0.45);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000000;
    }
    .doc-modal-backdrop.open { display: flex; }
    .doc-modal {
      background: white;
      border-radius: 12px;
      width: min(560px, 90vw);
      max-height: 80vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.25);
    }
    .doc-modal .doc-header {
      padding: 14px 16px;
      border-bottom: 1px solid #eee;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 14px;
      font-weight: 600;
      color: #1a1a2e;
    }
    .doc-modal .doc-header button {
      background: none; border: none; cursor: pointer; font-size: 18px; color: #888;
    }
    .doc-modal .doc-body {
      padding: 16px;
      overflow-y: auto;
      font-size: 13px;
      line-height: 1.6;
      color: #333;
    }
    .doc-modal .doc-footer {
      padding: 10px 16px;
      border-top: 1px solid #eee;
      display: flex;
      justify-content: flex-end;
    }
    .doc-modal .doc-footer a {
      font-size: 12px;
      color: #4338ca;
    }
  `;

  class RagWidget extends HTMLElement {
    connectedCallback() {
      this.apiBase = this.getAttribute("api-base") || "http://localhost:8000";
      this.orgId = this.getAttribute("org-id") || "demo-org";
      this.mode = this.getAttribute("mode") || "floating"; // "floating" | "inline"
      this.sessionId = null;

      const shadow = this.attachShadow({ mode: "open" });
      const style = document.createElement("style");
      style.textContent = STYLES;
      shadow.appendChild(style);

      const wrapper = document.createElement("div");
      wrapper.className = this.mode === "inline" ? "inline" : "";
      shadow.appendChild(wrapper);
      this._wrapper = wrapper;

      if (this.mode === "inline") {
        this._renderInline(wrapper);
      } else {
        this._renderFloating(wrapper);
      }

      // Document viewer modal lives once per widget instance, reused for
      // any citation clicked. It's just an overlay in the same shadow DOM
      // — opening it never touches the host page or this.sessionId.
      const modalBackdrop = document.createElement("div");
      modalBackdrop.className = "doc-modal-backdrop";
      modalBackdrop.innerHTML = `
        <div class="doc-modal">
          <div class="doc-header">
            <span data-doc-title>Document</span>
            <button data-doc-close aria-label="Close">✕</button>
          </div>
          <div class="doc-body" data-doc-body></div>
          <div class="doc-footer">
            <a href="#" target="_blank" rel="noopener" data-doc-newtab>Open in new tab ↗</a>
          </div>
        </div>
      `;
      shadow.appendChild(modalBackdrop);
      this._modal = modalBackdrop;
      modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) modalBackdrop.classList.remove("open");
      });
      modalBackdrop.querySelector("[data-doc-close]").addEventListener("click", () =>
        modalBackdrop.classList.remove("open")
      );
    }

    _openDocument(citation) {
      // Opening this never reloads the page, never touches this.sessionId,
      // and the chat panel underneath keeps every message it already had.
      this._modal.querySelector("[data-doc-title]").textContent = citation.title;
      this._modal.querySelector("[data-doc-body]").innerHTML = `
        <p><strong>${citation.title}</strong></p>
        <p>${citation.snippet}</p>
        <p style="color:#999;font-size:12px;">
          In production this pane would render the actual PDF/HTML via an
          &lt;iframe&gt; pointed at a signed GCS URL, or via PDF.js for finer
          control over PDF rendering.
        </p>
      `;
      this._modal.querySelector("[data-doc-newtab]").href = citation.url;
      this._modal.classList.add("open");
    }

    _renderInline(root) {
      root.innerHTML = `
        <div class="panel">
          <div class="header">Ask a question</div>
          <div class="body" data-body></div>
          <div class="composer">
            <input type="text" placeholder="e.g. What is the refund policy?" data-input />
            <button data-send>Ask</button>
          </div>
          <div class="meta">Connected to ${this.apiBase}</div>
        </div>
      `;
      this._wireComposer(root);
    }

    _renderFloating(root) {
      root.innerHTML = `
        <button class="launcher" data-launcher aria-label="Open chat">💬</button>
        <div class="floating-panel panel" data-panel>
          <div class="header">
            <span>Ask us anything</span>
            <button class="close" data-close aria-label="Close">✕</button>
          </div>
          <div class="body" data-body></div>
          <div class="composer">
            <input type="text" placeholder="Type your question..." data-input />
            <button data-send>Send</button>
          </div>
        </div>
      `;
      const launcher = root.querySelector("[data-launcher]");
      const panel = root.querySelector("[data-panel]");
      launcher.addEventListener("click", () => panel.classList.toggle("open"));
      root.querySelector("[data-close]").addEventListener("click", () =>
        panel.classList.remove("open")
      );
      this._wireComposer(root);
    }

    _wireComposer(root) {
      const input = root.querySelector("[data-input]");
      const sendBtn = root.querySelector("[data-send]");
      const send = () => {
        const question = input.value.trim();
        if (!question) return;
        input.value = "";
        this._ask(root, question);
      };
      sendBtn.addEventListener("click", send);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") send();
      });
    }

    async _ask(root, question) {
      const body = root.querySelector("[data-body]");
      const sendBtn = root.querySelector("[data-send]");

      const userMsg = document.createElement("div");
      userMsg.className = "msg user";
      userMsg.textContent = question;
      body.appendChild(userMsg);

      const loadingMsg = document.createElement("div");
      loadingMsg.className = "msg bot loading";
      loadingMsg.textContent = "Thinking...";
      body.appendChild(loadingMsg);
      body.scrollTop = body.scrollHeight;

      sendBtn.disabled = true;
      try {
        const res = await fetch(`${this.apiBase}/api/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: this.sessionId,
            question,
            filters: { org_id: this.orgId },
          }),
        });
        const data = await res.json();
        this.sessionId = data.session_id;

        loadingMsg.remove();
        const botMsg = document.createElement("div");
        botMsg.className = "msg bot";
        botMsg.textContent = data.answer;
        body.appendChild(botMsg);

        if (data.citations && data.citations.length) {
          const citWrap = document.createElement("div");
          citWrap.className = "citations";
          data.citations.forEach((c) => {
            const el = document.createElement("div");
            el.className = "citation";
            el.innerHTML = `
              <div class="title">📄 ${c.title}</div>
              <div class="snippet">
                ${c.snippet}
                <div class="open-doc" data-open-doc>Open full document ↗</div>
              </div>
            `;
            // Click the title: expand/collapse the short preview inline.
            el.querySelector(".title").addEventListener("click", () =>
              el.classList.toggle("expanded")
            );
            // Click "Open full document": modal viewer, session untouched.
            el.querySelector("[data-open-doc]").addEventListener("click", (e) => {
              e.stopPropagation();
              this._openDocument(c);
            });
            citWrap.appendChild(el);
          });
          body.appendChild(citWrap);
        }
      } catch (err) {
        loadingMsg.textContent =
          "Couldn't reach the backend. Is it running on " + this.apiBase + "?";
        loadingMsg.classList.remove("loading");
      } finally {
        sendBtn.disabled = false;
        body.scrollTop = body.scrollHeight;
      }
    }
  }

  customElements.define("rag-widget", RagWidget);
})();
