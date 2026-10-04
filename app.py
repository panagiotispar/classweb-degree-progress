import streamlit as st
import pandas as pd
import re
import plotly.graph_objects as go

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Πορεία προς το Πτυχίο", page_icon="🎓", layout="wide")

# --- HUD (SIDEBAR) ---
with st.sidebar:
    st.header("🎒 Inventory")
    st.markdown("Φόρτωσε το αρχείο Excel (**H καρτέλα μου - Όλα τα μαθήματα.xlsx**) από το ClassWeb για να τροφοδοτήσεις τη μηχανή.")
    
    # Το κουμπί μεταφέρθηκε εδώ!
    uploaded_file = st.file_uploader("Drop Excel File", type=['xlsx'])

    if uploaded_file is not None:
        st.sidebar.success("✅ Το αρχείο αναλύθηκε με επιτυχία!")

    st.markdown("---")
    st.markdown("🕹️ **System Status:** Online\n\n👨‍💻 **Developer:** @panagiotispar")

# --- ΚΕΝΤΡΙΚΗ ΟΘΟΝΗ ---
st.markdown("""
<style>
/* Εισαγωγή γραμματοσειράς 'Share Tech Mono' από τα Google Fonts για καθαρή Terminal/HUD αισθητική */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

.terminal-container {
    display: inline-block;
    max-width: 100%;
}

.typewriter-text {
    font-family: 'Share Tech Mono', Consolas, 'Courier New', monospace;
    color: #00ffcc; /* Cyberpunk Neon Cyan χρώμα */
    text-shadow: 0px 0px 8px rgba(0, 255, 204, 0.6);
    font-size: 2.2rem;
    white-space: nowrap;
    overflow: hidden;
    border-right: 0.15em solid #00ffcc; /* Ο κέρσορας που αναβοσβήνει */
    animation: typing 2.5s steps(45, end), blink-caret 0.75s step-end infinite;
    margin-bottom: 20px;
}

/* Animation για το γράψιμο γράμμα-γράμμα */
@keyframes typing {
    from { width: 0; }
    to { width: 100%; }
}

/* Animation για το αναβόσβημα του κέρσορα */
@keyframes blink-caret {
    from, to { border-color: transparent; }
    50% { border-color: #00ffcc; }
}
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

def create_plotly_charts(df):
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
    
    for year in years:
        for period in periods:
            key = (year, period)
            courses_in_period = detailed_data.get(key, [])
            
            # 1. Μετράμε ΠΟΣΑ είναι τα ΚΑΝΟΝΙΚΑ μαθήματα (εξαιρούμε Πρακτική ΚΑΙ Διπλωματική)
            count_regular = sum(1 for c in courses_in_period if not re.search(r'ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ|ΔΙΠΛΩΜΑΤΙΚΗ', str(c[0]), re.IGNORECASE))
            current_total += count_regular
            
            # 2. Υπολογισμός Μ.Ο. και ECTS βάσει ΟΛΩΝ των μαθημάτων της εξεταστικής (συμπεριλαμβάνονται Πρακτική/Διπλωματική)
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
                # Αν πέρασε μόνο πρακτική/διπλωματική, βάζουμε τιρκουάζ χρώμα στη μπάρα που θα είναι στο 0!
                colors_bar.append('#3498db' if count_regular > 0 else '#1abc9c') 
                text = f"<b>📅 {period} '{year[-2:]} ({count_regular} μαθήματα)</b><br>"
                text += "━"*30 + "<br>"
                for course_name, grade, ects in courses_in_period:
                    # Επισημαίνουμε στο tooltip ότι η Πρακτική/Διπλωματική εξαιρείται από το πλήθος
                    if re.search(r'ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ|ΔΙΠΛΩΜΑΤΙΚΗ', str(course_name), re.IGNORECASE):
                        text += f"▪ {course_name}  [{grade}] <i>({ects} ECTS)</i> <b>[Εξαιρείται]</b><br>"
                    else:
                        text += f"▪ {course_name}  [{grade}] <i>({ects} ECTS)</i><br>"
                
                text_gpa = f"<b>📅 {period} '{year[-2:]}</b><br>" + "━"*15 + f"<br>Νέος Μ.Ο: <b>{current_gpa}</b>"
            else:
                colors_bar.append('#ecf0f1')
                text = f"<b>📅 {period} '{year[-2:]}</b><br>" + "━"*15 + "<br>Κανένα περασμένο μάθημα"
                text_gpa = f"<b>📅 {period} '{year[-2:]}</b><br>" + "━"*15 + f"<br>Μ.Ο: <b>{current_gpa}</b> (Αμετάβλητος)"
                
            hover_texts.append(text)
            hover_texts_gpa.append(text_gpa)

    # --- 1. ΑΘΡΟΙΣΤΙΚΟ ΓΡΑΦΗΜΑ (Cumulative) ---
    static_texts_cum = [f"<b>{val}</b>" if val > y_values_cum[max(0, i-1)] and i != len(y_values_cum)-1 else "" for i, val in enumerate(y_values_cum)]
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=x_labels, y=y_values_cum, mode='lines+markers+text', text=static_texts_cum, textposition='top left',
        textfont=dict(color='#2c3e50', size=11), hoverinfo='text', hovertext=hover_texts,
        line=dict(shape='hv', color='#2980b9', width=3), marker=dict(size=8, color='white', line=dict(color='#2980b9', width=2)),
        fill='tozeroy', fillcolor='rgba(52, 152, 219, 0.3)', hoverlabel=dict(bgcolor="#f8f9fa", bordercolor="#bdc3c7", font=dict(size=12, color='#2c3e50'), align="left")
    ))
    fig_cum.add_annotation(
        x=x_labels[-1], y=y_values_cum[-1], text=f"<b>ΣΥΝΟΛΟ: {y_values_cum[-1]}</b>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="black", ax=-60, ay=-40,
        bgcolor="#f1c40f", bordercolor="#f39c12", borderwidth=3, borderpad=6, font=dict(size=16, color="black")
    )
    fig_cum.update_layout(
        title=dict(text='<b>Η Πορεία προς το Πτυχίο (Αθροιστική Πρόοδος)</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        yaxis_title=dict(text='Σύνολο Περασμένων Μαθημάτων', font=dict(color='#2c3e50')), plot_bgcolor='white', margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(tickangle=-90, showgrid=True, gridcolor='rgba(149, 165, 166, 0.3)', type='category', range=[-0.5, len(x_labels) - 0.5]),
        yaxis=dict(showgrid=True, gridcolor='rgba(149, 165, 166, 0.3)', range=[0, max(y_values_cum) + 10])
    )

    # --- 2. ΡΑΒΔΟΓΡΑΜΜΑ (Bar Chart) ---
    static_texts_bar = [f"<b>{val}</b>" if val > 0 else "" for val in y_values_bar]
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=x_labels, y=y_values_bar, marker_color=colors_bar, text=static_texts_bar, textposition='outside',
        textfont=dict(color='#2c3e50', size=11), hoverinfo='text', hovertext=hover_texts,
        hoverlabel=dict(bgcolor="#f8f9fa", bordercolor="#bdc3c7", font=dict(size=12, color='#2c3e50'), align="left")
    ))
    fig_bar.update_layout(
        title=dict(text='<b>Ιστορικό Επιτυχίας Μαθημάτων ανά Εξεταστική</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        yaxis_title=dict(text='Αριθμός Περασμένων Μαθημάτων', font=dict(color='#2c3e50')), plot_bgcolor='white', margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(tickangle=-90, showgrid=True, gridcolor='rgba(189, 195, 199, 0.5)', type='category', range=[-0.5, len(x_labels) - 0.5]),
        yaxis=dict(showgrid=True, gridcolor='rgba(189, 195, 199, 0.5)', range=[0, max(y_values_bar) + 2])
    )

    # --- 3. ΓΡΑΦΗΜΑ ΕΞΕΛΙΞΗΣ Μ.Ο. (GPA Tracker) ---
    fig_gpa = go.Figure()
    valid_gpas = [g for g in y_values_gpa if g is not None]
    min_gpa = min(valid_gpas) - 0.2 if valid_gpas else 5.0
    max_gpa = max(valid_gpas) + 0.2 if valid_gpas else 10.0

    fig_gpa.add_trace(go.Scatter(
        x=x_labels, y=y_values_gpa, mode='lines+markers',
        hoverinfo='text', hovertext=hover_texts_gpa,
        line=dict(shape='spline', smoothing=0.3, color='#27ae60', width=4),
        marker=dict(size=10, color='white', line=dict(color='#27ae60', width=2)),
        fill='tozeroy', fillcolor='rgba(39, 174, 96, 0.15)',
        hoverlabel=dict(bgcolor="#f8f9fa", bordercolor="#bdc3c7", font=dict(size=12, color='#2c3e50'), align="left")
    ))
    
    if valid_gpas:
        fig_gpa.add_annotation(
            x=x_labels[-1], y=valid_gpas[-1], text=f"<b>Τρέχων Μ.Ο: {valid_gpas[-1]}</b>",
            showarrow=True, arrowhead=2, ax=-50, ay=-30, bgcolor="#27ae60", font=dict(color="white")
        )

    fig_gpa.update_layout(
        title=dict(text='<b>Εξέλιξη Μέσου Όρου (GPA Tracker)</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        yaxis_title=dict(text='Σταθμικός Μέσος Όρος', font=dict(color='#2c3e50')), plot_bgcolor='white', margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(tickangle=-90, showgrid=True, gridcolor='rgba(149, 165, 166, 0.3)', type='category', range=[-0.5, len(x_labels) - 0.5]),
        yaxis=dict(showgrid=True, gridcolor='rgba(149, 165, 166, 0.3)', range=[min_gpa, max_gpa])
    )

    # --- 4. ΚΑΤΑΝΟΜΗ ΒΑΘΜΟΛΟΓΙΩΝ (Grade Distribution) ---
    grade_counts = df['Βαθμός'].value_counts().sort_index()
    dist_labels = [str(g) for g in grade_counts.index]
    dist_values = grade_counts.values
    
    fig_dist = go.Figure()
    fig_dist.add_trace(go.Bar(
        x=dist_labels, y=dist_values, 
        marker_color='#8e44ad',
        text=[f"<b>{val}</b>" for val in dist_values], textposition='outside',
        textfont=dict(color='#2c3e50', size=11),
        hoverinfo='x+y',
        hoverlabel=dict(bgcolor="#f8f9fa", bordercolor="#bdc3c7", font=dict(size=12, color='#2c3e50'), align="left")
    ))
    
    max_dist = max(dist_values) if len(dist_values) > 0 else 10
    
    fig_dist.update_layout(
        title=dict(text='<b>Κατανομή Βαθμολογιών (Πλήθος ανά Βαθμό)</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        xaxis_title=dict(text='Βαθμός', font=dict(color='#2c3e50')), 
        yaxis_title=dict(text='Αριθμός Μαθημάτων', font=dict(color='#2c3e50')), 
        plot_bgcolor='white', margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showgrid=False, type='category'),
        yaxis=dict(showgrid=True, gridcolor='rgba(189, 195, 199, 0.5)', range=[0, max_dist + 2])
    )

    # --- 5. ΚΑΤΑΝΟΜΗ ΑΝΑ ΚΑΤΗΓΟΡΙΑ (Donut Chart) ---
    # Ομαδοποιούμε υπολογίζοντας ταυτόχρονα το άθροισμα των ECTS και το πλήθος των μαθημάτων
    category_stats = df.groupby('Κατηγορία').agg(
        Total_ECTS=('ECTS', 'sum'),
        Course_Count=('Μάθημα', 'count')
    ).reset_index()
    
    fig_category = go.Figure()
    fig_category.add_trace(go.Pie(
        labels=category_stats['Κατηγορία'], 
        values=category_stats['Total_ECTS'], 
        customdata=category_stats['Course_Count'], # Περνάμε το πλήθος των μαθημάτων ως custom δεδομένο
        hole=0.45,
        textinfo='percent+label',
        textposition='inside',
        hovertemplate="<b>%{label}</b><br>%{value} ECTS (%{customdata} μαθήματα)<br>%{percent}<extra></extra>",
        marker=dict(colors=['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6', '#34495e'], 
                    line=dict(color='#ffffff', width=2))
    ))
    
    fig_category.update_layout(
        title=dict(text='<b>Συγκέντρωση ECTS ανά Κατηγορία</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False 
    )

    # --- 6. ΣΥΣΧΕΤΙΣΗ ΒΑΘΜΟΥ - ΔΥΣΚΟΛΙΑΣ - ΧΡΟΝΟΥ (3D Scatter Plot) ---
    scatter_df = df[~df['Μάθημα'].str.contains('ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ|ΔΙΠΛΩΜΑΤΙΚΗ', case=False, na=False)].copy()
    
    # Ομαδοποιούμε πλέον ΚΑΙ με βάση το Ακαδημαϊκό Έτος για τον άξονα Z
    grouped_scatter = scatter_df.groupby(['ECTS', 'Βαθμός', 'Ακαδ. Έτος']).agg(
        Μαθήματα=('Μάθημα', lambda x: '<br>▪ '.join(x)),
        Πλήθος=('Μάθημα', 'count')
    ).reset_index()
    
    # Υπολογίζουμε δυναμικό μέγεθος για τις σφαίρες (10 base + 5 για κάθε επιπλέον μάθημα)
    marker_sizes = [10 + (count * 5) for count in grouped_scatter['Πλήθος']]
    
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter3d(
        x=grouped_scatter['ECTS'],
        y=grouped_scatter['Βαθμός'],
        z=grouped_scatter['Ακαδ. Έτος'], # Ο χρόνος στον άξονα του βάθους
        mode='markers',
        marker=dict(
            size=marker_sizes,
            color=grouped_scatter['Βαθμός'], # Χρωματισμός βάσει βαθμού (Heatmap effect)
            colorscale='YlOrRd',             # Παλέτα χρωμάτων από κίτρινο σε κόκκινο
            line=dict(width=2, color='#2c3e50'), # Σκούρο περίγραμμα για να ξεχωρίζουν οι σφαίρες
            opacity=0.85
        ),
        text="▪ " + grouped_scatter['Μαθήματα'],
        customdata=grouped_scatter['Πλήθος'],
        hovertemplate="<b>Έτος: %{z}</b><br>%{customdata} Μαθήματα:<br>%{text}<br>" + "━"*15 + "<br>Βαθμός: %{y} | ECTS: %{x}<extra></extra>"
    ))
    
    fig_scatter.update_layout(
        title=dict(text='<b>3D Χωρική Ανάλυση (Δυσκολία vs Βαθμός vs Χρόνος)</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        scene=dict(
            xaxis_title='ECTS',
            yaxis_title='Βαθμός',
            zaxis_title='Ακαδ. Έτος',
            xaxis=dict(showgrid=True, gridcolor='rgba(189, 195, 199, 0.5)', backgroundcolor="rgba(240, 240, 240, 0.5)"),
            yaxis=dict(showgrid=True, gridcolor='rgba(189, 195, 199, 0.5)', range=[4.5, 10.5], backgroundcolor="rgba(240, 240, 240, 0.5)"),
            zaxis=dict(
                showgrid=True, 
                gridcolor='rgba(189, 195, 199, 0.5)', 
                backgroundcolor="rgba(240, 240, 240, 0.5)",
                type='category',               # Δηλώνουμε ότι ο άξονας έχει κατηγορίες (κείμενο)
                categoryorder='array',         # Επιλέγουμε ταξινόμηση βάσει δικής μας λίστας
                categoryarray=years            # Περνάμε τη σωστή, χρονολογική σειρά!
            )
        ),
        margin=dict(l=0, r=0, b=0, t=60),
        scene_camera=dict(eye=dict(x=1.6, y=1.6, z=0.6))
    )

    return fig_cum, fig_bar, fig_gpa, fig_dist, fig_category, fig_scatter


# Main Εφαρμογή
if uploaded_file is not None:
    try:
        raw_data = pd.read_excel(uploaded_file, header=1)
        cleaned_df = clean_classweb_data(raw_data)
        
        # --- 1. ΠΡΟΕΤΟΙΜΑΣΙΑ ΔΕΔΟΜΕΝΩΝ ΚΑΙ ΥΠΟΛΟΓΙΣΜΟΙ ---
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

        # Δημιουργία Γραφημάτων (τα φτιάχνουμε εδώ για να τα μοιράσουμε μετά στα tabs)
        fig_cum, fig_bar, fig_gpa, fig_dist, fig_category, fig_scatter = create_plotly_charts(cleaned_df)
        
        

        # --- 2. ΔΗΜΙΟΥΡΓΙΑ ΤΩΝ TABS (SECTORS) ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 Base Camp", 
            "📈 Analytics Engine", 
            "🌌 3D Space & Timeline", 
            "🔮 Simulator & Tools",
            "⚔️ Co-op Mode"
        ])
        
        # ==========================================
        # TAB 1: BASE CAMP (Overview & Gamification)
        # ==========================================
        with tab1:
            # RPG LEVELING SYSTEM
            level_ranks = [
                (0, "Lvl 1: Hello World Novice 🐣"), (30, "Lvl 2: Loop Scripter 🔁"),
                (60, "Lvl 3: Bug Hunter 🐛"), (90, "Lvl 4: Object-Oriented Knight 🛡️"),
                (120, "Lvl 5: Tree Traverser 🌲"), (150, "Lvl 6: Database Ranger 🗄️"),
                (180, "Lvl 7: Machine Learning Apprentice 🤖"), (210, "Lvl 8: The 8-Bit Legend 👾"),
                (240, "Lvl 9: 3D Rendering Mage 🧙‍♂️"), (270, "Lvl 10: System Architect 🏛️"),
                (300, "MAX Lvl: Master of the Code 👑")
            ]
            
            if total_ects >= 300:
                current_lvl_num, current_xp, rank_title = "MAX", 30, level_ranks[-1][1]
                avatar = "🧙‍♂️" # Μάγος του Κώδικα
            else:
                current_lvl_num = int(total_ects // 30) + 1
                current_xp = total_ects % 30
                for cap, title in reversed(level_ranks):
                    if total_ects >= cap:
                        rank_title = title
                        break
                
                # Δυναμικό Avatar βάσει Level (Κάθε 2 levels αλλάζει η "μορφή" σου)
                if current_lvl_num <= 2:
                    avatar = "🥚" # 1ο έτος (Αυγό)
                elif current_lvl_num <= 4:
                    avatar = "🤓" # 2ο έτος (Σπασίκλας/Φοιτητής)
                elif current_lvl_num <= 6:
                    avatar = "🥷" # 3ο έτος (Ninja)
                elif current_lvl_num <= 8:
                    avatar = "🦾" # 4ο έτος (Cyborg/Hardware)
                else:
                    avatar = "🦸‍♂️" # 5ο έτος (Tech Hero)
                        
            xp_percent = (current_xp / 30) * 100
            
            # Εντυπωσιακή εμφάνιση Avatar και Rank με animation
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 20px; background-color: #1a252f; padding: 15px 20px; border-radius: 12px; border-left: 5px solid #f1c40f; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
                <div style="font-size: 3.5rem; margin-right: 20px; text-shadow: 0 0 15px rgba(241, 196, 15, 0.6); animation: float-avatar 3s ease-in-out infinite;">
                    {avatar}
                </div>
                <div>
                    <div style="color: #bdc3c7; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 5px;">Current Evolution</div>
                    <h3 style="margin: 0; color: white; font-size: 1.8rem;">{rank_title}</h3>
                </div>
            </div>
            <style>
            @keyframes float-avatar {{
                0% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-8px); }}
                100% {{ transform: translateY(0px); }}
            }}
            </style>
            """, unsafe_allow_html=True)

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

            with st.expander("📜 Δες όλο το Skill Tree (Ιστορικό Levels)"):
                for cap, title in level_ranks:
                    if total_ects >= 300 and cap == 300:
                        st.success(f"👑 **{title}** (300 ECTS) — **MAX LEVEL UNLOCKED!**")
                    elif total_ects >= cap + 30 or total_ects >= 300:
                        st.markdown(f"✅ ~~{title}~~ *(Ξεκλείδωσε στα {cap} ECTS)*")
                    elif total_ects >= cap:
                        st.info(f"🟢 **{title}** *(Τρέχον Level — Ξεκίνησε στα {cap} ECTS)*")
                    else:
                        st.markdown(f"🔒 <span style='color: gray;'>*{title}* *(Απαιτεί {cap} ECTS)*</span>", unsafe_allow_html=True)
            
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
                    boss_html = """
                    <div style="background: linear-gradient(145deg, #2c1a1a, #4a0e0e); border: 2px solid #e74c3c; border-radius: 10px; padding: 15px; margin-bottom: 0px; margin-top: 10px; box-shadow: 0 0 15px rgba(231, 76, 60, 0.4); text-align: center; animation: pulse-red 2s infinite; height: 130px; display: flex; flex-direction: column; justify-content: center;">
                        <h3 style="color: #e74c3c; margin: 0; font-size: 1.3rem; text-shadow: 0 0 10px rgba(231,76,60,0.8);">⚠️ FINAL BOSS: LURKING</h3>
                        <div style="color: #f5b7b1; font-size: 0.95rem; margin-top: 5px;">Η Διπλωματική Εργασία (30 ECTS) εκκρεμεί...</div>
                    </div>
                    """
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
                net_df = cleaned_df[cleaned_df['Μάθημα'].str.contains(r'Δίκτυα Υπολογιστών Ι\s*(Ι|I|1)\b', case=False, na=False, regex=True)]
                
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
                    
                    # CSS για το Pulsing Glow Effect και το Hover
                    st.markdown("""
                    <style>
                    @keyframes pulse-gold {
                        0% { box-shadow: 0 0 5px #f1c40f, inset 0 0 2px #f1c40f; border-color: #f1c40f; }
                        50% { box-shadow: 0 0 20px #f39c12, inset 0 0 10px #f39c12; border-color: #f39c12; }
                        100% { box-shadow: 0 0 5px #f1c40f, inset 0 0 2px #f1c40f; border-color: #f1c40f; }
                    }
                    .loot-badge {
                        background: linear-gradient(145deg, #1a252f, #2c3e50);
                        border: 2px solid #f1c40f;
                        border-radius: 12px;
                        padding: 15px;
                        text-align: center;
                        animation: pulse-gold 2.5s infinite ease-in-out;
                        transition: transform 0.2s;
                        margin-bottom: 15px;
                        min-height: 140px; /* Για να είναι ομοιόμορφα τα κουτάκια */
                    }
                    .loot-badge:hover {
                        transform: translateY(-8px);
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    cols = st.columns(4)
                    for i, b in enumerate(badges):
                        with cols[i % 4]:
                            # Δημιουργία του custom κουτιού για κάθε achievement
                            st.markdown(f"""
                            <div class="loot-badge">
                                <div style="font-size: 2.5rem; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">{b['icon']}</div>
                                <div style="color: #f1c40f; font-weight: bold; font-size: 1.1rem; margin-bottom: 8px;">{b['title']}</div>
                                <div style="color: #ecf0f1; font-size: 0.85rem; line-height: 1.3;">{b['desc']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("🏆 Milestones")
                sem_stats_df = pd.DataFrame([{'Period': f"{p} '{y[-2:]}", 'Count': len(g), 'GPA': (g['Βαθμός']*g['ECTS']).sum()/g['ECTS'].sum() if g['ECTS'].sum()>0 else 0} for (y, p), g in regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος'])])
                golden = sem_stats_df.sort_values(by=['Count', 'GPA'], ascending=[False, False]).iloc[0]
                dark = sem_stats_df.sort_values(by=['GPA', 'Count'], ascending=[True, True]).iloc[0]
                best_c = regular_courses_df.loc[regular_courses_df['Βαθμός'].idxmax()]
                
                cf1, cf2, cf3 = st.columns(3)
                cf1.info(f"🌟 **Χρυσή Εξεταστική:**\n\n**{golden['Period']}** ({int(golden['Count'])} μαθ. | Μ.Ο. {golden['GPA']:.2f})")
                cf2.warning(f"💀 **Πιο Δύσκολη Εξεταστική:**\n\n**{dark['Period']}** (Μ.Ο. {dark['GPA']:.2f})")
                cf3.success(f"💯 **Καλύτερο Μάθημα:**\n\n**{best_c['Μάθημα']}** ({best_c['Βαθμός']})")

        # ==========================================
        # TAB 2: ANALYTICS ENGINE (2D Charts)
        # ==========================================
        with tab2:
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
                        exp_course_grade = st.slider(f"Στόχος Μ.Ο. εναπομεινάντων:", 5.0, 10.0, ai_grade, 0.1)
                    else:
                        exp_course_grade, missing_course_ects = 0, 0
                        st.info("Έχεις περάσει όλα τα απαιτούμενα μαθήματα!")
                        
                with col_s2:
                    if not has_thesis:
                        st.info("💡 **Tip:** Στη Διπλωματική ο στόχος ορίστηκε στο 9.0 από προεπιλογή.")
                        exp_thesis_grade = st.slider("Στόχος Διπλωματικής (30 ECTS):", 5.0, 10.0, 9.0, 0.1)
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
            
            st.markdown("---")
            st.subheader("🐙 Εξαγωγή για το GitHub")
            with st.expander("Δημιουργία Markdown κώδικα για το προφίλ σου (README.md)"):
                bar_len = 20
                filled_len = int(min(total_ects / 300, 1.0) * bar_len)
                md_text = f"## 🎓 Academic Profile (@panagiotispar)\n\n**University of Ioannina** | Computer Science and Engineering\n\n### 📊 Base Stats\n- ⚔️ **Rank:** {rank_title}\n- 🎯 **GPA:** {final_gpa:.2f} / 10.0\n- 📚 **Courses:** {total_courses} / 47\n- 🎓 **Progress:** `[{'█' * filled_len + '░' * (bar_len - filled_len)}]` {(total_ects / 300) * 100:.1f}% ({total_ects:g}/300 ECTS)\n\n"
                if 'badges' in locals() and badges:
                    md_text += "### 🏅 Unlocked Achievements\n" + "".join([f"- **{b['icon']} {b['title']}**: {b['desc']}\n" for b in badges])
                st.code(md_text, language='markdown')
                st.download_button("💾 Κατέβασμα ως progress.md", md_text, "progress.md", "text/markdown")
                
            with st.expander("Προεπισκόπηση Καθαρών Δεδομένων (Raw Data)"):
                st.dataframe(cleaned_df)

        # ==========================================
        # TAB 5: CO-OP MODE (Split-Screen Multiplayer)
        # ==========================================
        with tab5:
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
                    
                    st.markdown("---")
                    
                    # UI Σύγκρισης 
                    col_p1, col_vs, col_p2 = st.columns([5, 1, 5])
                    
                    with col_p1:
                        st.markdown("<h3 style='text-align: center; color: #3498db;'>🔵 Player 1 (Εσύ)</h3>", unsafe_allow_html=True)
                        st.metric("Τρέχων Μ.Ο. (GPA)", f"{final_gpa:.2f}")
                        st.metric("Περασμένα Μαθήματα", f"{total_courses} ( {total_ects:g} / 300 ECTS )")
                        st.metric("Max Streak (Σερί Εξεταστικών)", f"{streak_1} 🔥")
                        st.metric("Achievements Unlocked", f"{badges_1} 🏅")
                        
                        st.markdown("<br><h5>💼 Ειδικά Μαθήματα</h5>", unsafe_allow_html=True)
                        st.info(f"**Διπλωματική:** {thesis_status_1}\n\n**Πρακτική Άσκηση:** {int_status_1}")
                        
                        if gold_1 is not None:
                            st.success(f"🌟 **Χρυσή Εξεταστική:**\n\n**{gold_1['Period']}** ({int(gold_1['Count'])} μαθήματα | Μ.Ο. {gold_1['GPA']:.2f})")
                            
                    with col_vs:
                        st.markdown("<h1 style='text-align: center; color: #95a5a6; margin-top: 150px;'>VS</h1>", unsafe_allow_html=True)
                        
                    with col_p2:
                        st.markdown("<h3 style='text-align: center; color: #e74c3c;'>🔴 Player 2 (Αντίπαλος)</h3>", unsafe_allow_html=True)
                        st.metric("Τρέχων Μ.Ο. (GPA)", f"{gpa_2:.2f}", delta=f"{gpa_2 - final_gpa:.2f}")
                        st.metric("Περασμένα Μαθήματα", f"{courses_2} ( {ects_2:g} / 300 ECTS )", delta=f"{courses_2 - total_courses}")
                        st.metric("Max Streak (Σερί Εξεταστικών)", f"{streak_2} 🔥", delta=f"{streak_2 - streak_1}")
                        st.metric("Achievements Unlocked", f"{badges_2} 🏅", delta=f"{badges_2 - badges_1}")
                        
                        st.markdown("<br><h5>💼 Ειδικά Μαθήματα</h5>", unsafe_allow_html=True)
                        st.info(f"**Διπλωματική:** {thesis_status_2}\n\n**Πρακτική Άσκηση:** {int_status_2}")

                        if gold_2 is not None:
                            st.success(f"🌟 **Χρυσή Εξεταστική:**\n\n**{gold_2['Period']}** ({int(gold_2['Count'])} μαθήματα | Μ.Ο. {gold_2['GPA']:.2f})")
                            
                    st.markdown("---")
                    
                    # Γράφημα Head-to-Head (Radar Chart)
                    st.subheader("📊 Head-to-Head Skill Matchup")
                    
                    categories = ['GPA (x10)', 'Σύνολο Μαθημάτων', 'Max Streak (x10)', 'Achievements (x10)', 'Πρόοδος Πτυχίου (%)']
                    
                    p1_stats = [final_gpa * 10, total_courses, streak_1 * 10, badges_1 * 10, min((total_ects / 300) * 100, 100)]
                    p2_stats = [gpa_2 * 10, courses_2, streak_2 * 10, badges_2 * 10, min((ects_2 / 300) * 100, 100)]
                    
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=p1_stats, theta=categories, fill='toself', name='Player 1', line_color='#3498db', opacity=0.8
                    ))
                    fig_radar.add_trace(go.Scatterpolar(
                        r=p2_stats, theta=categories, fill='toself', name='Player 2', line_color='#e74c3c', opacity=0.8
                    ))
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, max(max(p1_stats), max(p2_stats)) + 5]),
                            bgcolor='#f8f9fa'
                        ),
                        showlegend=True, margin=dict(t=40, b=40)
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Το αρχείο του Player 2 δεν μπόρεσε να αναγνωστεί σωστά: {e}")

    except Exception as e:
        st.error(f"Προέκυψε σφάλμα κατά την ανάγνωση του αρχείου: {e}")
