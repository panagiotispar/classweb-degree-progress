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
    # Κρατάμε ΠΛΕΟΝ και τη στήλη ECTS
    df = df[['Μάθημα', 'Βαθμός', 'Εξ. περίοδος', 'Β.Π.', 'Π.Π.', 'ECTS']].copy()
    
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
            
            # Μετράμε ΠΟΣΑ είναι τα ΚΑΝΟΝΙΚΑ μαθήματα (εξαιρούμε την πρακτική από την καταμέτρηση)
            count_regular = sum(1 for c in courses_in_period if not re.search(r'ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ', str(c[0]), re.IGNORECASE))
            current_total += count_regular
            
            # Αλλά υπολογίζουμε τον Μ.Ο. και τα ECTS βάσει ΟΛΩΝ των μαθημάτων της εξεταστικής (μαζί με την πρακτική)
            for course_name, grade, ects in courses_in_period:
                cumulative_points += grade * ects
                cumulative_ects += ects
                
            current_gpa = round(cumulative_points / cumulative_ects, 2) if cumulative_ects > 0 else None
            
            label = f"{period}<br>'{year[-2:]}"
            x_labels.append(label)
            y_values_cum.append(current_total)
            y_values_bar.append(count_regular) # Το ραβδόγραμμα θα δείχνει μόνο τα κανονικά
            y_values_gpa.append(current_gpa)
            
            # Αν υπάρχει ΕΣΤΩ ΚΑΙ ΕΝΑ μάθημα (κανονικό ή πρακτική) σε αυτή την εξεταστική
            if len(courses_in_period) > 0:
                # Αν πέρασε μόνο πρακτική, βάζουμε ένα διαφορετικό χρώμα (τιρκουάζ) στη μπάρα που θα είναι στο 0!
                colors_bar.append('#3498db' if count_regular > 0 else '#1abc9c') 
                text = f"<b>📅 {period} '{year[-2:]} ({count_regular} μαθήματα)</b><br>"
                text += "━"*30 + "<br>"
                for course_name, grade, ects in courses_in_period:
                    if re.search(r'ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ', str(course_name), re.IGNORECASE):
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
    
    # Βρίσκουμε το ελάχιστο και μέγιστο του Μ.Ο. για να "ζουμάρουμε" σωστά τον άξονα Υ
    valid_gpas = [g for g in y_values_gpa if g is not None]
    min_gpa = min(valid_gpas) - 0.2 if valid_gpas else 5.0
    max_gpa = max(valid_gpas) + 0.2 if valid_gpas else 10.0

    fig_gpa.add_trace(go.Scatter(
        x=x_labels, y=y_values_gpa, mode='lines+markers',
        hoverinfo='text', hovertext=hover_texts_gpa,
        line=dict(shape='spline', smoothing=0.3, color='#27ae60', width=4), # Πράσινο χρώμα και καμπύλες
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
        yaxis=dict(showgrid=True, gridcolor='rgba(149, 165, 166, 0.3)', range=[min_gpa, max_gpa]) # Ζουμ στον άξονα Υ για να φαίνονται οι διακυμάνσεις!
    )

    return fig_cum, fig_bar, fig_gpa


# Main Εφαρμογή
if uploaded_file is not None:
    try:
        raw_data = pd.read_excel(uploaded_file, header=1)
        cleaned_df = clean_classweb_data(raw_data)
        
        st.success("✅ Το αρχείο διαβάστηκε και καθαρίστηκε με επιτυχία!")
        
        # Εντοπισμός πρακτικής 
        is_internship = cleaned_df['Μάθημα'].str.contains('ΠΡΑΚΤΙΚΗ ΑΣΚΗΣΗ', case=False, na=False)
        internship_df = cleaned_df[is_internship]
        
        st.markdown("---")
        st.subheader("📊 Η Πρόοδός σου με μια ματιά")
        
        # Μετράμε πλήθος ΜΟΝΟ από τα κανονικά, αλλά ECTS/ΜΟ από ΟΛΑ
        total_courses = len(cleaned_df[~is_internship]) 
        total_ects = cleaned_df['ECTS'].sum() 
        target_courses = 47
        
        if total_ects > 0:
            final_gpa = (cleaned_df['Βαθμός'] * cleaned_df['ECTS']).sum() / total_ects
        else:
            final_gpa = 0.0
            
        # --- Λογική Κατηγορίας Πτυχίου ---
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
        # --------------------------------------
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Περασμένα Μαθήματα", value=f"{total_courses} / {target_courses}")
        with col2:
            st.metric(label="Σύνολο ECTS", value=f"{total_ects:g}")
        with col3:
            st.metric(label="Τρέχων Μ.Ο.", value=f"{final_gpa:.2f}")
        with col4:
            st.metric(label="Υπολείπονται", value=f"{max(0, target_courses - total_courses)} μαθήματα")
            
        # Εμφάνιση μηνύματος κλίμακας πτυχίου
        if final_gpa >= 5.0:
            st.success(f"🎯 **Κλίμακα Πτυχίου:** Η τρέχουσα βαθμολογία σου αντιστοιχεί στο **{degree_class}**. {target_msg}")
            
        if not internship_df.empty:
            internship_ects = internship_df['ECTS'].sum()
            st.info(f"📌 Εντοπίστηκε Πρακτική Άσκηση. Προστέθηκαν τα ECTS ({internship_ects:g}) και συνυπολογίστηκε κανονικά στον Μ.Ο., αλλά εξαιρέθηκε από την καταμέτρηση των {target_courses} μαθημάτων.")
            
        progress_val = min(total_courses / target_courses, 1.0)
        st.progress(progress_val)
        st.markdown("---")
        
        with st.expander("Προεπισκόπηση Καθαρών Δεδομένων"):
            st.dataframe(cleaned_df)
        
        # Περνάμε ΟΛΑ τα δεδομένα στα γραφήματα για να δουν την πρακτική
        fig_cum, fig_bar, fig_gpa = create_plotly_charts(cleaned_df)
        
        st.plotly_chart(fig_cum, use_container_width=True)
        st.plotly_chart(fig_gpa, use_container_width=True)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    except Exception as e:
        st.error(f"Προέκυψε σφάλμα κατά την ανάγνωση του αρχείου: {e}")
