"""
Lumina Tutor: live demo UI for the Algorithmic Instructional Designer Agent
=====================================================================================
Streamlit + custom HTML/CSS/JS. One file. Run:   streamlit run app.py

Backends (chosen automatically, switchable in the sidebar):
  * LIVE  : talks to the JSON bridge that runs inside your Colab/Jupyter session (bridge_cell.py).
            That bridge drives the REAL Step 8 TutorSession through the REAL Step 10 LangGraph (LB_APP)
            and serves the Step 9/10 metrics. Nothing is re-implemented here.
  * DEMO  : a small built-in engine with a sample lesson and the same ladder rules, so the UI also runs
            standalone (for example on a laptop without the notebook). Clearly labelled "Demo data".

HTML/CSS go in through st.markdown(unsafe_allow_html=True). Streamlit strips <script> tags from markdown, so the JavaScript
(auto-scroll, count-up numbers, confetti) is injected through a zero-height components.html iframe that reaches the page via window.parent.
"""
import os, re, json, time, html, uuid, hashlib, random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components

BACKEND_URL = os.environ.get("TUTOR_BACKEND_URL", "http://127.0.0.1:8765")
IST = timezone(timedelta(hours=5, minutes=30))
REVIEW_DAYS = [1, 3, 7, 14, 30]
LADDER = [("1", "Hint", "Nudge, then a new variant"), ("2", "Worked example", "Similar example + half-solved task"), ("3", "Prerequisite check", "One level back in the graph"),
          ("4", "New representation", "Analogy, trace, tiny steps, teach-back"), ("5", "Park & handoff", "A person takes over")]

st.set_page_config(page_title="Lumina Tutor | Adaptive learning", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# =====================================================================================================================
# 1. DESIGN SYSTEM (CSS)
# =====================================================================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--bg:#070910;--glass:rgba(255,255,255,.045);--glass2:rgba(255,255,255,.075);--line:rgba(255,255,255,.09);--txt:#e8ebf4;--mut:#8b93a7;--ac1:#7c83ff;--ac2:#22d3ee;--ok:#34d399;--warn:#fbbf24;--bad:#fb7185;--rad:18px;}
html,body,.stApp{background:var(--bg)!important;color:var(--txt);font-family:'Inter',system-ui,sans-serif;}
.stApp:before{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(60vw 45vh at 12% 8%,rgba(124,131,255,.22),transparent 60%),radial-gradient(50vw 40vh at 92% 12%,rgba(34,211,238,.14),transparent 60%),radial-gradient(55vw 50vh at 60% 100%,rgba(168,85,247,.14),transparent 60%);animation:drift 18s ease-in-out infinite alternate;}
@keyframes drift{from{transform:translate3d(0,0,0) scale(1)}to{transform:translate3d(-2%,2%,0) scale(1.06)}}
header[data-testid="stHeader"]{background:transparent!important;}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
.block-container{padding:1.1rem 2rem 2rem 2rem!important;max-width:1500px!important;position:relative;z-index:1;}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.01em;color:var(--txt)!important;}
::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:8px}
/* top bar */
.topbar{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;margin-bottom:16px;border:1px solid var(--line);border-radius:16px;background:var(--glass);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);}
.brand{display:flex;align-items:center;gap:12px;font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.15rem;}
.logo{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--ac1),var(--ac2));display:grid;place-items:center;box-shadow:0 6px 24px rgba(124,131,255,.45);font-size:18px;}
.brand small{display:block;font-family:'Inter';font-weight:500;color:var(--mut);font-size:.72rem;letter-spacing:.02em;margin-top:1px;}
.pill{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border-radius:999px;border:1px solid var(--line);background:var(--glass);font-size:.74rem;color:var(--mut);margin-left:8px;}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 0 rgba(52,211,153,.6);animation:pulse 2s infinite;}
.dot.demo{background:var(--warn);box-shadow:0 0 0 0 rgba(251,191,36,.6);}
@keyframes pulse{70%{box-shadow:0 0 0 8px rgba(52,211,153,0)}100%{box-shadow:0 0 0 0 rgba(52,211,153,0)}}
/* glass cards */
.card{border:1px solid var(--line);border-radius:var(--rad);padding:16px 18px;background:linear-gradient(180deg,var(--glass2),var(--glass));backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);box-shadow:0 10px 40px rgba(0,0,0,.35);margin-bottom:14px;animation:rise .5s ease both;}
.card h4{margin:0 0 12px 0;font-size:.78rem!important;font-weight:600;color:var(--mut)!important;text-transform:uppercase;letter-spacing:.09em;display:flex;align-items:center;gap:8px;}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.grid{display:grid;gap:12px;}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}
.kpi{border:1px solid var(--line);border-radius:14px;padding:12px 14px;background:rgba(255,255,255,.03);}
.kpi .v{font-family:'Space Grotesk','Inter',system-ui,sans-serif;font-size:1.55rem;font-weight:700;line-height:1.1}.kpi .l{color:var(--mut);font-size:.72rem;margin-top:4px}.kpi .s{font-size:.7rem;color:var(--mut);opacity:.8}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.mut{color:var(--mut)}
.gtext{background:linear-gradient(90deg,var(--ac1),var(--ac2));-webkit-background-clip:text;background-clip:text;color:transparent;}
/* chat */
.chat-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.chat-head .t{font-family:'Space Grotesk','Inter',system-ui,sans-serif;font-weight:600;font-size:1.05rem}.chat-head .s{color:var(--mut);font-size:.78rem;margin-top:2px}
.chat-scroll{height:min(52vh,560px);overflow-y:auto;padding:10px 12px;border:1px solid var(--line);border-radius:var(--rad);background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.02));margin-bottom:12px;scroll-behavior:smooth;}
.msg{display:flex;gap:10px;margin:12px 0;animation:rise .35s ease both;}
.msg.student{flex-direction:row-reverse}
.av{flex:0 0 34px;height:34px;border-radius:11px;display:grid;place-items:center;font-size:16px;border:1px solid var(--line);}
.msg.tutor .av{background:linear-gradient(135deg,rgba(124,131,255,.35),rgba(34,211,238,.25));}
.msg.student .av{background:rgba(255,255,255,.07)}
.bub{max-width:82%;padding:12px 15px;border-radius:16px;font-size:.92rem;line-height:1.55;border:1px solid var(--line);}
.msg.tutor .bub{background:var(--glass2);border-top-left-radius:5px;}
.msg.student .bub{background:linear-gradient(135deg,rgba(124,131,255,.55),rgba(34,211,238,.4));border-color:rgba(255,255,255,.18);border-top-right-radius:5px;color:#fff;}
.bub .who{font-size:.68rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin-bottom:5px}
.msg.student .bub .who{color:rgba(255,255,255,.75)}
.bub p{margin:0 0 7px 0}.bub p:last-child{margin-bottom:0}
.bub pre{margin:8px 0;padding:10px 12px;border-radius:12px;background:rgba(0,0,0,.45);border:1px solid var(--line);overflow-x:auto;font-family:'JetBrains Mono',monospace;font-size:.8rem;color:#c7d2fe;white-space:pre-wrap;}
.bub code{font-family:'JetBrains Mono',monospace;font-size:.82rem;background:rgba(0,0,0,.35);padding:1px 6px;border-radius:6px}
.opt{display:flex;gap:10px;align-items:flex-start;padding:7px 10px;margin:5px 0;border:1px solid var(--line);border-radius:10px;background:rgba(255,255,255,.03);font-family:'JetBrains Mono',monospace;font-size:.8rem}
.opt b{color:var(--ac2);min-width:16px}
.sys{display:flex;justify-content:center;margin:14px 0;animation:rise .35s ease both}
.chip{display:inline-flex;align-items:center;gap:7px;padding:5px 12px;border-radius:999px;font-size:.74rem;border:1px solid var(--line);background:var(--glass);color:var(--mut)}
.chip.ok{color:var(--ok);border-color:rgba(52,211,153,.35);background:rgba(52,211,153,.08)}
.chip.warn{color:var(--warn);border-color:rgba(251,191,36,.35);background:rgba(251,191,36,.08)}
.chip.bad{color:var(--bad);border-color:rgba(251,113,133,.35);background:rgba(251,113,133,.08)}
.chip.ac{color:#c7d2fe;border-color:rgba(124,131,255,.4);background:rgba(124,131,255,.1)}
.tcard{margin-top:9px;padding:11px 13px;border-radius:12px;border:1px solid rgba(124,131,255,.3);background:rgba(124,131,255,.08);font-size:.86rem}
.tcard .tt{font-weight:600;font-size:.76rem;letter-spacing:.06em;text-transform:uppercase;color:#c7d2fe;margin-bottom:6px}
.tcard ol,.tcard ul{margin:4px 0 4px 18px;padding:0}
.typing{display:inline-flex;gap:4px}.typing i{width:6px;height:6px;border-radius:50%;background:var(--mut);animation:blink 1.2s infinite}.typing i:nth-child(2){animation-delay:.2s}.typing i:nth-child(3){animation-delay:.4s}
@keyframes blink{0%,80%,100%{opacity:.25}40%{opacity:1}}
/* ladder */
.ladder{display:flex;align-items:flex-start;gap:0;margin:6px 0 4px}
.step{flex:1;text-align:center;position:relative}
.step:not(:last-child):after{content:'';position:absolute;top:15px;left:50%;width:100%;height:2px;background:var(--line);z-index:0}
.step.done:not(:last-child):after{background:linear-gradient(90deg,var(--ac1),var(--ac2))}
.node{position:relative;z-index:1;width:32px;height:32px;margin:0 auto;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:.8rem;background:#10131d;border:2px solid var(--line);color:var(--mut);transition:all .4s}
.step.done .node{border-color:var(--ac1);color:#fff;background:linear-gradient(135deg,var(--ac1),var(--ac2));}
.step.now .node{box-shadow:0 0 0 6px rgba(124,131,255,.18),0 0 24px rgba(34,211,238,.55);animation:glow 1.8s infinite alternate}
.step.danger.now .node,.step.danger.done .node{background:linear-gradient(135deg,#fb7185,#f43f5e);border-color:#fb7185;box-shadow:0 0 0 6px rgba(251,113,133,.18),0 0 24px rgba(251,113,133,.5)}
@keyframes glow{to{transform:scale(1.12)}}
.step .lb{font-size:.66rem;margin-top:8px;color:var(--mut);line-height:1.25}.step.now .lb{color:var(--txt);font-weight:600}
/* progress, ring, bars */
.ring{--p:0;width:92px;height:92px;border-radius:50%;background:conic-gradient(var(--ok) calc(var(--p)*1%),rgba(255,255,255,.08) 0);display:grid;place-items:center;transition:all .6s}
.ring>div{width:72px;height:72px;border-radius:50%;background:#0c0f18;display:grid;place-items:center;font-family:'Space Grotesk','Inter',system-ui,sans-serif;font-weight:700;font-size:1.1rem}
.exrow{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--line);font-size:.84rem}.exrow:last-child{border:0}
.exrow .nm{flex:1}.exrow .pt{color:var(--mut);font-size:.72rem}
.pips{display:flex;gap:5px}.pip{width:22px;height:8px;border-radius:5px;background:rgba(255,255,255,.1)}.pip.on{background:linear-gradient(90deg,var(--ok),#6ee7b7)}.pip.fail{background:var(--bad)}
.bar{height:8px;border-radius:6px;background:rgba(255,255,255,.08);overflow:hidden}.bar>i{display:block;height:100%;border-radius:6px;background:linear-gradient(90deg,var(--ac1),var(--ac2));transition:width .8s}
.mood{display:flex;flex-wrap:wrap;gap:8px}
.big{font-family:'Space Grotesk','Inter',system-ui,sans-serif;font-size:1.35rem;font-weight:700}
.hand{border-radius:14px;padding:13px 15px;border:1px solid var(--line)}
.hand.ok{background:rgba(52,211,153,.08);border-color:rgba(52,211,153,.3)}.hand.warn{background:rgba(251,191,36,.08);border-color:rgba(251,191,36,.3)}.hand.bad{background:rgba(251,113,133,.1);border-color:rgba(251,113,133,.4)}
.tl{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.tl .d{padding:4px 9px;border-radius:8px;border:1px dashed var(--line);font-size:.72rem;color:var(--mut)}
table.t{width:100%;border-collapse:collapse;font-size:.78rem}table.t td,table.t th{padding:7px 6px;border-bottom:1px solid var(--line);text-align:left}table.t th{color:var(--mut);font-weight:500}
.mono{font-family:'JetBrains Mono',monospace;font-size:.74rem}
/* streamlit widgets */
div[data-testid="stForm"]{border:1px solid var(--line)!important;border-radius:16px!important;background:var(--glass)!important;backdrop-filter:blur(16px);padding:12px 14px!important;}
.stTextInput input,.stTextArea textarea{background:rgba(0,0,0,.35)!important;border:1px solid var(--line)!important;border-radius:12px!important;color:var(--txt)!important;font-family:'JetBrains Mono',monospace!important;font-size:.88rem!important;}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:var(--ac1)!important;box-shadow:0 0 0 3px rgba(124,131,255,.25)!important;}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,[data-testid^='stBaseButton']{color:var(--txt)!important;border-radius:12px!important;border:1px solid var(--line)!important;background:var(--glass2)!important;color:var(--txt)!important;font-weight:600!important;transition:all .2s!important;}
.stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover,[data-testid^='stBaseButton']:hover{transform:translateY(-1px);border-color:rgba(124,131,255,.6)!important;box-shadow:0 8px 24px rgba(124,131,255,.25);}
.stFormSubmitButton>button,[data-testid='stBaseButton-secondaryFormSubmit']{background:linear-gradient(135deg,var(--ac1),#5b63f5)!important;border:0!important;color:#fff!important;}
.stRadio label,.stRadio p{color:var(--txt)!important}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{background:transparent;color:var(--mut);border-radius:10px 10px 0 0;padding:8px 14px;font-weight:600}
.stTabs [aria-selected="true"]{color:#fff!important;background:var(--glass)!important}
.stTabs [data-baseweb="tab-highlight"]{background:linear-gradient(90deg,var(--ac1),var(--ac2))!important}
[data-testid="stSidebar"]{background:#0a0d15!important;border-right:1px solid var(--line)}
#sb-toggle{position:fixed;top:40px;left:4px;width:28px;height:28px;padding:0;border-radius:9px;border:1px solid var(--line);background:var(--glass2);color:var(--txt);font:700 .7rem 'JetBrains Mono',monospace;cursor:pointer;z-index:10000;display:grid;place-items:center;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);transition:left .25s,box-shadow .2s,border-color .2s;}
#sb-toggle:hover{border-color:rgba(124,131,255,.6);box-shadow:0 6px 18px rgba(124,131,255,.3);}
.stAlert{border-radius:14px!important}
@media (max-width:900px){.block-container{padding:.8rem!important}.g3{grid-template-columns:1fr 1fr}.bub{max-width:92%}}
</style>
"""


def H(s: str):
    """Render HTML through st.markdown. Newlines+indent are removed so Markdown never treats the HTML as a code block."""
    st.markdown(re.sub(r"\n\s*", "", s.strip()), unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def pre(code: str) -> str:
    return "<pre>" + esc(code).replace("\n", "&#10;") + "</pre>"


# =====================================================================================================================
# 2. BACKENDS
# =====================================================================================================================
class BackendError(Exception):
    pass


class LiveBackend:
    """HTTP client of bridge_cell.py: the real Step 8 engine inside the real Step 10 LangGraph."""
    mode = "live"
    label = "Live engine · LangGraph + Step 8 tutor"

    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self.oracle_ok = False

    def _call(self, method: str, path: str, body: Optional[dict] = None, timeout: float = 60):
        import urllib.request, urllib.error
        req = urllib.request.Request(self.url + path, method=method, data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise BackendError(json.loads(e.read() or b"{}").get("error", str(e)))
        except Exception as e:
            raise BackendError(str(e))

    def health(self) -> dict:
        h = self._call("GET", "/health", timeout=2.5)
        self.oracle_ok = bool(h.get("oracle"))
        return h

    def start(self, learner: str) -> dict: return self._call("POST", "/start", {"learner": learner})
    def reply(self, tid: str, reply: dict) -> dict: return self._call("POST", "/reply", {"thread_id": tid, "reply": reply})
    def oracle(self, tid: str) -> dict: return self._call("GET", f"/oracle?thread_id={tid}")
    def metrics(self) -> dict: return self._call("GET", "/metrics")
    def packet_md(self, tid: str) -> Optional[str]: return self._call("GET", f"/packet?thread_id={tid}").get("markdown")


# ---------- DEMO engine: same rules as the real ladder, small sample lesson (clearly labelled demo data) ----------
def _opts(*o): return "\n".join(f"{L}) {t}" for L, t in zip("ABCD", o))

DEMO = {
    "id": "L01", "title": "Fetch a web page with Python requests",
    "objective": "By the end of this lesson you can fetch a web page and read its status code.",
    "problem": "Mario's Pizza has its menu on a web page. How would you grab that page from Python in one line?",
    "pretest": [
        {"id": "L01-R1", "concept": "c_import", "prompt": "Which line makes the requests library available in your script?", "options": {"A": "include requests", "B": "import requests", "C": "load requests", "D": "use requests"}, "correct": "B", "tags": {"A": "m_c_style_include", "C": "m_load", "D": "m_use"}},
        {"id": "L01-R2", "concept": "c_url", "prompt": "What does a URL identify?", "options": {"A": "A Python variable", "B": "A file on your laptop", "C": "The address of a web page", "D": "A password"}, "correct": "C", "tags": {"A": "m_url_var", "B": "m_url_file", "D": "m_url_pwd"}},
        {"id": "L01-R3", "concept": "c_variable", "prompt": "In r = f(x), what is r?", "options": {"A": "A function", "B": "A variable holding the result", "C": "A loop", "D": "An error"}, "correct": "B", "tags": {"A": "m_r_func", "C": "m_r_loop", "D": "m_r_err"}},
    ],
    "exercises": [
        {"id": "L01-E1", "part": "guided_practice", "type": "choice", "concept": "c_get_call", "hints": ["Think about the HTTP verb for reading a page.", "The function has the same name as that verb: three letters.", "It starts with g and ends with t."],
         "worked": "To read news_url and keep it in page we write: page = requests.get(news_url)", "completion": "Complete: r = requests.____(menu_url)",
         "variants": [("V1", "Mario's Pizza menu lives at menu_url. Which line downloads it?\n" + _opts("r = requests.fetch(menu_url)", "r = requests.get(menu_url)", "r = requests.open(menu_url)", "r = requests.read(menu_url)"), "B"),
                      ("V2", "Luigi's Pasta page is at pasta_url. Which line downloads it?\n" + _opts("r = requests.get(pasta_url)", "r = requests.pull(pasta_url)", "r = requests.load(pasta_url)", "r = requests.grab(pasta_url)"), "A"),
                      ("V3", "Sushi Zen's page is at sushi_url. Which line downloads it?\n" + _opts("r = requests.take(sushi_url)", "r = requests.fetch(sushi_url)", "r = requests.read(sushi_url)", "r = requests.get(sushi_url)"), "D"),
                      ("V4", "Taco Loco's page is at taco_url. Which line downloads it?\n" + _opts("r = requests.pull(taco_url)", "r = requests.open(taco_url)", "r = requests.get(taco_url)", "r = requests.load(taco_url)"), "C")]},
        {"id": "L01-E2", "part": "guided_practice", "type": "code_line", "concept": "c_get_call", "hints": ["You need the requests module and one function call.", "Store the result in r using =.", "r = requests.g..(menu_url)"],
         "worked": "To read news_url into page: page = requests.get(news_url)", "completion": "Complete: r = requests.____(menu_url)",
         "variants": [("V1", "Write ONE line that downloads menu_url and stores the response in r.", "r = requests.get(menu_url)"), ("V2", "Write ONE line that downloads pasta_url and stores the response in r.", "r = requests.get(pasta_url)"),
                      ("V3", "Write ONE line that downloads sushi_url and stores the response in r.", "r = requests.get(sushi_url)"), ("V4", "Write ONE line that downloads taco_url and stores the response in r.", "r = requests.get(taco_url)")]},
        {"id": "L01-E3", "part": "free_practice", "type": "short_text", "concept": "c_status", "hints": ["The response object r has attributes.", "One attribute holds the number like 200 or 404.", "It is two words joined by an underscore."],
         "worked": "For a response resp, resp.ok tells if the request worked. Another attribute holds the number.", "completion": "Complete: print(r.____)",
         "variants": [("V1", "After r = requests.get(menu_url), which attribute of r holds the numeric HTTP status, such as 200?", "status_code"), ("V2", "After x = requests.get(pasta_url), which attribute of x holds the number 200 or 404?", "status_code"),
                      ("V3", "Which attribute of a response holds its HTTP status number?", "status_code"), ("V4", "Name the response attribute that tells you 200 or 404.", "status_code")]},
        {"id": "L01-E4", "part": "assessment", "type": "code_line", "concept": "c_status", "hints": ["Use the response r.", "Use the attribute you just learned.", "code = r.s..."],
         "worked": "Similar: n = resp.status_code stores the number in n.", "completion": "Complete: code = r.____",
         "variants": [("V1", "Write ONE line that stores the numeric status of response r in code.", "code = r.status_code"), ("V2", "Write ONE line that stores the numeric status of response page in num.", "num = page.status_code"),
                      ("V3", "Write ONE line that stores the numeric status of response resp in s.", "s = resp.status_code"), ("V4", "Write ONE line that stores the numeric status of response answer in value.", "value = answer.status_code")]},
    ],
}
DEMO_PREREQ = {"c_get_call": ["c_import", "c_url"], "c_status": ["c_get_call"]}


def _norm(s: str) -> str:
    s = str(s).strip().strip("`").strip().rstrip(";").replace('"', "'").lower()
    return re.sub(r"\s*([=(),.])\s*", r"\1", re.sub(r"\s+", " ", s))


class DemoEngine:
    mode = "demo"
    label = "Demo engine · built-in sample lesson"
    oracle_ok = True

    def __init__(self):
        self.S: Dict[str, dict] = {}

    def health(self): return {"ok": True, "engine": "demo"}

    # ---- helpers ----
    def _ex(self, eid): return next(e for e in DEMO["exercises"] if e["id"] == eid)

    def _variant(self, st, e):
        used = [a["variant"] for a in st["attempts"]]
        cands = [v for v in [x[0] for x in e["variants"]] if v not in st["streak_variants"]] or [x[0] for x in e["variants"]]
        return sorted(cands, key=lambda v: (used.count(v), v))[0]

    def _present(self, s):
        for e in DEMO["exercises"]:
            st = s["ex"][e["id"]]
            blocked = any(DEMO_PREREQ.get(e["concept"]) and False for _ in [0]) or any(self._ex(p)["concept"] == e["concept"] for p in s["parked"])
            if not st["mastered"] and e["id"] not in s["parked"] and not blocked:
                v = self._variant(st, e); q = next(x for x in e["variants"] if x[0] == v)
                s["cur"] = e["id"]; s["pending"] = {"kind": "exercise", "exercise_id": e["id"], "variant": v, "prompt": q[1], "answer_type": e["type"], "hints": e["hints"],
                                                    "index": DEMO["exercises"].index(e) + 1, "total": len(DEMO["exercises"]), "part": e["part"]}
                s["wait"] = "exercise"; return
        s["pending"], s["wait"], s["done"] = {}, "done", True
        now = datetime.now(IST)
        for e in DEMO["exercises"]:
            if s["ex"][e["id"]]["mastered"]:
                s["reviews"].append({"exercise_id": e["id"], "kind": "post_mastery", "interval_days": 1, "due_at": (now + timedelta(days=1)).replace(hour=10, minute=0).isoformat()})
        s["summary"] = {"mastered": [e for e in s["ex"] if s["ex"][e]["mastered"]], "parked": s["parked"]}

    def _log(self, s, **kw):
        s["seq"] += 1; s["events"].append({"seq": s["seq"], **kw})

    def start(self, learner: str) -> dict:
        tid = "demo-" + uuid.uuid4().hex[:8]
        s = {"learner": learner, "ex": {e["id"]: {"fails": 0, "attempts": [], "sigs": {}, "streak_variants": [], "mastered": False, "level": 0, "teach": False, "diag": 0} for e in DEMO["exercises"]},
             "events": [], "seq": 0, "mood": [], "route": None, "parked": [], "packets": [], "reviews": [], "trace": ["start"], "done": False, "outcome": None, "diagnostic": None,
             "wait": "pretest", "pending": {"kind": "pretest", "questions": [{"id": q["id"], "prompt": q["prompt"], "options": q["options"]} for q in DEMO["pretest"]]}, "cur": None,
             "session_fails": 0, "first_try": 0, "summary": None, "oseq": 0, "handoff": {}}
        self.S[tid] = s
        return self.view(tid)

    def oracle(self, tid):
        s = self.S[tid]; p = s["pending"]
        if p.get("kind") == "exercise":
            e = self._ex(p["exercise_id"]); q = next(x for x in e["variants"] if x[0] == p["variant"])
            wrong = {"choice": next(L for L in "ABCD" if L != q[2]), "short_text": "status", "code_line": "r = requests.fetch(menu_url)"}[e["type"]]
            return {"kind": "exercise", "correct": q[2], "wrong": wrong}
        pool = {q["id"]: q for q in DEMO["pretest"]}
        ids = [x["id"] for x in p.get("questions", [])]
        return {"kind": p.get("kind", "none"), "correct": {i: pool[i]["correct"] for i in ids}, "wrong": {i: next(L for L in "ABCD" if L != pool[i]["correct"]) for i in ids}}

    def reply(self, tid: str, rep: dict) -> dict:
        s = self.S[tid]; p = s["pending"]; kind = p.get("kind")
        if kind == "pretest":
            wrong = [q for q in DEMO["pretest"] if str(rep["answers"].get(q["id"], "")).strip().upper()[:1] != q["correct"]]
            concepts = sorted({q["concept"] for q in wrong})
            route = "skip_recall" if not wrong else "stop_suggest_previous" if len(wrong) == 3 else "bridge" if len(concepts) == 1 else "remedial_first"
            s["route"] = {"route": route, "weak_concepts": concepts, "learner_text": {"skip_recall": "You already know what you need. Let's start the lesson.", "bridge": "Good start! One small idea needs a quick refresher (3-4 minutes).",
                                                                                      "remedial_first": "Let's strengthen a couple of earlier ideas first.", "stop_suggest_previous": "These basics look new, and that is fine. Let's build the foundation first."}[route]}
            self._log(s, type="pretest", route=route); s["trace"].append("handle:pretest")
            if route == "stop_suggest_previous":
                s["done"], s["wait"], s["pending"] = True, "done", {}; s["summary"] = {"route": route}
            else:
                self._present(s)
            return self.view(tid)
        eid = p["exercise_id"]; st = s["ex"][eid]; e = self._ex(eid)
        if kind == "diagnostic":
            pool = {q["id"]: q for q in DEMO["pretest"]}
            gaps = sorted({pool[i]["concept"] for i, a in rep["answers"].items() if str(a).strip().upper()[:1] != pool[i]["correct"]})
            s["diagnostic"] = {"gap": bool(gaps), "gap_concepts": gaps, "bridges": [f"B_{g}_3min" for g in gaps], "external": [],
                               "learner_text": "Found it: one earlier idea is shaky. Here's a 3-4 minute refresher, then we come back." if gaps else "Your basics are solid, so the issue is in this step. Let's try it a different way.", "seq": s["seq"] + 1}
            self._log(s, type="diagnostic", exercise=eid); s["trace"].append("handle:diagnostic_done"); self._present(s); return self.view(tid)
        # ---- exercise answer ----
        v = p["variant"]; q = next(x for x in e["variants"] if x[0] == v); ans = str(rep.get("answer", "")).strip()
        if rep.get("quit"):
            s["done"], s["wait"], s["pending"] = True, "done", {}; s["trace"].append("handle:quit"); return self.view(tid)
        if e["type"] == "choice":
            ok = ans.upper()[:1] == q[2]
            opts = {m.group(1): m.group(2) for m in re.finditer(r"^([A-D])\) (.+)$", q[1], re.M)}
            sig = None if ok else "m_" + (re.search(r"requests\.(\w+)", opts.get(ans.upper()[:1], "") or "") or [None, "unknown_option"])[1]
        else:
            ok = _norm(ans) == _norm(q[2]); sig = None if ok else ("m_" + re.sub(r"\W+", "_", _norm(ans))[:18]) if ans else "u_empty"
        t = float(rep.get("time_sec", 30)); hints = min(int(rep.get("hints", 0)), 3)
        rote = False
        if ok and st["teach"]:
            terms = ["status", "code", "get", "response", "request", "url", "page", "attribute"]
            rote = len(str(rep.get("explanation", "")).split()) < 6 or sum(t_ in str(rep.get("explanation", "")).lower() for t_ in terms) < 2
            if not rote: st["teach"] = False
        s["oseq"] += 1
        if rote:
            s["outcome"] = {"exercise_id": eid, "variant": v, "result": "pass_but_rote", "mastered": False, "handoff": False, "signals": ["rote_answer"], "action": None, "mood_flags": s["mood"], "seq": s["oseq"],
                            "message": "Right answer! Before we move on, explain in your own words why it works. We'll try one more variant."}
            self._log(s, type="attempt", exercise=eid, variant=v, result="pass_but_rote"); self._present(s); return self.view(tid)
        st["attempts"].append({"variant": v, "result": "pass" if ok else "fail", "signature": sig, "hints": hints, "time": t})
        if ok:
            if not st["streak_variants"].__contains__(v): st["streak_variants"].append(v)
            if len(st["attempts"]) == 1: s["first_try"] += 1
            st["mastered"] = len(st["streak_variants"]) >= 2
            s["outcome"] = {"exercise_id": eid, "variant": v, "result": "pass", "mastered": st["mastered"], "handoff": False, "signals": [], "action": None, "mood_flags": s["mood"], "seq": s["oseq"],
                            "message": ("Nice, that's right!" if len(st["attempts"]) == 1 else "Right! Well done.") + (" You've mastered this one." if st["mastered"] else " One more variant to confirm it.")}
            if s["first_try"] >= 3 and "confident" not in s["mood"]: s["mood"].append("confident")
            self._log(s, type="attempt", exercise=eid, variant=v, result="pass", level=st["level"]); s["trace"].append("handle:mastered" if st["mastered"] else "handle:retry"); self._present(s); return self.view(tid)
        # ---- failure ----
        st["fails"] += 1; s["session_fails"] += 1; st["streak_variants"] = []; st["sigs"][sig] = st["sigs"].get(sig, 0) + 1
        fails = [a for a in st["attempts"] if a["result"] == "fail"]; sigs = [a["signature"] for a in fails]
        sg = []
        if len(fails) >= 2: sg.append("same_mistake" if len(set(sigs)) == 1 else "different_mistakes")
        if t < 8: sg.append("fast_wrong")
        if t > 120: sg.append("slow_wrong")
        if sum(a["hints"] for a in st["attempts"][-3:]) / len(st["attempts"][-3:]) >= 1.5 and len(st["attempts"]) >= 2: sg.append("hint_dependent")
        level, shortcut = min(st["fails"], 5), False
        if level == 2 and any(c >= 2 for c in st["sigs"].values()): level, shortcut = 3, True
        st["level"] = level
        pre_ = []
        if "same_mistake" in sg: pre_.append(f"You may be thinking that `{ans[:60]}` works here, but check it against the lesson again: this exact answer came up twice.")
        if "fast_wrong" in sg: pre_.append("Let's slow down: re-read the explanation piece first, then try again.")
        if "hint_dependent" in sg: pre_.append("Let's fade the hints: this time try the half-solved version first.")
        kinds = {1: "hint_then_variant", 2: "worked_example_completion", 3: "backward_diagnostic", 4: "change_representation", 5: "park_and_handoff"}
        soft = {1: "Not quite. That's a very common slip. Here's a small nudge.", 2: "Let's look at a similar example together, then you finish a half-solved one.",
                3: "Let's take one step back and check the idea underneath this. It's often the real reason things feel hard.",
                4: "Let's look at it a different way. We'll go in tiny steps, and then you can explain it back in your own words.",
                5: "You've worked really hard on this. Pushing harder won't help right now, so I'm saving your progress and asking a person to help you."}
        payload = {1: {"hint": e["hints"][0], "next": "new_variant"}, 2: {"worked_example": e["worked"], "completion_problem": e["completion"]}, 3: {}, 4: {"minimal_steps": e["hints"], "trace": e["worked"], "analogy": "Think of a waiter: you give the exact order (the URL) and the kitchen hands back a tray (the response). The tray has a receipt with a number on it (the status).", "teach_back": "In your own words: what does the correct line do, and why does it work?"}, 5: {}}[level]
        if level == 3:
            qs = DEMO["pretest"][:2] if st["diag"] % 2 == 0 else DEMO["pretest"][1:]; st["diag"] += 1
            payload = {"prerequisite_concepts": DEMO_PREREQ.get(e["concept"], []), "questions": [{"id": x["id"], "prompt": x["prompt"], "options": x["options"]} for x in qs], "question_ids": [x["id"] for x in qs]}
        if level == 4: st["teach"] = True
        if s["session_fails"] >= 6 or st["fails"] >= 4:
            for m in ("needs_break",):
                if m not in s["mood"]: s["mood"].append(m)
        if st["fails"] >= 3 and "frustrated" not in s["mood"]: s["mood"].append("frustrated")
        if sum(1 for a in fails if a["time"] < 8) >= 2 and "rushed_guessing" not in s["mood"]: s["mood"].append("rushed_guessing")
        handoff = level == 5
        msg = " ".join(pre_ + [soft[level]]) + (" A 5-minute break is a great idea. Your progress is saved." if "needs_break" in s["mood"] and not handoff else "")
        s["outcome"] = {"exercise_id": eid, "variant": v, "result": "fail", "error_signature": sig, "mastered": False, "handoff": handoff, "signals": sg, "mood_flags": s["mood"], "seq": s["oseq"], "message": msg,
                        "action": {"kind": kinds[level], "level": level, "learner_text": soft[level], "payload": payload, "prefix": pre_, "shortcut": shortcut}}
        self._log(s, type="attempt", exercise=eid, variant=v, result="fail", signature=sig, level=level, action=kinds[level], signals=sg, fail_count=st["fails"])
        if handoff:
            s["parked"].append(eid); s["handoff"][eid] = {}; now = datetime.now(IST)
            rev = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            s["packets"].append({"recipient": "teacher", "learner_ref": "L-" + hashlib.sha256(s["learner"].encode()).hexdigest()[:10], "lesson_id": "L01", "exercise_id": eid, "stuck_concept": e["concept"], "stuck_concept_name": e["concept"].replace("c_", "").replace("_", " ").title(),
                                 "attempts": [{"n": i + 1, **a} for i, a in enumerate(st["attempts"])], "error_pattern": st["sigs"], "signals_seen": sorted({x for ev in s["events"] for x in (ev.get("signals") or [])}),
                                 "treatments_tried": [ev["action"] for ev in s["events"] if ev.get("action")], "hints_shown": sum(a["hints"] for a in st["attempts"]), "representation_changed": True, "mood_flags": s["mood"],
                                 "diagnosis": ["Repeated misconception: same wrong answer several times" if any(c >= 2 for c in st["sigs"].values()) else "A different mistake every time: weak foundation or overload"],
                                 "suggested_next_step": ["Talk the idea through with one concrete counter-example.", "The learner continues with the parts that do not depend on this concept.", f"A revisit is scheduled for {rev.strftime('%Y-%m-%d %H:%M %z')}."],
                                 "open_parts": [x["id"] for x in DEMO["exercises"] if x["concept"] != e["concept"]], "revisit_at": rev.isoformat()})
            s["reviews"].append({"exercise_id": eid, "kind": "after_park", "interval_days": 1, "due_at": rev.isoformat()}); s["trace"].append("handle:fail5"); s["trace"].append("park"); self._present(s)
        elif level == 3:
            s["pending"] = {"kind": "diagnostic", "exercise_id": eid, "question_ids": payload["question_ids"], "questions": payload["questions"]}; s["wait"] = "diagnostic"; s["trace"].append("handle:diagnostic_needed")
        else:
            s["trace"].append("handle:retry"); self._present(s)
        return self.view(tid)

    def metrics(self) -> dict:
        return {"lesson": {"id": "L01", "title": DEMO["title"]}, "demo": True, "cohort_n": 60,
                "quality": {"pass_rate_per_round": [[1, 0.75], [2, 0.88]], "rounds_to_publish": 2, "hallucination_rate": 0.0, "claims": 14, "pacing_lint_pass": True, "baseline_pass_rate": 0.31, "lift": 0.57},
                "outcomes": {"first_attempt_pass_rate": 0.62, "mastery_within_3": 0.81, "time_to_mastery_sec": 412, "hints_per_attempt": 0.44, "handoff_rate": 0.07, "transfer_score": 0.74, "retention_7d": None},
                "health": {"sim_vs_human": {"pearson": None}, "ladder": [{"level": 1, "treatment": "hint_then_variant", "cases": 38, "unstuck_rate": 0.66}, {"level": 2, "treatment": "worked_example_completion", "cases": 17, "unstuck_rate": 0.59},
                                                                         {"level": 3, "treatment": "backward_diagnostic", "cases": 9, "unstuck_rate": 0.44}, {"level": 4, "treatment": "change_representation", "cases": 5, "unstuck_rate": 0.4}]},
                "gate": {"verdict": "PUBLISH", "checks": [{"check": "Loop A pass rate >= 80%", "ok": True, "hard": True}, {"check": "Pacing lint: no errors", "ok": True, "hard": True}, {"check": "Hallucination rate = 0", "ok": True, "hard": True},
                                                          {"check": "No exercise reveals its own answer", "ok": True, "hard": True}, {"check": "Contamination warning", "ok": False, "hard": False}]},
                "flags": [{"exercise_id": "L01-E3", "learners": 60, "failed_twice": 12, "share": 0.2, "flagged": False}]}

    def packet_md(self, tid):
        s = self.S[tid]
        return packet_markdown(s["packets"][-1]) if s["packets"] else None

    def view(self, tid: str) -> dict:
        s = self.S[tid]
        exs = []
        for e in DEMO["exercises"]:
            st = s["ex"][e["id"]]
            exs.append({"id": e["id"], "part": e["part"], "answer_type": e["type"], "concept": e["concept"], "fail_count": st["fails"], "ladder_level": st["level"], "streak": len(st["streak_variants"]), "mastered": st["mastered"],
                        "signatures": st["sigs"], "attempts": [{"variant": a["variant"], "result": a["result"], "signature": a["signature"], "hints": a["hints"], "time": a["time"]} for a in st["attempts"]]})
        att = [e for e in s["events"] if e["type"] == "attempt"]
        return {"thread_id": tid, "learner_id": s["learner"], "mode": "demo", "lesson": {"id": "L01", "title": DEMO["title"], "objective": DEMO["objective"], "problem": DEMO["problem"]},
                "waiting": s["wait"], "pending": s["pending"], "current_ex": s["cur"] or (s["pending"] or {}).get("exercise_id"), "exercises": exs, "mood": s["mood"], "route": s["route"],
                "signals": att[-1].get("signals", []) if att else [], "parked": s["parked"], "packets": s["packets"], "reviews": s["reviews"], "outcome": s["outcome"], "diagnostic": s["diagnostic"],
                "teach_back_pending": bool(s["cur"] and s["ex"][s["cur"]]["teach"]), "events": s["events"][-40:], "trace": s["trace"][-40:], "done": s["done"], "left": False, "summary": s["summary"],
                "session_fails": s["session_fails"], "handoff": s["handoff"], "reviews_projected_days": REVIEW_DAYS}


def packet_markdown(p: dict) -> str:
    L = [f"# Handoff packet for the {p.get('recipient', 'teacher')}", "", f"**Learner:** `{p['learner_ref']}` | **Lesson:** {p['lesson_id']} | **Exercise:** {p['exercise_id']}", f"**Stuck on:** {p['stuck_concept_name']} (`{p['stuck_concept']}`)", "",
         "## What the system thinks"] + [f"- {d}" for d in p["diagnosis"]] + ["", "## Suggested next step"] + [f"- {x}" for x in p["suggested_next_step"]]
    L += ["", "## What was already tried", f"- Treatments in order: {' -> '.join(p['treatments_tried']) or 'none'}", f"- Hints shown in total: {p['hints_shown']}", "", "## Error pattern"] + [f"- `{k}`: {v}x" for k, v in p["error_pattern"].items()]
    L += ["", "## All attempts", "| # | variant | result | error | hints | seconds |", "|---|---|---|---|---|---|"] + [f"| {a['n']} | {a['variant']} | {a['result']} | {a.get('signature') or a.get('error_signature') or ''} | {a.get('hints', a.get('hints_used', 0))} | {a.get('time', a.get('time_sec', 0)):.0f} |" for a in p["attempts"]]
    return "\n".join(L)


# =====================================================================================================================
# 3. STATE
# =====================================================================================================================
ss = st.session_state
for k, v in {"messages": [], "view": None, "backend": None, "mode": "Auto", "hints_shown": 0, "t_present": time.time(), "last_outcome": 0, "last_diag": 0, "last_present": None, "celebrate": 0, "error": None,
             "learner": "Student", "demo_engine": None, "metrics": None}.items():
    ss.setdefault(k, v)


def pick_backend():
    """Auto: live bridge if reachable, else the built-in demo engine."""
    if ss.mode in ("Auto", "Live"):
        try:
            b = LiveBackend(BACKEND_URL); b.health(); return b
        except BackendError:
            if ss.mode == "Live":
                raise
    if ss.demo_engine is None:
        ss.demo_engine = DemoEngine()
    return ss.demo_engine


def add(role: str, blocks: List[dict]):
    ss.messages.append({"role": role, "blocks": blocks, "t": datetime.now().strftime("%H:%M")})


def say(text: str, *extra):
    add("tutor", [{"k": "text", "v": text}, *extra])


def parse_options(prompt: str):
    opts = {m.group(1): m.group(2) for m in re.finditer(r"^\s*([A-D])\)\s*(.+)$", prompt, re.M)}
    stem = re.sub(r"^\s*[A-D]\)\s*.+$", "", prompt, flags=re.M).strip()
    return stem, opts


def exercise_blocks(p: dict) -> List[dict]:
    stem, opts = parse_options(p["prompt"])
    part = {"guided_practice": "Guided practice", "free_practice": "Free practice", "assessment": "Assessment"}.get(p.get("part"), "Practice")
    b = [{"k": "chip", "v": f"Exercise {p.get('index', '?')} of {p.get('total', '?')} · {part}", "c": "ac"}, {"k": "text", "v": stem}]
    if opts:
        b.append({"k": "options", "v": opts})
    return b


def action_blocks(out: dict) -> List[dict]:
    a = out.get("action")
    if not a:
        return []
    pl, k = a.get("payload", {}), a["kind"]
    if k == "hint_then_variant":
        return [{"k": "card", "t": "Level 1 · Nudge", "lines": [f"💡 {pl['hint']}"]}, {"k": "text", "v": "Here is a fresh variant of the same skill."}]
    if k == "worked_example_completion":
        return [{"k": "card", "t": "Level 2 · Worked example", "lines": [pl["worked_example"]]}, {"k": "card", "t": "Now you finish this half-solved task", "code": pl["completion_problem"]}]
    if k == "change_representation":
        lines = [f"Tiny step {i}: {x}" for i, x in enumerate(pl["minimal_steps"], 1)]
        blocks = [{"k": "card", "t": "Level 4 · A different way to see it", "lines": lines + [f"Trace: {pl['trace']}"] + ([f"🧠 Analogy: {pl['analogy']}"] if pl.get("analogy") else [])},
                  {"k": "text", "v": pl["teach_back"]}]
        return blocks
    return []


def ingest(view: dict, first: bool = False):
    """Turn the backend response into chat messages (tutor side)."""
    ss.view = view
    out, dg = view.get("outcome"), view.get("diagnostic")
    if out and out["seq"] > ss.last_outcome:
        ss.last_outcome = out["seq"]
        res = out["result"]
        chip = {"pass": ("Correct", "ok"), "fail": ("Not yet", "warn"), "pass_but_rote": ("Correct, but explain it", "warn")}[res]
        blocks = [{"k": "text", "v": out["message"]}]
        if out.get("signals"):
            blocks.append({"k": "chips", "v": [(s.replace("_", " "), "warn") for s in out["signals"]]})
        blocks += action_blocks(out)
        if out.get("mastered"):
            ss.celebrate = out["seq"]
            blocks.append({"k": "chip", "v": "🎉 Mastered: two correct answers on different variants", "c": "ok"})
        add("tutor", blocks)
        if out.get("action"):
            lv = out["action"]["level"]
            add("system", [{"k": "chip", "v": f"Fail ladder · level {lv} · {LADDER[lv - 1][1]}" + (" (same error twice: shortcut)" if out["action"].get("shortcut") else ""), "c": "bad" if lv == 5 else "warn" if lv >= 3 else "ac"}])
    if dg and dg["seq"] > ss.last_diag:
        ss.last_diag = dg["seq"]
        add("tutor", [{"k": "text", "v": dg["learner_text"]}, {"k": "chip", "v": ("Gap found: " + ", ".join(dg["gap_concepts"])) if dg["gap"] else "No gap in the prerequisites", "c": "warn" if dg["gap"] else "ok"}])
    p = view.get("pending") or {}
    key = (p.get("kind"), p.get("exercise_id"), p.get("variant"), tuple(p.get("question_ids", []) or []), len(ss.messages) if p.get("kind") == "pretest" else 0)
    if view["waiting"] != "done" and key != ss.last_present:
        ss.last_present = key; ss.hints_shown = 0; ss.t_present = time.time()
        if p["kind"] == "pretest":
            if first:
                say(f"Welcome! I'm your tutor for **{view['lesson']['title']}**.")
                add("tutor", [{"k": "text", "v": view["lesson"]["problem"]}, {"k": "text", "v": view["lesson"]["objective"]}, {"k": "chip", "v": "First, a 3-question quick check (no pressure)", "c": "ac"}])
        elif p["kind"] == "diagnostic":
            add("tutor", [{"k": "chip", "v": "Quick prerequisite check · 2 questions", "c": "ac"}])
        elif p["kind"] == "exercise":
            if ss.view.get("route") and not any(m.get("tag") == "route" for m in ss.messages):
                r = view["route"]; add("tutor", [{"k": "text", "v": r["learner_text"]}, {"k": "chip", "v": "Route: " + r["route"].replace("_", " "), "c": "ac"}]); ss.messages[-1]["tag"] = "route"
            add("tutor", exercise_blocks(p))
    if view["done"]:
        if not any(m.get("tag") == "done" for m in ss.messages):
            sm = view.get("summary") or {}
            if view.get("parked"):
                add("tutor", [{"k": "text", "v": "I've parked the exercise you were stuck on and prepared a handoff packet for your teacher. You can continue with the parts that don't depend on it, and I'll bring it back tomorrow."}])
            else:
                add("tutor", [{"k": "text", "v": "Lesson complete! You've mastered every exercise. I'll bring them back at spaced intervals to lock them in."}, {"k": "chip", "v": "🏁 Lesson complete", "c": "ok"}])
            ss.messages[-1]["tag"] = "done"


def start_session():
    ss.messages, ss.last_outcome, ss.last_diag, ss.last_present, ss.celebrate, ss.error = [], 0, 0, None, 0, None
    try:
        ss.backend = pick_backend()
        ingest(ss.backend.start(ss.learner or "Student"), first=True)
    except BackendError as e:
        ss.error = f"Could not start: {e}"


def send(reply: dict, shown: Optional[str] = None):
    if shown is not None:
        add("student", [{"k": "text" if reply.get("answer_type") != "code" else "code", "v": shown}])
    try:
        ingest(ss.backend.reply(ss.view["thread_id"], reply))
    except BackendError as e:
        ss.error = f"Engine error: {e}"


def answer_exercise(text: str, explanation: Optional[str] = None):
    p = ss.view["pending"]
    rep = {"answer": text, "time_sec": round(time.time() - ss.t_present, 1), "hints": ss.hints_shown}
    if explanation:
        rep["explanation"] = explanation
    shown = text if len(text) < 2 else text
    add("student", [{"k": "code" if p.get("answer_type") == "code_line" else "text", "v": shown}])
    send(rep)


# =====================================================================================================================
# 4. RENDERING
# =====================================================================================================================
def render_block(b: dict) -> str:
    k = b["k"]
    if k == "text":
        t = esc(b["v"]); t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t); t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        return f"<p>{t}</p>"
    if k == "code":
        return pre(b["v"])
    if k == "options":
        return "".join(f"<div class='opt'><b>{L}</b><span>{esc(t)}</span></div>" for L, t in b["v"].items())
    if k == "chip":
        return f"<div style='margin:6px 0'><span class='chip {b.get('c', '')}'>{esc(b['v'])}</span></div>"
    if k == "chips":
        return "<div style='margin:6px 0;display:flex;gap:6px;flex-wrap:wrap'>" + "".join(f"<span class='chip {c}'>{esc(t)}</span>" for t, c in b["v"]) + "</div>"
    if k == "card":
        body = "".join(f"<div>{esc(x)}</div>" for x in b.get("lines", [])) + (pre(b["code"]) if b.get("code") else "")
        return f"<div class='tcard'><div class='tt'>{esc(b['t'])}</div>{body}</div>"
    return ""


def chat_html(thinking: bool = False) -> str:
    out = []
    for m in ss.messages:
        if m["role"] == "system":
            out.append("<div class='sys'>" + "".join(render_block(b) for b in m["blocks"]) + "</div>")
            continue
        who, av = ("Tutor", "🎓") if m["role"] == "tutor" else (ss.learner or "You", "🧑")
        out.append(f"<div class='msg {m['role']}'><div class='av'>{av}</div><div class='bub'><div class='who'>{esc(who)} · {m['t']}</div>{''.join(render_block(b) for b in m['blocks'])}</div></div>")
    if thinking:
        out.append("<div class='msg tutor'><div class='av'>🎓</div><div class='bub'><span class='typing'><i></i><i></i><i></i></span></div></div>")
    return "<div class='chat-scroll' id='chatscroll'>" + "".join(out) + "</div>"


def cur_ex(v):
    return next((e for e in v["exercises"] if e["id"] == v.get("current_ex")), v["exercises"][0])


def ladder_html(level: int) -> str:
    out = []
    for i, (n, name, _) in enumerate(LADDER, 1):
        cls = "done" if i <= level else ""
        cls += " now" if i == level else ""
        cls += " danger" if i == 5 else ""
        out.append(f"<div class='step {cls}'><div class='node'>{n}</div><div class='lb'>{esc(name)}</div></div>")
    return "<div class='ladder'>" + "".join(out) + "</div>"


MOOD = {"confident": ("😎", "Confident", "ok"), "frustrated": ("😖", "Frustrated", "bad"), "rushed_guessing": ("⚡", "Rushing / guessing", "warn"), "needs_break": ("☕", "Needs a break", "warn"), "quit_attempt": ("🚪", "Leaving", "bad")}
SIGNAL_TXT = {"same_mistake": "Same mistake → misconception", "different_mistakes": "Different mistakes → weak foundation", "fast_wrong": "Very fast wrong → guessing", "slow_wrong": "Slow then wrong → confusion",
              "hint_dependent": "Hint dependent → fade hints", "rote_answer": "Right answer, weak explanation → rote"}


def live_tab(v: dict):
    exs, c = v["exercises"], cur_ex(v)
    mastered = sum(e["mastered"] for e in exs)
    attempts = [a for e in exs for a in e["attempts"]]
    first_pass = [e["attempts"][0]["result"] == "pass" for e in exs if e["attempts"]]
    hpa = (sum(a["hints"] for a in attempts) / len(attempts)) if attempts else 0
    avg_t = (sum(a["time"] for a in attempts) / len(attempts)) if attempts else 0
    # --- overview
    pct = int(100 * mastered / max(1, len(exs)))
    rows = ""
    for e in exs:
        pips = "".join(f"<span class='pip {'on' if i < e['streak'] else ''}'></span>" for i in range(2))
        st_ = "✅" if e["mastered"] else "⏸️" if e["id"] in v["parked"] else ("▶️" if e["id"] == v.get("current_ex") and not v["done"] else "·")
        rows += f"<div class='exrow'><span>{st_}</span><span class='nm'>{e['id']}<div class='pt'>{e['part'].replace('_', ' ')}</div></span><div class='pips'>{pips}</div><span class='mut mono'>{e['fail_count']} fails</span></div>"
    H(f"""<div class='card'><h4>📈 Session overview</h4><div style='display:flex;gap:18px;align-items:center'>
        <div class='ring' style='--p:{pct}'><div><span><span data-count='{pct}'>{pct}</span>%</span></div></div>
        <div style='flex:1'>{rows}</div></div>
        <div class='grid g3' style='margin-top:14px'>
          <div class='kpi'><div class='v'><span data-count='{len(attempts)}'>{len(attempts)}</span></div><div class='l'>Attempts</div></div>
          <div class='kpi'><div class='v'>{(f"{100 * sum(first_pass) / len(first_pass):.0f}%" if first_pass else "n/a")}</div><div class='l'>First-attempt pass</div></div>
          <div class='kpi'><div class='v'>{hpa:.1f}</div><div class='l'>Hints / attempt · {avg_t:.0f}s avg</div></div></div></div>""")
    # --- ladder
    lvl = c["ladder_level"]
    tip = LADDER[lvl - 1][2] if lvl else "No failure yet: learner is on track"
    H(f"""<div class='card'><h4>🪜 Fail ladder · {esc(c['id'])}</h4>{ladder_html(lvl)}
        <div style='margin-top:12px;display:flex;justify-content:space-between;align-items:center'><span class='mut' style='font-size:.8rem'>{esc(tip)}</span>
        <span class='chip {'bad' if lvl >= 5 else 'warn' if lvl >= 3 else 'ac'}'>level <b data-count='{lvl}'>{lvl}</b> / 5</span></div></div>""")
    # --- student state
    flags = "".join(f"<span class='chip {MOOD[m][2]}'>{MOOD[m][0]} {MOOD[m][1]}</span>" for m in v["mood"] if m in MOOD) or "<span class='chip ok'>🙂 Focused</span>"
    sigs = "".join(f"<span class='chip warn'>{esc(SIGNAL_TXT.get(s, s))}</span>" for s in v["signals"]) or "<span class='chip'>No error signal yet</span>"
    errs = "".join(f"<span class='chip mono'>{esc(k)} ×{n}</span>" for e in exs for k, n in e["signatures"].items()) or "<span class='mut' style='font-size:.8rem'>no errors recorded</span>"
    spark = "".join(f"<span class='pip {'on' if a['result'] == 'pass' else 'fail'}' title='{esc(a['variant'])}'></span>" for a in attempts) or "<span class='mut' style='font-size:.8rem'>waiting for the first answer</span>"
    H(f"""<div class='card'><h4>🧠 Student state</h4><div class='mood'>{flags}</div>
        <div style='margin-top:12px' class='mut'><div style='font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px'>Error signals</div><div class='mood'>{sigs}</div></div>
        <div style='margin-top:12px' class='mut'><div style='font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px'>Error signatures</div><div class='mood'>{errs}</div></div>
        <div style='margin-top:12px'><div class='mut' style='font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px'>Attempt timeline</div><div class='pips'>{spark}</div></div></div>""")
    # --- handoff + revisit
    hand = v.get("packets") or []
    if hand:
        p = hand[-1]
        H(f"""<div class='card'><h4>🤝 Park &amp; handoff</h4><div class='hand bad'><div class='big bad'>Parked · handoff to {esc(p.get('recipient', 'teacher'))}</div>
            <div class='mut' style='margin-top:6px;font-size:.84rem'>Stuck on <b>{esc(p['stuck_concept_name'])}</b> ({esc(p['exercise_id'])}) after 5 fails. Learner continues with: {esc(', '.join(p['open_parts']) or 'nothing else in this lesson')}.</div>
            <div style='margin-top:10px;font-size:.84rem'><b>Diagnosis</b><ul style='margin:4px 0 0 18px'>{''.join(f'<li>{esc(d)}</li>' for d in p['diagnosis'])}</ul></div>
            <div style='margin-top:8px;font-size:.84rem'><b>Suggested next step</b><ul style='margin:4px 0 0 18px'>{''.join(f'<li>{esc(d)}</li>' for d in p['suggested_next_step'])}</ul></div></div></div>""")
        try:
            md = ss.backend.packet_md(v["thread_id"])
            if md:
                st.download_button("⬇️ Download handoff packet (.md)", md, file_name=f"handoff_{p['exercise_id']}.md", mime="text/markdown", use_container_width=True)
        except BackendError:
            pass
    else:
        tone, txt = ("warn", "Watching closely: prerequisite check or new representation in progress") if lvl >= 3 else ("ok", "On track: no handoff needed")
        H(f"""<div class='card'><h4>🤝 Park &amp; handoff</h4><div class='hand {tone}'><div class='big {tone}'>{'Watching' if tone == 'warn' else 'On track'}</div><div class='mut' style='margin-top:4px;font-size:.84rem'>{txt}. A person is called in at Fail 5.</div></div></div>""")
    done = [e for e in exs if e["mastered"]]
    tl = "".join(f"<span class='d'>day +{d}</span>" for d in v.get("reviews_projected_days", REVIEW_DAYS))
    sched = "".join(f"<span class='chip ok'>{esc(r['exercise_id'])} · {esc(r['kind'].replace('_', ' '))} · {esc(r['due_at'][:16].replace('T', ' '))}</span>" for r in v.get("reviews", []))
    H(f"""<div class='card'><h4>🗓️ Spaced revisit</h4><div class='mut' style='font-size:.82rem'>{len(done)} exercise(s) mastered. Each comes back at expanding intervals; the 7-day review feeds the retention metric.</div>
        <div class='tl'>{tl}</div><div class='mood' style='margin-top:10px'>{sched or "<span class='mut' style='font-size:.8rem'>Reviews are scheduled when an exercise is mastered or parked.</span>"}</div></div>""")


def system_tab(be):
    try:
        m = ss.metrics or be.metrics(); ss.metrics = m
    except BackendError as e:
        st.warning(f"Metrics unavailable: {e}"); return
    q, o, g = m["quality"], m["outcomes"], m["gate"]
    pr = q["pass_rate_per_round"][-1][1] if q.get("pass_rate_per_round") else None
    pct = lambda x, d=0: "n/a" if x is None else f"{100 * x:.{d}f}%"
    vt = "ok" if g["verdict"] == "PUBLISH" else "bad"
    note = "Sample numbers (demo engine)" if m.get("demo") else f"Learner data: synthetic cohort of {m.get('cohort_n', '?')} scripted learners through the same graph"
    H(f"""<div class='card'><h4>🚦 Release gate · lesson {esc(m['lesson']['id'])}</h4><div style='display:flex;align-items:center;gap:14px;flex-wrap:wrap'>
        <div class='big {vt}'>{esc(g['verdict'])}</div><div class='mut' style='font-size:.82rem'>{esc(m['lesson']['title'])}</div></div>
        <div style='margin-top:10px'>{''.join(f"<div class='exrow'><span>{'✅' if c['ok'] else ('⚠️' if not c['hard'] else '❌')}</span><span class='nm' style='font-size:.8rem'>{esc(c['check'])}</span><span class='pt'>{'hard' if c['hard'] else 'warning'}</span></div>" for c in g['checks'])}</div></div>""")
    H(f"""<div class='card'><h4>🏗️ Lesson quality · Loop A (Steps 5-7)</h4><div class='grid g3'>
        <div class='kpi'><div class='v gtext'>{pct(pr)}</div><div class='l'>Pass rate (last round)</div><div class='s'>threshold 80%</div></div>
        <div class='kpi'><div class='v {'ok' if q['hallucination_rate'] == 0 else 'bad'}'>{pct(q['hallucination_rate'])}</div><div class='l'>Hallucination rate</div><div class='s'>{q.get('claims', '?')} claims verified</div></div>
        <div class='kpi'><div class='v'>{pct(q['baseline_pass_rate'])}</div><div class='l'>No-lesson baseline</div><div class='s'>lift {('+' + pct(q['lift'])) if q.get('lift') is not None else 'n/a'}</div></div></div></div>""")
    H(f"""<div class='card'><h4>👩‍🎓 Learner outcomes · Loop B (Steps 8-10)</h4><div class='mut' style='font-size:.74rem;margin-bottom:8px'>{esc(note)}</div><div class='grid g3'>
        <div class='kpi'><div class='v'>{pct(o.get('first_attempt_pass_rate'))}</div><div class='l'>First-attempt pass</div></div>
        <div class='kpi'><div class='v'>{pct(o.get('mastery_within_3'))}</div><div class='l'>Mastery within 3</div></div>
        <div class='kpi'><div class='v'>{(o.get('time_to_mastery_sec') or 0) / 60:.1f}m</div><div class='l'>Time to mastery</div></div>
        <div class='kpi'><div class='v'>{o.get('hints_per_attempt') or 0:.2f}</div><div class='l'>Hints / attempt</div></div>
        <div class='kpi'><div class='v {'warn' if (o.get('handoff_rate') or 0) > 0.1 else ''}'>{pct(o.get('handoff_rate'))}</div><div class='l'>Handoff rate (Fail 5+)</div></div>
        <div class='kpi'><div class='v'>{pct(o.get('transfer_score'))}</div><div class='l'>Transfer score</div></div></div></div>""")
    lad = m["health"]["ladder"]
    bars = "".join(f"<div style='margin:8px 0'><div style='display:flex;justify-content:space-between;font-size:.78rem'><span>{r['level']} · {esc(r['treatment'].replace('_', ' '))}</span><span class='mut'>{pct(r['unstuck_rate'])} · n={r['cases']}</span></div><div class='bar'><i style='width:{100 * r['unstuck_rate']:.0f}%'></i></div></div>" for r in lad)
    fl = "".join(f"<tr><td>{esc(f['exercise_id'])}</td><td>{f['failed_twice']}/{f['learners']}</td><td>{pct(f['share'])}</td><td class='{'bad' if f['flagged'] else 'ok'}'>{'FLAGGED' if f['flagged'] else 'ok'}</td></tr>" for f in m["flags"])
    H(f"""<div class='card'><h4>⚙️ System health</h4><div style='font-size:.78rem' class='mut'>Ladder effectiveness: share of learners who passed right after each treatment</div>{bars}
        <div style='margin-top:14px' class='mut'>Aggregate flags (30% fail twice rule)</div><table class='t'><tr><th>Exercise</th><th>Failed ≥2×</th><th>Share</th><th>Status</th></tr>{fl}</table></div>""")


def trace_tab(v: dict, be):
    nodes = " → ".join(f"<span class='chip mono'>{esc(t)}</span>" for t in v.get("trace", [])[-14:])
    H(f"<div class='card'><h4>🔀 LangGraph node trace (last 14)</h4><div class='mood'>{nodes or '<span class=mut>no nodes yet</span>'}</div><div class='mut' style='margin-top:10px;font-size:.78rem'>The graph pauses before <b>handle_reply</b> and waits for the learner. State is checkpointed after every node.</div></div>")
    rows = "".join(f"<tr><td class='mono'>{e.get('seq')}</td><td>{esc(e.get('type'))}</td><td>{esc(e.get('exercise') or '')}</td><td>{esc(e.get('variant') or '')}</td><td class='{'ok' if e.get('result') == 'pass' else 'warn' if e.get('result') else ''}'>{esc(e.get('result') or e.get('route') or '')}</td><td>{esc(e.get('action') or '')}</td><td class='mono'>{esc(e.get('signature') or '')}</td></tr>" for e in v.get("events", [])[-14:])
    H(f"<div class='card'><h4>📜 Engine events</h4><table class='t'><tr><th>#</th><th>type</th><th>exercise</th><th>variant</th><th>result</th><th>treatment</th><th>error</th></tr>{rows}</table></div>")
    H(f"<div class='card'><h4>🔌 Backend</h4><div class='mut' style='font-size:.82rem'>{esc(be.label)}<br>session <span class='mono'>{esc(v['thread_id'])}</span> · learner <span class='mono'>{esc(v['learner_id'])}</span></div></div>")


# =====================================================================================================================
# 5. PAGE
# =====================================================================================================================
H(CSS)

with st.sidebar:
    st.markdown("### Session")
    ss.learner = st.text_input("Learner name", value=ss.learner, key="learner_in")
    ss.mode = st.radio("Backend", ["Auto", "Live", "Demo"], index=["Auto", "Live", "Demo"].index(ss.mode), help="Auto: live LangGraph bridge if reachable, otherwise the built-in demo engine.")
    if st.button("🔄 New session", use_container_width=True, key="new_session"):
        ss.demo_engine = None; ss.metrics = None
        start_session(); st.rerun()
    demo_controls = st.toggle("Presenter controls", value=True, help="One-click correct/wrong answers so you can show the whole fail ladder in a minute.")
    st.caption(f"Bridge URL: {BACKEND_URL}")
    st.caption("Press Ctrl + B to hide / show this panel.")

if ss.view is None and ss.error is None:
    if ss.mode == "Demo":
        ss.demo_engine = ss.demo_engine or DemoEngine()
    start_session()
be = ss.backend
live = bool(be and be.mode == "live")
H(f"""<div class='topbar'><div class='brand'><div class='logo'>🎓</div><div>Lumina Tutor<small>Adaptive instructional design · Gagné × Merrill · LangGraph</small></div></div>
    <div><span class='pill'><span class='dot {'' if live else 'demo'}'></span>{'Live engine connected' if live else 'Demo engine (sample data)'}</span><span class='pill'>Loop A + Loop B</span><span class='pill'>Lesson {esc(ss.view['lesson']['id']) if ss.view else '-'}</span></div></div>""")

if ss.error:
    st.error(ss.error)
    st.stop()

v = ss.view
left, right = st.columns([1.38, 1], gap="large")

with left:
    p = v["pending"] or {}
    H(f"""<div class='chat-head'><div><div class='t'>💬 Tutor chat</div><div class='s'>{esc(v['lesson']['title'])}</div></div>
        <div><span class='chip ac'>{esc(p.get('part', 'lesson').replace('_', ' ')) if p.get('kind') == 'exercise' else (p.get('kind') or 'done')}</span></div></div>""")
    H(chat_html())

    # ---------------- answer area ----------------
    kind = v["waiting"]
    oracle = {}
    if demo_controls and kind != "done" and getattr(be, "oracle_ok", False):
        try:
            oracle = be.oracle(v["thread_id"])
        except BackendError:
            oracle = {}
    if kind in ("pretest", "diagnostic"):
        qs = p.get("questions", [])
        with st.form(f"quick_{kind}_{len(ss.messages)}", clear_on_submit=False):
            st.markdown(f"**{'Quick check' if kind == 'pretest' else 'Prerequisite check'}**")
            picks = {}
            for q in qs:
                picks[q["id"]] = st.radio(q["prompt"], list(q["options"].keys()), format_func=lambda L, q=q: f"{L}) {q['options'][L]}", key=f"r_{q['id']}_{len(ss.messages)}", index=None)
            go = st.form_submit_button("Submit answers", use_container_width=True)
        if go:
            if any(x is None for x in picks.values()):
                st.warning("Please answer every question (a guess is fine).")
            else:
                add("student", [{"k": "text", "v": "My answers: " + ", ".join(f"{k.split('-')[-1]}: {x}" for k, x in picks.items())}])
                send({"answers": picks}); st.rerun()
        if oracle:
            c1, c2 = st.columns(2)
            if c1.button("🎬 Presenter: answer all correctly", use_container_width=True, key=f"oc_{kind}_{len(ss.messages)}"):
                add("student", [{"k": "text", "v": "(presenter) all correct"}]); send({"answers": oracle["correct"]}); st.rerun()
            if c2.button("🎬 Presenter: one weak spot", use_container_width=True, key=f"ow_{kind}_{len(ss.messages)}"):
                first = next(iter(oracle["correct"]))
                add("student", [{"k": "text", "v": "(presenter) one weak spot"}]); send({"answers": {**oracle["correct"], first: oracle["wrong"][first]}}); st.rerun()
    elif kind == "exercise":
        stem, opts = parse_options(p["prompt"])
        hints = p.get("hints", [])
        tb = st.text_area("Explain in your own words (teach-back)", key=f"tb_{len(ss.messages)}", height=70, placeholder="What does the correct line do, and why does it work?") if v.get("teach_back_pending") else None
        if opts:
            cols = st.columns(len(opts))
            for col, (L, t) in zip(cols, opts.items()):
                if col.button(f"{L}", key=f"opt_{L}_{len(ss.messages)}", use_container_width=True, help=t):
                    answer_exercise(L, tb); st.rerun()
        else:
            with st.form(f"ans_{len(ss.messages)}", clear_on_submit=True):
                txt = st.text_input("Your answer", placeholder="Type your answer, then press Enter", label_visibility="collapsed")
                c1, c2 = st.columns([4, 1])
                sent = c2.form_submit_button("Send ➤", use_container_width=True)
            if sent and txt.strip():
                answer_exercise(txt.strip(), tb); st.rerun()
        b1, b2, b3 = st.columns([1, 1, 1])
        if b1.button(f"💡 Hint ({ss.hints_shown}/{len(hints)})", use_container_width=True, disabled=ss.hints_shown >= len(hints), key=f"hint_{len(ss.messages)}_{ss.hints_shown}"):
            ss.hints_shown += 1; add("tutor", [{"k": "card", "t": f"Hint level {ss.hints_shown}", "lines": [hints[ss.hints_shown - 1]]}]); st.rerun()
        if b3.button("🚪 I want to stop", use_container_width=True, key=f"quit_{len(ss.messages)}"):
            send({"quit": True}); st.rerun()
        if oracle:
            c1, c2 = st.columns(2)
            if c1.button("🎬 Presenter: correct answer", use_container_width=True, key=f"oc_{len(ss.messages)}"):
                answer_exercise(oracle["correct"], "It calls the function that reads the page and keeps the status code of the response in a variable"); st.rerun()
            if c2.button("🎬 Presenter: wrong answer", use_container_width=True, key=f"ow_{len(ss.messages)}"):
                answer_exercise(oracle["wrong"]); st.rerun()
    else:
        H("<div class='card'><h4>🏁 Session finished</h4><div class='mut' style='font-size:.86rem'>Start a new session to show another learner path.</div></div>")
        if st.button("🔄 Start new session", use_container_width=True, key="new_session_main"):
            ss.demo_engine = None; ss.metrics = None
            start_session(); st.rerun()

with right:
    t1, t2, t3 = st.tabs(["Live session", "System metrics", "Engine trace"])
    with t1:
        live_tab(v)
    with t2:
        system_tab(be)
    with t3:
        trace_tab(v, be)

# =====================================================================================================================
# 6. JAVASCRIPT (zero-height iframe that reaches the page through window.parent)
# =====================================================================================================================
JS = f"""
<script>
(function(){{
  const doc = window.parent.document;
  // 1) keep the chat scrolled to the newest message
  const box = doc.getElementById('chatscroll'); if (box) box.scrollTop = box.scrollHeight;
  // 2) count-up animation for every [data-count] number (only when the value changed)
  doc.querySelectorAll('[data-count]').forEach(el => {{
    const to = parseFloat(el.dataset.count), from = parseFloat(el.dataset.prev ?? '0');
    if (isNaN(to) || from === to) {{ el.dataset.prev = to; return; }}
    const t0 = performance.now(), dur = 700;
    const tick = t => {{ const k = Math.min(1, (t - t0) / dur); el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(tick); }};
    requestAnimationFrame(tick); el.dataset.prev = to;
  }});
  // 3) confetti when an exercise has just been mastered (once per event)
  const seq = {int(ss.celebrate)};
  if (seq > 0 && window.parent.sessionStorage.getItem('celebrated') !== String(seq)) {{
    window.parent.sessionStorage.setItem('celebrated', String(seq));
    const c = doc.createElement('canvas'); c.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:9999';
    c.width = window.parent.innerWidth; c.height = window.parent.innerHeight; doc.body.appendChild(c);
    const g = c.getContext('2d'), cols = ['#7c83ff','#22d3ee','#34d399','#fbbf24','#fb7185'];
    const P = Array.from({{length: 120}}, () => ({{x: c.width/2, y: c.height*0.35, vx: (Math.random()-.5)*14, vy: Math.random()*-12-2, s: Math.random()*6+3, col: cols[(Math.random()*cols.length)|0], r: Math.random()*6}}));
    let n = 0; (function f(){{ g.clearRect(0,0,c.width,c.height); P.forEach(p => {{ p.vy += .35; p.x += p.vx; p.y += p.vy; p.r += .2; g.save(); g.translate(p.x,p.y); g.rotate(p.r); g.fillStyle = p.col; g.fillRect(-p.s/2,-p.s/2,p.s,p.s*.6); g.restore(); }});
      if (++n < 110) requestAnimationFrame(f); else c.remove(); }})();
  }}
}})();
</script>
"""
try:
    st.iframe(JS, height=1)          # newer Streamlit
except (AttributeError, TypeError):
    components.html(JS, height=0)    # older Streamlit

# =====================================================================================================================
# 7. SIDEBAR TOGGLE (<< / >> button and Ctrl + B)
# =====================================================================================================================
SB_JS = """
<script>
(function(){
  const win = window.parent, doc = win.document;
  const S = win.__sbToggle = win.__sbToggle || {};
  // remove whatever an earlier run of this script installed (reruns must not stack listeners)
  if (S.timer) win.clearInterval(S.timer);
  if (S.onKey) doc.removeEventListener('keydown', S.onKey, true);
  if (S.onResize) win.removeEventListener('resize', S.onResize);
  const old = doc.getElementById('sb-toggle'); if (old) old.remove();

  const sidebar = () => doc.querySelector('section[data-testid="stSidebar"]');
  const isOpen = () => {
    const sb = sidebar(); if (!sb) return false;
    if (sb.getAttribute('aria-expanded') === 'false') return false;
    return sb.getBoundingClientRect().right > 40;
  };
  // Streamlit's own collapse / expand controls (names differ a little between versions)
  const CLOSE = ['[data-testid="stSidebarCollapseButton"]', '[data-testid="stSidebar"] button[kind="header"]', '[data-testid="baseButton-header"]'];
  const OPEN  = ['[data-testid="stExpandSidebarButton"]', '[data-testid="stSidebarCollapsedControl"]', '[data-testid="collapsedControl"]'];
  const click = sels => {
    for (const s of sels) {
      const el = doc.querySelector(s);
      if (el) { (el.tagName === 'BUTTON' ? el : (el.querySelector('button') || el)).click(); return true; }
    }
    return false;
  };
  const toggle = () => { if (isOpen()) click(CLOSE); else click(OPEN); win.setTimeout(place, 350); };

  const btn = doc.createElement('button');
  btn.id = 'sb-toggle'; btn.type = 'button';
  btn.addEventListener('click', toggle);
  doc.body.appendChild(btn);

  function place() {
    const open = isOpen(), sb = sidebar();
    btn.textContent = open ? '<<' : '>>';
    btn.title = (open ? 'Hide' : 'Show') + ' sidebar (Ctrl + B)';
    btn.style.left = (open && sb ? Math.round(sb.getBoundingClientRect().right + 4) : 4) + 'px';
  }
  S.onKey = e => {
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && String(e.key).toLowerCase() === 'b') { e.preventDefault(); toggle(); }
  };
  S.onResize = place;
  doc.addEventListener('keydown', S.onKey, true);
  win.addEventListener('resize', S.onResize);
  S.timer = win.setInterval(place, 300);
  place();
})();
</script>
"""
try:
    st.iframe(SB_JS, height=1)          # newer Streamlit
except (AttributeError, TypeError):
    components.html(SB_JS, height=0)    # older Streamlit
