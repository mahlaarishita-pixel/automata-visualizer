import streamlit as st
import pandas as pd
from graphviz import Digraph

st.set_page_config(page_title="Automata Studio | DFA & NFA Visualizer", page_icon="🔷", layout="wide", initial_sidebar_state="expanded")

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background: radial-gradient(circle at 12% 8%, #172554 0, #0b1224 38%, #080d19 100%); color:#e8eefc;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#111c35,#0b1224); border-right:1px solid #263655;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif!important; color:#f5f7ff!important;}
.hero {padding:1.35rem 1.6rem; border:1px solid #34466c; border-radius:20px; background:linear-gradient(115deg,rgba(37,99,235,.24),rgba(124,58,237,.22),rgba(14,165,233,.12)); margin-bottom:1rem;}
.hero-kicker {color:#8bd5ff; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:700;}
.hero-title {font-family:'Space Grotesk';font-size:2.1rem;font-weight:700;color:#fff;line-height:1.15;margin:.35rem 0;}
.hero-sub {color:#bdc9e3;font-size:.98rem;}
.panel {background:rgba(17,29,53,.78);border:1px solid #2c3d5f;border-radius:16px;padding:1rem 1.1rem;margin-bottom:.7rem;}
.metric {background:linear-gradient(145deg,#172746,#111b31);border:1px solid #34476c;border-radius:14px;padding:1rem;}
.metric-label {color:#9fb2d4;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;}
.metric-value {font-family:'Space Grotesk';font-size:1.55rem;font-weight:700;color:#fff;}
.small-muted {color:#9fb0cf;font-size:.85rem;}
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {border:1px solid #34476c;border-radius:12px;overflow:hidden;}
.stButton>button {border-radius:10px;border:1px solid #4768bb;background:linear-gradient(100deg,#2563eb,#6d4be8);color:white;font-weight:700;}
.stButton>button:hover {border-color:#8bb7ff;color:white;box-shadow:0 0 18px #2563eb55;}
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stSelectbox"] div {border-radius:9px;}
div[data-testid="stAlert"] {border-radius:12px;}
hr {border-color:#293a5b;}
</style>
""", unsafe_allow_html=True)

EXAMPLES = {
    "DFA · strings ending in 01": {
        "mode":"DFA","states":["q0","q1","q2"],"alphabet":["0","1"],"start":"q0","final":["q2"],
        "transitions":{"q0":{"0":["q1"],"1":["q0"]},"q1":{"0":["q1"],"1":["q2"]},"q2":{"0":["q1"],"1":["q0"]}}
    },
    "DFA · even number of 1s": {
        "mode":"DFA","states":["q0","q1"],"alphabet":["0","1"],"start":"q0","final":["q0"],
        "transitions":{"q0":{"0":["q0"],"1":["q1"]},"q1":{"0":["q1"],"1":["q0"]}}
    },
    "NFA · strings containing 01": {
        "mode":"NFA","states":["q0","q1","q2"],"alphabet":["0","1"],"start":"q0","final":["q2"],
        "transitions":{"q0":{"0":["q0","q1"],"1":["q0"]},"q1":{"0":[],"1":["q2"]},"q2":{"0":["q2"],"1":["q2"]}}
    },
    "ε-NFA · accepts 0 or 1": {
        "mode":"ε-NFA","states":["q0","q1","q2"],"alphabet":["0","1"],"start":"q0","final":["q1","q2"],
        "transitions":{"q0":{"0":[],"1":[],"ε":["q1","q2"]},"q1":{"0":["q1"],"1":[]},"q2":{"0":[],"1":["q2"]}}
    }
}

def parse_csv(s):
    return [x.strip() for x in s.split(",") if x.strip()]

def eps_closure(states, trans):
    closure=set(states); stack=list(states)
    while stack:
        q=stack.pop()
        for nxt in trans.get(q,{}).get("ε",[]):
            if nxt not in closure:
                closure.add(nxt); stack.append(nxt)
    return closure

def simulate(mode, states, alphabet, start, finals, trans, word):
    active=eps_closure({start},trans) if mode=="ε-NFA" else {start}
    rows=[{"Step":0,"Read":"START","Active state(s)":", ".join(sorted(active)),"Remaining input":word,"Transition applied":"Initial state"}]
    path_edges=[]
    for i,ch in enumerate(word, start=1):
        if ch not in alphabet:
            return rows, active, False, f"Symbol '{ch}' is not in the alphabet."
        nxt=set()
        used=[]
        for q in sorted(active):
            destinations=trans.get(q,{}).get(ch,[])
            for d in destinations:
                nxt.add(d); used.append(f"{q} --{ch}--> {d}"); path_edges.append((q,d,ch))
        if mode=="ε-NFA":
            closed=eps_closure(nxt,trans)
            for a in sorted(nxt):
                for b in sorted(closed):
                    if b in eps_closure({a},trans) and a!=b:
                        path_edges.append((a,b,"ε"))
            nxt=closed
        active=nxt
        rows.append({"Step":i,"Read":ch,"Active state(s)":", ".join(sorted(active)) if active else "∅","Remaining input":word[i:],"Transition applied":"; ".join(used) if used else "No transition"})
        if not active:
            # Continue rows for remaining characters to show the machine is stuck.
            for j, rest in enumerate(word[i:], start=i+1):
                rows.append({"Step":j,"Read":rest,"Active state(s)":"∅","Remaining input":word[j:],"Transition applied":"No active state"})
            break
    accepted=bool(active & set(finals))
    return rows, active, accepted, None

def make_graph(states, alphabet, trans, start, finals, active=None, used_edges=None):
    active=active or set(); used_edges=used_edges or []
    dot=Digraph()
    dot.attr(rankdir="LR",bgcolor="transparent",pad="0.25",nodesep="0.65",ranksep="0.8")
    dot.attr("node",shape="circle",style="filled",fillcolor="#172746",color="#8ba6d8",fontcolor="#f5f7ff",penwidth="1.8",fontname="Arial",width=".72",height=".72")
    dot.attr("edge",color="#7185aa",fontcolor="#c5d3ee",fontname="Arial",fontsize="11",penwidth="1.5",arrowsize=".75")
    dot.node("__start",label="",shape="none",width="0",height="0")
    dot.edge("__start",start,color="#38bdf8",penwidth="2.5")
    for q in states:
        attrs={}
        if q in finals: attrs.update(shape="doublecircle",peripheries="2")
        if q in active: attrs.update(fillcolor="#14532d",color="#4ade80",penwidth="2.8")
        dot.node(q,**attrs)
    grouped={}
    for q in states:
        for sym in list(alphabet)+(["ε"] if "ε" in trans.get(q,{}) else []):
            for d in trans.get(q,{}).get(sym,[]):
                key=(q,d); grouped.setdefault(key,[]).append(sym)
    hot={(a,b,s) for a,b,s in used_edges}
    for (a,b), syms in grouped.items():
        label=", ".join(syms)
        is_hot=any((a,b,s) in hot for s in syms)
        dot.edge(a,b,label=label,color="#fbbf24" if is_hot else "#7185aa",fontcolor="#fde68a" if is_hot else "#c5d3ee",penwidth="3" if is_hot else "1.5")
    return dot

# ---------- Header ----------
st.markdown("""<div class="hero"><div class="hero-kicker">CSET302 · Automata Theory & Computability</div>
<div class="hero-title">🔷 Automata Studio</div><div class="hero-sub">DFA / NFA String Processing & Visualization System · Design, simulate and understand finite automata.</div></div>""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🧭 Workspace")
    st.caption("Build a machine, run an input string, and inspect its computation.")
    example_name=st.selectbox("Load an example machine",list(EXAMPLES.keys()))
    if st.button("✨ Load selected example",use_container_width=True):
        st.session_state["machine_example"]=example_name
        st.rerun()
    st.divider()
    st.markdown("### 📚 Quick guide")
    st.markdown("1. Choose DFA, NFA or ε-NFA.\n2. Define states and alphabet.\n3. Complete the transition table.\n4. Select the start and final states.\n5. Process a string and inspect the trace.")
    st.caption("Tip: In NFA cells, enter multiple destinations separated by commas.")

if "machine_example" not in st.session_state:
    st.session_state["machine_example"]=list(EXAMPLES.keys())[0]
ex=EXAMPLES[st.session_state["machine_example"]]

# Initialize editable defaults from selected example when loading.
if "loaded_example" not in st.session_state or st.session_state.loaded_example != st.session_state.machine_example:
    st.session_state.loaded_example=st.session_state.machine_example
    st.session_state.mode=ex["mode"]
    st.session_state.states_text=", ".join(ex["states"])
    st.session_state.alphabet_text=", ".join(ex["alphabet"])
    st.session_state.start_state=ex["start"]
    st.session_state.final_states=ex["final"]
    rows=[]
    for q in ex["states"]:
        row={"State":q}
        for sym in ex["alphabet"] + (["ε"] if ex["mode"]=="ε-NFA" else []):
            row[sym]=", ".join(ex["transitions"].get(q,{}).get(sym,[]))
        rows.append(row)
    st.session_state.transition_editor=pd.DataFrame(rows)

# ---------- Machine definition ----------
left,right=st.columns([.92,1.08],gap="large")
with left:
    st.markdown("### 1. 🛠️ Define the machine")
    mode=st.radio("Machine type",["DFA","NFA","ε-NFA"],horizontal=True,key="mode")
    c1,c2=st.columns(2)
    with c1: states_text=st.text_input("States Q (comma separated)",key="states_text")
    with c2: alphabet_text=st.text_input("Alphabet Σ (single characters)",key="alphabet_text")
    states=parse_csv(states_text); alphabet=parse_csv(alphabet_text)
    if mode=="ε-NFA" and "ε" not in alphabet:
        transition_symbols=alphabet+["ε"]
    else: transition_symbols=alphabet
    if mode!="ε-NFA": transition_symbols=[s for s in transition_symbols if s!="ε"]
    if not states: st.warning("Add at least one state.")
    if not alphabet: st.warning("Add at least one alphabet symbol.")
    if any(len(x)!=1 for x in alphabet): st.warning("Each alphabet symbol must be exactly one character.")
    if mode=="DFA":
        st.caption("A DFA must have exactly one destination for every state-symbol pair.")
    else:
        st.caption("For NFA cells, enter one or more destination states separated by commas. Leave blank for no transition.")
    # Rebuild table if dimensions don't match current machine definition.
    expected_cols=["State"]+transition_symbols
    current=st.session_state.get("transition_editor")
    if not isinstance(current,pd.DataFrame) or list(current.columns)!=expected_cols or len(current)!=len(states) or (len(current) and list(current["State"])!=states):
        data=[]
        for q in states:
            rr={"State":q}
            for sym in transition_symbols: rr[sym]=""
            data.append(rr)
        st.session_state.transition_editor=pd.DataFrame(data,columns=expected_cols)
    edited=st.data_editor(st.session_state.transition_editor,use_container_width=True,hide_index=True,
        column_config={"State":st.column_config.TextColumn("State",disabled=True)},key="transition_table")
    st.session_state.transition_editor=edited
    s1,s2=st.columns(2)
    with s1:
        start=st.selectbox("→ Start state",states if states else ["-"],key="start_state")
    with s2:
        finals=st.multiselect("★ Accepting state(s)",states,default=[x for x in st.session_state.final_states if x in states],key="final_states")
    st.markdown("<div class='small-muted'>The start arrow marks the initial state. Double circles indicate accepting states.</div>",unsafe_allow_html=True)

    trans={q:{} for q in states}
    errors=[]
    for _,r in edited.iterrows():
        q=str(r["State"])
        for sym in transition_symbols:
            raw=str(r.get(sym,"")).strip()
            dest=parse_csv(raw)
            for d in dest:
                if d not in states: errors.append(f"{q} on '{sym}' points to unknown state '{d}'.")
            if mode=="DFA" and sym in alphabet and len(dest)!=1:
                errors.append(f"DFA requires exactly one destination for {q} on '{sym}'.")
            trans.setdefault(q,{})[sym]=dest
    if mode=="DFA" and not errors and states and alphabet:
        st.success("Machine definition looks valid.")
    elif errors:
        st.warning("Check the transition table before running the machine.")
        for e in errors[:5]: st.caption("• "+e)

with right:
    st.markdown("### 2. 🗺️ State diagram")
    valid_machine=bool(states and alphabet and start in states and not errors and all(len(x)==1 for x in alphabet))
    if valid_machine:
        st.graphviz_chart(make_graph(states,alphabet,trans,start,finals),use_container_width=True)
        st.markdown("<div class='small-muted'>🔵 Start state &nbsp;&nbsp; 🟢 Active state &nbsp;&nbsp; ◎ Accepting state</div>",unsafe_allow_html=True)
    else:
        st.info("Complete a valid machine definition to display its state diagram.")
    with st.expander("📖 Formal definition"):
        st.code(f"{mode}  M = (Q, Σ, δ, q₀, F)\nQ = {{{', '.join(states)}}}\nΣ = {{{', '.join(alphabet)}}}\nq₀ = {start}\nF = {{{', '.join(finals)}}}",language="text")

st.divider()
st.markdown("### 3. ▶️ Process a string")
col_in,col_btn=st.columns([4,1])
with col_in: word=st.text_input("Input string (leave empty for ε)",value="110101",key="input_word",placeholder="e.g. 0101")
with col_btn:
    st.write("")
    run=st.button("🚀 Run string",use_container_width=True)
if run:
    if not valid_machine:
        st.error("Please fix the machine definition first.")
    elif any(ch not in alphabet for ch in word):
        st.error("Input contains a symbol outside the alphabet.")
    elif mode=="DFA" and any(len(trans[q].get(sym,[]))!=1 for q in states for sym in alphabet):
        st.error("DFA is incomplete. Add exactly one transition for every state and alphabet symbol.")
    else:
        trace,active,accepted,error=simulate(mode,states,alphabet,start,finals,trans,word)
        st.session_state.last_run={"trace":trace,"active":active,"accepted":accepted,"word":word,"mode":mode,"states":states,"alphabet":alphabet,"trans":trans,"start":start,"finals":finals}
        st.session_state.last_step=len(trace)-1
        if error: st.error(error)
last=st.session_state.get("last_run")
if last:
    trace=last["trace"]
    step=st.slider("Step through computation",0,len(trace)-1,value=min(st.session_state.get("last_step",len(trace)-1),len(trace)-1),key="step_slider")
    st.session_state.last_step=step
    current_row=trace[step]
    st.markdown(f"<div class='panel'><b>Step {current_row['Step']} of {len(trace)-1}</b> &nbsp; · &nbsp; Read: <b>{current_row['Read']}</b> &nbsp; · &nbsp; Active state(s): <b>{current_row['Active state(s)']}</b><br><span class='small-muted'>Remaining input: {current_row['Remaining input'] or 'ε'} &nbsp; | &nbsp; {current_row['Transition applied']}</span></div>",unsafe_allow_html=True)
    if last["accepted"]:
        st.success(f"✅ ACCEPTED — all input is read and the machine ends in accepting state(s): {', '.join(sorted(last['active'] & set(last['finals'])))}.")
    else:
        st.error("❌ REJECTED — the input is fully processed, but no accepting state is active.")
    m1,m2,m3=st.columns(3)
    with m1: st.markdown(f"<div class='metric'><div class='metric-label'>Machine</div><div class='metric-value'>{last['mode']}</div></div>",unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric'><div class='metric-label'>Input length</div><div class='metric-value'>{len(last['word'])}</div></div>",unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric'><div class='metric-label'>Final active states</div><div class='metric-value'>{len(last['active'])}</div></div>",unsafe_allow_html=True)
    st.markdown("### 4. 🧾 Step-by-step trace")
    st.caption("Each row applies the transition function to the current active state set.")
    st.dataframe(pd.DataFrame(trace),use_container_width=True,hide_index=True)
    st.markdown("### 5. 🧵 Computation path")
    used=[]
    for row in trace[1:]:
        if row["Transition applied"] not in ("No transition","No active state"):
            # Highlight actual transition edges based on transition text.
            for part in row["Transition applied"].split("; "):
                if " --" in part and "-->" in part:
                    a,rest=part.split(" --",1); sym,b=rest.split("-->",1); used.append((a,b.strip(),sym))
    st.graphviz_chart(make_graph(last["states"],last["alphabet"],last["trans"],last["start"],last["finals"],last["active"],used),use_container_width=True)
    st.download_button("⬇️ Download trace as CSV",pd.DataFrame(trace).to_csv(index=False).encode("utf-8"),file_name="automata_trace.csv",mime="text/csv")
else:
    st.info("Enter an input string and click **Run string** to see the result, processing trace and computation path.")

st.divider()
st.markdown("<div style='text-align:center;color:#8294b8;font-size:.82rem;padding:.5rem'>Automata Studio · Educational simulator for finite automata · Built with Python & Streamlit</div>",unsafe_allow_html=True)
