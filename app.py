import json
from streamlit_local_storage import LocalStorage
import streamlit as st
import pandas as pd
import re
import plotly.graph_objects as go
import time

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Πορεία προς το Πτυχίο", page_icon="🎓", layout="wide"

# --- BOOT-UP SEQUENCE (TRUE SPLASH SCREEN) ---
if 'boot_sequence_done' not in st.session_state:
    boot_placeholder = st.empty()
    
    boot_placeholder.markdown("""
    <style>
    .boot-overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #05070a; z-index: 9999999;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        font-family: 'Share Tech Mono', Consolas, monospace; color: #00ffcc;
        animation: hide-boot 0.5s ease-in 3.8s forwards; 
    }
    
    @keyframes hide-boot {
        0% { opacity: 1; }
        100% { opacity: 0; visibility: hidden; }
    }
    
    .boot-ascii {
        font-size: 16px; line-height: 1.2; white-space: pre; text-align: center;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.8); margin-bottom: 25px;
    }
    
    .boot-terminal {
        width: 480px; font-size: 1.1rem; line-height: 1.6;
        text-shadow: 0 0 5px rgba(0, 255, 204, 0.5); text-align: left;
    }
    
    .t-line { overflow: hidden; white-space: nowrap; opacity: 0; }
    .l1 { animation: type-line 0.4s steps(30, end) 0.5s forwards; }
    .l2 { animation: type-line 0.4s steps(30, end) 1.5s forwards; }
    .l3 { animation: type-line 0.4s steps(30, end) 2.5s forwards; }
    .l4 { animation: type-line 0.4s steps(30, end) 3.5s forwards; color: #2ecc71; text-shadow: 0 0 10px #2ecc71;}
    
    @keyframes type-line {
        0% { width: 0; opacity: 1; }
        100% { width: 100%; opacity: 1; }
    }
    </style>
    
    <div class="boot-overlay">
        <div class="boot-ascii">
     _    _   ____    _____ 
    | |  | | / __ \  |_   _|
    | |  | || |  | |   | |  
    | |__| || |__| |  _| |_ 
     \____/  \____/  |_____|
    --- MAINFRAME LINK ---
        </div>
        <div class="boot-terminal">
            <div class="t-line l1">> INITIALIZING SYSTEM...</div>
            <div class="t-line l2">> CONNECTING TO UOI NETWORK [||||||||||]</div>
            <div class="t-line l3">> DECRYPTING ACADEMIC RECORDS... OK.</div>
            <div class="t-line l4">> ACCESS GRANTED. WELCOME, MERCENARY.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Σταματάμε το Streamlit για 4.2 δευτερόλεπτα ώστε να παίξει το Animation ανενόχλητο!
    time.sleep(4.2)
    # Καθαρίζουμε την οθόνη εκκίνησης και προχωράμε
    boot_placeholder.empty()
    st.session_state.boot_sequence_done = True

# --- SAVE ENGINE & MEMORY INITIALIZATION ---
localS = LocalStorage()

# Αρχικοποίηση των μεταβλητών στο session_state (αν δεν υπάρχουν)
if 'unlocked_themes' not in st.session_state:
    st.session_state.unlocked_themes = []
if 'boss_milestones' not in st.session_state:
    st.session_state.boss_milestones = [False, False, False, False]
if 'memory_notes' not in st.session_state:
    st.session_state.memory_notes = ""
if 'active_theme' not in st.session_state:
    st.session_state.active_theme = "Cyberpunk (Cyan)"

# Προσωρινές μεταβλητές για το Simulator (ΔΕΝ σώζονται στο .sav)
if 'sim_thesis_grade' not in st.session_state:
    st.session_state.sim_thesis_grade = 9.0
if 'loadout_missions' not in st.session_state:
    st.session_state.loadout_missions = []

# Αόρατο Auto-Load από τον Browser
if 'browser_load_attempted' not in st.session_state:
    saved_state = localS.getItem("mercenary_save")
    if saved_state:
        try:
            parsed_state = json.loads(saved_state)
            st.session_state.unlocked_themes = parsed_state.get('themes', [])
            st.session_state.boss_milestones = parsed_state.get('boss', [False]*4)
            st.session_state.memory_notes = parsed_state.get('notes', "")
            st.session_state.active_theme = parsed_state.get('active_theme', "Cyberpunk (Cyan)")
        except:
            pass
    st.session_state.browser_load_attempted = True

# --- HUD (SIDEBAR) ---
with st.sidebar:
    # Στήνουμε 5 "αόρατα" κουτιά για να κλειδώσουμε την ακριβή σειρά!
    sidebar_top = st.container()
    hud_container = sidebar_top.container()
    time_machine_container = sidebar_top.container()
    sidebar_mid = st.container()
    sidebar_bot = st.container()

# Το Inventory μπαίνει στο μεσαίο κουτί
with sidebar_mid:
    st.markdown("---")
    st.header("🎒 Inventory")
    st.markdown("Φόρτωσε το αρχείο Excel (**H καρτέλα μου - Όλα τα μαθήματα.xlsx**) από το ClassWeb.")
    
    uploaded_file = st.file_uploader("Drop Excel File", type=['xlsx'])

    if uploaded_file is not None:
        st.success("✅ Το αρχείο αναλύθηκε με επιτυχία!")

    # --- 💾 MEMORY CARD (SAVE / LOAD STATE) ---
    st.markdown("---")
    st.markdown("<h4 style='color: #bdc3c7; font-family: monospace; font-size: 1rem;'>💾 Memory Card</h4>", unsafe_allow_html=True)
    st.markdown("<div style='color: #7f8c8d; font-size: 1rem; margin-bottom: -45px;'>Αποθήκευσε/φόρτωσε την πρόοδό σου (Theme, Notes, Boss HP).</div>", unsafe_allow_html=True)    
    
    # 1. Συγκέντρωση των δεδομένων (ΜΟΝΟ μόνιμα στοιχεία)
    current_state = {
        'themes': st.session_state.unlocked_themes,
        'boss': st.session_state.boss_milestones,
        'notes': st.session_state.memory_notes,
        'active_theme': st.session_state.active_theme
    }
    state_json = json.dumps(current_state)
    
    # 2. Αόρατο Auto-Save στον Browser (ενημερώνεται σε κάθε αλλαγή)
    localS.setItem("mercenary_save", state_json)
    
    # 3. Manual Export (Λήψη αρχείου .sav)
    st.download_button(
        label="⬇️ Export Save (.sav)",
        data=state_json,
        file_name="player_state.sav",
        mime="application/json",
        use_container_width=True
    )
    
    # 4. Manual Import (Ανέβασμα αρχείου .sav)
    uploaded_save = st.file_uploader("Upload Save (.sav)", type=['sav'], label_visibility="collapsed")
    if uploaded_save is not None and 'manual_load_done' not in st.session_state:
        try:
            loaded_data = json.load(uploaded_save)
            st.session_state.unlocked_themes = loaded_data.get('themes', [])
            st.session_state.boss_milestones = loaded_data.get('boss', [False]*4)
            st.session_state.memory_notes = loaded_data.get('notes', "")
            st.session_state.active_theme = loaded_data.get('active_theme', "Cyberpunk (Cyan)")
            st.session_state.manual_load_done = True
            st.success("✅ Save Loaded!")
            st.rerun()
        except Exception as e:
            st.error("Corrupted Save!")

    # --- 🎨 GLOBAL NEON CUSTOMIZER ---
    st.markdown("---")
    st.markdown("<h4 style='color: #bdc3c7; font-family: monospace; font-size: 1rem;'>🎨 UI Theme Override</h4>", unsafe_allow_html=True)
    
    theme_options = {
        "Cyberpunk (Cyan)": {"hex": "#00ffcc", "rgba": "rgba(0, 255, 204, "},
        "Matrix (Green)": {"hex": "#00ff00", "rgba": "rgba(0, 255, 0, "},
        "Sith (Red)": {"hex": "#ff003c", "rgba": "rgba(255, 0, 60, "},
        "Synthwave (Pink)": {"hex": "#ff007f", "rgba": "rgba(255, 0, 127, "},
        "Hacker (Amber)": {"hex": "#ffb000", "rgba": "rgba(255, 176, 0, "}
    }
    
    if "metal" in st.session_state.unlocked_themes:
        theme_options["Heavy Metal (Blood Red)"] = {"hex": "#9e0000", "rgba": "rgba(158, 0, 0, "}
    if "arcade" in st.session_state.unlocked_themes:
        theme_options["Retro 8-Bit (Arcade Orange)"] = {"hex": "#ff5500", "rgba": "rgba(255, 85, 0, "}
    if "johto" in st.session_state.unlocked_themes:
        theme_options["Johto Edition (Legendary Gold)"] = {"hex": "#ffd700", "rgba": "rgba(255, 215, 0, "}
        
    # Εύρεση του index για να διαβάζει σωστά το φορτωμένο theme
    theme_list = list(theme_options.keys())
    try:
        def_index = theme_list.index(st.session_state.active_theme)
    except ValueError:
        def_index = 0
        
    # Το κλειδί "key" λέει στο Streamlit να σώζει την επιλογή απευθείας στο st.session_state.active_theme
    selected_theme = st.selectbox("Επίλεξε Χρωματικό Προφίλ:", options=theme_list, index=def_index, key="active_theme", label_visibility="collapsed")
    
    primary_color = theme_options[selected_theme]["hex"]
    primary_rgba = theme_options[selected_theme]["rgba"]

# --- ΚΕΝΤΡΙΚΗ ΟΘΟΝΗ ---
st.markdown(f"""
<style>
/* Εισαγωγή γραμματοσειράς 'Share Tech Mono' */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

.terminal-container {{
    display: inline-block;
    max-width: 100%;
}}

.typewriter-text {{
    font-family: 'Share Tech Mono', Consolas, 'Courier New', monospace;
    color: {primary_color}; 
    text-shadow: 0px 0px 8px {primary_rgba}0.6);
    font-size: 2.2rem;
    white-space: nowrap;
    overflow: hidden;
    border-right: 0.15em solid {primary_color}; 
    animation: typing 2.5s steps(45, end), blink-caret 0.75s step-end infinite;
    margin-bottom: 20px;
}}

@keyframes typing {{
    from {{ width: 0; }}
    to {{ width: 100%; }}
}}

@keyframes blink-caret {{
    from, to {{ border-color: transparent; }}
    50% {{ border-color: {primary_color}; }}
}}
</style>

<div class="terminal-container">
    <div class="typewriter-text">root@cse-uoi:~$ ./Πορεία_προς_το_Πτυχίο.exe</div>
</div>
""", unsafe_allow_html=True)

# Μήνυμα αναμονής αν δεν έχει ανέβει αρχείο
if uploaded_file is None:
    st.info("👈 Πρόσβαση κλειδωμένη. Φόρτωσε το ακαδημαϊκό σου αρχείο στο Inventory (αριστερά) για να ενεργοποιηθεί το Dashboard!")

def clean_classweb_data(df):
    # Κρατάμε ΠΛΕΟΝ και τις στήλες ECTS και Κατηγορία
    df = df[['Μάθημα', 'Βαθμός', 'Εξ. περίοδος', 'Β.Π.', 'Π.Π.', 'ECTS', 'Κατηγορία']].copy()
    
    # 1. Καθαρισμός του HTML από το όνομα του μαθήματος
    df['Μάθημα'] = df['Μάθημα'].apply(lambda x: re.sub(r'<a id=.*', '', str(x)).strip())
    
    # 2. ΦΙΛΤΡΟ ΠΕΡΑΣΜΕΝΩΝ
    df = df[(df['Β.Π.'] == 'Ναι') | (df['Π.Π.'] == 'Ναι')]
    
    # 3. Καθαρισμός Βαθμού
    df = df.dropna(subset=['Βαθμός'])
    df['Βαθμός'] = pd.to_numeric(df['Βαθμός'], errors='coerce')
    df['Βαθμός'] = df['Βαθμός'].apply(lambda x: x / 10 if x > 10 else x)
    df = df[df['Βαθμός'] >= 5.0]
    
    # Μετατροπή των ECTS σε καθαρούς αριθμούς
    df['ECTS'] = pd.to_numeric(df['ECTS'], errors='coerce').fillna(0)
    
    # 4. Σπάσιμο της περιόδου
    def parse_period(text):
        text = str(text).upper()
        year_match = re.search(r'(\d{4})-(\d{4})', text)
        if year_match:
            year = f"{year_match.group(1)}-{year_match.group(2)[-2:]}"
        else:
            year = "Άγνωστο"
            
        if 'ΦΕΒΡΟΥΑΡΙΟΣ' in text or 'ΙΑΝΟΥΑΡΙΟΣ' in text:
            period = 'Φεβ'
        elif 'ΙΟΥΝΙΟΣ' in text:
            period = 'Ιουν'
        elif 'ΣΕΠΤΕΜΒΡΙΟΣ' in text:
            period = 'Σεπ'
        else:
            period = 'Άλλο'
            
        return pd.Series([year, period])
        
    df[['Ακαδ. Έτος', 'Περίοδος']] = df['Εξ. περίοδος'].apply(parse_period)
    
    return df

def create_plotly_charts(df, p_hex, p_rgba):
    detailed_data = {}
    for _, row in df.iterrows():
        key = (row['Ακαδ. Έτος'], row['Περίοδος'])
        if key not in detailed_data:
            detailed_data[key] = []
        detailed_data[key].append((row['Μάθημα'], row['Βαθμός'], row['ECTS']))

    min_year = min([int(y.split('-')[0]) for y in df['Ακαδ. Έτος'] if y != "Άγνωστο"])
    max_year = max([int(y.split('-')[0]) for y in df['Ακαδ. Έτος'] if y != "Άγνωστο"])
    
    years = [f"{y}-{str(y+1)[-2:]}" for y in range(min_year, max_year + 1)]
    periods = ['Φεβ', 'Ιουν', 'Σεπ']
    
    x_labels = []
    y_values_cum = []
    y_values_bar = []
    y_values_gpa = []
    
    hover_texts = []
    hover_texts_gpa = []
    
    current_total = 0
    cumulative_points = 0.0
    cumulative_ects = 0.0
    colors_bar = []
    
    # Global Cyberpunk Theme Configuration
    neon_grid = f'{p_rgba}0.1)'
    neon_text = '#bdc3c7'
    neon_title = p_hex
    cyber_bg = 'rgba(0,0,0,0)'
    hover_bg = '#0a0e17'
    font_family = "'Share Tech Mono', monospace"

    for year in years:
        for period in periods:
            key = (year, period)
            courses_in_period = detailed_data.get(key, [])
            
            count_regular = sum(1 for c in courses_in_period if not re.search(r'ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ|ΔΙΠΛΩΜΑΤΙΚΗ', str(c[0]), re.IGNORECASE))
            current_total += count_regular
            
            for course_name, grade, ects in courses_in_period:
                cumulative_points += grade * ects
                cumulative_ects += ects
                
            current_gpa = round(cumulative_points / cumulative_ects, 2) if cumulative_ects > 0 else None
            
            label = f"{period}<br>'{year[-2:]}"
            x_labels.append(label)
            y_values_cum.append(current_total)
            y_values_bar.append(count_regular)
            y_values_gpa.append(current_gpa)
            
            if len(courses_in_period) > 0:
                colors_bar.append(p_hex if count_regular > 0 else '#9b59b6') 
                text = f"<b>📅 {period} '{year[-2:]} ({count_regular} μαθήματα)</b><br>"
                text += "━"*30 + "<br>"
                for course_name, grade, ects in courses_in_period:
                    if re.search(r'ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ|ΔΙΠΛΩΜΑΤΙΚΗ', str(course_name), re.IGNORECASE):
                        text += f"▪ {course_name}  [{grade}] <i>({ects} XP)</i> <b style='color:#f39c12;'>[SPECIAL]</b><br>"
                    else:
                        text += f"▪ {course_name}  [{grade}] <i>({ects} XP)</i><br>"
                text_gpa = f"<b>📅 {period} '{year[-2:]}</b><br>" + "━"*15 + f"<br>Νέος Μ.Ο: <b>{current_gpa}</b>"
            else:
                colors_bar.append('rgba(255,255,255,0.05)')
                text = f"<b>📅 {period} '{year[-2:]}</b><br>" + "━"*15 + "<br>NO DATA (Σύστημα σε Αναμονή)"
                text_gpa = f"<b>📅 {period} '{year[-2:]}</b><br>" + "━"*15 + f"<br>Μ.Ο: <b>{current_gpa}</b> (Αμετάβλητος)"
                
            hover_texts.append(text)
            hover_texts_gpa.append(text_gpa)

    # --- Κοινό Update Layout Helper ---
    def apply_cyber_theme(fig, title_text, y_title):
        fig.update_layout(
            title=dict(text=f'<b>{title_text}</b>', font=dict(family=font_family, size=18, color=neon_title), x=0.5),
            paper_bgcolor=cyber_bg, plot_bgcolor=cyber_bg, font=dict(family=font_family, color=neon_text),
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(tickangle=-90, showgrid=True, gridcolor=neon_grid, zeroline=False, type='category'),
            yaxis=dict(title=dict(text=y_title, font=dict(color='#7f8c8d')), showgrid=True, gridcolor=neon_grid, zerolinecolor=neon_grid)
        )
        return fig

    # --- 1. ΑΘΡΟΙΣΤΙΚΟ ΓΡΑΦΗΜΑ (Cumulative) ---
    static_texts_cum = [f"<b>{val}</b>" if val > y_values_cum[max(0, i-1)] and i != len(y_values_cum)-1 else "" for i, val in enumerate(y_values_cum)]
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=x_labels, y=y_values_cum, mode='lines+markers+text', text=static_texts_cum, textposition='top left',
        textfont=dict(color=p_hex, size=12), hoverinfo='text', hovertext=hover_texts,
        line=dict(shape='hv', color=p_hex, width=3), marker=dict(size=8, color='#0a0e17', line=dict(color=p_hex, width=2)),
        fill='tozeroy', fillcolor=f'{p_rgba}0.1)', hoverlabel=dict(bgcolor=hover_bg, bordercolor=p_hex, font=dict(family=font_family, size=12, color='#ecf0f1'))
    ))
    fig_cum.add_annotation(
        x=x_labels[-1], y=y_values_cum[-1], text=f"<b>MAX: {y_values_cum[-1]}</b>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor=p_hex, ax=-60, ay=-40,
        bgcolor="#0a0e17", bordercolor=p_hex, borderwidth=1, borderpad=6, font=dict(family=font_family, size=14, color=p_hex)
    )
    fig_cum = apply_cyber_theme(fig_cum, "SYS.PROGRESS_TRACKER (Αθροιστικά Μαθήματα)", "Σύνολο Περασμένων")

    # --- 2. ΡΑΒΔΟΓΡΑΜΜΑ (Bar Chart) ---
    static_texts_bar = [f"<b>{val}</b>" if val > 0 else "" for val in y_values_bar]
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=x_labels, y=y_values_bar, marker_color=colors_bar, marker_line=dict(color=p_hex, width=1),
        text=static_texts_bar, textposition='outside', textfont=dict(color=p_hex, size=12),
        hoverinfo='text', hovertext=hover_texts, hoverlabel=dict(bgcolor=hover_bg, bordercolor=p_hex, font=dict(family=font_family, size=12, color='#ecf0f1'))
    ))
    fig_bar = apply_cyber_theme(fig_bar, "LOAD_HISTORY (Επιτυχίες / Εξεταστική)", "Αριθμός Μαθημάτων")

    # --- 3. ΓΡΑΦΗΜΑ ΕΞΕΛΙΞΗΣ Μ.Ο. (GPA Tracker) ---
    fig_gpa = go.Figure()
    valid_gpas = [g for g in y_values_gpa if g is not None]
    min_gpa = min(valid_gpas) - 0.2 if valid_gpas else 5.0
    max_gpa = max(valid_gpas) + 0.2 if valid_gpas else 10.0

    fig_gpa.add_trace(go.Scatter(
        x=x_labels, y=y_values_gpa, mode='lines+markers', hoverinfo='text', hovertext=hover_texts_gpa,
        line=dict(shape='spline', smoothing=0.3, color='#f1c40f', width=4), # Neon Yellow για το GPA
        marker=dict(size=10, color='#0a0e17', line=dict(color='#f1c40f', width=2)),
        fill='tozeroy', fillcolor='rgba(241, 196, 15, 0.1)',
        hoverlabel=dict(bgcolor=hover_bg, bordercolor="#f1c40f", font=dict(family=font_family, size=12, color='#ecf0f1'))
    ))
    if valid_gpas:
        fig_gpa.add_annotation(
            x=x_labels[-1], y=valid_gpas[-1], text=f"<b>GPA: {valid_gpas[-1]}</b>",
            showarrow=True, arrowhead=2, ax=-50, ay=-30, bgcolor="#111b24", bordercolor="#f1c40f", font=dict(family=font_family, color="#f1c40f")
        )
    fig_gpa = apply_cyber_theme(fig_gpa, "PERFORMANCE_RATING (GPA Tracker)", "Σταθμικός Μ.Ο.")
    fig_gpa.update_yaxes(range=[min_gpa, max_gpa])

    # --- 4. ΚΑΤΑΝΟΜΗ ΒΑΘΜΟΛΟΓΙΩΝ (Grade Distribution) ---
    grade_counts = df['Βαθμός'].value_counts().sort_index()
    dist_labels = [str(g) for g in grade_counts.index]
    dist_values = grade_counts.values
    
    fig_dist = go.Figure()
    fig_dist.add_trace(go.Bar(
        x=dist_labels, y=dist_values, marker_color='#ff007f', marker_line=dict(color='#ff007f', width=1), # Neon Pink
        text=[f"<b>{val}</b>" for val in dist_values], textposition='outside', textfont=dict(color='#ff007f', size=12),
        hoverinfo='x+y', hoverlabel=dict(bgcolor=hover_bg, bordercolor="#ff007f", font=dict(family=font_family, size=12, color='#ecf0f1'))
    ))
    fig_dist = apply_cyber_theme(fig_dist, "GRADE_DISPERSION (Κατανομή Βαθμών)", "Πλήθος")
    fig_dist.update_xaxes(showgrid=False)

    # --- 5. ΚΑΤΑΝΟΜΗ ΑΝΑ ΚΑΤΗΓΟΡΙΑ (Donut Chart) ---
    category_stats = df.groupby('Κατηγορία').agg(Total_ECTS=('ECTS', 'sum'), Course_Count=('Μάθημα', 'count')).reset_index()
    
    fig_category = go.Figure()
    fig_category.add_trace(go.Pie(
        labels=category_stats['Κατηγορία'], values=category_stats['Total_ECTS'], customdata=category_stats['Course_Count'],
        hole=0.5, textinfo='percent', textposition='inside',
        hovertemplate="<b>%{label}</b><br>%{value} XP (%{customdata} Quests)<br>%{percent}<extra></extra>",
        hoverlabel=dict(bgcolor=hover_bg, bordercolor="#bdc3c7", font=dict(family=font_family, size=12, color='#ecf0f1')),
        marker=dict(
            colors=['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6', '#00ffcc'], 
            line=dict(color='#0a0e17', width=2) # Σκούρο περίγραμμα για να χωρίζουν τα κομμάτια
        )
    ))
    fig_category.update_layout(
        title=dict(text='<b>XP_DISTRIBUTION (Κατηγορίες)</b>', font=dict(family=font_family, size=18, color=neon_title), x=0.5),
        paper_bgcolor=cyber_bg, plot_bgcolor=cyber_bg, font=dict(family=font_family, color=neon_text),
        margin=dict(l=20, r=20, t=60, b=20), showlegend=False 
    )

    # --- 6. ΣΥΣΧΕΤΙΣΗ ΒΑΘΜΟΥ - ΔΥΣΚΟΛΙΑΣ - ΧΡΟΝΟΥ (3D Scatter Plot) ---
    scatter_df = df[~df['Μάθημα'].str.contains('ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ|ΔΙΠΛΩΜΑΤΙΚΗ', case=False, na=False)].copy()
    grouped_scatter = scatter_df.groupby(['ECTS', 'Βαθμός', 'Ακαδ. Έτος']).agg(Μαθήματα=('Μάθημα', lambda x: '<br>▪ '.join(x)), Πλήθος=('Μάθημα', 'count')).reset_index()
    marker_sizes = [10 + (count * 5) for count in grouped_scatter['Πλήθος']]
    
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter3d(
        x=grouped_scatter['ECTS'], y=grouped_scatter['Βαθμός'], z=grouped_scatter['Ακαδ. Έτος'],
        mode='markers',
        marker=dict(size=marker_sizes, color=grouped_scatter['Βαθμός'], colorscale='Electric', line=dict(width=1, color='#000'), opacity=0.9),
        text="▪ " + grouped_scatter['Μαθήματα'], customdata=grouped_scatter['Πλήθος'],
        hovertemplate="<b>Year: %{z}</b><br>%{customdata} Data Nodes:<br>%{text}<br>" + "━"*15 + "<br>Grade: %{y} | XP: %{x}<extra></extra>",
        hoverlabel=dict(bgcolor=hover_bg, bordercolor="#00ffcc", font=dict(family=font_family, size=12, color='#ecf0f1'))
    ))
    
    fig_scatter.update_layout(
        title=dict(text='<b>SPATIAL_ANALYSIS (Δυσκολία vs Βαθμός vs Χρόνος)</b>', font=dict(family=font_family, size=20, color=neon_title), x=0.5),
        paper_bgcolor=cyber_bg, plot_bgcolor=cyber_bg, font=dict(family=font_family, color=neon_text),
        scene=dict(
            xaxis_title='XP (ECTS)', yaxis_title='Grade', zaxis_title='Year',
            xaxis=dict(showgrid=True, gridcolor=neon_grid, backgroundcolor="#0a0e17"),
            yaxis=dict(showgrid=True, gridcolor=neon_grid, backgroundcolor="#0a0e17", range=[4.5, 10.5]),
            zaxis=dict(showgrid=True, gridcolor=neon_grid, backgroundcolor="#0a0e17", type='category', categoryorder='array', categoryarray=years)
        ),
        margin=dict(l=0, r=0, b=0, t=60), scene_camera=dict(eye=dict(x=1.6, y=1.6, z=0.6))
    )

    return fig_cum, fig_bar, fig_gpa, fig_dist, fig_category, fig_scatter


# Main Εφαρμογή
if uploaded_file is not None:
    try:
        raw_data = pd.read_excel(uploaded_file, header=1)
        cleaned_df = clean_classweb_data(raw_data)

        # --- 1. TIME MACHINE (ΕΜΦΑΝΙΣΗ ΚΑΙ ΛΟΓΙΚΗ) ---
        period_weight = {'Φεβ': 1, 'Ιουν': 2, 'Σεπ': 3, 'Άλλο': 4}
        unique_periods = cleaned_df[['Ακαδ. Έτος', 'Περίοδος']].drop_duplicates()
        unique_periods = unique_periods[unique_periods['Ακαδ. Έτος'] != 'Άγνωστο']
        unique_periods['Weight'] = unique_periods['Περίοδος'].map(period_weight)
        unique_periods = unique_periods.sort_values(by=['Ακαδ. Έτος', 'Weight'])
        timeline_labels = [f"{row['Περίοδος']} '{row['Ακαδ. Έτος'][-2:]}" for _, row in unique_periods.iterrows()]
        
        with time_machine_container:
            st.markdown("<h3 style='color: #f1c40f; font-family: monospace; font-size: 1.1rem; margin-bottom: 5px; text-transform: uppercase;'>⏳ Time Machine</h3>", unsafe_allow_html=True)
            time_machine_on = st.toggle("Ενεργοποίηση Χρονομηχανής")
            
            if time_machine_on and timeline_labels:
                # ΕΔΩ ΛΥΝΕΤΑΙ ΤΟ BUG: Περνάμε το value ρητά και δεν βασιζόμαστε στο session state!
                selected_time = st.select_slider(
                    "Ταξίδι στο Χρόνο:",
                    options=timeline_labels,
                    value=timeline_labels[-1],
                    label_visibility="collapsed"
                )
                st.markdown(f"""
                <div style="background: repeating-linear-gradient(45deg, #2a0808, #2a0808 10px, #1a0000 10px, #1a0000 20px); border: 2px solid #e74c3c; padding: 15px; margin-bottom: 25px; border-radius: 8px; text-align: center; box-shadow: 0 0 20px rgba(231, 76, 60, 0.4); animation: pulse-danger 1.5s infinite;">
                    <span style="color: #e74c3c; font-family: monospace; font-size: 1.1rem; font-weight: bold; letter-spacing: 1px;">⚠️ TIMELINE ALTERED</span><br><br>
                    <span style="color: #ecf0f1; font-size: 0.95rem;">Προβολή Στατιστικών:<br><strong style="font-size: 1.2rem; color: #f1c40f;">{selected_time}</strong></span>
                </div>
                """, unsafe_allow_html=True)
            else:
                selected_time = timeline_labels[-1] if timeline_labels else None

        # --- 2. ΦΙΛΤΡΑΡΙΣΜΑ ΔΕΔΟΜΕΝΩΝ ΠΑΡΕΛΘΟΝΤΟΣ ---
        if time_machine_on and selected_time in timeline_labels:
            selected_idx = timeline_labels.index(selected_time)
            valid_periods = unique_periods.iloc[:selected_idx+1]
            
            cleaned_df = pd.merge(cleaned_df, valid_periods[['Ακαδ. Έτος', 'Περίοδος']], on=['Ακαδ. Έτος', 'Περίοδος'], how='inner')
            
            def parse_raw_period(text):
                text = str(text).upper()
                year_match = re.search(r'(\d{4})-(\d{4})', text)
                year = f"{year_match.group(1)}-{year_match.group(2)[-2:]}" if year_match else "Άγνωστο"
                if 'ΦΕΒΡΟΥΑΡΙΟΣ' in text or 'ΙΑΝΟΥΑΡΙΟΣ' in text: period = 'Φεβ'
                elif 'ΙΟΥΝΙΟΣ' in text: period = 'Ιουν'
                elif 'ΣΕΠΤΕΜΒΡΙΟΣ' in text: period = 'Σεπ'
                else: period = 'Άλλο'
                return pd.Series([year, period])
                
            raw_data[['Ακαδ. Έτος', 'Περίοδος']] = raw_data['Εξ. περίοδος'].apply(parse_raw_period)
            raw_data = pd.merge(raw_data, valid_periods[['Ακαδ. Έτος', 'Περίοδος']], on=['Ακαδ. Έτος', 'Περίοδος'], how='inner')

        # 6. ΚΕΝΤΡΙΚΟ WARNING BANNER ΠΑΝΩ ΑΠΟ ΤΑ TABS
        if time_machine_on:
            st.error(f"⏳ **ΠΡΟΣΟΧΗ - Η ΧΡΟΝΟΜΗΧΑΝΗ ΕΙΝΑΙ ΕΝΕΡΓΗ:** Βλέπετε το ακαδημαϊκό σας προφίλ όπως ήταν την περίοδο **{selected_time}**. Απενεργοποιήστε τη από το αριστερό μενού για να δείτε τα τρέχοντα στατιστικά σας!", icon="⚠️")

        # --- 3. ΥΠΟΛΟΓΙΣΜΟΣ UNPASSED COURSES & STATS ---
        raw_quests = raw_data.copy()
        raw_quests['Μάθημα'] = raw_quests['Μάθημα'].apply(lambda x: re.sub(r'<a id=.*', '', str(x)).strip())
        passed_courses = raw_quests[(raw_quests['Β.Π.'] == 'Ναι') | (raw_quests['Π.Π.'] == 'Ναι')]['Μάθημα'].unique()
        unpassed_df = raw_quests[~raw_quests['Μάθημα'].isin(passed_courses)].copy()
        
        if not unpassed_df.empty:
            unpassed_df = unpassed_df[~unpassed_df['Μάθημα'].str.contains('ΠΡΑΚΤΙΚΗ|ΔΙΠΛΩΜΑΤΙΚΗ|Δίκτυα Υπολογιστών Ι', case=False, na=False, regex=True)]
            unpassed_df = unpassed_df.drop_duplicates(subset=['Μάθημα'])
            unpassed_df['ECTS'] = pd.to_numeric(unpassed_df['ECTS'], errors='coerce').fillna(0)
            top_quests = unpassed_df.sort_values(by='ECTS', ascending=False).head(3)
        else:
            top_quests = pd.DataFrame()
        
        is_internship = cleaned_df['Μάθημα'].str.contains('ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ', case=False, na=False)
        is_thesis = cleaned_df['Μάθημα'].str.contains('ΔΙΠΛΩΜΑΤΙΚΗ', case=False, na=False)
        internship_df = cleaned_df[is_internship]
        thesis_df = cleaned_df[is_thesis]
        regular_courses_df = cleaned_df[~(is_internship | is_thesis)].copy()
        
        total_courses = len(regular_courses_df) 
        total_ects = cleaned_df['ECTS'].sum() 
        target_courses = 47
        
        if total_ects > 0:
            final_gpa = (cleaned_df['Βαθμός'] * cleaned_df['ECTS']).sum() / total_ects
        else:
            final_gpa = 0.0
            
        if final_gpa >= 8.5:
            degree_class = "Άριστα 🏆"
            target_msg = "Βρίσκεσαι στην υψηλότερη βαθμίδα! Συνέχισε την εξαιρετική δουλειά!"
        elif final_gpa >= 6.5:
            degree_class = "Λίαν Καλώς 🥈"
            diff = 8.5 - final_gpa
            target_msg = f"Απέχεις **{diff:.2f}** μονάδες από το **Άριστα**!"
        elif final_gpa >= 5.0:
            degree_class = "Καλώς 🥉"
            diff = 6.5 - final_gpa
            target_msg = f"Απέχεις **{diff:.2f}** μονάδες από το **Λίαν Καλώς**!"
        else:
            degree_class = "-"
            target_msg = ""

        # --- 4. ΥΠΟΛΟΓΙΣΜΟΣ RPG LEVEL ---
        level_ranks = [
            (0, "Lvl 1: Hello World Novice 🐣"), (30, "Lvl 2: Loop Scripter 🔁"),
            (60, "Lvl 3: Bug Hunter 🐛"), (90, "Lvl 4: Object-Oriented Knight 🛡️"),
            (120, "Lvl 5: Tree Traverser 🌲"), (150, "Lvl 6: Database Ranger 🗄️️"),
            (180, "Lvl 7: Machine Learning Apprentice 🤖"), (210, "Lvl 8: The 8-Bit Legend 👾"),
            (240, "Lvl 9: 3D Rendering Mage 🧙‍♂️"), (270, "Lvl 10: System Architect 🏛️"),
            (300, "MAX Lvl: Master of the Code 👑")
        ]
        
        if total_ects >= 300:
            current_lvl_num, current_xp, rank_title = "MAX", 30, level_ranks[-1][1]
            avatar = "🧙‍♂️" 
        else:
            current_lvl_num = int(total_ects // 30) + 1
            current_xp = total_ects % 30
            for cap, title in reversed(level_ranks):
                if total_ects >= cap:
                    rank_title = title
                    break
            
            if current_lvl_num <= 2: avatar = "🥚"
            elif current_lvl_num <= 4: avatar = "🤓"
            elif current_lvl_num <= 6: avatar = "🥷"
            elif current_lvl_num <= 8: avatar = "🦾"
            else: avatar = "🦸‍♂️"
                    
        xp_percent = (current_xp / 30) * 100

        # --- 5. ΕΜΦΑΝΙΣΗ HUD ΣΤΟ ΣΩΣΤΟ CONTAINER ---
        with hud_container:
            st.markdown(f"<h3 style='color: {primary_color}; font-family: monospace; font-size: 1.1rem; margin-bottom: 5px; text-transform: uppercase;'>🛡️ Active HUD</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background: #0a0e17; border: 1px solid {primary_color}; border-radius: 8px; padding: 15px; margin-bottom: 25px; box-shadow: 0 0 10px {primary_rgba}0.15);">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="font-size: 2.5rem; margin-right: 15px; text-shadow: 0 0 10px rgba(241,196,15,0.5);">{avatar}</div>
                    <div style="overflow: hidden;">
                        <div style="color: #f1c40f; font-weight: bold; font-size: 1.4rem; font-family: 'Share Tech Mono', monospace;">{final_gpa:.2f} <span style="font-size: 0.8rem; color: #7f8c8d;">GPA</span></div>
                        <div style="color: #bdc3c7; font-size: 0.75rem; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;" title="{rank_title}">{rank_title}</div>
                    </div>
                </div>
                <div style="font-family: monospace; font-size: 0.85rem; color: #ecf0f1; margin-bottom: 5px; display: flex; justify-content: space-between;">
                    <span>LVL {current_lvl_num if current_lvl_num != 'MAX' else 'MAX'}</span>
                    <span style="color: #f39c12;">{current_xp:g}/30 XP</span>
                </div>
                <div style="background: rgba(255,255,255,0.05); border-radius: 5px; height: 6px; width: 100%; overflow: hidden; border: 1px solid #34495e;">
                    <div style="width: {xp_percent}%; background: linear-gradient(90deg, #f39c12, #f1c40f); height: 100%; box-shadow: 0 0 5px #f1c40f;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Δημιουργία Γραφημάτων
        fig_cum, fig_bar, fig_gpa, fig_dist, fig_category, fig_scatter = create_plotly_charts(cleaned_df, primary_color, primary_rgba)

        # --- GLOBAL ARCHETYPE ENGINE (Υπολογίζεται 1 φορά για όλα τα Tabs!) ---
        def remove_accents(text):
            accents = {'Ά':'Α', 'Έ':'Ε', 'Ή':'Η', 'Ί':'Ι', 'Ό':'Ο', 'Ύ':'Υ', 'Ώ':'Ω', 'Ϊ':'Ι', 'Ϋ':'Υ', 'ά':'Α', 'έ':'Ε', 'ή':'Η', 'ί':'Ι', 'ό':'Ο', 'ύ':'Υ', 'ώ':'Ω', 'ϊ':'Ι', 'ϋ':'Υ'}
            res = str(text)
            for acc, no_acc in accents.items():
                res = res.replace(acc, no_acc)
            return res.upper()

        def get_skill_branch(course_name):
            name = remove_accents(course_name)
            if any(w in name for w in ['ΓΡΑΦΙΚ', 'ΟΡΑΣΗ', 'ΠΟΛΥΜΕΣ', 'ΑΛΛΗΛΕΠΙΔΡΑΣ', 'ΕΙΚΟΝΑΣ', 'ΗΧΟΥ', '3D']): return 'Graphics & Vision'
            elif any(w in name for w in ['ΑΣΦΑΛΕΙ', 'ΚΡΥΠΤΟΓΡΑΦ', 'ΚΑΚΟΒΟΥΛ', 'ΑΜΥΝΑ', 'ΙΟΥΣ', 'ΕΠΙΘΕΣΕΙΣ']): return 'Cybersecurity'
            elif any(w in name for w in ['ΔΙΚΤΥ', 'ΤΗΛΕΠΙΚΟΙΝ', 'ΣΗΜΑΤ', 'ΑΣΥΡΜΑΤ', 'ΔΙΑΔΙΚΤΥ', 'ΖΕΥΞΕΙΣ']): return 'Networks & Comms'
            elif any(w in name for w in ['ΚΥΚΛΩΜΑΤ', 'ΨΗΦΙΑΚ', 'ΑΡΧΙΤΕΚΤΟΝΙΚ', 'ΗΛΕΚΤΡΟΝΙΚ', 'ΜΙΚΡΟΕΠΕΞΕΡΓΑΣΤ', 'VLSI', 'ΦΥΣΙΚ', 'ΑΞΙΟΠΙΣΤΙ']): return 'Hardware & Architecture'
            elif any(w in name for w in ['ΛΟΓΙΣΜΟΣ', 'ΑΛΓΕΒΡΑ', 'ΜΑΘΗΜΑΤ', 'ΠΙΘΑΝΟΤΗΤ', 'ΣΤΑΤΙΣΤΙΚ', 'ΑΡΙΘΜΗΤΙΚ', 'ΥΠΟΛΟΓΙΣΜΟΥ', 'ΓΡΑΦΗΜΑΤ', 'ΠΟΛΥΠΛΟΚΟΤΗΤ', 'ΒΕΛΤΙΣΤΟΠΟΙΗΣ']): return 'Math & Theory'
            elif any(w in name for w in ['ΝΟΗΜΟΣΥΝ', 'ΒΑΣΕΙΣ', 'ΜΑΘΗΣΗ', 'ΡΟΜΠΟΤΙΚ', 'ΓΛΩΣΣΑΣ', 'ΕΞΟΡΥΞ', 'ΔΕΔΟΜΕΝ', 'ΠΛΗΡΟΦΟΡΙΑ']): return 'Data & AI'
            elif any(w in name for w in ['ΠΡΟΓΡΑΜΜΑΤΙΣΜ', 'ΛΟΓΙΣΜΙΚ', 'ΑΛΓΟΡΙΘΜ', 'ΔΟΜΕΣ', 'ΜΕΤΑΦΡΑΣΤ', 'ΛΕΙΤΟΥΡΓΙΚ', 'ΚΑΤΑΝΕΜΗΜΕΝ', 'ΠΑΡΑΛΛΗΛ', 'ΣΥΣΤΗΜΑΤ', 'ΑΝΤΙΚΕΙΜΕΝΟΣΤΡΕΦ']): return 'Software & Systems'
            else: return 'General / Core'

        branch_df = cleaned_df.copy()
        if not branch_df.empty:
            branch_df['Skill_Branch'] = branch_df['Μάθημα'].apply(get_skill_branch)
            branch_df['Power_Score'] = 0.004 * (branch_df['ECTS'] * (branch_df['Βαθμός'] ** 4.5))
            radar_df = branch_df[branch_df['Skill_Branch'] != 'General / Core']
            cat_scores = radar_df.groupby('Skill_Branch')['Power_Score'].sum().reset_index()
            
            if not cat_scores.empty:
                max_cat_row = cat_scores.loc[cat_scores['Power_Score'].idxmax()]
                dom_cat = max_cat_row['Skill_Branch']
            else:
                dom_cat = 'None'
        else:
            cat_scores = pd.DataFrame()
            dom_cat = 'None'

        if dom_cat == 'Software & Systems': a_title, a_desc, a_icon, a_color = "Cyber-Mage", "Master of Software & Architectures", "🧙‍♂️", "#3498db" 
        elif dom_cat == 'Hardware & Architecture': a_title, a_desc, a_icon, a_color = "Mecha-Paladin", "Hardware & Circuitry Specialist", "🦾", "#e74c3c" 
        elif dom_cat == 'Networks & Comms': a_title, a_desc, a_icon, a_color = "Network Ninja", "Data Routing & Comms Agent", "🥷", "#9b59b6" 
        elif dom_cat == 'Math & Theory': a_title, a_desc, a_icon, a_color = "Logic Oracle", "Math & Theoretical Foundations", "👁️", "#f1c40f" 
        elif dom_cat == 'Data & AI': a_title, a_desc, a_icon, a_color = "AI-Netrunner", "Machine Learning & Data Analyst", "🧠", "#00ffcc" 
        elif dom_cat == 'Graphics & Vision': a_title, a_desc, a_icon, a_color = "Holo-Artisan", "3D Graphics & Visual Computing", "🎨", "#ff007f" 
        elif dom_cat == 'Cybersecurity': a_title, a_desc, a_icon, a_color = "Stealth Decker", "System Security & Defense", "🛡️", "#00ff00" 
        else: a_title, a_desc, a_icon, a_color = "Tech-Mercenary", "Balanced Tech Generalist", "⚔️", "#ffffff"
        
        # --- CYBERPUNK TABS CSS ---
        st.markdown(f"""
        <style>
        div[data-baseweb="tab-highlight"] {{ display: none; }}
        div[data-baseweb="tab-list"] {{ gap: 12px; margin-bottom: 10px; }}
        
        button[data-baseweb="tab"] {{
            background-color: #111b24 !important; border: 1px solid #2c3e50 !important;
            border-radius: 6px !important; color: #7f8c8d !important; padding: 10px 24px !important;
            font-family: 'Share Tech Mono', monospace !important; font-size: 1.1rem !important;
            transition: all 0.3s ease-in-out !important; margin: 0 !important; margin-top: 2px !important;
        }}
        
        button[data-baseweb="tab"]:hover {{
            border-color: {primary_color} !important; color: {primary_color} !important;
            box-shadow: 0 0 10px {primary_rgba}0.2), inset 0 0 8px {primary_rgba}0.1) !important;
            transform: translateY(-2px);
        }}
        
        button[aria-selected="true"] {{
            background: linear-gradient(180deg, #111b24 0%, {primary_rgba}0.15) 100%) !important;
            border: 1px solid {primary_color} !important; border-bottom: 3px solid {primary_color} !important;
            color: {primary_color} !important;
            box-shadow: 0 5px 15px {primary_rgba}0.2), inset 0 -10px 20px {primary_rgba}0.3) !important;
            text-shadow: 0 0 8px {primary_rgba}0.8) !important; transform: translateY(-2px);
        }}
        </style>
        """, unsafe_allow_html=True)

        # --- 2. ΔΗΜΙΟΥΡΓΙΑ ΤΩΝ TABS (SECTORS) ---
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏠 Base Camp", 
            "📈 Analytics Engine", 
            "🌌 3D Space & Timeline", 
            "🔮 Simulator",
            "🧠 Study Hub",
            "⚔️ Co-op Mode"
        ])
        
        # ==========================================
        # TAB 1: BASE CAMP (Overview & Gamification)
        # ==========================================
        with tab1:
            # --- 🕵️‍♂️ CYBER-MERCENARY ID CARD (UNIVERSAL) ---
            
            # 1. Υπολογισμός Achievements για την κάρτα
            total_badges = 0
            if not regular_courses_df.empty:
                if (regular_courses_df['Βαθμός'] == 10).any(): total_badges += 1
                ects_per_period = regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος'])['ECTS'].sum()
                if not ects_per_period.empty and ects_per_period.max() >= 30: total_badges += 1
                sept_courses = regular_courses_df[regular_courses_df['Περίοδος'] == 'Σεπ']
                if not sept_courses.empty and sept_courses.groupby('Ακαδ. Έτος').size().max() >= 3: total_badges += 1
                if not thesis_df.empty: total_badges += 1
                if not internship_df.empty: total_badges += 1
                
                period_counts = { (y, p): len(g) for (y, p), g in regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος']) if y != "Άγνωστο" }
                if period_counts:
                    min_yr = min([int(y.split('-')[0]) for y, p in period_counts.keys()])
                    max_yr = max([int(y.split('-')[0]) for y, p in period_counts.keys()])
                    current_streak, max_streak = 0, 0
                    for y in range(min_yr, max_yr + 1):
                        for p in ['Φεβ', 'Ιουν', 'Σεπ']:
                            if period_counts.get((f"{y}-{str(y+1)[-2:]}", p), 0) >= 2:
                                current_streak += 1
                                max_streak = max(max_streak, current_streak)
                            else: current_streak = 0
                    if max_streak >= 3: total_badges += 1

            # 2. Γρήγορος υπολογισμός Dominant Class (Archetype)

            
            # 3. Καθαρισμός του Rank Title (π.χ. από "Lvl 10: System Architect 🏛️" γίνεται "SYSTEM ARCHITECT")
            clean_rank = re.sub(r'[^\w\s-]', '', rank_title.split(':')[1] if ':' in rank_title else rank_title).strip()

            # Δημιουργία της 3D Ηλεκτρονικής Ταυτότητας
            html_card = f"""<link href="https://fonts.googleapis.com/css2?family=Libre+Barcode+39+Text&display=swap" rel="stylesheet">
<div style="display: flex; justify-content: center; margin-bottom: 30px; perspective: 1000px;">
<div style="background: linear-gradient(135deg, #0a0e17 0%, #111b24 100%); border: 2px solid {a_color}; border-radius: 15px; width: 100%; max-width: 680px; padding: 25px; box-shadow: 0 10px 30px {a_color}40, inset 0 0 20px rgba(0,0,0,0.8); display: flex; align-items: center; position: relative; overflow: hidden; transform: rotateX(2deg) rotateY(-2deg); transition: transform 0.3s ease;">
<!-- Holographic Glare Animation -->
<div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: linear-gradient(45deg, rgba(255,255,255,0) 40%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0) 60%); transform: rotate(30deg); pointer-events: none; animation: holo-glare 5s infinite linear;"></div>
<!-- Avatar Box -->
<div style="background: rgba(0,0,0,0.5); border: 2px solid {a_color}; border-radius: 12px; width: 130px; height: 130px; display: flex; justify-content: center; align-items: center; font-size: 5rem; text-shadow: 0 0 20px {a_color}; margin-right: 25px; flex-shrink: 0; position: relative; box-shadow: inset 0 0 15px {a_color}40;">
{avatar}
<div style="position: absolute; bottom: -12px; background: {a_color}; color: #000; font-size: 0.7rem; font-weight: bold; padding: 3px 10px; border-radius: 4px; text-transform: uppercase; box-shadow: 0 0 10px {a_color};">VERIFIED</div>
</div>
<!-- ID Details -->
<div style="flex-grow: 1; z-index: 2;">
<div style="color: #7f8c8d; font-size: 0.75rem; letter-spacing: 3px; margin-bottom: 2px; font-family: 'Share Tech Mono', monospace;">MERCENARY ID // UOI-CSE</div>
<h2 style="color: #ecf0f1; margin: 0 0 10px 0; font-family: 'Share Tech Mono', monospace; font-size: 2.2rem; letter-spacing: 1px; text-transform: uppercase;">{clean_rank.upper()}</h2>
<!-- Stats Grid -->
<div style="display: flex; gap: 15px; margin-bottom: 15px;">
<div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; border-left: 3px solid {a_color}; flex: 1;">
<div style="color: #7f8c8d; font-size: 0.65rem; text-transform: uppercase; margin-bottom: 3px;">Class Profile</div>
<div style="color: {a_color}; font-weight: bold; font-size: 1rem; text-shadow: 0 0 5px {a_color}80;">{a_title}</div>
</div>
<div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #f1c40f; flex: 1;">
<div style="color: #7f8c8d; font-size: 0.65rem; text-transform: uppercase; margin-bottom: 3px;">Level</div>
<div style="color: #f1c40f; font-weight: bold; font-size: 1rem;">{current_lvl_num if current_lvl_num == 'MAX' else f"LVL {current_lvl_num}"}</div>
</div>
<div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #3498db;">
<div style="color: #7f8c8d; font-size: 0.65rem; text-transform: uppercase; margin-bottom: 3px;">Overall GPA</div>
<div style="color: #3498db; font-weight: bold; font-size: 1.1rem;">{final_gpa:.2f}</div>
</div>
</div>
<!-- Footer: Barcode & Hardware -->
<div style="display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px dashed #34495e; padding-top: 10px;">
<div style="font-family: 'Libre Barcode 39 Text', cursive; font-size: 3rem; color: #bdc3c7; line-height: 0.7; text-shadow: 0 0 5px rgba(255,255,255,0.2);">*UOI-{int(total_ects)}*</div>
<div style="text-align: right; color: #7f8c8d; font-size: 0.7rem; font-family: monospace; line-height: 1.4;">
STATUS: <span style="color: #2ecc71; font-weight: bold; text-shadow: 0 0 5px #2ecc71;">ONLINE</span><br>
ACHIEVEMENTS: <span style="color: #f1c40f; font-weight: bold;">{total_badges} UNLOCKED</span>
</div>
</div>
</div>
</div>
</div>
<style>
@keyframes holo-glare {{
0% {{ transform: translateX(-120%) rotate(30deg); }}
100% {{ transform: translateX(200%) rotate(30deg); }}
}}
</style>"""
            st.markdown(html_card, unsafe_allow_html=True)

            # --- GRADUATION EASTER EGG ---
            if total_ects >= 300:
                # 1. Ταυτόχρονα μπαλόνια ΚΑΙ χιόνι για μέγιστο εφέ
                st.balloons()
                st.snow() 
                
                # 2. Το toast μήνυμα που ήδη είχες
                st.toast('Συγχαρητήρια, Μηχανικέ! Το ταξίδι ολοκληρώθηκε! 🎓', icon='🎆')
                
                # 3. Ένα μεγάλο, επίσημο Success Banner στην οθόνη
                st.success('### 🎓 Πτυχίο Μηχανικού: ΕΠΙΤΥΧΙΑ! 🌟\nΣυγχαρητήρια! Συμπλήρωσες τα απαιτούμενα ECTS και το ταξίδι σου ολοκληρώθηκε με επιτυχία!')


            # Custom CSS XP Bar με Animated Character 
            st.markdown(f"""
            <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; color: white; margin-bottom: 15px; font-weight: bold; font-family: monospace; font-size: 1.1rem;">
                    <span>{ 'Level ' + str(current_lvl_num) if current_lvl_num != 'MAX' else 'Level MAX' }</span>
                    <span>{current_xp:g} / 30 XP</span>
                </div>
                <!-- Δοχείο Μπάρας με visible overflow για να μη κόβεται ο χαρακτήρας -->
                <div style="position: relative; width: 100%; background-color: #1a252f; border-radius: 20px; height: 22px; border: 2px solid #34495e; overflow: visible;">
                    <!-- Γέμισμα Μπάρας -->
                    <div style="width: {xp_percent}%; background: linear-gradient(90deg, #f39c12 0%, #f1c40f 100%); height: 100%; border-radius: 20px; box-shadow: 0 0 10px #f1c40f; transition: width 1s ease-in-out;"></div>
                    <!-- Ο Χαρακτήρας (Μεγαλύτερος, κοιτάει δεξιά και μετακινήθηκε πιο κάτω) -->
                    <div style="position: absolute; top: -22px; left: calc({xp_percent}% - 25px); font-size: 35px; transform: scaleX(-1); display: inline-block; transition: left 1s ease-in-out; text-shadow: 0 2px 4px rgba(0,0,0,0.5); z-index: 10;">
                        🏃‍♀️
                    </div>
                </div>
                <div style="text-align: right; color: #bdc3c7; font-size: 0.85rem; margin-top: 12px;">
                    Συνολικά ECTS: {total_ects:g}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- DYNAMIC SKILL TREE (ECTS EXPANSION) ---
            with st.expander("🌌 Neural Network Skill Tree (Dynamic Progression)", expanded=True):
                
                # 1. Προετοιμασία Δεδομένων: Κρατάμε τα περασμένα μαθήματα και τα ταξινομούμε χρονολογικά
                accents_dict = {'Ά':'Α', 'Έ':'Ε', 'Ή':'Η', 'Ί':'Ι', 'Ό':'Ο', 'Ύ':'Υ', 'Ώ':'Ω', 'Ϊ':'Ι', 'Ϋ':'Υ', 'ά':'Α', 'έ':'Ε', 'ή':'Η', 'ί':'Ι', 'ό':'Ο', 'ύ':'Υ', 'ώ':'Ω', 'ϊ':'Ι', 'ϋ':'Υ'}
                tree_df = cleaned_df[cleaned_df['Βαθμός'] >= 5.0].copy()
                
                period_weight = {'Φεβ': 1, 'Ιουν': 2, 'Σεπ': 3, 'Άλλο': 4}
                tree_df['P_Weight'] = tree_df['Περίοδος'].map(period_weight)
                tree_df = tree_df.sort_values(by=['Ακαδ. Έτος', 'P_Weight']).reset_index(drop=True)
                
                # Υπολογίζουμε τα αθροιστικά ECTS (πόσα είχε όταν πέρασε το μάθημα)
                tree_df['Cum_ECTS'] = tree_df['ECTS'].cumsum()
                
                # 2. Κατηγοριοποίηση στα Skill Branches (Ο Κάθετος Άξονας Υ)
                def assign_branch(name):
                    n = ''.join(accents_dict.get(c, c) for c in str(name)).upper()
                    if any(w in n for w in ['ΓΡΑΦΙΚ', 'ΟΡΑΣΗ', 'ΠΟΛΥΜΕΣ', 'ΑΛΛΗΛΕΠΙΔΡΑΣ', 'ΕΙΚΟΝΑΣ', 'ΗΧΟΥ', '3D']): return 'Graphics & Vision'
                    if any(w in n for w in ['ΑΣΦΑΛΕΙ', 'ΚΡΥΠΤΟΓΡΑΦ', 'ΚΑΚΟΒΟΥΛ', 'ΑΜΥΝΑ', 'ΙΟΥΣ']): return 'Cybersecurity'
                    if any(w in n for w in ['ΔΙΚΤΥ', 'ΤΗΛΕΠΙΚΟΙΝ', 'ΣΗΜΑΤ', 'ΑΣΥΡΜΑΤ', 'ΔΙΑΔΙΚΤΥ']): return 'Networks & Comms'
                    if any(w in n for w in ['ΚΥΚΛΩΜΑΤ', 'ΨΗΦΙΑΚ', 'ΑΡΧΙΤΕΚΤΟΝΙΚ', 'ΗΛΕΚΤΡΟΝΙΚ', 'ΜΙΚΡΟΕΠΕΞΕΡΓΑΣΤ', 'VLSI', 'ΦΥΣΙΚ']): return 'Hardware'
                    if any(w in n for w in ['ΛΟΓΙΣΜΟΣ', 'ΑΛΓΕΒΡΑ', 'ΜΑΘΗΜΑΤ', 'ΠΙΘΑΝΟΤΗΤ', 'ΣΤΑΤΙΣΤΙΚ', 'ΑΡΙΘΜΗΤΙΚ']): return 'Math & Theory'
                    if any(w in n for w in ['ΝΟΗΜΟΣΥΝ', 'ΒΑΣΕΙΣ', 'ΜΑΘΗΣΗ', 'ΡΟΜΠΟΤΙΚ', 'ΓΛΩΣΣΑΣ', 'ΕΞΟΡΥΞ', 'ΔΕΔΟΜΕΝ', 'ΠΛΗΡΟΦΟΡΙΑ']): return 'Data & AI'
                    if any(w in n for w in ['ΠΡΟΓΡΑΜΜΑΤΙΣΜ', 'ΛΟΓΙΣΜΙΚ', 'ΑΛΓΟΡΙΘΜ', 'ΔΟΜΕΣ', 'ΜΕΤΑΦΡΑΣΤ', 'ΛΕΙΤΟΥΡΓΙΚ', 'ΣΥΣΤΗΜΑΤ']): return 'Software & Systems'
                    return 'General / Core'
                    
                tree_df['Branch'] = tree_df['Μάθημα'].apply(assign_branch)
                
                branch_y_map = {
                    'Cybersecurity': 4, 'Data & AI': 3, 'Software & Systems': 2, 'Graphics & Vision': 1,
                    'General / Core': 0, 'Hardware': -1, 'Networks & Comms': -2, 'Math & Theory': -3
                }
                
                b_colors = {
                    'Cybersecurity': '#00ff00', 'Data & AI': '#00ffcc', 'Software & Systems': '#3498db', 
                    'Graphics & Vision': '#ff007f', 'General / Core': '#bdc3c7', 'Hardware': '#e74c3c', 
                    'Networks & Comms': '#9b59b6', 'Math & Theory': '#f1c40f'
                }
                
                # 3. Χτίσιμο των Κλαδιών (Edges) από τη Ρίζα (0,0)
                edge_traces = []
                for branch, y_val in branch_y_map.items():
                    b_df = tree_df[tree_df['Branch'] == branch]
                    if b_df.empty: continue
                    
                    x_vals = [0] + b_df['Cum_ECTS'].tolist()
                    y_vals = [0] + [y_val] * len(b_df)
                    
                    edge_traces.append(go.Scatter(
                        x=x_vals, y=y_vals, mode='lines',
                        line=dict(color=b_colors[branch], width=3, shape='spline', smoothing=0.4),
                        hoverinfo='none', showlegend=False
                    ))
                    
                # 4. Χτίσιμο των Κόμβων (Nodes - Μαθήματα)
                node_x, node_y, node_t, node_c, node_s, node_lc = [0], [0], ["<b>ROOT_NODE</b><br>Σύστημα Ενεργό<br>0 ECTS"], ['#ffffff'], [18], [primary_color]
                
                for _, r in tree_df.iterrows():
                    node_x.append(r['Cum_ECTS'])
                    node_y.append(branch_y_map[r['Branch']])
                    node_t.append(f"<b>{r['Μάθημα']}</b><br>Βαθμός: {r['Βαθμός']}<br>ECTS: +{r['ECTS']}<br>Σύνολο ECTS: {r['Cum_ECTS']}")
                    node_c.append('#0a0e17')
                    node_s.append(12)
                    node_lc.append(b_colors[r['Branch']])
                    
                # Highlight στον τελευταίο κόμβο (Τρέχουσα Πρόοδος)
                if not tree_df.empty:
                    node_x.append(tree_df.iloc[-1]['Cum_ECTS'])
                    node_y.append(branch_y_map[tree_df.iloc[-1]['Branch']])
                    node_t.append(f"<b>CURRENT POSITION</b><br>Σύνολο: {tree_df.iloc[-1]['Cum_ECTS']} ECTS")
                    node_c.append(primary_color)
                    node_s.append(22)
                    node_lc.append('#ffffff')

                node_trace = go.Scatter(
                    x=node_x, y=node_y, mode='markers', hoverinfo='text', text=node_t,
                    marker=dict(size=node_s, color=node_c, line=dict(color=node_lc, width=2), symbol='hexagon'),
                    showlegend=False
                )

                # 5. Ζωγραφική του Χώρου (Η σελίδα Α4 με τα 10 τμήματα)
                fig_tree = go.Figure(data=edge_traces + [node_trace])
                
                max_ects = max(300, total_ects + 30)
                num_zones = int(max_ects // 30) + 1
                
                for i in range(num_zones):
                    x0 = i * 30
                    x1 = (i + 1) * 30
                    lvl_name = f"LVL {i+1}" if i < 10 else "MAX"
                    
                    # Ζώνες Φόντου (εναλλάξ σκιές για να ξεχωρίζουν τα Levels)
                    fig_tree.add_vrect(
                        x0=x0, x1=x1, 
                        fillcolor='rgba(255, 255, 255, 0.03)' if i % 2 == 0 else 'rgba(0, 0, 0, 0)',
                        layer="below", line_width=1, line_dash="dot", line_color="rgba(255,255,255,0.2)"
                    )
                    
                    # Τίτλοι των Levels στην κορυφή
                    fig_tree.add_annotation(
                        x=x0 + 15, y=5.2, text=f"<b>{lvl_name}</b>",
                        showarrow=False, font=dict(color='rgba(255,255,255,0.4)', size=14, family="'Share Tech Mono', monospace")
                    )

                fig_tree.update_layout(
                    title=dict(text='<b>DYNAMIC SKILL TREE (ECTS EXPANSION)</b>', font=dict(color=primary_color, family="'Share Tech Mono', monospace", size=16)),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                    margin=dict(t=50, b=30, l=10, r=20), height=550,
                    xaxis=dict(showgrid=False, zeroline=False, title="Αθροιστικά ECTS", color='#7f8c8d'),
                    yaxis=dict(
                        showgrid=False, zeroline=False, 
                        tickvals=list(branch_y_map.values()), ticktext=list(branch_y_map.keys()),
                        tickfont=dict(color='#bdc3c7', size=11, family="'Share Tech Mono', monospace"), range=[-4.5, 6]
                    ),
                    hoverlabel=dict(bgcolor='#0a0e17', bordercolor=primary_color, font=dict(family="'Share Tech Mono', monospace", color='#ecf0f1', size=13))
                )
                
                st.plotly_chart(fig_tree, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🎒 Inventory Stats")
            
            # CSS για τα Custom Inventory Cards
            st.markdown("""
            <style>
            .inventory-card {
                background-color: #16212b;
                border: 2px solid #2c3e50;
                border-radius: 12px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            .inventory-card:hover {
                border-color: #00ffcc; /* Neon Cyan Hover */
                box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
                transform: translateY(-5px);
            }
            .card-title {
                color: #7f8c8d;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 5px;
                font-weight: bold;
            }
            .card-value {
                color: #ecf0f1;
                font-size: 1.9rem;
                font-family: 'Share Tech Mono', monospace;
                text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                margin-bottom: 10px;
            }
            .card-icon {
                font-size: 1.6rem;
                margin-bottom: 8px;
            }
            .mini-bar-bg {
                background-color: rgba(255,255,255,0.1);
                border-radius: 6px;
                height: 8px;
                width: 100%;
                overflow: hidden;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
            }
            .mini-bar-fill-blue { background: linear-gradient(90deg, #2980b9, #3498db); height: 100%; transition: width 1s ease; }
            .mini-bar-fill-green { background: linear-gradient(90deg, #229954, #2ecc71); height: 100%; transition: width 1s ease; }
            </style>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="inventory-card">
                    <div>
                        <div class="card-icon">📚</div>
                        <div class="card-title">Μαθήματα</div>
                        <div class="card-value">{total_courses} / {target_courses}</div>
                    </div>
                    <div class="mini-bar-bg"><div class="mini-bar-fill-blue" style="width: {min(total_courses / target_courses, 1.0) * 100}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"""
                <div class="inventory-card">
                    <div>
                        <div class="card-icon">📜</div>
                        <div class="card-title">Σύνολο ECTS</div>
                        <div class="card-value">{total_ects:g} / 300</div>
                    </div>
                    <div class="mini-bar-bg"><div class="mini-bar-fill-green" style="width: {min(total_ects / 300, 1.0) * 100}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"""
                <div class="inventory-card">
                    <div>
                        <div class="card-icon">🎯</div>
                        <div class="card-title">Τρέχων Μ.Ο.</div>
                    </div>
                    <div class="card-value" style="color: #f1c40f; font-size: 2.2rem; margin-bottom: 0;">{final_gpa:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col4:
                missing_courses = max(0, target_courses - total_courses)                
                if missing_courses == 0:
                    status_text = "Μένει Διπλωματική!" if thesis_df.empty else "Απόφοιτος!"
                    status_icon = "🚀" if thesis_df.empty else "🎓"
                else:
                    if missing_courses <= 5:
                        num_color = "#4CAF50"
                        status_text = f"Πολύ κοντά στην πηγή!<br>Μένουν <span style='color: {num_color}; font-weight: bold;'>{missing_courses}</span> μαθ."
                    elif missing_courses <= 15:
                        num_color = "#00f2fe" 
                        status_text = f"Μπήκες στην τελική ευθεία!<br>Μένουν <span style='color: {num_color}; font-weight: bold;'>{missing_courses}</span> μαθ."
                    elif missing_courses <= 30:
                        num_color = "#ffa726"
                        status_text = f"Έχουμε δρόμο ακόμα!<br>Μένουν <span style='color: {num_color}; font-weight: bold;'>{missing_courses}</span> μαθ."
                    else:
                        num_color = "#ff4b4b" 
                        status_text = f"Δυνατά για τη συνέχεια!<br>Μένουν <span style='color: {num_color}; font-weight: bold;'>{missing_courses}</span> μαθ."
                        
                    status_icon = "💧" if missing_courses <= 5 else ("🛣️" if missing_courses <= 15 else ("💪" if missing_courses <= 30 else "✍️"))
                    
                st.markdown(f"""
                <div class="inventory-card">
                    <div>
                        <div class="card-icon">{status_icon}</div>
                        <div class="card-title">Status Πτυχίου</div>
                    </div>
                    <div class="card-value" style="font-size: 1.3rem; margin-bottom: 0; padding-top: 10px; line-height: 1.4;">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)

            if final_gpa >= 5.0:
                st.success(f"🎯 **Κλίμακα Πτυχίου:** Η τρέχουσα βαθμολογία σου αντιστοιχεί στο **{degree_class}**. {target_msg}")
            if not internship_df.empty:
                st.info(f"📌 Εντοπίστηκε Πρακτική Άσκηση. Προστέθηκαν τα ECTS ({internship_df['ECTS'].sum():g}) στον Μ.Ο., αλλά εξαιρέθηκε από την καταμέτρηση των {target_courses} μαθημάτων.")

            # --- BOSS ARENA (ΔΙΠΛΩΜΑΤΙΚΗ & ΔΙΚΤΥΑ Ι) ---
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                if thesis_df.empty:
                    # Υπολογισμός Damage από το session_state.boss_milestones 
                    damage_taken = sum(st.session_state.boss_milestones)
                    boss_hp = 100 - (damage_taken * 25)
                    
                    # Δυναμικά states και χρώματα βάσει HP
                    if boss_hp > 50:
                        b_color, b_glow, b_title = "#e74c3c", "rgba(231,76,60,0.4)", "⚠️ FINAL BOSS: LURKING"
                    elif boss_hp > 0:
                        b_color, b_glow, b_title = "#f39c12", "rgba(243,156,18,0.5)", "🔥 BOSS IS WEAKENED!"
                    else:
                        b_color, b_glow, b_title = "#2ecc71", "rgba(46,204,113,0.6)", "💀 FINISHING BLOW READY!"
                        
                    st.markdown(f"""
                    <div style="background: linear-gradient(145deg, #1a0f0f, #2a1111); border: 2px solid {b_color}; border-radius: 10px; padding: 15px; margin-bottom: 10px; margin-top: 10px; box-shadow: 0 0 15px {b_glow}; text-align: center; transition: all 0.4s ease;">
                    <h3 style="color: {b_color}; margin: 0; font-size: 1.2rem; text-shadow: 0 0 10px {b_glow}; transition: color 0.4s ease;">{b_title}</h3>
                    <div style="color: #f5b7b1; font-size: 0.9rem; margin-top: 5px;">Διπλωματική Εργασία (30 ECTS)</div>
                        
                    <!-- Μπάρα Ζωής (HP) -->
                    <div style="background: #0a0e17; border: 1px solid #34495e; border-radius: 8px; height: 16px; margin-top: 12px; position: relative; overflow: hidden; box-shadow: inset 0 0 5px #000;">
                    <div style="width: {boss_hp}%; background: {b_color}; height: 100%; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1), background 0.4s ease;"></div>
                    <div style="position: absolute; top: 0; left: 0; width: 100%; font-family: 'Share Tech Mono', monospace; font-size: 0.65rem; color: #fff; line-height: 16px; font-weight: bold; text-shadow: 1px 1px 2px #000;">HP: {boss_hp} / 100</div>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<div style='font-size: 0.8rem; color: #7f8c8d; font-family: monospace; margin-bottom: 5px;'>// TACTICAL MILESTONES:</div>", unsafe_allow_html=True)
                    
                    # Interactive Checkboxes (Το UI της ζημιάς)
                    m1 = st.checkbox("📖 1. Έρευνα & Βιβλιογραφία", value=st.session_state.boss_milestones[0])
                    m2 = st.checkbox("💻 2. Υλοποίηση", value=st.session_state.boss_milestones[1])
                    m3 = st.checkbox("📝 3. Συγγραφή Κειμένου & Μετρήσεις", value=st.session_state.boss_milestones[2])
                    m4 = st.checkbox("🎯 4. Ολοκλήρωση Παρουσίασης", value=st.session_state.boss_milestones[3])
                    
                    # Έλεγχος αλλαγών. Αν ο χρήστης τσεκάρει/ξε-τσεκάρει κάτι, ανανεώνουμε το state και κάνουμε άμεσα rerun.
                    if [m1, m2, m3, m4] != st.session_state.boss_milestones:
                        st.session_state.boss_milestones = [m1, m2, m3, m4]
                        st.rerun()
                        
                else:
                    thesis_grade = thesis_df.iloc[0]['Βαθμός']
                    boss_html = f"""
                    <div style="background: linear-gradient(145deg, #1a2a1a, #0e3a0e); border: 2px solid #2ecc71; border-radius: 10px; padding: 15px; margin-bottom: 0px; margin-top: 10px; box-shadow: 0 0 15px rgba(46, 204, 113, 0.4); text-align: center; animation: pulse-green 3s infinite; height: 130px; display: flex; flex-direction: column; justify-content: center;">
                        <h3 style="color: #2ecc71; margin: 0; font-size: 1.3rem; text-shadow: 0 0 10px rgba(46,204,113,0.8);">🐉 FINAL BOSS DEFEATED!</h3>
                        <div style="color: #a9dfbf; font-size: 1rem; margin-top: 5px;">Διπλωματική ολοκληρώθηκε με: <strong>{thesis_grade}</strong> 🏆</div>
                    </div>
                    """
                    st.markdown(boss_html, unsafe_allow_html=True)
                
            with col_b2:
                # Αναζήτηση για τα Δίκτυα Ι (πιάνει Λατινικό/Ελληνικό I ή τον αριθμό 1 με Regex)
                net_df = cleaned_df[cleaned_df['Μάθημα'].str.contains(r'Δ[ιί]κτυα Υπολογιστ[ωώ]ν\s*[ΙI1](?!\s*[ΙI1])', case=False, na=False, regex=True)]
                
                if net_df.empty:
                    net_html = """
                    <div style="background: linear-gradient(145deg, #2b1055, #4b1a7d); border: 2px solid #9b59b6; border-radius: 10px; padding: 15px; margin-bottom: 0px; margin-top: 10px; box-shadow: 0 0 15px rgba(155, 89, 182, 0.4); text-align: center; animation: pulse-purple 2s infinite; height: 130px; display: flex; flex-direction: column; justify-content: center;">
                        <h3 style="color: #9b59b6; margin: 0; font-size: 1.3rem; text-shadow: 0 0 10px rgba(155,89,182,0.8);">💀 HIDDEN BOSS: ALIVE</h3>
                        <div style="color: #d7bde2; font-size: 0.95rem; margin-top: 5px;">Ο εφιάλτης "Δίκτυα Υπολογιστών Ι" παραμονεύει...</div>
                    </div>
                    """
                else:
                    net_grade = net_df.iloc[0]['Βαθμός']
                    net_html = f"""
                    <div style="background: linear-gradient(145deg, #0f2027, #203a43); border: 2px solid #3498db; border-radius: 10px; padding: 15px; margin-bottom: 0px; margin-top: 10px; box-shadow: 0 0 15px rgba(52, 152, 219, 0.4); text-align: center; animation: pulse-blue 3s infinite; height: 130px; display: flex; flex-direction: column; justify-content: center;">
                        <h3 style="color: #3498db; margin: 0; font-size: 1.3rem; text-shadow: 0 0 10px rgba(52,152,219,0.8);">🛡️ NIGHTMARE CLEARED!</h3>
                        <div style="color: #aed6f1; font-size: 1rem; margin-top: 5px;">Δίκτυα Υπολογιστών Ι: Επέζησες με <strong>{net_grade}</strong> ⚔️</div>
                    </div>
                    """
                st.markdown(net_html, unsafe_allow_html=True)
                
            # Ενοποιημένο CSS για όλα τα Boss Animations
            st.markdown("""
            <style>
            @keyframes pulse-red { 0% { box-shadow: 0 0 5px rgba(231,76,60,0.2); } 50% { box-shadow: 0 0 20px rgba(231,76,60,0.6); } 100% { box-shadow: 0 0 5px rgba(231,76,60,0.2); } }
            @keyframes pulse-green { 0% { box-shadow: 0 0 5px rgba(46,204,113,0.2); } 50% { box-shadow: 0 0 20px rgba(46,204,113,0.6); } 100% { box-shadow: 0 0 5px rgba(46,204,113,0.2); } }
            @keyframes pulse-purple { 0% { box-shadow: 0 0 5px rgba(155,89,182,0.2); } 50% { box-shadow: 0 0 20px rgba(155,89,182,0.6); } 100% { box-shadow: 0 0 5px rgba(155,89,182,0.2); } }
            @keyframes pulse-blue { 0% { box-shadow: 0 0 5px rgba(52,152,219,0.2); } 50% { box-shadow: 0 0 20px rgba(52,152,219,0.6); } 100% { box-shadow: 0 0 5px rgba(52,152,219,0.2); } }
            </style>
            """, unsafe_allow_html=True)
            # --------------------------------------

            # --- LIVE TERMINAL SYSTEM LOG ---
            st.markdown("---")
            st.subheader("📟 Live System Log")
            
            # Δημιουργία χρονολογικής σειράς για να βρούμε τα 5 πιο πρόσφατα
            log_df = cleaned_df.copy()
            # Βαρύτητα περιόδου για σωστή χρονολογική ταξινόμηση
            period_weight = {'Φεβ': 1, 'Ιουν': 2, 'Σεπ': 3, 'Άλλο': 4}
            log_df['Period_Weight'] = log_df['Περίοδος'].map(period_weight)
            
            # Ταξινόμηση πρώτα με Έτος (φθίνουσα) και μετά με Περίοδο (φθίνουσα)
            recent_courses = log_df.sort_values(by=['Ακαδ. Έτος', 'Period_Weight'], ascending=[False, False]).head(5)
            recent_courses = recent_courses.iloc[::-1]
            
            # Δημιουργία του HTML για το Terminal
            terminal_lines = ""
            for _, row in recent_courses.iterrows():
                course = row['Μάθημα']
                grade = row['Βαθμός']
                ects = row['ECTS']
                terminal_lines += f"<span style='color: #00ffcc;'>[SYS_UPDATE]</span> &gt; Course '{course}' cleared. Grade: <span style='color: #f1c40f;'>{grade}</span><br>"
                if ects > 0:
                    terminal_lines += f"<span style='color: #2ecc71;'>[XP_GAIN]</span> &gt; +{ects:g} ECTS acquired.<br>"
            
            terminal_lines += "<span style='color: #00ffcc;'>[STATUS]</span> &gt; Saving progress... OK.<br><span class='blink-cursor'>_</span>"
            
            # Το UI του Terminal
            st.markdown(f"""
            <div style="background-color: #0a0e17; border: 1px solid #34495e; border-radius: 8px; padding: 15px; font-family: 'Share Tech Mono', monospace; font-size: 0.95rem; color: #ecf0f1; box-shadow: inset 0 0 10px #000; overflow-x: auto; margin-bottom: 20px;">
                <div style="color: #7f8c8d; font-size: 0.8rem; margin-bottom: 10px; border-bottom: 1px solid #2c3e50; padding-bottom: 5px;">root@cse-uoi:~/logs/recent_activity.log</div>
                <div style="line-height: 1.5;">
                    {terminal_lines}
                </div>
            </div>
            <style>
            .blink-cursor {{
                animation: blinker 1s linear infinite;
                color: #00ffcc;
                font-weight: bold;
            }}
            @keyframes blinker {{
                50% {{ opacity: 0; }}
            }}
            </style>
            """, unsafe_allow_html=True)

            # --- ACTIVE QUEST BOARD (REMATCHES) ---
            if not top_quests.empty:
                st.markdown("---")
                st.subheader("📜 Active Bounties (Rematch Required)")
                
                cols = st.columns(len(top_quests))
                for idx, (_, row) in enumerate(top_quests.iterrows()):
                    quest_name = row['Μάθημα']
                    quest_ects = row['ECTS']
                    
                    with cols[idx]:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px dashed #e74c3c; border-radius: 8px; padding: 20px 15px 15px 15px; position: relative; box-shadow: 2px 2px 10px rgba(231, 76, 60, 0.1); height: 100%; transition: transform 0.2s;">
                            <div style="position: absolute; top: -12px; left: 15px; background: #e74c3c; color: #fff; font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-family: monospace;">WANTED ALIVE</div>
                            <h4 style="color: #e74c3c; margin-top: 5px; margin-bottom: 10px; font-size: 1.1rem; text-shadow: 0 0 5px rgba(231, 76, 60, 0.3);">{quest_name}</h4>
                            <div style="color: #bdc3c7; font-size: 0.95rem;">
                                ⚔️ <strong>Type:</strong> Revenge Quest<br>
                                💰 <strong>Bounty:</strong> <span style="color: #2ecc71; font-weight: bold;">{quest_ects:g} ECTS / XP</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            # --- 3D HOLO-CARDS CSS ENGINE ---
            st.markdown("""
            <style>
            /* Κοινό εφέ για όλες τις 3D κάρτες */
            .holo-card {
                position: relative;
                overflow: hidden;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                transform-style: preserve-3d;
            }
            
            /* Το εφέ της "γυαλάδας" (holographic glare) που περνάει από πάνω */
            .holo-card::after {
                content: '';
                position: absolute;
                top: 0; left: -150%; width: 50%; height: 100%;
                background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.15) 50%, rgba(255,255,255,0) 100%);
                transform: skewX(-25deg);
                transition: left 0.6s ease-in-out;
                z-index: 1;
                pointer-events: none;
            }
            
            .holo-card:hover::after {
                left: 200%;
            }

            /* Achievements (Χρυσό) */
            @keyframes pulse-gold {
                0% { box-shadow: 0 0 5px #f1c40f, inset 0 0 2px #f1c40f; border-color: #f1c40f; }
                50% { box-shadow: 0 0 15px #f39c12, inset 0 0 5px #f39c12; border-color: #f39c12; }
                100% { box-shadow: 0 0 5px #f1c40f, inset 0 0 2px #f1c40f; border-color: #f1c40f; }
            }
            .loot-badge {
                background: linear-gradient(145deg, #1a252f, #2c3e50);
                border: 2px solid #f1c40f;
                border-radius: 12px;
                padding: 15px;
                text-align: center;
                animation: pulse-gold 3s infinite ease-in-out;
                min-height: 140px;
                z-index: 2;
            }
            .loot-badge:hover {
                animation: none; /* Σταματάει το pulse για να αναλάβει το 3D hover */
                transform: perspective(800px) scale(1.08) rotateX(-5deg) rotateY(5deg) translateZ(10px);
                box-shadow: 10px 15px 25px rgba(0,0,0,0.7), 0 0 25px rgba(241, 196, 15, 0.8);
                border-color: #fff;
            }

            /* Trophies & Survival */
            .trophy-card {
                background: linear-gradient(145deg, #2a2000, #1a1000);
                border: 1px solid #f1c40f;
                border-radius: 6px;
                padding: 8px 12px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                box-shadow: 0 0 10px rgba(241, 196, 15, 0.1);
            }
            .trophy-card:hover {
                transform: perspective(600px) scale(1.03) rotateX(3deg) rotateY(-3deg);
                box-shadow: -5px 8px 15px rgba(0,0,0,0.5), 0 0 15px rgba(241, 196, 15, 0.4);
            }
            
            .survival-card {
                background: #111;
                border: 1px solid #333;
                border-left: 3px dashed #e74c3c;
                border-radius: 4px;
                padding: 8px 12px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
                background-image: repeating-linear-gradient(-45deg, transparent, transparent 5px, rgba(255,0,0,0.03) 5px, rgba(255,0,0,0.03) 10px);
            }
            .survival-card:hover {
                transform: perspective(600px) scale(1.03) rotateX(-3deg) rotateY(3deg);
                box-shadow: 5px 8px 15px rgba(0,0,0,0.5), 0 0 15px rgba(231, 76, 60, 0.3);
                border-left-style: solid;
            }
            
            /* Classes για το αιωρούμενο (floating) εσωτερικό κείμενο/εικονίδια */
            .float-30 { transform: translateZ(30px); }
            .float-20 { transform: translateZ(20px); }
            .float-10 { transform: translateZ(10px); }
            
            .card-icon { font-size: 1.4rem; margin-right: 12px; transform: translateZ(20px); }
            .card-details { flex-grow: 1; overflow: hidden; transform: translateZ(10px); }
            .course-title { font-size: 0.85rem; font-weight: bold; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .trophy-title { color: #f1c40f; text-shadow: 0 0 3px rgba(241,196,15,0.4); }
            .survival-title { color: #bdc3c7; }
            .grade-badge {
                background: #000; padding: 4px 8px; border-radius: 4px;
                font-family: 'Share Tech Mono', monospace; font-size: 1rem; font-weight: bold; margin-left: 10px;
                transform: translateZ(15px);
            }
            .trophy-badge { border: 1px solid #f1c40f; color: #f1c40f; box-shadow: 0 0 5px rgba(241,196,15,0.2); }
            .survival-badge { border: 1px solid #7f8c8d; color: #e74c3c; }
            </style>
            """, unsafe_allow_html=True)

            # ACHIEVEMENTS & FUN FACTS
            if not regular_courses_df.empty:
                st.markdown("---")
                badges = []
                if (regular_courses_df['Βαθμός'] == 10).any(): badges.append({"icon": "🎯", "title": "Απόλυτο 10άρι", "desc": "Πέτυχες 10 σε τουλάχιστον ένα μάθημα!"})
                ects_per_period = regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος'])['ECTS'].sum()
                if not ects_per_period.empty and ects_per_period.max() >= 30: badges.append({"icon": "🚂", "title": "Μηχανή ECTS", "desc": f"Συγκέντρωσες {ects_per_period.max():g} ECTS σε μία εξεταστική!"})
                sept_courses = regular_courses_df[regular_courses_df['Περίοδος'] == 'Σεπ']
                if not sept_courses.empty and sept_courses.groupby('Ακαδ. Έτος').size().max() >= 3: badges.append({"icon": "🛡️", "title": "Αντεπίθεση Σεπτέμβρη", "desc": "Έσωσες τη χρονιά!"})
                if not thesis_df.empty: badges.append({"icon": "🐉", "title": "Boss Defeated", "desc": "Ολοκλήρωσες τη Διπλωματική!"})
                if not internship_df.empty: badges.append({"icon": "🌐", "title": "Hello World!", "desc": "Ολοκλήρωσες την Πρακτική!"})
                
                period_counts = { (y, p): len(g) for (y, p), g in regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος']) if y != "Άγνωστο" }
                if period_counts:
                    min_yr, max_yr = min([int(y.split('-')[0]) for y, p in period_counts.keys()]), max([int(y.split('-')[0]) for y, p in period_counts.keys()])
                    current_streak, max_streak = 0, 0
                    for y in range(min_yr, max_yr + 1):
                        for p in ['Φεβ', 'Ιουν', 'Σεπ']:
                            if period_counts.get((f"{y}-{str(y+1)[-2:]}", p), 0) >= 2:
                                current_streak += 1
                                max_streak = max(max_streak, current_streak)
                            else: current_streak = 0
                    if max_streak >= 3: badges.append({"icon": "🔥", "title": "On Fire", "desc": f"Πέρασες 2+ μαθήματα για {max_streak} σερί εξεταστικές!"})
                
                if badges:
                    st.subheader("🏅 Legendary Achievements (Loot)")
                    cols = st.columns(4)
                    for i, b in enumerate(badges):
                        with cols[i % 4]:
                            st.markdown(f"""
                            <div class="loot-badge holo-card">
                                <div class="float-30" style="font-size: 2.5rem; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">{b['icon']}</div>
                                <div class="float-20" style="color: #f1c40f; font-weight: bold; font-size: 1.1rem; margin-bottom: 8px;">{b['title']}</div>
                                <div class="float-10" style="color: #ecf0f1; font-size: 0.85rem; line-height: 1.3;">{b['desc']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # --- HALL OF FAME, MILESTONES & SURVIVAL ---
                st.markdown("---")
                st.subheader("🏛 Hall of Fame & Milestones")
                
                sem_stats_df = pd.DataFrame([{'Period': f"{p} '{y[-2:]}", 'Count': len(g), 'GPA': (g['Βαθμός']*g['ECTS']).sum()/g['ECTS'].sum() if g['ECTS'].sum()>0 else 0} for (y, p), g in regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος'])])
                if not sem_stats_df.empty:
                    golden = sem_stats_df.sort_values(by=['Count', 'GPA'], ascending=[False, False]).iloc[0]
                    dark = sem_stats_df.sort_values(by=['GPA', 'Count'], ascending=[True, True]).iloc[0]
                    
                    cf1, cf2 = st.columns(2)
                    cf1.info(f"🌟 **Χρυσή Εξεταστική:** **{golden['Period']}** ({int(golden['Count'])} μαθ. | Μ.Ο. {golden['GPA']:.2f})")
                    cf2.warning(f"💀 **Πιο Δύσκολη Εξεταστική:** **{dark['Period']}** ({int(dark['Count'])} μαθ. | Μ.Ο. {dark['GPA']:.2f})")
                
                st.markdown("<br>", unsafe_allow_html=True)

                top_5_courses = regular_courses_df.nlargest(5, 'Βαθμός')
                survival_courses = regular_courses_df[regular_courses_df['Βαθμός'] == 5.0].tail(5)
                
                col_t, col_s = st.columns(2)
                
                # --- ΣΤΗΛΗ 1: TROPHY ROOM (Top 5) ---
                with col_t:
                    st.markdown("<h5 style='color: #f1c40f; margin-bottom: 10px; border-bottom: 1px solid #f1c40f; padding-bottom: 4px;'>🏆 Top 5 Trophies</h5>", unsafe_allow_html=True)
                    for _, row in top_5_courses.iterrows():
                        st.markdown(f"""
                        <div class="trophy-card holo-card">
                            <div class="card-icon">🥇</div>
                            <div class="card-details" title="{row['Μάθημα']}">
                                <div class="course-title trophy-title">{row['Μάθημα']}</div>
                                <div style="font-size: 0.75rem; color: #bdc3c7;">📅 {row['Περίοδος']} '{row['Ακαδ. Έτος'][-2:]}</div>
                            </div>
                            <div class="grade-badge trophy-badge">{row['Βαθμός']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # --- ΣΤΗΛΗ 2: WALL OF SURVIVAL (5.0) ---
                with col_s:
                    st.markdown("<h5 style='color: #7f8c8d; margin-bottom: 10px; border-bottom: 1px solid #7f8c8d; padding-bottom: 4px;'>🛡️ Barely Survived (5.0)</h5>", unsafe_allow_html=True)
                    if survival_courses.empty:
                        st.info("Δεν έχεις περάσει κανένα μάθημα με 5.0! 🦾")
                    else:
                        for _, row in survival_courses.iterrows():
                            st.markdown(f"""
                            <div class="survival-card holo-card">
                                <div class="card-icon">🪖</div>
                                <div class="card-details" title="{row['Μάθημα']}">
                                    <div class="course-title survival-title">{row['Μάθημα']}</div>
                                    <div style="font-size: 0.75rem; color: #7f8c8d;">⚠️ {row['Περίοδος']} '{row['Ακαδ. Έτος'][-2:]}</div>
                                </div>
                                <div class="grade-badge survival-badge">{row['Βαθμός']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                # --- DATA EXTRACTION PROTOCOL (GITHUB & RAW DATA) ---
                st.markdown("---")
                st.subheader("💾 Data Extraction Protocol")
                
                col_ex1, col_ex2 = st.columns(2)
                
                with col_ex1:
                    with st.expander("🐙 Εξαγωγή Προφίλ για GitHub (README.md)"):
                        bar_len = 20
                        filled_len = int(min(total_ects / 300, 1.0) * bar_len)
                        md_text = f"## 🎓 Academic Profile (@panagiotispar)\n\n**University of Ioannina** | Computer Engineering and Informatics\n\n### 📊 Base Stats\n- ⚔️ **Rank:** {rank_title}\n- 🎯 **GPA:** {final_gpa:.2f} / 10.0\n- 📚 **Courses:** {total_courses} / 47\n- 🎓 **Progress:** `[{'█' * filled_len + '░' * (bar_len - filled_len)}]` {(total_ects / 300) * 100:.1f}% ({total_ects:g}/300 ECTS)\n\n"
                        if 'badges' in locals() and badges:
                            md_text += "### 🏅 Unlocked Achievements\n" + "".join([f"- **{b['icon']} {b['title']}**: {b['desc']}\n" for b in badges])
                        st.code(md_text, language='markdown')
                        st.download_button("💾 Κατέβασμα ως progress.md", md_text, "progress.md", "text/markdown", use_container_width=True)
                        
                with col_ex2:
                    with st.expander("🗄️ Προεπισκόπηση Καθαρών Δεδομένων (Raw Data)"):
                        st.dataframe(cleaned_df, use_container_width=True)
                        csv = cleaned_df.to_csv(index=False).encode('utf-8')
                        st.download_button("💾 Κατέβασμα Database (.csv)", csv, "academic_database.csv", "text/csv", use_container_width=True)

        # ==========================================
        # TAB 2: ANALYTICS ENGINE (2D Charts)
        # ==========================================
        with tab2:
            # --- PLAYER ARCHETYPE (ADVANCED SKILL PROFILING) ---
            st.subheader("🧬 Player Archetype (Skill Profiling)")
            
            if not cleaned_df.empty and not cat_scores.empty:
                col_arch1, col_arch2 = st.columns([1, 2])
                
                with col_arch1:
                    st.markdown(f"""
                    <div style='background: #0a0e17; border: 1px solid {a_color}; border-radius: 12px; padding: 25px 15px; text-align: center; height: 100%; box-shadow: 0 0 15px {a_color}44; display: flex; flex-direction: column; justify-content: center;'>
                        <div style='font-size: 3.5rem; text-shadow: 0 0 15px {a_color}; margin-bottom: 10px;'>{a_icon}</div>
                        <div style='color: #7f8c8d; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase;'>Dominant Class</div>
                        <h3 style='color: {a_color}; margin: 5px 0; font-family: monospace; font-size: 1.6rem;'>{a_title}</h3>
                        <div style='color: #bdc3c7; font-size: 0.85rem;'>{a_desc}</div>
                        <div style='margin-top: 15px; font-size: 0.75rem; color: #7f8c8d; border-top: 1px dashed #34495e; padding-top: 10px;'>
                            Highest Power Branch: <strong style='color: #ecf0f1;'>{dom_cat}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_arch2:
                    all_branches = ['Software & Systems', 'Hardware & Architecture', 'Math & Theory', 'Data & AI', 'Networks & Comms', 'Graphics & Vision', 'Cybersecurity']
                    radar_plot_df = pd.DataFrame({'Skill_Branch': all_branches})
                    radar_plot_df = radar_plot_df.merge(cat_scores, on='Skill_Branch', how='left').fillna(0)
                    radar_plot_df['Power_Score'] = radar_plot_df['Power_Score'].round(0)
                    
                    fig_archetype = go.Figure(go.Scatterpolar(
                        r=radar_plot_df['Power_Score'], theta=radar_plot_df['Skill_Branch'],
                        fill='toself', name='Skill Power', line_color=a_color, opacity=0.8,
                        hovertemplate='<b>%{theta}</b><br>Power Level: %{r:.0f}<extra></extra>'
                    ))
                    fig_archetype.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, showticklabels=False, gridcolor='rgba(255,255,255,0.1)'),
                            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=12, color='#bdc3c7')),
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        showlegend=False, margin=dict(t=30, b=30, l=60, r=60),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320
                    )
                    st.plotly_chart(fig_archetype, use_container_width=True)

            # --- SPEEDRUN PREDICTOR & VELOCITY TRACKER ---
            from datetime import datetime
            st.markdown("---")
            st.subheader("⏱️ Velocity Tracker (Πρόβλεψη Πτυχίου)")
            
            if not cleaned_df.empty:
                # 1. Υπολογισμός Ενεργών Εξεταστικών
                active_periods = cleaned_df[['Ακαδ. Έτος', 'Περίοδος']].drop_duplicates()
                num_periods = len(active_periods)
                
                if total_ects >= 300:
                    st.success("🎓 Έχεις ήδη τερματίσει το παιχνίδι! Το Velocity σου κλείδωσε.")
                elif num_periods > 0:
                    # 2. Αλγόριθμος Ταχύτητας
                    velocity = total_ects / num_periods
                    rem_ects = 300 - total_ects
                    
                    # 5 Κατηγορίες Ταχύτητας (Ranks)
                    if velocity >= 20:
                        v_badge, v_color, v_desc = "Academic Weapon 🚀", "#ff007f", "Ασύλληπτος ρυθμός. Το σύστημα δυσκολεύεται να σε ακολουθήσει!"
                    elif velocity >= 17:
                        v_badge, v_color, v_desc = "Speedrunner ⚡", "#f1c40f", "Τρέχεις με ιλιγγιώδη ρυθμό. Προσοχή στο Overheating!"
                    elif velocity >= 13:
                        v_badge, v_color, v_desc = "Steady Grinder ⚙️", "#3498db", "Σταθερός και αξιόπιστος ρυθμός. Βέλτιστη λειτουργία."
                    elif velocity >= 8:
                        v_badge, v_color, v_desc = "Tactical Survivor 🛡️", "#e74c3c", "Προσεκτικά βήματα. Focus στην επιβίωση."
                    else:
                        v_badge, v_color, v_desc = "Zen Explorer 🧘", "#9b59b6", "Απολαμβάνεις το side-content. Το πτυχίο μπορεί να περιμένει."
                        
                    # 3. Πραγματικός Χρόνος (Real-Time Time Machine)
                    now = datetime.now()
                    curr_month = now.month
                    curr_year = now.year
                    
                    # Χαρτογράφηση του πραγματικού μήνα στην ΕΠΟΜΕΝΗ εξεταστική
                    if curr_month >= 10 or curr_month <= 2:
                        next_period = 'Φεβ'
                        base_year = curr_year + 1 if curr_month >= 10 else curr_year
                    elif 3 <= curr_month <= 6:
                        next_period = 'Ιουν'
                        base_year = curr_year
                    else:
                        next_period = 'Σεπ'
                        base_year = curr_year
                        
                    p_order = ['Φεβ', 'Ιουν', 'Σεπ']
                    curr_idx = p_order.index(next_period)
                    
                    # Υπολογισμός Εξεταστικών που απομένουν (Δυναμικός Αλγόριθμος Διπλωματικής)
                    if thesis_df.empty:
                        rem_courses_ects = max(0, rem_ects - 30) # Πόσα ECTS χρωστάει πέρα από τη διπλωματική
                        threshold = velocity * (2/3) # Δυναμικό όριο: Τα 2/3 της ταχύτητάς του
                        
                        if rem_courses_ects <= threshold:
                            # Αν χρωστάει "λίγα", τα ενσωματώνουμε σε 1 εξεταστική μαζί με τη διπλωματική
                            periods_needed = 1
                            if rem_courses_ects == 0:
                                req_text = "Απαιτείται <b>1</b> εξεταστική (Μόνο Διπλωματική)."
                            else:
                                req_text = f"Απαιτείται <b>1</b> εξεταστική (Διπλωματική & {rem_courses_ects:g} ECTS)."
                        else:
                            # Αν χρωστάει "πολλά", υπολογίζουμε το χρόνο για τα μαθήματα + 1 εξεταστική για διπλωματική
                            course_periods = max(1, int(round(rem_courses_ects / velocity)))
                            periods_needed = course_periods + 1
                            req_text = f"Απαιτούνται <b>{periods_needed}</b> εξεταστικές (Διπλωματική & {rem_courses_ects:g} ECTS)."
                    else:
                        # Αν έχει περάσει τη διπλωματική, κανονικός υπολογισμός
                        periods_needed = int((rem_ects / velocity) + 0.99) if velocity > 0 else 99
                        periods_needed = max(1, periods_needed)
                        req_text = f"Απαιτούνται <b>{periods_needed}</b> εξεταστικές ακόμα."
                    
                    # Προβολή στο μέλλον με βάση τις εξεταστικές
                    steps_to_advance = periods_needed - 1
                    for _ in range(steps_to_advance):
                        curr_idx += 1
                        if curr_idx > 2:
                            curr_idx = 0
                            base_year += 1
                            
                    grad_period = f"{p_order[curr_idx]} '{str(base_year)[-2:]}"
                    
                    # 4. Εμφάνιση του Dashboard Widget
                    st.markdown(f"""
<div style="display: flex; gap: 15px; margin-top: 15px; flex-wrap: wrap;">
<div style="flex: 1; min-width: 200px; background: #0a0e17; border: 1px solid {v_color}; border-left: 4px solid {v_color}; border-radius: 8px; padding: 20px; box-shadow: 0 0 15px {v_color}20;">
<div style="color: #7f8c8d; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Velocity Status</div>
<div style="color: {v_color}; font-size: 1.6rem; font-family: 'Share Tech Mono', monospace; font-weight: bold; text-shadow: 0 0 10px {v_color}80;">{v_badge}</div>
<div style="color: #bdc3c7; font-size: 0.85rem; margin-top: 5px;">{v_desc}</div>
</div>
    
<div style="flex: 1; min-width: 200px; background: #111b24; border: 1px dashed #3498db; border-radius: 8px; padding: 20px; text-align: center; box-shadow: inset 0 0 10px rgba(0,0,0,0.5);">
<div style="color: #7f8c8d; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Average Speed</div>
<div style="color: #3498db; font-size: 2.2rem; font-family: 'Share Tech Mono', monospace; font-weight: bold; text-shadow: 0 0 10px rgba(52,152,219,0.5);">{velocity:.1f} <span style="font-size: 1rem; color: #bdc3c7;">ECTS/Εξεταστική</span></div>
</div>
    
<div style="flex: 1; min-width: 200px; background: #0a0e17; border: 1px solid #2ecc71; border-right: 4px solid #2ecc71; border-radius: 8px; padding: 20px; text-align: right; box-shadow: 0 0 15px rgba(46,204,113,0.2);">
<div style="color: #7f8c8d; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Est. Graduation</div>
<div style="color: #2ecc71; font-size: 1.8rem; font-family: 'Share Tech Mono', monospace; font-weight: bold; text-shadow: 0 0 10px rgba(46,204,113,0.5);">{grad_period}</div>
<div style="color: #bdc3c7; font-size: 0.85rem; margin-top: 5px;">{req_text}</div>
</div>
</div>
""", unsafe_allow_html=True)

            # --- CYBER-GRID ACTIVITY HEATMAP ---
            st.markdown("---")
            st.subheader("🟩 Cyber-Grid Activity (Server Heatmap)")
            st.markdown("<span style='color: #7f8c8d; font-size: 0.9rem;'>Ανάλυση εποχικότητας: Δες σε ποιες περιόδους κάνεις το μεγαλύτερο Power-Leveling.</span>", unsafe_allow_html=True)
            
            if not cleaned_df.empty:
                # 1. Δημιουργία 2D Πίνακα για το Heatmap
                heatmap_df = cleaned_df.groupby(['Ακαδ. Έτος', 'Περίοδος'])['ECTS'].sum().reset_index()
                
                # Ορισμός Αξόνων (Χ = Έτη, Υ = Εξεταστικές)
                years = sorted(cleaned_df['Ακαδ. Έτος'].unique())
                periods = ['Φεβ', 'Ιουν', 'Σεπ'] # Σταθερή σειρά για τον κάθετο άξονα
                
                z_data = []
                hover_data = []
                # Ορίζουμε το ταβάνι (Overclock) γύρω στα 40 ECTS
                max_ects_val = heatmap_df['ECTS'].max() if not heatmap_df.empty else 30
                z_max = max(40, max_ects_val) 
                
                for p in periods:
                    p_row = []
                    h_row = []
                    for y in years:
                        # Ψάχνουμε αν υπάρχει εγγραφή για το συγκεκριμένο έτος και περίοδο
                        val_series = heatmap_df[(heatmap_df['Ακαδ. Έτος'] == y) & (heatmap_df['Περίοδος'] == p)]['ECTS']
                        val = val_series.sum() if not val_series.empty else 0
                        
                        p_row.append(val)
                        
                        # Προσαρμοσμένο Cyber Hover Text
                        if val == 0:
                            status = "OFFLINE (0 ECTS)"
                        elif val <= 15:
                            status = "LOW POWER MODE"
                        elif val <= 30:
                            status = "OPTIMAL YIELD"
                        else:
                            status = "OVERCLOCK DETECTED ⚠️️"
                            
                        h_row.append(f"<b>Έτος:</b> {y}<br><b>Περίοδος:</b> {p}<br><b>Απόδοση:</b> {val} ECTS<br><b>Status:</b> {status}")
                        
                    z_data.append(p_row)
                    hover_data.append(h_row)
                    
                # 2. Χτίσιμο του Plotly Heatmap
                fig_heat = go.Figure(data=go.Heatmap(
                    z=z_data, x=years, y=periods, text=hover_data,
                    hoverinfo='text',
                    colorscale=[
                        [0.0, '#05070a'],       # 0 ECTS: Σκοτεινό background (κλειστό LED)
                        [0.1, '#112233'],       # Ελάχιστη δραστηριότητα (Σκούρο μπλε/γκρι)
                        [0.5, a_color],         # Κανονική δραστηριότητα (Παίρνει το χρώμα της κλάσης σου/Archetype!)
                        [1.0, '#ffffff']        # Overclock (Max ECTS): Λευκό/Λαμπερό
                    ],
                    zmin=0, zmax=z_max,
                    xgap=6, ygap=6, # Τα κενά μεταξύ των κουτιών για να θυμίζει GitHub Contribution Graph
                    showscale=False
                ))
                
                fig_heat.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=20, l=40, r=20), height=220,
                    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(family="'Share Tech Mono', monospace", color='#bdc3c7')),
                    yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(family="'Share Tech Mono', monospace", color='#bdc3c7'), autorange='reversed'),
                    hoverlabel=dict(bgcolor='#0a0e17', bordercolor=a_color, font=dict(family="'Share Tech Mono', monospace", color='#ecf0f1', size=13))
                )
                
                st.plotly_chart(fig_heat, use_container_width=True)

            # --- ΥΠΟΛΟΙΠΑ ΓΡΑΦΗΜΑΤΑ (ORIGINAL) ---
            st.markdown("---")
            st.subheader("Γραμμική & Αθροιστική Ανάλυση")
            st.plotly_chart(fig_cum, use_container_width=True)
            st.plotly_chart(fig_gpa, use_container_width=True)
            
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1: st.plotly_chart(fig_dist, use_container_width=True) 
            with c_chart2: st.plotly_chart(fig_category, use_container_width=True)

        # ==========================================
        # TAB 3: 3D SPACE & TIMELINE 
        # ==========================================
        with tab3:
            st.subheader("Χωρική Ανάλυση & Ιστορικό")
            st.markdown("Περιηγήσου στον 3D χώρο για να δεις τη σχέση Δυσκολίας - Βαθμού στον χρόνο.")
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.plotly_chart(fig_bar, use_container_width=True)

        # ==========================================
        # TAB 4: SIMULATOR & TOOLS
        # ==========================================
        with tab4:
            st.subheader("🔮 AI Προσομοιωτής Βαθμού")
            has_thesis = not thesis_df.empty
            current_points = (cleaned_df['Βαθμός'] * cleaned_df['ECTS']).sum()
            missing_total_ects = max(0, 300 - total_ects)
            missing_courses = max(0, target_courses - total_courses)
            
            if missing_total_ects > 0 or missing_courses > 0:
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    if missing_courses > 0:
                        missing_course_ects = missing_total_ects - (30 if not has_thesis else 0)
                        temp_df = regular_courses_df.copy().reset_index(drop=True)
                        if not temp_df.empty:
                            temp_df['Distance'] = abs(temp_df['ECTS'] - (missing_course_ects/missing_courses)) + 1.5 * ((len(temp_df)-1 - temp_df.index) / max(1, len(temp_df)-1))
                            ai_pred = temp_df.nsmallest(min(7, len(temp_df)), 'Distance')['Βαθμός'].mean()
                            ai_grade = float(max(5.0, min(10.0, round(ai_pred, 1))))
                        else: ai_grade = 7.5
                        
                        st.info(f"🤖 **k-NN Πρόβλεψη:** Αναμένεται να γράψεις **~{ai_grade}** στα {missing_courses} μαθήματα.")
                        
                        # --- Cloud Fix: Απόλυτη προστασία από NoneType στα Sliders ---
                        if st.session_state.get('sim_course_grade') is None:
                            st.session_state['sim_course_grade'] = ai_grade
                            
                        exp_course_grade = st.slider("Στόχος Μ.Ο. εναπομεινάντων:", min_value=5.0, max_value=10.0, step=0.1, key="sim_course_grade")
                    else:
                        exp_course_grade, missing_course_ects = 0, 0
                        st.info("Έχεις περάσει όλα τα απαιτούμενα μαθήματα!")
                        
                with col_s2:
                    if not has_thesis:
                        st.info("💡 **Tip:** Στη Διπλωματική ο στόχος ορίστηκε στο 9.0 από προεπιλογή.")
                        
                        if st.session_state.get('sim_thesis_grade') is None:
                            st.session_state['sim_thesis_grade'] = 9.0
                            
                        exp_thesis_grade = st.slider("Στόχος Διπλωματικής (30 ECTS):", min_value=5.0, max_value=10.0, step=0.1, key="sim_thesis_grade")
                    else:
                        exp_thesis_grade = 0
                        st.success("Έχεις ήδη περάσει τη Διπλωματική Εργασία! 🐉")
                
                future_points = current_points + (missing_course_ects * exp_course_grade) + (30 * exp_thesis_grade if not has_thesis else 0)
                future_ects = total_ects + missing_course_ects + (30 if not has_thesis else 0)
                simulated_gpa = future_points / future_ects if future_ects > 0 else 0.0
                
                sim_class = "Άριστα 🏆" if simulated_gpa >= 8.5 else "Λίαν Καλώς 🥈" if simulated_gpa >= 6.5 else "Καλώς 🥉"
                st.success(f"✨ **Τελική Προβολή Πτυχίου:** Τελικός βαθμός **{simulated_gpa:.2f} ({sim_class})**!")
            else:
                st.info("Έχεις συγκεντρώσει 300+ ECTS! Ο βαθμός σου έχει κλειδώσει.")

            # --- MISSION LOADOUT (TACTICAL PLANNER) ---
            st.markdown("---")
            st.subheader("🎯 Mission Loadout (Στρατηγικό Πλάνο Εξεταστικής)")
            st.markdown("Επίλεξε συγκεκριμένα 'Bounties' (μη περασμένα μαθήματα) για το επόμενο session. Όρισε τους στόχους σου και δες τη live πρόβλεψη.")
            
            loadout_options = raw_quests[~raw_quests['Μάθημα'].isin(passed_courses)].drop_duplicates(subset=['Μάθημα']).copy()
            loadout_options['ECTS'] = pd.to_numeric(loadout_options['ECTS'], errors='coerce').fillna(0)
            
            if not loadout_options.empty:
                ae_col1, ae_col2 = st.columns([1, 2.5])
                with ae_col1:
                    if st.button("⚡ AUTO-EQUIP (AI Loadout)", use_container_width=True):
                        import random
                        available = loadout_options[['Μάθημα', 'ECTS']].to_dict('records')
                        
                        heavy = [c for c in available if c['ECTS'] >= 6]
                        light = [c for c in available if c['ECTS'] < 6]
                        
                        random.shuffle(heavy)
                        random.shuffle(light)
                        
                        optimized_loadout = []
                        curr_ects = 0
                        
                        for c in heavy[:2]:
                            if curr_ects + c['ECTS'] <= 34:
                                optimized_loadout.append(c['Μάθημα'])
                                curr_ects += c['ECTS']
                                
                        for c in light + heavy[2:]:
                            if curr_ects + c['ECTS'] <= 33: 
                                optimized_loadout.append(c['Μάθημα'])
                                curr_ects += c['ECTS']
                            if curr_ects >= 28: 
                                break
                                
                        st.session_state.loadout_missions = optimized_loadout
                        st.rerun()
                        
                with ae_col2:
                    st.markdown("<div style='padding-top: 8px; color: #7f8c8d; font-size: 0.85rem;'><b>Knapsack Alg:</b> Αυτόματη σύνθεση ιδανικού Loadout (~30 ECTS) με μίξη δύσκολων και εύκολων μαθημάτων. <span style='color: #f1c40f;'>Κάνε κλικ ξανά για re-roll!</span></div>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                valid_missions = loadout_options['Μάθημα'].tolist()
                
                # Αν υπάρχουν επιλεγμένα μαθήματα που πλέον δεν είναι valid, τα σβήνουμε
                if 'loadout_missions' in st.session_state and st.session_state.loadout_missions is not None:
                    st.session_state.loadout_missions = [m for m in st.session_state.loadout_missions if m in valid_missions]
                else:
                    st.session_state.loadout_missions = []
                
                selected_missions = st.multiselect(
                    "Ενεργοποίηση Αποστολών:",
                    options=valid_missions,
                    key="loadout_missions",
                    placeholder="Επίλεξε μαθήματα από τη λίστα..."
                )
                
                if selected_missions:
                    pre_mission_ects = sum([loadout_options[loadout_options['Μάθημα'] == m].iloc[0]['ECTS'] for m in selected_missions])
                    mission_count = len(selected_missions)
                    
                    is_overclocked = pre_mission_ects > 35
                    
                    if pre_mission_ects <= 15:
                        d_color, d_title, d_msg, d_icon = "#2ecc71", "SYSTEM SECURE", "Ελαφρύς φόρτος. Ιδανικό για High Grades.", "🛡️"
                    elif pre_mission_ects <= 35:
                        d_color, d_title, d_msg, d_icon = "#3498db", "STANDARD PROTOCOL", "Κανονική εξεταστική. Απαιτείται Focus.", "⚙️"
                    else:
                        d_color, d_title, d_msg, d_icon = "#ff003c", "CRITICAL OVERLOAD", "SYSTEM INSTABILITY DETECTED. COOLING FAILURE IMMINENT.", "⚠️"

                    if is_overclocked:
                        st.markdown(f"""
                        <div style='background: repeating-linear-gradient(45deg, #2a0808, #2a0808 10px, #1a0000 10px, #1a0000 20px); border: 2px solid {d_color}; border-radius: 6px; padding: 15px; margin-top: 15px; margin-bottom: 25px; box-shadow: 0 0 30px {d_color}80, inset 0 0 20px {d_color}60; display: flex; align-items: center; animation: overclock-flash 0.3s infinite alternate;'>
                            <div style='font-size: 2.8rem; margin-right: 15px; text-shadow: 0 0 15px {d_color}; animation: shake 0.2s infinite;'>{d_icon}</div>
                            <div>
                                <div style='color: {d_color}; font-family: monospace; font-weight: bold; font-size: 1.3rem; letter-spacing: 2px; text-shadow: 0 0 8px {d_color};'>{d_title} [ {pre_mission_ects:g} ECTS ]</div>
                                <div style='color: #fff; font-size: 0.95rem; font-weight: bold;'>{mission_count} Ενεργά Bounties — <span style='color: #f1c40f;'>{d_msg}</span></div>
                            </div>
                        </div>
                        <style>
                        @keyframes overclock-flash {{ 0% {{ box-shadow: 0 0 10px {d_color}40, inset 0 0 10px {d_color}40; border-color: #800000; }} 100% {{ box-shadow: 0 0 40px {d_color}, inset 0 0 30px {d_color}; border-color: {d_color}; }} }}
                        @keyframes shake {{ 0% {{ transform: translate(1px, 1px) rotate(0deg); }} 25% {{ transform: translate(-1px, -2px) rotate(-1deg); }} 50% {{ transform: translate(-3px, 0px) rotate(1deg); }} 75% {{ transform: translate(3px, 2px) rotate(0deg); }} 100% {{ transform: translate(1px, -1px) rotate(1deg); }} }}
                        </style>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='background: #0a0e17; border: 1px solid {d_color}; border-left: 5px solid {d_color}; border-radius: 4px; padding: 12px 15px; margin-top: 15px; margin-bottom: 25px; box-shadow: 0 0 15px {d_color}40; display: flex; align-items: center;'>
                            <div style='font-size: 1.8rem; margin-right: 15px; text-shadow: 0 0 10px {d_color};'>{d_icon}</div>
                            <div>
                                <div style='color: {d_color}; font-family: monospace; font-weight: bold; font-size: 1.15rem; letter-spacing: 1px;'>{d_title} [ {pre_mission_ects:g} ECTS ]</div>
                                <div style='color: #bdc3c7; font-size: 0.9rem;'>{mission_count} Ενεργά Bounties — <i>{d_msg}</i></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<h5 style='color: #00ffcc; font-family: monospace;'>⚙️ Target Parameters (Στόχοι Βαθμολογίας)</h5>", unsafe_allow_html=True)
                    
                    mission_points = 0.0
                    mission_ects = 0.0
                    
                    cols = st.columns(3)
                    for i, mission in enumerate(selected_missions):
                        mission_data = loadout_options[loadout_options['Μάθημα'] == mission].iloc[0]
                        m_ects = mission_data['ECTS']
                        
                        m_border = "#ff003c" if is_overclocked else "#f39c12"
                        m_bg = "background: rgba(255, 0, 60, 0.1);" if is_overclocked else "background: #111b24;"
                        
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div style='{m_bg} padding: 10px; border-radius: 8px; border-left: 3px solid {m_border}; margin-bottom: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); transition: all 0.3s;'>
                                <div style='color: #bdc3c7; font-size: 0.85rem; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{mission}'>{mission}</div>
                                <div style='color: #2ecc71; font-size: 0.8rem; font-family: monospace;'>Reward: {m_ects} ECTS</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # --- Cloud Fix για τα Loadout Grades ---
                            grade_key = f"grade_{mission}"
                            if st.session_state.get(grade_key) is None:
                                st.session_state[grade_key] = 5.0
                                
                            target_grade = st.number_input("Target Grade:", min_value=5.0, max_value=10.0, step=0.5, key=grade_key, label_visibility="collapsed")
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            mission_points += target_grade * m_ects
                            mission_ects += m_ects 
                    
                    session_gpa = mission_points / mission_ects if mission_ects > 0 else 0.0
                    proj_ects = total_ects + mission_ects
                    proj_gpa = (current_points + mission_points) / proj_ects if proj_ects > 0 else 0.0
                    
                    rounded_current = round(final_gpa, 2)
                    rounded_proj = round(proj_gpa, 2)
                    diff = rounded_proj - rounded_current
                    
                    if abs(diff) < 0.001:
                        diff_str = "0.00"
                        diff_color = "#7f8c8d"
                    elif diff > 0:
                        diff_str = f"+{diff:.2f}"
                        diff_color = "#2ecc71"
                    else:
                        diff_str = f"{diff:.2f}"
                        diff_color = "#e74c3c"
                    
                    box_anim = "animation: overclock-stat 0.5s infinite alternate;" if is_overclocked else ""
                    box_border = "#ff003c" if is_overclocked else "#34495e"
                    
                    st.markdown(f"""
                    <style>
                    .loadout-stat {{
                        background: #0a0e17;
                        border: 1px solid {box_border};
                        border-radius: 8px;
                        padding: 15px;
                        text-align: center;
                        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
                        {box_anim}
                    }}
                    @keyframes overclock-stat {{ 0% {{ box-shadow: inset 0 0 10px rgba(255,0,60,0.2); border-color: #800000; }} 100% {{ box-shadow: inset 0 0 30px rgba(255,0,60,0.6); border-color: #ff003c; }} }}
                    .loadout-label {{ color: #7f8c8d; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }}
                    .loadout-val {{ font-size: 2.2rem; font-family: 'Share Tech Mono', monospace; margin: 5px 0; }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"<h5 style='color: {'#ff003c' if is_overclocked else '#f1c40f'}; margin-top: 15px; padding-bottom: 5px;'>📊 Session Projection {'(OVERCLOCKED - WARNING!)' if is_overclocked else ''}</h5>", unsafe_allow_html=True)
                    
                    l_col1, l_col2, l_col3 = st.columns(3)
                    
                    with l_col1:
                        st.markdown(f"""
                        <div class='loadout-stat' style='{("border-color: #ff003c;" if is_overclocked else "border-color: #3498db;")}'>
                            <div class='loadout-label'>Session GPA</div>
                            <div class='loadout-val' style='color: #3498db; text-shadow: 0 0 10px rgba(52,152,219,0.5);'>{session_gpa:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with l_col2:
                        st.markdown(f"""
                        <div class='loadout-stat' style='{("border-color: #ff003c;" if is_overclocked else "border-color: #2ecc71;")}'>
                            <div class='loadout-label'>New Total ECTS</div>
                            <div class='loadout-val' style='color: #2ecc71; text-shadow: 0 0 10px rgba(46,204,113,0.5);'>{proj_ects:g} <span style='font-size: 1rem; color: #7f8c8d;'>(+{mission_ects:g})</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with l_col3:
                        st.markdown(f"""
                        <div class='loadout-stat' style='{("border-color: #ff003c;" if is_overclocked else "border-color: #f1c40f;")}'>
                            <div class='loadout-label'>Projected Overall GPA</div>
                            <div class='loadout-val' style='color: #f1c40f; text-shadow: 0 0 10px rgba(241,196,15,0.5);'>{rounded_proj:.2f} <span style='font-size: 1rem; color: {diff_color};'>({diff_str})</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("📡 Το Loadout είναι άδειο. Διάλεξε Bounties από τη λίστα ή πάτα το AUTO-EQUIP!")
            else:
                st.success("Δεν υπάρχουν χρωστούμενα μαθήματα! Το Loadout είναι άδειο. 🎓")

        # ==========================================
        # TAB 5: DEEP DIVE STUDY HUB
        # ==========================================
        with tab5:
            # --- DEEP DIVE STUDY HUB (3-COLUMN LAYOUT) ---
            st.subheader("🧠 Deep Dive Study Hub")
            st.markdown("Ολοκληρωμένο περιβάλλον εστίασης. Διαχειρίσου τον χρόνο σου, κράτα γρήγορες σημειώσεις και μείνε στο 'Zone' με το Cyber-Radio.")
            
            # Χωρίζουμε τον χώρο σε 3 στήλες (Αριστερά: 1, Κέντρο: 1.5, Δεξιά: 1)
            hub_col1, hub_col2, hub_col3 = st.columns([1, 1.5, 1], gap="large")
            
            with hub_col1:
                st.markdown("<h4 style='color: #e74c3c; font-family: monospace;'>📝 Memory Buffer</h4>", unsafe_allow_html=True)
                st.markdown("<span style='color: #7f8c8d; font-size: 0.85rem;'>Προσωρινή μνήμη για SOS, ιδέες ή bugs.</span>", unsafe_allow_html=True)
                
                # ΠΡΟΣΘΗΚΗ ΤΟΥ KEY ΕΔΩ:
                buffer_notes = st.text_area(
                    "Scratchpad", 
                    placeholder="> Γράψε εδώ... π.χ.\n- Να δω τον αλγόριθμο Dijkstra\n- Κεφάλαιο 4, σελ. 112 SOS\n- Fix line 45 στο script", 
                    height=365, 
                    label_visibility="collapsed",
                    key="memory_notes" 
                )
                
                # Κουμπί εξαγωγής σημειώσεων
                st.download_button(
                    label="💾 Export Notes (.txt)",
                    data=buffer_notes,
                    file_name="deep_dive_notes.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
            with hub_col2:
                st.markdown("<h4 style='color: #00ffcc; font-family: monospace;'>⏳ Focus Core</h4>", unsafe_allow_html=True)
                st.markdown("<span style='color: #7f8c8d; font-size: 0.85rem;'>Διαχείριση χρόνου και Deep Dive cycles.</span>", unsafe_allow_html=True)
                
                # Το κεντρικό Pomodoro (Παραμένει ίδιο)
                pomodoro_html = """
                <!DOCTYPE html>
                <html>
                <head>
                <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
                <style>
                body {
                    background-color: transparent;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                    font-family: 'Share Tech Mono', monospace;
                    color: #00ffcc;
                }
                .pomodoro-container {
                    background: #0a0e17;
                    border: 2px solid #00ffcc;
                    border-radius: 12px;
                    padding: 20px 25px;
                    text-align: center;
                    box-shadow: 0 0 15px rgba(0, 255, 204, 0.2), inset 0 0 20px rgba(0, 255, 204, 0.1);
                    width: 100%;
                    box-sizing: border-box;
                }
                .mission-input {
                    background: #111b24;
                    border: 1px dashed #34495e;
                    color: #f1c40f;
                    padding: 10px;
                    width: 100%;
                    box-sizing: border-box;
                    border-radius: 6px;
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 0.95rem;
                    margin-bottom: 15px;
                    text-align: center;
                    outline: none;
                    transition: border-color 0.3s, box-shadow 0.3s;
                }
                .mission-input:focus { border-color: #f1c40f; box-shadow: 0 0 10px rgba(241, 196, 15, 0.3); }
                .timer-display {
                    font-size: 4.2rem;
                    text-shadow: 0 0 15px rgba(0, 255, 204, 0.8);
                    margin-bottom: 5px;
                    letter-spacing: 2px;
                    transition: color 0.3s, text-shadow 0.3s;
                }
                .mode-text {
                    color: #f39c12;
                    font-size: 0.9rem;
                    margin-bottom: 10px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }
                .progress-bg {
                    background: rgba(255,255,255,0.05);
                    border-radius: 10px;
                    height: 8px;
                    width: 100%;
                    margin: 10px 0 15px 0;
                    overflow: hidden;
                    border: 1px solid #1a252f;
                }
                .progress-fill {
                    background: #00ffcc;
                    height: 100%;
                    width: 100%;
                    transition: width 1s linear, background 0.3s;
                    box-shadow: 0 0 10px #00ffcc;
                }
                .btn-group { display: flex; justify-content: center; gap: 8px; margin-top: 10px; }
                .btn {
                    background: #111b24;
                    color: #ecf0f1;
                    border: 1px solid #34495e;
                    padding: 8px 10px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 0.85rem;
                    transition: all 0.2s ease-in-out;
                    flex-grow: 1;
                }
                .btn:hover { border-color: #00ffcc; color: #00ffcc; box-shadow: 0 0 10px rgba(0, 255, 204, 0.4); transform: translateY(-2px); }
                .stats { margin-top: 15px; font-size: 0.9rem; color: #7f8c8d; border-top: 1px dashed #34495e; padding-top: 10px; }
                .stats span { color: #2ecc71; font-weight: bold; font-size: 1.1rem; }
                </style>
                </head>
                <body>
                <div class="pomodoro-container">
                    <input type="text" class="mission-input" id="mission" placeholder="🎯 Input Active Mission..." />
                    <div class="mode-text" id="mode-text">SYSTEM STANDBY</div>
                    <div class="timer-display" id="timer">30:00</div>
                    <div class="progress-bg"><div class="progress-fill" id="progress"></div></div>
                    <div class="btn-group">
                        <button class="btn" onclick="startTimer()">START</button>
                        <button class="btn" onclick="pauseTimer()">PAUSE</button>
                        <button class="btn" onclick="resetTimer()">RESET</button>
                    </div>
                    <div class="btn-group">
                        <button class="btn" style="border-color: #e67e22; color: #e67e22;" onclick="toggleMode()" id="mode-btn">SWITCH TO REST MODE</button>
                    </div>
                    <div class="stats">Deep Dive Cycles: <span id="cycles">0</span></div>
                </div>
                
                <script>
                    const WORK_TIME = 30 * 60;
                    const REST_TIME = 5 * 60;
                    let timeLeft = WORK_TIME;
                    let totalTime = WORK_TIME;
                    let timerId = null;
                    let isWorkMode = true;
                    let cycles = 0;
                    
                    const display = document.getElementById('timer');
                    const modeText = document.getElementById('mode-text');
                    const modeBtn = document.getElementById('mode-btn');
                    const progressFill = document.getElementById('progress');
                    const cyclesDisplay = document.getElementById('cycles');
                    const missionInput = document.getElementById('mission');
                    
                    const alertSound = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3'); 
                    
                    function updateDisplay() {
                        let minutes = Math.floor(timeLeft / 60);
                        let seconds = timeLeft % 60;
                        display.textContent = (minutes < 10 ? '0' : '') + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
                        progressFill.style.width = ((timeLeft / totalTime) * 100) + '%';
                    }
                    
                    function updateTheme() {
                        let color = isWorkMode ? '#e74c3c' : '#3498db';
                        if (timerId === null && timeLeft === totalTime) color = '#00ffcc';
                        display.style.color = color;
                        display.style.textShadow = `0 0 15px ${color}`;
                        progressFill.style.background = color;
                        progressFill.style.boxShadow = `0 0 10px ${color}`;
                    }
                    
                    function startTimer() {
                        if (timerId !== null) return;
                        missionInput.disabled = true; missionInput.style.opacity = '0.7';
                        modeText.textContent = isWorkMode ? 'DEEP DIVE: ACTIVE' : 'COOLING PROTOCOL';
                        modeText.style.color = isWorkMode ? '#e74c3c' : '#3498db';
                        
                        timerId = setInterval(() => {
                            timeLeft--;
                            updateDisplay();
                            if (timeLeft <= 0) {
                                clearInterval(timerId); timerId = null;
                                alertSound.play();
                                if (isWorkMode) { cycles++; cyclesDisplay.textContent = cycles; }
                                toggleMode();
                            }
                        }, 1000);
                        updateTheme(); 
                    }
                    
                    function pauseTimer() {
                        if (timerId === null) return;
                        clearInterval(timerId); timerId = null;
                        modeText.textContent = 'SYSTEM PAUSED'; modeText.style.color = '#f1c40f';
                        missionInput.disabled = false; missionInput.style.opacity = '1';
                        display.style.color = '#f1c40f'; display.style.textShadow = '0 0 15px rgba(241, 196, 15, 0.8)';
                        progressFill.style.background = '#f1c40f'; progressFill.style.boxShadow = '0 0 10px #f1c40f';
                    }
                    
                    function resetTimer() {
                        clearInterval(timerId); timerId = null;
                        totalTime = isWorkMode ? WORK_TIME : REST_TIME; timeLeft = totalTime;
                        missionInput.disabled = false; missionInput.style.opacity = '1';
                        updateDisplay();
                        modeText.textContent = 'SYSTEM STANDBY'; modeText.style.color = '#f39c12';
                        updateTheme();
                    }
                    
                    function toggleMode() {
                        isWorkMode = !isWorkMode;
                        modeBtn.textContent = isWorkMode ? 'SWITCH TO REST MODE' : 'SWITCH TO WORK MODE';
                        resetTimer();
                    }
                </script>
                </body>
                </html>
                """
                # Μειώσαμε το height από 420 σε 380 για να "μαζέψει" το κενό από κάτω
                st.components.v1.html(pomodoro_html, height=360) 

                st.info("💡 **Focus Tip:** Όσο το Focus Core είναι κόκκινο, βάλε το κινητό σε DND.", icon="🔒")
                
            with hub_col3:
                st.markdown("<h4 style='color: #f39c12; font-family: monospace;'>📻 Cyber-Radio</h4>", unsafe_allow_html=True)
                st.markdown("<span style='color: #7f8c8d; font-size: 0.85rem;'>Analog Frequency Tuner.</span>", unsafe_allow_html=True)
                
                # ΝΕΟ ΟΛΟΚΛΗΡΩΜΕΝΟ RADIO COMPONENT (Ευθυγραμμισμένο με το Pomodoro)
                radio_html = """
                <!DOCTYPE html>
                <html>
                <head>
                <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
                <style>
                body { font-family: 'Share Tech Mono', monospace; color: #ecf0f1; margin: 0; display: flex; justify-content: center; background-color: transparent; }
                .radio-box {
                    background: #0a0e17;
                    border: 2px solid #f39c12;
                    border-radius: 12px;
                    width: 100%;
                    padding: 20px 25px;
                    box-shadow: 0 0 15px rgba(243, 156, 18, 0.2), inset 0 0 20px rgba(0,0,0,0.8);
                    box-sizing: border-box;
                    text-align: center;
                }
                
                /* Custom Analog Slider */
                .slider-container { margin-bottom: 20px; position: relative; }
                .labels { display: flex; justify-content: space-between; font-size: 0.75rem; color: #7f8c8d; margin-bottom: 8px; padding: 0 5px; }
                input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
                input[type=range]::-webkit-slider-thumb {
                    -webkit-appearance: none; height: 24px; width: 12px; border-radius: 3px;
                    background: #e74c3c; cursor: pointer; box-shadow: 0 0 10px #e74c3c;
                    border: 2px solid #fff; margin-top: -10px;
                }
                input[type=range]::-webkit-slider-runnable-track {
                    width: 100%; height: 4px; cursor: pointer; background: #34495e; border-radius: 2px;
                }
                
                /* LED Screen */
                .led-screen {
                    background: #05070a; border: 1px solid #f39c12; padding: 12px; border-radius: 6px;
                    font-size: 1.05rem; margin-bottom: 20px; text-shadow: 0 0 8px #f39c12; color: #f39c12;
                    box-shadow: inset 0 0 10px rgba(243,156,18,0.2); transition: all 0.3s;
                }
                
                /* Video Player Frame */
                .screen-container {
                    background: #000; border-radius: 6px; overflow: hidden; position: relative;
                    height: 210px; border: 1px solid #2c3e50;
                }
                iframe { width: 100%; height: 100%; border: none; }
                .offline-msg { display: flex; align-items: center; justify-content: center; height: 100%; color: #34495e; font-size: 0.95rem; letter-spacing: 1px;}
                
                /* Custom AUX Input */
                .aux-input {
                    width: 90%; background: #111b24; border: 1px dashed #00ffcc; color: #00ffcc;
                    padding: 10px; font-family: 'Share Tech Mono', monospace; font-size: 0.85rem;
                    margin-top: 15px; border-radius: 4px; outline: none; display: none; text-align: center;
                }
                .aux-input::placeholder { color: #00ffcc; opacity: 0.5; }
                .aux-input:focus { border: 1px solid #00ffcc; box-shadow: 0 0 10px rgba(0,255,204,0.3); }
                </style>
                </head>
                <body>
                <div class="radio-box">
                    <div class="slider-container">
                        <div class="labels">
                            <span>OFF</span><span>98.5</span><span>101.2</span><span>104.4</span><span>107.8</span><span>AUX</span>
                        </div>
                        <input type="range" id="freq-slider" min="0" max="5" value="1">
                    </div>
                    <div class="led-screen" id="led">TUNED: 98.5 FM (LOFI)</div>
                    <div class="screen-container" id="screen">
                        <!-- iframe or offline msg goes here -->
                    </div>
                    <input type="text" id="aux-input" class="aux-input" placeholder="🔗 Paste YouTube URL & Press Enter...">
                </div>

                <script>
                    const slider = document.getElementById('freq-slider');
                    const led = document.getElementById('led');
                    const screen = document.getElementById('screen');
                    const auxInput = document.getElementById('aux-input');

                    const stations = [
                        { name: "POWER OFF", color: "#34495e", url: null },
                        { name: "TUNED: 98.5 FM (LOFI)", color: "#e67e22", url: "https://www.youtube.com/embed/lTRiuFIWV54" },
                        { name: "TUNED: 101.2 FM (JAZZ)", color: "#1abc9c", url: "https://www.youtube.com/embed/MYPVQccHhAQ?autoplay=1" },
                        { name: "TUNED: 104.4 FM (FANTASY STUDY)", color: "#6c5ce7", url: "https://www.youtube.com/embed/mm0QSsRwzUo?autoplay=1" },
                        { name: "TUNED: 107.8 FM (PIANO)", color: "#2980b9", url: "https://www.youtube.com/embed/rZxbHDtlcPU?autoplay=1" },
                        { name: "AUXILIARY LINK ACTIVE", color: "#00ffcc", url: "aux" }
                    ];

                    function getEmbedUrl(url) {
                        let vid = "";
                        if (url.includes("v=")) {
                            vid = url.split("v=")[1].substring(0,11);
                        } else if (url.includes("youtu.be/")) {
                            vid = url.split("youtu.be/")[1].substring(0,11);
                        }
                        return vid ? "https://www.youtube.com/embed/" + vid + "?autoplay=1" : "";
                    }

                    function updateRadio() {
                        const val = parseInt(slider.value);
                        const st = stations[val];

                        // Αλλαγή Χρωμάτων LED
                        led.textContent = st.name;
                        led.style.color = st.color;
                        led.style.textShadow = `0 0 8px ${st.color}`;
                        led.style.borderColor = st.color;
                        led.style.boxShadow = `inset 0 0 10px ${st.color}40`;

                        // Αλλαγή Οθόνης / Iframe
                        if (st.url === null) {
                            screen.innerHTML = '<div class="offline-msg">[ ΣΥΣΤΗΜΑ ΑΝΕΝΕΡΓΟ ]</div>';
                            auxInput.style.display = "none";
                        } else if (st.url === "aux") {
                            screen.innerHTML = '<div class="offline-msg" style="color:#00ffcc;">[ ΑΝΑΜΟΝΗ ΣΗΜΑΤΟΣ AUX ]</div>';
                            auxInput.style.display = "inline-block";
                            auxInput.value = "";
                        } else {
                            screen.innerHTML = `<iframe src="${st.url}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
                            auxInput.style.display = "none";
                        }
                    }

                    // Listener για το Enter στο πεδίο AUX
                    auxInput.addEventListener('keypress', function (e) {
                        if (e.key === 'Enter') {
                            const embed = getEmbedUrl(this.value);
                            if (embed) {
                                screen.innerHTML = `<iframe src="${embed}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
                            } else {
                                screen.innerHTML = '<div class="offline-msg" style="color:#e74c3c;">[ INVALID SIGNAL ]</div>';
                            }
                        }
                    });

                    // Αρχικοποίηση
                    slider.addEventListener('input', updateRadio);
                    updateRadio();
                </script>
                </body>
                </html>
                """
                st.components.v1.html(radio_html, height=472)

        # ==========================================
        # TAB 6: CO-OP MODE (Split-Screen Multiplayer)
        # ==========================================
        with tab6:
            st.subheader("⚔️ Co-op Mode: Player 1 vs Player 2")
            st.markdown("Ανέβασε το αρχείο Excel ενός συμφοιτητή σου για να συγκρίνετε αναλυτικά τα στατιστικά, τη Διπλωματική, την Πρακτική και τα Achievements σας!")
            
            uploaded_file_2 = st.file_uploader("Επίλεξε το αρχείο του Player 2", type=['xlsx'], key="p2_upload")
            
            if uploaded_file_2 is not None:
                try:
                    # Καθαρισμός δεδομένων P2
                    raw_p2 = pd.read_excel(uploaded_file_2, header=1)
                    df_p2 = clean_classweb_data(raw_p2)
                    
                    is_int_2 = df_p2['Μάθημα'].str.contains('ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ', case=False, na=False)
                    is_the_2 = df_p2['Μάθημα'].str.contains('ΔΙΠΛΩΜΑΤΙΚΗ', case=False, na=False)
                    internship_df_2 = df_p2[is_int_2]
                    thesis_df_2 = df_p2[is_the_2]
                    reg_p2 = df_p2[~(is_int_2 | is_the_2)].copy()
                    
                    ects_2 = df_p2['ECTS'].sum()
                    courses_2 = len(reg_p2)
                    gpa_2 = (df_p2['Βαθμός'] * df_p2['ECTS']).sum() / ects_2 if ects_2 > 0 else 0.0
                    
                    # Βοηθητικές Συναρτήσεις για Co-op Stats
                    def get_max_streak(df_reg):
                        p_counts = { (y, p): len(g) for (y, p), g in df_reg.groupby(['Ακαδ. Έτος', 'Περίοδος']) if y != "Άγνωστο" }
                        mx_str = 0
                        if p_counts:
                            min_y = min([int(y.split('-')[0]) for y, p in p_counts.keys()])
                            max_y = max([int(y.split('-')[0]) for y, p in p_counts.keys()])
                            curr_str = 0
                            for y in range(min_y, max_y + 1):
                                for p in ['Φεβ', 'Ιουν', 'Σεπ']:
                                    if p_counts.get((f"{y}-{str(y+1)[-2:]}", p), 0) >= 2:
                                        curr_str += 1
                                        mx_str = max(mx_str, curr_str)
                                    else: curr_str = 0
                        return mx_str

                    def get_golden_sem(df_reg):
                        stats = pd.DataFrame([{'Period': f"{p} '{y[-2:]}", 'Count': len(g), 'GPA': (g['Βαθμός']*g['ECTS']).sum()/g['ECTS'].sum() if g['ECTS'].sum()>0 else 0} for (y, p), g in df_reg.groupby(['Ακαδ. Έτος', 'Περίοδος'])])
                        if not stats.empty:
                            return stats.sort_values(by=['Count', 'GPA'], ascending=[False, False]).iloc[0]
                        return None
                        
                    def get_badges_count(df_reg, df_thesis, df_int):
                        count = 0
                        if not df_reg.empty:
                            if (df_reg['Βαθμός'] == 10).any(): count += 1
                            ects_per_period = df_reg.groupby(['Ακαδ. Έτος', 'Περίοδος'])['ECTS'].sum()
                            if not ects_per_period.empty and ects_per_period.max() >= 30: count += 1
                            sept = df_reg[df_reg['Περίοδος'] == 'Σεπ']
                            if not sept.empty and sept.groupby('Ακαδ. Έτος').size().max() >= 3: count += 1
                            if get_max_streak(df_reg) >= 3: count += 1
                        if not df_thesis.empty: count += 1
                        if not df_int.empty: count += 1
                        return count

                    streak_1 = get_max_streak(regular_courses_df)
                    streak_2 = get_max_streak(reg_p2)
                    
                    gold_1 = get_golden_sem(regular_courses_df)
                    gold_2 = get_golden_sem(reg_p2)
                    
                    badges_1 = get_badges_count(regular_courses_df, thesis_df, internship_df)
                    badges_2 = get_badges_count(reg_p2, thesis_df_2, internship_df_2)
                    
                    # Status Διπλωματικής & Πρακτικής
                    thesis_status_1 = f"✅ Ολοκληρώθηκε (Βαθμός: **{thesis_df.iloc[0]['Βαθμός']}**)" if not thesis_df.empty else "❌ Εκκρεμεί"
                    thesis_status_2 = f"✅ Ολοκληρώθηκε (Βαθμός: **{thesis_df_2.iloc[0]['Βαθμός']}**)" if not thesis_df_2.empty else "❌ Εκκρεμεί"
                    
                    int_status_1 = "✅ Ολοκληρώθηκε" if not internship_df.empty else "❌ Εκκρεμεί"
                    int_status_2 = "✅ Ολοκληρώθηκε" if not internship_df_2.empty else "❌ Εκκρεμεί"
                    
                    # --- Υπολογισμός Level & Archetype για τον Player 2 ---
                    if ects_2 >= 300:
                        lvl_2, rank_2, avatar_2 = "MAX", level_ranks[-1][1], "🧙‍♂️"
                    else:
                        lvl_2 = int(ects_2 // 30) + 1
                        for cap, title in reversed(level_ranks):
                            if ects_2 >= cap:
                                rank_2 = title
                                break
                        if lvl_2 <= 2: avatar_2 = "🥚"
                        elif lvl_2 <= 4: avatar_2 = "🤓"
                        elif lvl_2 <= 6: avatar_2 = "🥷"
                        elif lvl_2 <= 8: avatar_2 = "🦾"
                        else: avatar_2 = "🦸‍♂️"
                        
                    # Καθαρισμός Ranks (Αφαίρεση Emojis & "Lvl X:")
                    clean_rank_1 = re.sub(r'[^\w\s-]', '', rank_title.split(':')[1] if ':' in rank_title else rank_title).strip()
                    clean_rank_2 = re.sub(r'[^\w\s-]', '', rank_2.split(':')[1] if ':' in rank_2 else rank_2).strip()
                    
                    # Υπολογισμός Archetype για τον Player 2
                    branch_df_2 = df_p2.copy()
                    if not branch_df_2.empty:
                        branch_df_2['Skill_Branch'] = branch_df_2['Μάθημα'].apply(get_skill_branch)
                        branch_df_2['Power_Score'] = 0.004 * (branch_df_2['ECTS'] * (branch_df_2['Βαθμός'] ** 4.5))
                        radar_df_2 = branch_df_2[branch_df_2['Skill_Branch'] != 'General / Core']
                        cat_scores_2 = radar_df_2.groupby('Skill_Branch')['Power_Score'].sum().reset_index()
                        dom_cat_2 = cat_scores_2.loc[cat_scores_2['Power_Score'].idxmax()]['Skill_Branch'] if not cat_scores_2.empty else 'None'
                    else: dom_cat_2 = 'None'
                    
                    if dom_cat_2 == 'Software & Systems': a_title_2, a_color_2 = "Cyber-Mage", "#3498db" 
                    elif dom_cat_2 == 'Hardware & Architecture': a_title_2, a_color_2 = "Mecha-Paladin", "#e74c3c" 
                    elif dom_cat_2 == 'Networks & Comms': a_title_2, a_color_2 = "Network Ninja", "#9b59b6" 
                    elif dom_cat_2 == 'Math & Theory': a_title_2, a_color_2 = "Logic Oracle", "#f1c40f" 
                    elif dom_cat_2 == 'Data & AI': a_title_2, a_color_2 = "AI-Netrunner", "#00ffcc" 
                    elif dom_cat_2 == 'Graphics & Vision': a_title_2, a_color_2 = "Holo-Artisan", "#ff007f" 
                    elif dom_cat_2 == 'Cybersecurity': a_title_2, a_color_2 = "Stealth Decker", "#00ff00" 
                    else: a_title_2, a_color_2 = "Tech-Mercenary", "#ffffff"

                    # Αποτροπή ίδιου χρώματος για να ξεχωρίζουν οι μπάρες και οι ταυτότητες!
                    if a_color == a_color_2:
                        a_color_2 = "#ff007f" # Δίνουμε το Neon Pink στον αντίπαλο αν έχετε το ίδιο Class
                    
                    # --- Συνάρτηση Παραγωγής ID Card HTML ---
                    def generate_id_card(p_name, p_color, p_avatar, p_class, p_lvl, p_rank, p_gpa, p_ects, p_badges):
                        html = f"""
                        <link href="https://fonts.googleapis.com/css2?family=Libre+Barcode+39+Text&display=swap" rel="stylesheet">
                        <div style="display: flex; justify-content: center; margin-bottom: 25px; perspective: 1000px; transform: scale(0.95); transform-origin: top center;">
                        <div style="background: linear-gradient(135deg, #0a0e17 0%, #111b24 100%); border: 2px solid {p_color}; border-radius: 15px; width: 100%; max-width: 680px; padding: 20px; box-shadow: 0 10px 30px {p_color}40, inset 0 0 20px rgba(0,0,0,0.8); display: flex; align-items: center; position: relative; overflow: hidden; transform: rotateX(2deg) rotateY(-2deg); transition: transform 0.3s ease;">
                        <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: linear-gradient(45deg, rgba(255,255,255,0) 40%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0) 60%); transform: rotate(30deg); pointer-events: none; animation: holo-glare 5s infinite linear;"></div>
                        <div style="background: rgba(0,0,0,0.5); border: 2px solid {p_color}; border-radius: 12px; width: 100px; height: 100px; display: flex; justify-content: center; align-items: center; font-size: 3.5rem; text-shadow: 0 0 20px {p_color}; margin-right: 20px; flex-shrink: 0; position: relative; box-shadow: inset 0 0 15px {p_color}40;">
                        {p_avatar}
                        <div style="position: absolute; bottom: -10px; background: {p_color}; color: #000; font-size: 0.6rem; font-weight: bold; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; box-shadow: 0 0 10px {p_color};">VERIFIED</div>
                        </div>
                        <div style="flex-grow: 1; z-index: 2;">
                        <div style="color: #7f8c8d; font-size: 0.65rem; letter-spacing: 2px; margin-bottom: 2px; font-family: 'Share Tech Mono', monospace;">MERCENARY ID // {p_name}</div>
                        <h2 style="color: #ecf0f1; margin: 0 0 8px 0; font-family: 'Share Tech Mono', monospace; font-size: 1.8rem; letter-spacing: 1px; text-transform: uppercase;">{p_rank}</h2>
                        <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                        <div style="background: rgba(255,255,255,0.05); padding: 6px 10px; border-radius: 6px; border-left: 3px solid {p_color}; flex: 1;">
                        <div style="color: #7f8c8d; font-size: 0.55rem; text-transform: uppercase; margin-bottom: 2px;">Class Profile</div>
                        <div style="color: {p_color}; font-weight: bold; font-size: 0.9rem; text-shadow: 0 0 5px {p_color}80;">{p_class}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.05); padding: 6px 10px; border-radius: 6px; border-left: 3px solid #f1c40f; flex: 1;">
                        <div style="color: #7f8c8d; font-size: 0.55rem; text-transform: uppercase; margin-bottom: 2px;">Level</div>
                        <div style="color: #f1c40f; font-weight: bold; font-size: 0.9rem;">{p_lvl if p_lvl == 'MAX' else f"LVL {p_lvl}"}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.05); padding: 6px 10px; border-radius: 6px; border-left: 3px solid #3498db;">
                        <div style="color: #7f8c8d; font-size: 0.55rem; text-transform: uppercase; margin-bottom: 2px;">Overall GPA</div>
                        <div style="color: #3498db; font-weight: bold; font-size: 0.9rem;">{p_gpa:.2f}</div>
                        </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px dashed #34495e; padding-top: 8px;">
                        <div style="font-family: 'Libre Barcode 39 Text', cursive; font-size: 2.2rem; color: #bdc3c7; line-height: 0.7; text-shadow: 0 0 5px rgba(255,255,255,0.2);">*UOI-{int(p_ects)}*</div>
                        <div style="text-align: right; color: #7f8c8d; font-size: 0.6rem; font-family: monospace; line-height: 1.4;">
                        ACHIEVEMENTS: <span style="color: #f1c40f; font-weight: bold;">{p_badges} UNLOCKED</span>
                        </div>
                        </div>
                        </div>
                        </div>
                        </div>
                        """
                        # Καθαρίζουμε τα newlines για να αποφύγουμε τα bugs του Markdown που είδαμε πριν!
                        return html.replace('\n', '')
                    
                    st.markdown("---")
                    
                    # UI Σύγκρισης - ΜΕΡΟΣ 1: Οι Ταυτότητες
                    col_p1, col_vs, col_p2 = st.columns([5, 1, 5])
                    
                    with col_p1:
                        st.markdown(f"<h3 style='text-align: center; color: {a_color}; text-shadow: 0 0 10px {a_color}80; font-family: monospace;'>P1 (ΕΣΥ)</h3>", unsafe_allow_html=True)
                        st.markdown(generate_id_card("PLAYER 1", a_color, avatar, a_title, current_lvl_num, clean_rank_1, final_gpa, total_ects, badges_1), unsafe_allow_html=True)
                        
                    with col_vs:
                        st.markdown("<h1 style='text-align: center; color: #f1c40f; margin-top: 130px; text-shadow: 0 0 15px #f1c40f; font-family: monospace;'>VS</h1>", unsafe_allow_html=True)
                        
                    with col_p2:
                        st.markdown(f"<h3 style='text-align: center; color: {a_color_2}; text-shadow: 0 0 10px {a_color_2}80; font-family: monospace;'>P2 (ΑΝΤΙΠΑΛΟΣ)</h3>", unsafe_allow_html=True)
                        st.markdown(generate_id_card("PLAYER 2", a_color_2, avatar_2, a_title_2, lvl_2, clean_rank_2, gpa_2, ects_2, badges_2), unsafe_allow_html=True)
                        
                    # UI Σύγκρισης - ΜΕΡΟΣ 2: ARCADE BARS (Full Width)
                    st.markdown("<br><h3 style='text-align: center; color: #bdc3c7; font-family: monospace; letter-spacing: 3px; margin-bottom: 30px;'>🔥 ARCADE MATCHUP 🔥</h3>", unsafe_allow_html=True)
                    
                    def make_arcade_row(label, str1, str2, val1, val2, is_float=False):
                        total = val1 + val2
                        
                        # Υπολογισμός ποσοστών 0-100 για να γεμίσει η ενιαία μπάρα αναλογικά
                        if total <= 0:
                            w1, w2 = 50, 50
                        else:
                            w1 = (val1 / total) * 100
                            w2 = (val2 / total) * 100
                            
                        # Υπολογισμός Νικητή και Διαφοράς με Badge
                        crown1, crown2 = "", ""
                        if val1 > val2:
                            diff = val1 - val2
                            diff_str = f"+{diff:.2f}" if is_float else f"+{int(diff)}"
                            crown1 = f"<span style='font-size: 0.85rem; color: #fff; font-weight: bold; background: rgba(0,0,0,0.6); padding: 3px 8px; border-radius: 12px; box-shadow: 0 0 5px rgba(0,0,0,0.5);'>({diff_str}) 👑</span>"
                        elif val2 > val1:
                            diff = val2 - val1
                            diff_str = f"+{diff:.2f}" if is_float else f"+{int(diff)}"
                            crown2 = f"<span style='font-size: 0.85rem; color: #fff; font-weight: bold; background: rgba(0,0,0,0.6); padding: 3px 8px; border-radius: 12px; box-shadow: 0 0 5px rgba(0,0,0,0.5);'>👑 ({diff_str})</span>"
                            
                        return f"""
                        <div style="margin-bottom: 25px; position: relative; z-index: 1;">
                            <!-- Label με σκούρο φόντο για να "κόβει" την κάθετη κίτρινη γραμμή -->
                            <div style="text-align: center; margin-bottom: 10px; position: relative; z-index: 3;">
                                <span style="background: #0e1117; padding: 5px 15px; color: #ecf0f1; font-family: 'Share Tech Mono', monospace; font-size: 0.95rem; letter-spacing: 2px; text-transform: uppercase; border-radius: 4px; border: 1px solid #2c3e50;">{label}</span>
                            </div>
                            
                            <!-- ΕΝΙΑΙΑ ΜΠΑΡΑ (Tug of War) -->
                            <div style="position: relative; width: 100%; height: 40px; background: #05070a; border-radius: 6px; display: flex; overflow: hidden; box-shadow: 0 0 15px rgba(0,0,0,0.8); border: 1px solid #34495e;">
                                
                                <!-- Player 1 Fill (Αριστερά) -->
                                <div style="width: {w1}%; background: {a_color}; opacity: 0.85; transition: width 1s ease-in-out; border-right: 3px solid #fff; box-shadow: inset 10px 0 30px rgba(0,0,0,0.6);"></div>
                                
                                <!-- Player 2 Fill (Δεξιά) -->
                                <div style="width: {w2}%; background: {a_color_2}; opacity: 0.85; transition: width 1s ease-in-out; box-shadow: inset -10px 0 30px rgba(0,0,0,0.6);"></div>
                                
                                <!-- Player 1 Text (Αριστερά) -->
                                <div style="position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #fff; font-size: 1.25rem; font-family: monospace; font-weight: bold; text-shadow: 1px 1px 2px #000, 0 0 10px #000; display: flex; align-items: center; gap: 10px; z-index: 3;">
                                    <span>{str1}</span>{crown1}
                                </div>
                                
                                <!-- Player 2 Text (Δεξιά) -->
                                <div style="position: absolute; right: 15px; top: 50%; transform: translateY(-50%); color: #fff; font-size: 1.25rem; font-family: monospace; font-weight: bold; text-shadow: 1px 1px 2px #000, 0 0 10px #000; display: flex; align-items: center; gap: 10px; z-index: 3;">
                                    {crown2}<span>{str2}</span>
                                </div>
                                
                                <!-- Σταθερό Κεντρικό VS (Καρφωμένο στο 50%) -->
                                <div style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 38px; height: 38px; background: #111b24; border: 2px solid #f1c40f; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #f1c40f; font-family: monospace; z-index: 4; box-shadow: 0 0 15px rgba(241, 196, 15, 0.8);">VS</div>
                            </div>
                        </div>
                        """
                        
                    arcade_html = f"""
                    <div style="position: relative; padding: 20px 0; max-width: 900px; margin: 0 auto;">
                        <!-- Η Κάθετη Γραμμή Μπήκε ΠΙΣΩ από όλα (z-index: 0) -->
                        <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 2px; background: rgba(241, 196, 15, 0.3); box-shadow: 0 0 15px rgba(241, 196, 15, 0.5); transform: translateX(-50%); z-index: 0; border-radius: 1px;"></div>
                        
                        {make_arcade_row("Overall GPA", f"{final_gpa:.2f}", f"{gpa_2:.2f}", final_gpa, gpa_2, True)}
                        {make_arcade_row("Total ECTS", f"{total_ects:g}", f"{ects_2:g}", total_ects, ects_2, False)}
                        {make_arcade_row("Max Exam Streak", f"{streak_1} 🔥", f"🔥 {streak_2}", streak_1, streak_2, False)}
                        {make_arcade_row("Achievements", f"{badges_1} 🏅", f"🏅 {badges_2}", badges_1, badges_2, False)}
                    </div>
                    """
                    st.markdown(arcade_html.replace('\n', ''), unsafe_allow_html=True)
                    
                    # UI Σύγκρισης - ΜΕΡΟΣ 3: Ειδικά Μαθήματα (Επιστροφή σε στήλες)
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_ex1, col_ex2 = st.columns(2)
                    
                    with col_ex1:
                        st.markdown(f"<h5 style='color: {a_color}; border-bottom: 1px solid {a_color}; padding-bottom: 5px; font-family: monospace;'>💼 Ειδικά Μαθήματα (P1)</h5>", unsafe_allow_html=True)
                        st.info(f"**Διπλωματική:** {thesis_status_1}\n\n**Πρακτική Άσκηση:** {int_status_1}")
                        if gold_1 is not None:
                            st.success(f"🌟 **Χρυσή Εξεταστική:**\n\n**{gold_1['Period']}** ({int(gold_1['Count'])} μαθήματα | Μ.Ο. {gold_1['GPA']:.2f})")

                    with col_ex2:
                        st.markdown(f"<h5 style='color: {a_color_2}; border-bottom: 1px solid {a_color_2}; padding-bottom: 5px; font-family: monospace;'>💼 Ειδικά Μαθήματα (P2)</h5>", unsafe_allow_html=True)
                        st.info(f"**Διπλωματική:** {thesis_status_2}\n\n**Πρακτική Άσκηση:** {int_status_2}")
                        if gold_2 is not None:
                            st.success(f"🌟 **Χρυσή Εξεταστική:**\n\n**{gold_2['Period']}** ({int(gold_2['Count'])} μαθήματα | Μ.Ο. {gold_2['GPA']:.2f})")

                    st.markdown("---")
                    
                    # --- AI MATCHUP VERDICT (Αλγόριθμος Νικητή) ---
                    st.subheader("🤖 AI Matchup Verdict")
                    
                    p1_score, p2_score = 0, 0
                    
                    if final_gpa > gpa_2: p1_score += 1
                    elif gpa_2 > final_gpa: p2_score += 1
                    
                    if total_ects > ects_2: p1_score += 1
                    elif ects_2 > total_ects: p2_score += 1
                    
                    if streak_1 > streak_2: p1_score += 1
                    elif streak_2 > streak_1: p2_score += 1
                    
                    if badges_1 > badges_2: p1_score += 1
                    elif badges_2 > badges_1: p2_score += 1
                    
                    if p1_score > p2_score:
                        v_title = "🏆 PLAYER 1 WINS (FLAWLESS VICTORY)"
                        v_color = "#00ffcc" # Neon Cyan
                        v_msg = "Ο Player 1 κυριαρχεί στο ακαδημαϊκό πεδίο μάχης. Τα στατιστικά του είναι τερματισμένα! Ο Player 2 πρέπει να επιστρέψει στο Base Camp για grinding."
                    elif p2_score > p1_score:
                        v_title = "🏆 PLAYER 2 WINS (DOMINATION)"
                        v_color = "#ff007f" # Neon Pink
                        v_msg = "Ο Player 2 έκανε speedrun το πτυχίο! Ο Player 1 έμεινε πίσω στο level scaling και χρειάζεται άμεσα energy drinks."
                    else:
                        v_title = "⚔️ ABSOLUTE TIE (SUDDEN DEATH REQUIRED)"
                        v_color = "#f1c40f" # Neon Yellow
                        v_msg = "Απόλυτη ισοπαλία! Και οι δύο παίκτες έχουν ακριβώς το ίδιο power level. Ένα επικό rematch στην επόμενη εξεταστική είναι μονόδρομος."
                        
                    st.markdown(f"""
                    <div style='background: #0a0e17; border: 2px solid {v_color}; border-radius: 10px; padding: 25px; text-align: center; box-shadow: 0 0 25px {v_color}44; margin-bottom: 30px; position: relative; overflow: hidden;'>
                        <div style='position: absolute; top: -10px; right: -10px; font-size: 5rem; opacity: 0.1;'>🥊</div>
                        <h2 style='color: {v_color}; margin-top: 0; font-family: monospace; letter-spacing: 2px;'>{v_title}</h2>
                        <div style='color: #ecf0f1; font-size: 1.1rem; line-height: 1.5;'>{v_msg}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # --- HEAD-TO-HEAD RADAR CHART (CYBERPUNK HUD) ---
                    st.subheader("📊 Head-to-Head Skill Matchup")
                    
                    categories = ['GPA (x10)', 'Σύνολο Μαθημάτων', 'Max Streak (x10)', 'Achievements (x10)', 'Πρόοδος Πτυχίου (%)']
                    
                    p1_stats = [final_gpa * 10, total_courses, streak_1 * 10, badges_1 * 10, min((total_ects / 300) * 100, 100)]
                    p2_stats = [gpa_2 * 10, courses_2, streak_2 * 10, badges_2 * 10, min((ects_2 / 300) * 100, 100)]
                    
                    fig_radar = go.Figure()
                    
                    # Player 1 Trace (Neon Cyan)
                    fig_radar.add_trace(go.Scatterpolar(
                        r=p1_stats, theta=categories, fill='toself', name='Player 1 (Εσύ)', 
                        line_color='#00ffcc', fillcolor='rgba(0, 255, 204, 0.3)', opacity=0.9,
                        hovertemplate='<b>%{theta}</b><br>Score: %{r:.1f}<extra></extra>'
                    ))
                    
                    # Player 2 Trace (Neon Pink)
                    fig_radar.add_trace(go.Scatterpolar(
                        r=p2_stats, theta=categories, fill='toself', name='Player 2 (Αντίπαλος)', 
                        line_color='#ff007f', fillcolor='rgba(255, 0, 127, 0.3)', opacity=0.9,
                        hovertemplate='<b>%{theta}</b><br>Score: %{r:.1f}<extra></extra>'
                    ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, showticklabels=False, gridcolor='rgba(0, 255, 204, 0.1)', range=[0, max(max(p1_stats), max(p2_stats)) + 5]),
                            angularaxis=dict(gridcolor='rgba(0, 255, 204, 0.1)', tickfont=dict(family="'Share Tech Mono', monospace", size=13, color='#bdc3c7')),
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="'Share Tech Mono', monospace", color='#bdc3c7'),
                        showlegend=True, 
                        legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5, font=dict(size=14)),
                        margin=dict(t=80, b=40, l=60, r=60),
                        hoverlabel=dict(bgcolor='#0a0e17', font=dict(family="'Share Tech Mono', monospace", size=13, color='#ecf0f1'))
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Το αρχείο του Player 2 δεν μπόρεσε να αναγνωστεί σωστά: {e}")

            # --- SYSTEM STATUS (ΚΑΤΩ ΜΕΡΟΣ SIDEBAR) ---
            with sidebar_bot:
                st.markdown("---")
                st.markdown("🕹️ **System Status:** Online\n\n👨‍💻 **Developer:** @panagiotispar")

            # ==========================================
            # ADMIN TERMINAL (CHEAT CODES & EASTER EGGS)
            # ==========================================
            with sidebar_bot:
                st.markdown("---")
                st.markdown("<h5 style='color: #00ffcc; font-family: monospace; margin-bottom: 0;'>>_ Admin Terminal</h5>", unsafe_allow_html=True)
                
                # Το πεδίο εισαγωγής
                cheat_code = st.text_input("Command:", placeholder="Type command...", label_visibility="collapsed").lower().strip()
                
                # Η λογική των Cheat Codes & Unlockables
                if cheat_code == "iddqd":
                    st.balloons()
                    st.snow()
                    st.success("🎮 **GOD MODE ACTIVATED:** Όλα τα bugs έγιναν features.")
                elif cheat_code == "matrix":
                    st.warning("🐇 Wake up, Neo... Το ClassWeb σε έχει.")
                elif cheat_code == "order66":
                    st.error("⚔️ **Executing Order 66...** Διαγραφή όλων των περασμένων μαθημάτων. (Just kidding!)")
                
                # --- THEME UNLOCKS ---
                elif cheat_code == "pantera":
                    if "metal" not in st.session_state.unlocked_themes:
                        st.session_state.unlocked_themes.append("metal")
                        st.rerun()
                    else:
                        st.success("🤘 **HEAVY METAL THEME** is already unlocked! (Check Customizer)")
                
                elif cheat_code == "konami":
                    if "arcade" not in st.session_state.unlocked_themes:
                        st.session_state.unlocked_themes.append("arcade")
                        st.rerun()
                    else:
                        st.success("👾 **RETRO 8-BIT THEME** is already unlocked! (Check Customizer)")
                        
                elif cheat_code == "johto":
                    if "johto" not in st.session_state.unlocked_themes:
                        st.session_state.unlocked_themes.append("johto")
                        st.rerun()
                    else:
                        st.success("⚡ **JOHTO EDITION THEME** is already unlocked! (Check Customizer)")
                
                elif cheat_code:
                    st.error("🔒 **ACCESS DENIED:** Unknown command or corrupted syntax.")
    except Exception as e:
        st.error(f"Προέκυψε σφάλμα κατά την ανάγνωση του αρχείου: {e}")
