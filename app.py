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
    df = df[['Μάθημα', 'Βαθμός', 'Εξ. περίοδος', 'Β.Π.', 'Π.Π.']].copy()
    
    # 1. Καθαρισμός του HTML από το όνομα του μαθήματος
    df['Μάθημα'] = df['Μάθημα'].apply(lambda x: re.sub(r'<a id=.*', '', str(x)).strip())
    
    df = df[(df['Β.Π.'] == 'Ναι') | (df['Π.Π.'] == 'Ναι')]
    
    # 3. Καθαρισμός Βαθμού
    df = df.dropna(subset=['Βαθμός'])
    df['Βαθμός'] = pd.to_numeric(df['Βαθμός'], errors='coerce')
    # Η μαγική γραμμή που φτιάχνει το 55 -> 5.5, 95 -> 9.5
    df['Βαθμός'] = df['Βαθμός'].apply(lambda x: x / 10 if x > 10 else x)
    
    # Δευτερεύων έλεγχος για σιγουριά
    df = df[df['Βαθμός'] >= 5.0]
    
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
    # Μετατροπή του Dataframe στη μορφή 'detailed_data'
    detailed_data = {}
    for _, row in df.iterrows():
        key = (row['Ακαδ. Έτος'], row['Περίοδος'])
        if key not in detailed_data:
            detailed_data[key] = []
        detailed_data[key].append((row['Μάθημα'], row['Βαθμός']))

    # Εύρεση του μικρότερου και μεγαλύτερου έτους για να χτιστεί ο άξονας Χ
    min_year = min([int(y.split('-')[0]) for y in df['Ακαδ. Έτος'] if y != "Άγνωστο"])
    max_year = max([int(y.split('-')[0]) for y in df['Ακαδ. Έτος'] if y != "Άγνωστο"])
    
    years = [f"{y}-{str(y+1)[-2:]}" for y in range(min_year, max_year + 1)]
    periods = ['Φεβ', 'Ιουν', 'Σεπ']
    
    x_labels = []
    y_values_cum = []
    y_values_bar = []
    hover_texts = []
    current_total = 0
    colors_bar = []
    
    # Χτίσιμο Δεδομένων για τα γραφήματα
    for year in years:
        for period in periods:
            key = (year, period)
            courses_passed = detailed_data.get(key, [])
            count = len(courses_passed)
            current_total += count
            
            label = f"{period}<br>'{year[-2:]}"
            x_labels.append(label)
            y_values_cum.append(current_total)
            y_values_bar.append(count)
            
            if count > 0:
                colors_bar.append('#3498db')
                text = f"<b>📅 {period} '{year[-2:]} ({count} μαθήματα)</b><br>"
                text += "━"*30 + "<br>"
                for course_name, grade in courses_passed:
                    text += f"▪ {course_name}  [{grade}]<br>"
            else:
                colors_bar.append('#ecf0f1')
                text = f"<b>📅 {period} '{year[-2:]}</b><br>"
                text += "━"*15 + "<br>Κανένα περασμένο μάθημα"
                
            hover_texts.append(text)

    # --- 1. ΑΘΡΟΙΣΤΙΚΟ ΓΡΑΦΗΜΑ ---
    static_texts_cum = []
    prev_val = -1
    for i, val in enumerate(y_values_cum):
        if val > prev_val and i != len(y_values_cum) - 1:
            static_texts_cum.append(f"<b>{val}</b>")
        else:
            static_texts_cum.append("")
        prev_val = val

    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=x_labels, y=y_values_cum, mode='lines+markers+text',
        text=static_texts_cum, textposition='top left',
        textfont=dict(color='#2c3e50', size=11), hoverinfo='text', hovertext=hover_texts,
        line=dict(shape='hv', color='#2980b9', width=3),
        marker=dict(size=8, color='white', line=dict(color='#2980b9', width=2)),
        fill='tozeroy', fillcolor='rgba(52, 152, 219, 0.3)',
        hoverlabel=dict(bgcolor="#f8f9fa", bordercolor="#bdc3c7", font=dict(size=12, color='#2c3e50'), align="left")
    ))
    val_final = y_values_cum[-1]
    fig_cum.add_annotation(
        x=x_labels[-1], y=val_final, text=f"<b>ΣΥΝΟΛΟ: {val_final}</b>",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="black",
        ax=-60, ay=-40, bgcolor="#f1c40f", bordercolor="#f39c12", borderwidth=3, borderpad=6, font=dict(size=16, color="black")
    )
    fig_cum.update_layout(
        title=dict(text='<b>Η Πορεία προς το Πτυχίο (Αθροιστική Πρόοδος)</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        yaxis_title=dict(text='Σύνολο Περασμένων Μαθημάτων', font=dict(color='#2c3e50')),
        plot_bgcolor='white', margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(tickangle=-90, showgrid=True, gridcolor='rgba(149, 165, 166, 0.3)', type='category', range=[-0.5, len(x_labels) - 0.5]),
        yaxis=dict(showgrid=True, gridcolor='rgba(149, 165, 166, 0.3)', range=[0, max(y_values_cum) + 10])
    )

    # --- 2. ΡΑΒΔΟΓΡΑΜΜΑ (BAR CHART) ---
    static_texts_bar = [f"<b>{val}</b>" if val > 0 else "" for val in y_values_bar]
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=x_labels, y=y_values_bar, marker_color=colors_bar, text=static_texts_bar, textposition='outside',
        textfont=dict(color='#2c3e50', size=11), hoverinfo='text', hovertext=hover_texts,
        hoverlabel=dict(bgcolor="#f8f9fa", bordercolor="#bdc3c7", font=dict(size=12, color='#2c3e50'), align="left")
    ))
    fig_bar.update_layout(
        title=dict(text='<b>Ιστορικό Επιτυχίας Μαθημάτων ανά Εξεταστική</b>', font=dict(size=20, color='#2c3e50'), x=0.5),
        yaxis_title=dict(text='Αριθμός Περασμένων Μαθημάτων', font=dict(color='#2c3e50')),
        plot_bgcolor='white', margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(tickangle=-90, showgrid=True, gridcolor='rgba(189, 195, 199, 0.5)', type='category', range=[-0.5, len(x_labels) - 0.5]),
        yaxis=dict(showgrid=True, gridcolor='rgba(189, 195, 199, 0.5)', range=[0, max(y_values_bar) + 2])
    )

    return fig_cum, fig_bar

# Main Εφαρμογή
if uploaded_file is not None:
    try:
        raw_data = pd.read_excel(uploaded_file, header=1)
        cleaned_df = clean_classweb_data(raw_data)
        
        st.success("✅ Το αρχείο διαβάστηκε και καθαρίστηκε με επιτυχία!")
        
        # Έβαλα τον πίνακα σε "επεκτεινόμενο μενού" (expander) για να μη γεμίζει όλη την οθόνη
        with st.expander("Προεπισκόπηση Καθαρών Δεδομένων"):
            st.dataframe(cleaned_df)
        
        # Παραγωγή γραφημάτων
        fig_cum, fig_bar = create_plotly_charts(cleaned_df)
        
        # Εμφάνιση των γραφημάτων (το use_container_width προσαρμόζει το πλάτος στην οθόνη/κινητό)
        st.plotly_chart(fig_cum, use_container_width=True)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    except Exception as e:
        st.error(f"Προέκυψε σφάλμα κατά την ανάγνωση του αρχείου: {e}")
