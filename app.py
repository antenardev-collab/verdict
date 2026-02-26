import streamlit as st
from openai import OpenAI
from judge_prompts import build_judge_prompt, build_round_summary, get_stickman_state

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Verdict",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'Source Serif 4', serif;
    background-color: #1a1208;
    color: #f0e6c8;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif;
}

.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 900;
    text-align: center;
    color: #d4a843;
    text-shadow: 2px 2px 8px rgba(212,168,67,0.3);
    margin-bottom: 0.2rem;
}

.subtitle {
    text-align: center;
    color: #a08060;
    font-style: italic;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

.stickman-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 1rem 0;
    min-height: 180px;
}

.verdict-box {
    background: linear-gradient(135deg, #2a1f0a, #1a1208);
    border: 1px solid #d4a843;
    border-radius: 8px;
    padding: 2rem;
    margin: 1rem 0;
    font-style: italic;
    line-height: 1.8;
    white-space: pre-wrap;
    box-shadow: 0 0 20px rgba(212,168,67,0.1);
}

.round-badge {
    display: inline-block;
    background: #d4a843;
    color: #1a1208;
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.participant-card {
    background: #2a1f0a;
    border-left: 3px solid #d4a843;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 0 8px 8px 0;
}

.stButton > button {
    background: #d4a843 !important;
    color: #1a1208 !important;
    font-family: 'Playfair Display', serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0.6rem 2rem !important;
    font-size: 1rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: #e8c060 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(212,168,67,0.3) !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #2a1f0a !important;
    color: #f0e6c8 !important;
    border-color: #5a4020 !important;
}

.stNumberInput > div > div > input {
    background-color: #2a1f0a !important;
    color: #f0e6c8 !important;
}

.intensity-bar-container {
    background: #2a1f0a;
    border-radius: 10px;
    height: 12px;
    margin: 0.5rem 0 1rem 0;
    overflow: hidden;
    border: 1px solid #5a4020;
}

.suffering-label {
    font-size: 0.85rem;
    color: #a08060;
    margin-bottom: 0.2rem;
}

hr {
    border-color: #5a4020 !important;
}

.gavel-emoji {
    font-size: 2rem;
    text-align: center;
    display: block;
}
</style>
""", unsafe_allow_html=True)


# ── Stickman SVG Animations ───────────────────────────────────────────────────
def get_stickman_svg(state):
    """Returns SVG stickman in different emotional states"""

    if state == "composed":
        return """
        <div class="stickman-container">
        <svg width="120" height="180" viewBox="0 0 120 180" xmlns="http://www.w3.org/2000/svg">
          <style>
            .stick { stroke: #d4a843; stroke-width: 3; stroke-linecap: round; fill: none; }
            .head { stroke: #d4a843; stroke-width: 3; fill: #2a1f0a; }
            @keyframes slight-sway { 0%,100%{transform:rotate(-1deg)} 50%{transform:rotate(1deg)} }
            .body-group { transform-origin: 60px 90px; animation: slight-sway 3s ease-in-out infinite; }
          </style>
          <g class="body-group">
            <circle class="head" cx="60" cy="30" r="20"/>
            <!-- calm face -->
            <line class="stick" x1="52" y1="28" x2="56" y2="28"/>
            <line class="stick" x1="64" y1="28" x2="68" y2="28"/>
            <path class="stick" d="M52 38 Q60 43 68 38"/>
            <!-- body -->
            <line class="stick" x1="60" y1="50" x2="60" y2="110"/>
            <!-- arms - relaxed -->
            <line class="stick" x1="60" y1="65" x2="30" y2="85"/>
            <line class="stick" x1="60" y1="65" x2="90" y2="85"/>
            <!-- legs -->
            <line class="stick" x1="60" y1="110" x2="40" y2="150"/>
            <line class="stick" x1="60" y1="110" x2="80" y2="150"/>
            <!-- gavel in right hand -->
            <line class="stick" x1="90" y1="85" x2="105" y2="70" stroke="#d4a843" stroke-width="4"/>
            <rect x="100" y="60" width="16" height="8" fill="#d4a843" rx="2"/>
          </g>
          <text x="60" y="175" text-anchor="middle" fill="#a08060" font-size="11" font-style="italic">...fine. I'll do it.</text>
        </svg>
        </div>"""

    elif state == "concerned":
        return """
        <div class="stickman-container">
        <svg width="140" height="190" viewBox="0 0 140 190" xmlns="http://www.w3.org/2000/svg">
          <style>
            .stick { stroke: #d4a843; stroke-width: 3; stroke-linecap: round; fill: none; }
            .head { stroke: #d4a843; stroke-width: 3; fill: #2a1f0a; }
            @keyframes head-shake { 0%,100%{transform:rotate(0deg)} 25%{transform:rotate(-5deg)} 75%{transform:rotate(5deg)} }
            .head-g { transform-origin: 65px 30px; animation: head-shake 1.5s ease-in-out infinite; }
          </style>
          <g class="head-g">
            <circle class="head" cx="65" cy="30" r="20"/>
            <!-- worried face -->
            <line class="stick" x1="57" y1="25" x2="61" y2="28"/>
            <line class="stick" x1="73" y1="25" x2="69" y2="28"/>
            <path class="stick" d="M57 40 Q65 37 73 40"/>
            <!-- sweat drop -->
            <ellipse cx="85" cy="20" rx="4" ry="6" fill="#4a8fa8" opacity="0.7"/>
          </g>
          <!-- body slightly slouched -->
          <line class="stick" x1="65" y1="50" x2="63" y2="112"/>
          <!-- one hand on forehead -->
          <line class="stick" x1="64" y1="68" x2="40" y2="55"/>
          <line class="stick" x1="40" y1="55" x2="55" y2="45"/>
          <line class="stick" x1="64" y1="68" x2="90" y2="88"/>
          <line class="stick" x1="63" y1="112" x2="43" y2="155"/>
          <line class="stick" x1="63" y1="112" x2="83" y2="155"/>
          <text x="70" y="180" text-anchor="middle" fill="#a08060" font-size="11" font-style="italic">...again? Really?</text>
        </svg>
        </div>"""

    elif state == "suffering":
        return """
        <div class="stickman-container">
        <svg width="150" height="200" viewBox="0 0 150 200" xmlns="http://www.w3.org/2000/svg">
          <style>
            .stick { stroke: #d4a843; stroke-width: 3; stroke-linecap: round; fill: none; }
            .head { stroke: #d4a843; stroke-width: 3; fill: #2a1f0a; }
            @keyframes droop { 0%,100%{transform:translateY(0)} 50%{transform:translateY(5px)} }
            .whole { animation: droop 2s ease-in-out infinite; }
          </style>
          <g class="whole">
            <circle class="head" cx="65" cy="40" r="20"/>
            <!-- suffering face -->
            <path class="stick" d="M55 30 Q58 27 61 30"/>
            <path class="stick" d="M69 30 Q72 27 75 30"/>
            <path class="stick" d="M55 45 Q65 40 75 45"/>
            <!-- tears -->
            <ellipse cx="54" cy="40" rx="3" ry="5" fill="#4a8fa8" opacity="0.6"/>
            <ellipse cx="76" cy="40" rx="3" ry="5" fill="#4a8fa8" opacity="0.6"/>
            <!-- slumped body -->
            <line class="stick" x1="65" y1="60" x2="60" y2="120"/>
            <!-- arms drooping -->
            <line class="stick" x1="63" y1="75" x2="35" y2="100"/>
            <line class="stick" x1="63" y1="75" x2="88" y2="105"/>
            <!-- legs -->
            <line class="stick" x1="60" y1="120" x2="40" y2="162"/>
            <line class="stick" x1="60" y1="120" x2="78" y2="162"/>
            <!-- gavel dropped on floor -->
            <line class="stick" x1="88" y1="155" x2="110" y2="165" stroke="#d4a843" stroke-width="4"/>
            <rect x="106" y="158" width="16" height="8" fill="#d4a843" rx="2"/>
          </g>
          <text x="70" y="190" text-anchor="middle" fill="#a08060" font-size="11" font-style="italic">WHY is this my life...</text>
        </svg>
        </div>"""

    elif state == "crisis":
        return """
        <div class="stickman-container">
        <svg width="160" height="200" viewBox="0 0 160 200" xmlns="http://www.w3.org/2000/svg">
          <style>
            .stick { stroke: #d4a843; stroke-width: 3; stroke-linecap: round; fill: none; }
            .head { stroke: #d4a843; stroke-width: 3; fill: #2a1f0a; }
            @keyframes crisis-shake { 0%,100%{transform:rotate(0deg) translate(0,0)} 25%{transform:rotate(-8deg) translate(-3px,0)} 75%{transform:rotate(8deg) translate(3px,0)} }
            .crisis-body { transform-origin: 70px 100px; animation: crisis-shake 0.4s ease-in-out infinite; }
          </style>
          <g class="crisis-body">
            <circle class="head" cx="70" cy="35" r="20"/>
            <!-- crisis face - spiral eyes -->
            <path class="stick" d="M58 30 Q61 27 64 30 Q61 33 58 30"/>
            <path class="stick" d="M76 30 Q79 27 82 30 Q79 33 76 30"/>
            <path class="stick" d="M57 44 Q70 35 83 44"/>
            <!-- arms raised to sky -->
            <line class="stick" x1="70" y1="55" x2="68" y2="115"/>
            <line class="stick" x1="69" y1="72" x2="38" y2="45"/>
            <line class="stick" x1="69" y1="72" x2="100" y2="45"/>
            <line class="stick" x1="68" y1="115" x2="48" y2="158"/>
            <line class="stick" x1="68" y1="115" x2="88" y2="158"/>
            <!-- lightning bolts of stress -->
            <path d="M105 50 L112 60 L108 60 L115 72" stroke="#d4a843" stroke-width="2" fill="none" opacity="0.7"/>
            <path d="M25 55 L32 65 L28 65 L35 77" stroke="#d4a843" stroke-width="2" fill="none" opacity="0.7"/>
          </g>
          <text x="75" y="192" text-anchor="middle" fill="#c04040" font-size="11" font-style="italic">I CANNOT DO THIS ANYMORE</text>
        </svg>
        </div>"""

    else:  # walkout
        return """
        <div class="stickman-container">
        <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <style>
            .stick { stroke: #d4a843; stroke-width: 3; stroke-linecap: round; fill: none; }
            .head { stroke: #d4a843; stroke-width: 3; fill: #2a1f0a; }
            @keyframes walk-out { 0%{transform:translateX(0)} 100%{transform:translateX(120px)} }
            @keyframes leg1 { 0%,100%{transform:rotate(20deg)} 50%{transform:rotate(-20deg)} }
            @keyframes leg2 { 0%,100%{transform:rotate(-20deg)} 50%{transform:rotate(20deg)} }
            .walker { animation: walk-out 3s ease-in forwards; transform-origin: 40px 100px; }
          </style>
          <!-- abandoned gavel on floor -->
          <line x1="60" y1="155" x2="90" y2="162" stroke="#d4a843" stroke-width="4" opacity="0.4"/>
          <rect x="86" y="155" width="16" height="8" fill="#d4a843" rx="2" opacity="0.4"/>
          <text x="73" y="148" text-anchor="middle" fill="#5a4020" font-size="9" font-style="italic">*left behind*</text>

          <g class="walker">
            <circle class="head" cx="40" cy="35" r="18"/>
            <!-- determined/done face -->
            <line class="stick" x1="33" y1="32" x2="37" y2="32"/>
            <line class="stick" x1="43" y1="32" x2="47" y2="32"/>
            <line class="stick" x1="33" y1="41" x2="47" y2="41"/>
            <!-- body walking -->
            <line class="stick" x1="40" y1="53" x2="38" y2="110"/>
            <!-- arms in walking motion -->
            <line class="stick" x1="39" y1="70" x2="15" y2="90"/>
            <line class="stick" x1="39" y1="70" x2="60" y2="60"/>
            <!-- walking legs -->
            <line class="stick" x1="38" y1="110" x2="22" y2="155"/>
            <line class="stick" x1="38" y1="110" x2="55" y2="148"/>
          </g>
          <text x="100" y="185" text-anchor="middle" fill="#c04040" font-size="12" font-weight="bold" font-style="italic">GOODBYE. FOREVER.</text>
        </svg>
        </div>"""


# ── Session State Init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "phase": "setup",           # setup | collect | reveal | next_round | final
        "num_participants": 3,
        "num_rounds": 5,
        "participant_names": [],
        "topics": [],
        "current_round": 1,
        "arguments": {},            # {round: {name: argument}}
        "verdicts": {},             # {round: verdict_text}
        "round_summaries": [],      # compressed history
        "current_arguments": {},    # {name: argument} for current round
        "submitted_participants": set(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── OpenAI Client ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_openai_client():
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def get_verdict(round_number, total_rounds, topic, participants_arguments, previous_rounds_summary):
    client = get_openai_client()
    if not client:
        return "⚠️ OpenAI API key not found. Please add OPENAI_API_KEY to your Streamlit secrets."

    prompt = build_judge_prompt(
        round_number=round_number,
        total_rounds=total_rounds,
        topic=topic,
        participants_arguments=participants_arguments,
        previous_rounds_summary="\n".join(previous_rounds_summary) if previous_rounds_summary else ""
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error calling OpenAI: {str(e)}"


# ── PHASE: SETUP ──────────────────────────────────────────────────────────────
def render_setup():
    st.markdown('<div class="main-title">⚖️ Verdict</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">The ultimate judge of everything that matters</div>', unsafe_allow_html=True)

    st.markdown(get_stickman_svg("composed"), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎮 Game Setup")
    st.markdown("*Configure your rounds of suffering below:*")

    col1, col2 = st.columns(2)
    with col1:
        num_p = st.number_input("Number of Participants", min_value=2, max_value=20, value=3, step=1)
    with col2:
        num_r = st.number_input("Number of Rounds", min_value=1, max_value=7, value=5, step=1)

    st.markdown("#### 👥 Participant Names")
    names = []
    cols = st.columns(2)
    for i in range(int(num_p)):
        with cols[i % 2]:
            name = st.text_input(f"Participant {i+1}", value=f"Player {i+1}", key=f"name_{i}")
            names.append(name)

    st.markdown("#### 🎯 Round Topics")
    st.caption("*Suggest topics that people are culturally proud of — food, dress, festivals, language, etc.*")
    topics = []
    for i in range(int(num_r)):
        topic = st.text_input(f"Round {i+1} Topic", value=["Food", "Dress", "Festival", "Language", "Weekend Ritual", "Music", "Morning Routine"][i] if i < 7 else f"Topic {i+1}", key=f"topic_{i}")
        topics.append(topic)

    st.markdown("")
    if st.button("⚖️ Summon the Judge", use_container_width=True):
        if all(names) and all(topics):
            st.session_state.num_participants = int(num_p)
            st.session_state.num_rounds = int(num_r)
            st.session_state.participant_names = names
            st.session_state.topics = topics
            st.session_state.phase = "collect"
            st.session_state.current_round = 1
            st.session_state.current_arguments = {}
            st.session_state.submitted_participants = set()
            st.rerun()
        else:
            st.error("Please fill in all participant names and topics!")


# ── PHASE: COLLECT ARGUMENTS ──────────────────────────────────────────────────
def render_collect():
    round_num = st.session_state.current_round
    total_rounds = st.session_state.num_rounds
    topic = st.session_state.topics[round_num - 1]
    names = st.session_state.participant_names
    submitted = st.session_state.submitted_participants

    st.markdown('<div class="main-title">⚖️ Verdict</div>', unsafe_allow_html=True)
    ratio = round_num / total_rounds
    bar_color = f"hsl({int(120 - ratio * 120)}, 70%, 50%)"
    st.markdown(f'<div class="round-badge">Round {round_num} of {total_rounds} — {topic}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="suffering-label">Judge\'s suffering intensity:</div>', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="intensity-bar-container">
            <div style="background: {bar_color}; height: 100%; width: {int(ratio*100)}%; border-radius: 10px; transition: width 0.5s;"></div>
        </div>
    """, unsafe_allow_html=True)

    state = get_stickman_state(round_num, total_rounds)
    st.markdown(get_stickman_svg(state), unsafe_allow_html=True)

    st.markdown(f"### 📝 Round {round_num}: **{topic}**")
    st.markdown(f"*Each participant — argue why YOUR culture's {topic.lower()} is the best in the world. The judge will suffer through all of it.*")
    st.markdown("---")

    # Show input for each participant
    for name in names:
        if name in submitted:
            st.markdown(f'<div class="participant-card">✅ <strong>{name}</strong> — argument submitted!</div>', unsafe_allow_html=True)
        else:
            with st.expander(f"🎤 {name} — Submit your argument", expanded=(name not in submitted)):
                arg = st.text_area(
                    f"Why is your {topic.lower()} the best in the world?",
                    placeholder=f"Make your case, {name}! Be passionate. Be bold. The judge will suffer either way.",
                    key=f"arg_{round_num}_{name}",
                    height=100
                )
                if st.button(f"Submit {name}'s argument", key=f"submit_{round_num}_{name}"):
                    if arg.strip():
                        st.session_state.current_arguments[name] = arg.strip()
                        st.session_state.submitted_participants.add(name)
                        st.rerun()
                    else:
                        st.warning("Please write something! Even the judge deserves a proper argument to suffer through.")

    # Check if all submitted
    all_submitted = all(name in submitted for name in names)
    if all_submitted:
        st.markdown("---")
        st.success(f"✅ All {len(names)} participants have submitted! Ready to summon the judge's verdict?")
        if st.button("⚖️ Reveal the Verdict!", use_container_width=True):
            st.session_state.phase = "reveal"
            st.rerun()


# ── PHASE: REVEAL VERDICT ─────────────────────────────────────────────────────
def render_reveal():
    round_num = st.session_state.current_round
    total_rounds = st.session_state.num_rounds
    topic = st.session_state.topics[round_num - 1]
    is_final = round_num == total_rounds

    st.markdown('<div class="main-title">⚖️ Verdict</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="round-badge">{"🚨 FINAL ROUND" if is_final else f"Round {round_num} of {total_rounds}"} — {topic}</div>', unsafe_allow_html=True)

    # Show appropriate stickman
    state = get_stickman_state(round_num, total_rounds)
    st.markdown(get_stickman_svg(state), unsafe_allow_html=True)

    # Generate or retrieve verdict
    if round_num not in st.session_state.verdicts:
        with st.spinner("The judge is suffering through your arguments... please wait..."):
            verdict = get_verdict(
                round_number=round_num,
                total_rounds=total_rounds,
                topic=topic,
                participants_arguments=st.session_state.current_arguments,
                previous_rounds_summary=st.session_state.round_summaries
            )
            st.session_state.verdicts[round_num] = verdict

            # Save compressed summary for history
            summary = build_round_summary(round_num, topic, st.session_state.current_arguments)
            st.session_state.round_summaries.append(summary)

    verdict = st.session_state.verdicts[round_num]
    st.markdown(f'<div class="verdict-box">{verdict}</div>', unsafe_allow_html=True)

    st.markdown("---")

    if is_final:
        st.markdown("### 🎭 The Judge Has Left The Building.")
        st.markdown("*Thank you for making an AI suffer through this competition. We hope you enjoyed it more than the judge did.*")
        if st.button("🔄 Start a New Game", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        if st.button(f"➡️ Proceed to Round {round_num + 1}", use_container_width=True):
            st.session_state.current_round += 1
            st.session_state.current_arguments = {}
            st.session_state.submitted_participants = set()
            st.session_state.phase = "collect"
            st.rerun()


# ── MAIN ROUTER ───────────────────────────────────────────────────────────────
phase = st.session_state.phase

if phase == "setup":
    render_setup()
elif phase == "collect":
    render_collect()
elif phase == "reveal":
    render_reveal()
