import streamlit as st
import pandas as pd
import re
import plotly.graph_objects as go

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Πορεία προς το Πτυχίο", page_icon="🎓", layout="wide")

st.title("🎓 Διαδραστική Πορεία προς το Πτυχίο")
st.markdown("Ανέβασε το αρχείο Excel (**H καρτέλα μου - Όλα τα μαθήματα.xlsx**) που εξάγεται από το ClassWeb για να δεις την αθροιστική σου πρόοδο.")

# Κουμπί ανεβάσματος αρχείου
uploaded_file = st.file_uploader("Επίλεξε το αρχείο Excel", type=['xlsx'])

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

    return fig_cum, fig_bar, fig_gpa, fig_dist, fig_category


# Main Εφαρμογή
if uploaded_file is not None:
    try:
        raw_data = pd.read_excel(uploaded_file, header=1)
        cleaned_df = clean_classweb_data(raw_data)
        
        st.success("✅ Το αρχείο διαβάστηκε και καθαρίστηκε με επιτυχία!")
        
        # Εντοπισμός Πρακτικής και Διπλωματικής
        is_internship = cleaned_df['Μάθημα'].str.contains('ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ', case=False, na=False)
        is_thesis = cleaned_df['Μάθημα'].str.contains('ΔΙΠΛΩΜΑΤΙΚΗ', case=False, na=False)
        
        internship_df = cleaned_df[is_internship]
        thesis_df = cleaned_df[is_thesis]
        
        st.markdown("---")
        st.subheader("📊 Η Πρόοδός σου με μια ματιά")
        
        # Μετράμε πλήθος ΜΟΝΟ από τα κανονικά (χωρίς Πρακτική και χωρίς Διπλωματική)
        regular_courses_df = cleaned_df[~(is_internship | is_thesis)].copy()
        total_courses = len(regular_courses_df) 
        total_ects = cleaned_df['ECTS'].sum() 
        target_courses = 47
        
        if total_ects > 0:
            final_gpa = (cleaned_df['Βαθμός'] * cleaned_df['ECTS']).sum() / total_ects
        else:
            final_gpa = 0.0
            
        # Λογική Κατηγορίας Πτυχίου
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
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="Περασμένα Μαθήματα", value=f"{total_courses} / {target_courses}")
            prog_courses = min(total_courses / target_courses, 1.0) * 100
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="flex-grow: 1; background-color: rgba(150, 150, 150, 0.2); border-radius: 8px; height: 14px; z-index: 0;">
                    <div style="width: {prog_courses}%; background-color: #3498db; height: 100%; border-radius: 8px; transition: width 0.5s;"></div>
                </div>
                <div style="margin-left: -10px; font-size: 1.3rem; z-index: 1; display: flex; align-items: center;">🏁</div>
            </div>
            <div style="margin-bottom: 15px;"></div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.metric(label="Σύνολο ECTS", value=f"{total_ects:g} / 300")
            prog_ects = min(total_ects / 300, 1.0) * 100
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="flex-grow: 1; background-color: rgba(150, 150, 150, 0.2); border-radius: 8px; height: 14px; z-index: 0;">
                    <div style="width: {prog_ects}%; background-color: #27ae60; height: 100%; border-radius: 8px; transition: width 0.5s;"></div>
                </div>
                <div style="margin-left: -11px; font-size: 1.3rem; z-index: 1; display: flex; align-items: center;">📜</div>
            </div>
            <div style="margin-bottom: 15px;"></div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.metric(label="Τρέχων Μ.Ο.", value=f"{final_gpa:.2f}")
            
        with col4:
            missing_courses = max(0, target_courses - total_courses)
            
            # Δυναμικά Boost Μηνύματα (Motivation)
            if missing_courses == 0:
                if thesis_df.empty:
                    st.metric(label="Status", value="Μένει Διπλωματική! 🚀")
                else:
                    st.metric(label="Status", value="Απόφοιτος! 🎓")
            elif missing_courses <= 5:
                st.metric(label="Πολύ κοντά στην πηγή! 💧", value=f"Μένουν {missing_courses} μαθήματα")
            elif missing_courses <= 15:
                st.metric(label="Μπήκες στην τελική ευθεία! 🏃", value=f"Μένουν {missing_courses} μαθήματα")
            elif missing_courses <= 30:
                st.metric(label="Έχουμε δρόμο ακόμα! 💪", value=f"Μένουν {missing_courses} μαθήματα")
            else:
                st.metric(label="Δυνατά για τη συνέχεια! 📚", value=f"Μένουν {missing_courses} μαθήματα")
            
        if final_gpa >= 5.0:
            st.success(f"🎯 **Κλίμακα Πτυχίου:** Η τρέχουσα βαθμολογία σου αντιστοιχεί στο **{degree_class}**. {target_msg}")
            
        if not internship_df.empty:
            internship_ects = internship_df['ECTS'].sum()
            st.info(f"📌 Εντοπίστηκε Πρακτική Άσκηση. Προστέθηκαν τα ECTS ({internship_ects:g}) στον Μ.Ο., αλλά εξαιρέθηκε από την καταμέτρηση των {target_courses} μαθημάτων.")
            
        # --- FUN FACTS SECTION ---
        if not regular_courses_df.empty:
            best_course_row = regular_courses_df.loc[regular_courses_df['Βαθμός'].idxmax()]
            
            sem_stats = []
            for (year, period), group in regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος']):
                cnt = len(group)
                sm_ects = group['ECTS'].sum()
                sm_pts = (group['Βαθμός'] * group['ECTS']).sum()
                sm_gpa = sm_pts / sm_ects if sm_ects > 0 else 0
                sem_stats.append({'Period': f"{period} '{year[-2:]}", 'Count': cnt, 'GPA': sm_gpa})
                
            if sem_stats:
                sem_stats_df = pd.DataFrame(sem_stats)
                golden_sem = sem_stats_df.sort_values(by=['Count', 'GPA'], ascending=[False, False]).iloc[0]
                dark_sem = sem_stats_df.sort_values(by=['GPA', 'Count'], ascending=[True, True]).iloc[0]
                
                st.markdown("---")
                st.subheader("🏆 Fun Facts & Milestones")
                c_f1, c_f2, c_f3 = st.columns(3)
                
                with c_f1:
                    st.info(f"🌟 **Χρυσή Εξεταστική:**\n\nΗ καλύτερη περίοδος ήταν ο **{golden_sem['Period']}**. Πέρασες **{int(golden_sem['Count'])}** μαθήματα με Μ.Ο. **{golden_sem['GPA']:.2f}**!")
                with c_f2:
                    st.warning(f"💀 **Πιο Δύσκολη Εξεταστική:**\n\nΟ **{dark_sem['Period']}** σε ζόρισε περισσότερο, με τον χαμηλότερο Μ.Ο. (**{dark_sem['GPA']:.2f}**).")
                with c_f3:
                    st.success(f"💯 **Το Καλύτερο Μάθημα:**\n\nΞεχώρισες στο **{best_course_row['Μάθημα']}** γράφοντας **{best_course_row['Βαθμός']}**!")
                    
        # --- ΝΕΟ: BADGES / ACHIEVEMENTS ---
        if not regular_courses_df.empty:
            badges = []
            
            # 1. Απόλυτο 10άρι
            if (regular_courses_df['Βαθμός'] == 10).any():
                badges.append({"icon": "🎯", "title": "Απόλυτο 10άρι", "desc": "Πέτυχες το απόλυτο 10άρι σε τουλάχιστον ένα μάθημα!"})
                
            # 2. Μηχανή των ECTS
            ects_per_period = regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος'])['ECTS'].sum()
            if not ects_per_period.empty and ects_per_period.max() >= 30:
                max_ects = ects_per_period.max()
                badges.append({"icon": "🚂", "title": "Μηχανή των ECTS", "desc": f"Συγκέντρωσες {max_ects:g} ECTS σε μία μόνο εξεταστική!"})
                
            # 3. Αντεπίθεση του Σεπτέμβρη
            sept_courses = regular_courses_df[regular_courses_df['Περίοδος'] == 'Σεπ']
            if not sept_courses.empty:
                sept_counts = sept_courses.groupby('Ακαδ. Έτος').size()
                if not sept_counts.empty and sept_counts.max() >= 3:
                    badges.append({"icon": "🛡️", "title": "Αντεπίθεση του Σεπτέμβρη", "desc": f"Έσωσες τη χρονιά περνώντας {sept_counts.max()} μαθήματα σε έναν Σεπτέμβρη!"})
                    
            # 4. Final Boss (Διπλωματική)
            if not thesis_df.empty:
                badges.append({"icon": "🐉", "title": "Boss Defeated", "desc": "Ολοκλήρωσες επιτυχώς τη Διπλωματική σου Εργασία!"})
                
            # 5. Πρώτα Βήματα (Πρακτική)
            if not internship_df.empty:
                badges.append({"icon": "🌐", "title": "Hello World!", "desc": "Μπήκες στον επαγγελματικό στίβο ολοκληρώνοντας την Πρακτική σου Άσκηση!"})
                
            # 6. Streak Εξεταστικών (On Fire)
            period_counts = {}
            for (year, period), group in regular_courses_df.groupby(['Ακαδ. Έτος', 'Περίοδος']):
                if year != "Άγνωστο":
                    period_counts[(year, period)] = len(group)
            
            if period_counts:
                min_yr = min([int(y.split('-')[0]) for y, p in period_counts.keys()])
                max_yr = max([int(y.split('-')[0]) for y, p in period_counts.keys()])
                
                current_streak = 0
                max_streak = 0
                
                # Σαρώνουμε χρονολογικά όλες τις πιθανές εξεταστικές περιόδους
                for y in range(min_yr, max_yr + 1):
                    year_str = f"{y}-{str(y+1)[-2:]}"
                    for p in ['Φεβ', 'Ιουν', 'Σεπ']:
                        # Προϋπόθεση: να περάσει τουλάχιστον 2 μαθήματα στην εξεταστική
                        if period_counts.get((year_str, p), 0) >= 2:
                            current_streak += 1
                            max_streak = max(max_streak, current_streak)
                        else:
                            current_streak = 0
                            
                if max_streak >= 3:
                    badges.append({"icon": "🔥", "title": "On Fire", "desc": f"Πέρασες 2+ μαθήματα για {max_streak} συνεχόμενες εξεταστικές!"})

            # Εμφάνιση Badges (δυναμική δημιουργία γραμμών ανά 4)
            if badges:
                st.markdown("---")
                st.subheader("🏅 Επιτεύγματα (Achievements)")
                cols_per_row = 4
                for i in range(0, len(badges), cols_per_row):
                    row_badges = badges[i:i+cols_per_row]
                    badge_cols = st.columns(cols_per_row)
                    for j, badge in enumerate(row_badges):
                        with badge_cols[j]:
                            st.info(f"**{badge['icon']} {badge['title']}**\n\n{badge['desc']}")
        # ----------------------------------------
        
        # --- ΠΡΟΣΟΜΟΙΩΤΗΣ Μ.Ο. (What-If) ---
        st.markdown("---")
        st.subheader("🔮 Προσομοιωτής Βαθμού Πτυχίου (What-If)")
        st.markdown("Υπολόγισε τον τελικό σου βαθμό συμπληρώνοντας τους στόχους σου για τα υπόλοιπα μαθήματα και τη Διπλωματική.")
        
        has_thesis = not thesis_df.empty
        current_points = (cleaned_df['Βαθμός'] * cleaned_df['ECTS']).sum()
        
        missing_total_ects = max(0, 300 - total_ects)
        missing_courses = max(0, target_courses - total_courses)
        
        if missing_total_ects > 0 or missing_courses > 0:
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                if missing_courses > 0:
                    expected_course_grade = st.slider(f"Στόχος Μ.Ο. για τα {missing_courses} μαθήματα που υπολείπονται:", min_value=5.0, max_value=10.0, value=7.5, step=0.1)
                    missing_course_ects = missing_total_ects - (30 if not has_thesis else 0)
                    missing_course_ects = max(0, missing_course_ects)
                else:
                    expected_course_grade = 0
                    missing_course_ects = 0
                    st.info("Έχεις περάσει όλα τα απαιτούμενα μαθήματα!")
                    
            with col_s2:
                if not has_thesis:
                    expected_thesis_grade = st.slider("Στόχος για Διπλωματική Εργασία (30 ECTS):", min_value=5.0, max_value=10.0, value=9.5, step=0.1)
                else:
                    expected_thesis_grade = 0
                    st.success("Έχεις ήδη περάσει τη Διπλωματική Εργασία!")
            
            future_points = current_points + (missing_course_ects * expected_course_grade) + (30 * expected_thesis_grade if not has_thesis else 0)
            future_ects = total_ects + missing_course_ects + (30 if not has_thesis else 0)
            
            simulated_gpa = future_points / future_ects if future_ects > 0 else 0.0
            
            if simulated_gpa >= 8.5:
                sim_class = "Άριστα 🏆"
            elif simulated_gpa >= 6.5:
                sim_class = "Λίαν Καλώς 🥈"
            else:
                sim_class = "Καλώς 🥉"
                
            st.info(f"✨ **Προβολή:** Αν πετύχεις αυτούς τους βαθμούς, θα ορκιστείς με τελικό βαθμό **{simulated_gpa:.2f} ({sim_class})**!")
        else:
            st.info("Έχεις ήδη συγκεντρώσει 300+ ECTS και έχεις περάσει όλα τα μαθήματα! Ο βαθμός σου έχει κλειδώσει.")
        # ----------------------------------------
        
        with st.expander("Προεπισκόπηση Καθαρών Δεδομένων"):
            st.dataframe(cleaned_df)
        
        # Περνάμε ΟΛΑ τα δεδομένα στα γραφήματα
        fig_cum, fig_bar, fig_gpa, fig_dist, fig_category = create_plotly_charts(cleaned_df)
        
        st.plotly_chart(fig_cum, use_container_width=True)
        st.plotly_chart(fig_gpa, use_container_width=True)
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.plotly_chart(fig_dist, use_container_width=True) 
        with col_chart2:
            st.plotly_chart(fig_category, use_container_width=True)
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
    except Exception as e:
        st.error(f"Προέκυψε σφάλμα κατά την ανάγνωση του αρχείου: {e}")
