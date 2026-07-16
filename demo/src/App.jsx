import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const formatDate = (value) => {
  if (!value) return "DATE REDACTED";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const getInitials = (name = "?") =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

const classifyPost = (post) => {
  const content = `${post.author || ""}\n${post.content || ""}`.toLowerCase();

  if (content.includes("急") || content.includes("徵") || content.includes("缺")) {
    return "HOT";
  }
  if (content.includes("台北") || content.includes("新北") || content.includes("線上")) {
    return "LOCAL";
  }
  if (post.url) {
    return "TRACE";
  }
  return "OPEN";
};

function LoadingScreen() {
  return (
    <main className="boot-screen">
      <div className="boot-card">
        <div className="boot-ring" />
        <p>BLACKBOX OS</p>
        <h1>Decrypting case index</h1>
        <span>CONNECTING TO MONGODB // POSTS COLLECTION</span>
      </div>
    </main>
  );
}

function App() {
  const [posts, setPosts] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadPosts() {
      setStatus("loading");
      setError("");

      try {
        const search = new URLSearchParams();
        search.set("limit", "180");
        if (query.trim()) search.set("search", query.trim());

        const response = await fetch(`${API_BASE}/api/posts?${search}`);
        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          throw new Error(payload?.error || `API ${response.status}`);
        }

        const payload = await response.json();
        if (!cancelled) {
          setPosts(payload.posts || []);
          setSelectedId((current) => current || payload.posts?.[0]?._id || null);
          setStatus("ready");
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message);
          setStatus("error");
        }
      }
    }

    const timer = window.setTimeout(loadPosts, query ? 240 : 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  const selectedPost = useMemo(
    () => posts.find((post) => post._id === selectedId) || posts[0],
    [posts, selectedId]
  );

  const groups = useMemo(() => {
    const map = new Map();
    posts.forEach((post) => {
      const group = post.group_name || "UNKNOWN CELL";
      map.set(group, (map.get(group) || 0) + 1);
    });
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [posts]);

  if (status === "loading" && posts.length === 0) {
    return <LoadingScreen />;
  }

  return (
    <main className="app-shell">
      <div className="screen-noise" />
      <section className="command-bar">
        <div>
          <p className="eyebrow">classified archive // mongodb live view</p>
          <h1>BLACKBOX CASE FILES</h1>
        </div>
        <div className="system-readout">
          <span>NODE: TPE-07</span>
          <strong>{posts.length.toString().padStart(3, "0")}</strong>
          <span>FILES ONLINE</span>
        </div>
      </section>

      <section className="dashboard">
        <aside className="left-rail">
          <label className="search-field">
            <span>TRACE QUERY</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="author / content / group"
            />
          </label>

          <div className="group-stack">
            <div className="panel-title">ACTIVE CELLS</div>
            {groups.length === 0 ? (
              <p className="empty-copy">No cells detected.</p>
            ) : (
              groups.slice(0, 6).map(([group, count]) => (
                <div className="cell-row" key={group}>
                  <span>{group}</span>
                  <strong>{count}</strong>
                </div>
              ))
            )}
          </div>

          <div className="signal-panel">
            <div className="panel-title">SIGNAL INTEGRITY</div>
            <div className="signal-grid">
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>
        </aside>

        <section className="case-list" aria-label="case files">
          <div className="list-header">
            <span>CASE INDEX</span>
            <span>{status === "loading" ? "SYNCING" : "LIVE"}</span>
          </div>

          {status === "error" ? (
            <div className="error-card">
              <strong>CONNECTION FAILED</strong>
              <p>{error}</p>
              <small>Run the demo API and check MONGO_URL / MONGO_DB.</small>
            </div>
          ) : null}

          {posts.map((post, index) => {
            const active = post._id === selectedPost?._id;
            return (
              <button
                className={`case-card ${active ? "active" : ""}`}
                key={post._id}
                onClick={() => setSelectedId(post._id)}
              >
                <span className="case-number">#{String(index + 1).padStart(3, "0")}</span>
                <div className="case-avatar">{getInitials(post.author)}</div>
                <div className="case-copy">
                  <strong>{post.author || "UNKNOWN SUBJECT"}</strong>
                  <p>{post.content || "No transcript available."}</p>
                </div>
                <span className={`tag tag-${classifyPost(post).toLowerCase()}`}>
                  {classifyPost(post)}
                </span>
              </button>
            );
          })}
        </section>

        <section className="file-viewer">
          {selectedPost ? (
            <>
              <div className="file-header">
                <div>
                  <p className="eyebrow">subject dossier</p>
                  <h2>{selectedPost.author || "UNKNOWN SUBJECT"}</h2>
                </div>
                <div className="stamp">REVIEW</div>
              </div>

              <div className="identity-strip">
                <div className="identity-mark">{getInitials(selectedPost.author)}</div>
                <div className="identity-field">
                  <span>AUTHOR // 人物</span>
                  <strong>{selectedPost.author || "UNKNOWN SUBJECT"}</strong>
                </div>
                <div className="identity-field date-field">
                  <span>DATETIME // 建檔時間</span>
                  <strong>{formatDate(selectedPost.datetime)}</strong>
                </div>
              </div>

              <div className="dossier-grid">
                <article className="record-sheet">
                  <header className="sheet-header">
                    <div>
                      <span>CONTENT</span>
                      <strong>情報內文</strong>
                    </div>
                    <small>MONGODB FIELD</small>
                  </header>
                  <div className="content-copy">
                    {(selectedPost.content || "No content captured.")
                      .split(/\r?\n/)
                      .filter((line) => line.trim())
                      .map((line, index) => <p key={`${index}-${line}`}>{line}</p>)}
                  </div>
                </article>

                <aside className="source-monitor">
                  <header className="monitor-header">
                    <div><i /> URL // 原始頁面</div>
                    <span>LIVE SOURCE</span>
                  </header>
                  <div className="matrix-feed">
                    <img src="/the-matrix-21.gif" alt="The Matrix digital rain" />
                    <div className="scanline" />
                    <div className="feed-label">
                      <span>VISUAL PROXY</span>
                      <strong>{selectedPost.url ? "SOURCE LOCKED" : "ARCHIVE MODE"}</strong>
                    </div>
                  </div>
                  <div className="embed-note">
                    <span>{selectedPost.url ? "原始頁面已封存為外部情報來源。" : "此案件沒有 URL 紀錄。"}</span>
                    <a
                      className={selectedPost.url ? "" : "disabled"}
                      href={selectedPost.url || undefined}
                      target="_blank"
                      rel="noreferrer"
                    >OPEN ↗</a>
                  </div>
                </aside>
              </div>

              <div className="mongo-fields">
                <div className="source-field">
                  <span>GROUP_NAME // 來源社團</span>
                  <strong>{selectedPost.group_name || "UNKNOWN CELL"}</strong>
                </div>
                <div className="code-field">
                  <span>POST_KEY</span>
                  <code>{selectedPost.post_key || "NOT CAPTURED"}</code>
                </div>
                <div className="code-field">
                  <span>_ID</span>
                  <code>{selectedPost._id}</code>
                </div>
              </div>

              <div className="evidence-strip">
                <a
                  className={selectedPost.url ? "evidence-link" : "evidence-link disabled"}
                  href={selectedPost.url || undefined}
                  target="_blank"
                  rel="noreferrer"
                >
                  OPEN SOURCE URL
                </a>
                <a
                  className={selectedPost.group_url ? "evidence-link" : "evidence-link disabled"}
                  href={selectedPost.group_url || undefined}
                  target="_blank"
                  rel="noreferrer"
                >
                  OPEN GROUP
                </a>
              </div>
            </>
          ) : (
            <div className="empty-file">
              <h2>NO CASE SELECTED</h2>
              <p>Awaiting MongoDB records.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default App;
