# ==============================================================================
# HIGH-END STREAMLIT APP: Analyse systematischer Bewertungsunterschiede (Bias)
# ==============================================================================
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy import stats
import streamlit as st
import plotly.express as px

# High-End PDF Generation Imports
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# --- 1. SEITEN-KONFIGURATION & DESIGN ---
st.set_page_config(
    page_title="Dashboard: Prüferübereinstimmung",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Eigenes CSS für ein noch edleres Design
st.markdown("""
<style>
/* Hier kann optional CSS ergänzt werden */
</style>
""", unsafe_allow_html=True)

# =======================================================================
# # --- HAUPTANWENDUNG STARTET HIER ---
# =======================================================================



# --- 2. HEADER ---
st.title("📊 Prüferübereinstimmung (t-Test)")

st.markdown("""
Diese Anwendung identifiziert systematische Strenge-/Milde-Effekte (Bias) zwischen Prüferpaaren auf Basis gepaarter t-Tests und der Effektstärke nach Cohen's d.

**💡 Methodische Erläuterung zum gepaarten t-Test:**
Der gepaarte t-Test ist ein statistisches Prüfverfahren, das analysiert, ob die Mittelwertdifferenz der Bewertungen von zwei Prüfern (die exakt dieselben Kandidaten beurteilt haben) signifikant von null abweicht. Fällt der Test signifikant aus, bedeutet dies, dass ein Prüfer systematisch strenger oder milder bewertet als der andere (Vorliegen eines Bias). Da Signifikanztests jedoch stark von der Stichprobengröße abhängen, wird ergänzend die Effektstärke (*Cohen's d*) berechnet. Sie quantifiziert das Ausmaß des Unterschieds und hilft dabei einzuschätzen, ob die Abweichung auch in der Praxis eine Relevanz hat.
""")
st.divider()

# --- 3. SIDEBAR: UPLOAD ---
with st.sidebar:
    st.header("⚙️ Daten & Einstellungen")
    uploaded_file = st.file_uploader("📁 App-Datenbank hochladen (Excel)", type=["xlsx", "xls"])
    
    st.info("💡 **Hinweis zu statistischen Anforderungen:**\n\n"
            "Für einen aussagekräftigen gepaarten t-Test sollten in der psychometrischen Fachliteratur (vgl. Bortz & Döring) "
            "idealerweise **mindestens 30 bis 50 Datensätze (Paarvergleiche)** vorliegen. Bei zu kleinen Stichproben fehlt dem Signifikanztest "
            "die notwendige Teststärke (Power), um systematische Bewertungsunterschiede (Bias) zuverlässig aufzudecken.")

    if not uploaded_file:
        st.info("Bitte laden Sie die standardisierte Prüfungsmatrix (Excel) hoch, um das Dashboard zu aktivieren.")
        st.stop()

# --- 4. DATENVERARBEITUNG (Robust & Fehlerfrei) ---
try:
    with st.spinner('Analysiere Daten und berechne statistische Modelle...'):
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        
        if 'Prüfungsdatum' not in df.columns and 'Jahr' not in df.columns:
            st.error("Fehler: Die Spalte 'Prüfungsdatum' oder 'Jahr' fehlt im Datensatz.")
            st.stop()
            
        if 'Jahr' not in df.columns:
            df['Jahr'] = pd.to_datetime(df['Prüfungsdatum'], format='%d.%m.%Y', errors='coerce').dt.year
            
        KRITERIEN = ['Inhalt', 'Aussprache_Intonation', 'Flüssigkeit', 'Korrektheit_Wortschatz']
        RUNDEN = ['A1_1', 'A1_2', 'A1_3', 'A2_1', 'A2_2', 'A2_3', 'B1_1', 'B1_2', 'B1_3', 'B2_1', 'B2_2', 'B2_3', 'C1_1', 'C1_2', 'C1_3']
        
        # Differenzen berechnen
        for runde in RUNDEN:
            for kriterium in KRITERIEN:
                c1 = f'Mündlich_{kriterium}_{runde}_P1'
                c2 = f'Mündlich_{kriterium}_{runde}_P2'
                if c1 in df.columns and c2 in df.columns:
                    df[c1] = pd.to_numeric(df[c1], errors='coerce')
                    df[c2] = pd.to_numeric(df[c2], errors='coerce')
                    df[f'Diff_{kriterium}_{runde}'] = df[c1] - df[c2]
                    
        # Ergebnisse sammeln
        results = []
        df_valid_year = df[df['Jahr'].notna()].copy()
        
        for runde in RUNDEN:
            niveau, teil = runde.split('_') # Sicheres Entpacken
            for kriterium in KRITERIEN:
                diff_col = f'Diff_{kriterium}_{runde}'
                if diff_col not in df_valid_year.columns:
                    continue
                    
                c1 = f'Mündlich_{kriterium}_{runde}_P1'
                c2 = f'Mündlich_{kriterium}_{runde}_P2'
                
                for jahr, gruppe in df_valid_year.groupby('Jahr'):
                    valid_df = gruppe[[c1, c2, diff_col]].dropna()
                    diffs = valid_df[diff_col]
                    n = len(diffs)
                    
                    mean_P1 = valid_df[c1].mean() if n > 0 else np.nan
                    mean_P2 = valid_df[c2].mean() if n > 0 else np.nan
                    
                    if n >= 2:
                        # 1-Sample T-Test auf die Differenzen testen (entspricht gepaartem T-Test)
                        t_stat, p_value = stats.ttest_1samp(diffs, 0.0, nan_policy='omit')
                        mean_diff = float(np.mean(diffs))
                        std_diff = float(np.std(diffs, ddof=1))
                        
                        cohens_d = mean_diff / std_diff if std_diff != 0 else 0
                        abs_d = abs(cohens_d) if pd.notna(cohens_d) else 0
                        
                        if pd.notna(p_value) and p_value < 0.05:
                            if abs_d < 0.2:
                                interpretation = "Sign. Bias, aber irrelevanter Effekt (|d| < 0,2)."
                                handlung = "Beobachten."
                                status = "⚠️ Beobachten"
                            elif abs_d < 0.8:
                                interpretation = "Sign. Bias, mittlerer Effekt (|d| < 0,8)."
                                handlung = "Kalibrierungssitzung zwingend."
                                status = "🚨 Kritisch"
                            else:
                                interpretation = "Sign. Bias, großer Effekt (|d| ≥ 0,8)."
                                handlung = "Dringende Nachschulung / Re-Zertifizierung."
                                status = "🚨 Kritisch"
                        else:
                            interpretation = "Kein signifikanter Bias (p ≥ 0,05)."
                            handlung = "Kein Handlungsbedarf."
                            status = "✅ OK"
                    else:
                        interpretation = "Zu wenig Daten (n < 2)."
                        handlung = "Daten sammeln."
                        status = "➖ N/A"
                        mean_diff, p_value, cohens_d = np.nan, np.nan, np.nan
                        
                    results.append({
                        'Status': status,
                        'Jahr': int(jahr),
                        'Niveau': niveau,
                        'Teil': f'Teil {teil}',
                        'Kriterium': kriterium.replace('_', ' '),
                        'n': n,
                        'x̄ P1': round(mean_P1, 2) if pd.notna(mean_P1) else np.nan,
                        'x̄ P2': round(mean_P2, 2) if pd.notna(mean_P2) else np.nan,
                        'Ø Diff': round(mean_diff, 2) if pd.notna(mean_diff) else np.nan,
                        'p-Wert': round(p_value, 4) if pd.notna(p_value) else np.nan,
                        'Cohen’s d': round(cohens_d, 2) if pd.notna(cohens_d) else np.nan,
                        'Interpretation': interpretation,
                        'Maßnahme': handlung
                    })
                    
        df_res = pd.DataFrame(results)
        if not df_res.empty:
            df_res = df_res.sort_values(['Status', 'Jahr', 'Niveau', 'Kriterium']).reset_index(drop=True)
            
except Exception as e:
    st.error(f"Fehler bei der Datenverarbeitung: {e}")
    st.stop()

# --- 5. SIDEBAR FILTER LOGIK (Niveau & Jahr) ---
with st.sidebar:
    st.divider()
    st.header("🔍 Filter")
    if not df_res.empty:
        jahre = ['Alle'] + sorted(df_res['Jahr'].unique().tolist())
        niveaus = ['Alle'] + sorted(df_res['Niveau'].unique().tolist())
        
        sel_jahr = st.selectbox("Prüfungsjahr:", jahre)
        sel_niv = st.selectbox("Sprachniveau (GER):", niveaus)
        
        # DataFrame filtern basierend auf der Auswahl
        df_f = df_res.copy()
        if sel_jahr != 'Alle': 
            df_f = df_f[df_f['Jahr'] == sel_jahr]
        if sel_niv != 'Alle': 
            df_f = df_f[df_f['Niveau'] == sel_niv]
    else:
        st.warning("Keine auswertbaren Daten gefunden.")
        st.stop()

# --- 6. DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs(("📈 KPI Dashboard & Grafiken", "📋 Detaillierte Datentabelle", "📄 Hochwertiger PDF-Report"))

with tab1:
    st.subheader(f"Performance & Bias Übersicht (Filter: {sel_niv} | {sel_jahr})")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    total_analyzed = len(df_f)
    critical_bias = len(df_f[df_f['Status'] == '🚨 Kritisch'])
    warn_bias = len(df_f[df_f['Status'] == '⚠️ Beobachten'])
    ok_bias = len(df_f[df_f['Status'] == '✅ OK'])
    
    col1.metric("Analysierte Paare", total_analyzed)
    col2.metric("✅ Unbedenklich", ok_bias)
    col3.metric("⚠️ Beobachten (d < 0.5)", warn_bias)
    col4.metric("🚨 Kritisch (d ≥ 0.5)", critical_bias, delta="-Handlungsbedarf", delta_color="inverse")
    
    st.divider()
    
    # Interaktiver Plotly Chart
    if not df_f.empty and 'Ø Diff' in df_f.columns:
        fig = px.bar(
            df_f, 
            x="Kriterium", 
            y="Ø Diff", 
            color="Status",
            title=f"Durchschnittliche Abweichung (P1 - P2) nach Kriterien",
            hover_data=["Niveau", "p-Wert", "Cohen’s d"],
            color_discrete_map={"✅ OK": "#28a745", "⚠️ Beobachten": "#ffc107", "🚨 Kritisch": "#dc3545", "➖ N/A": "#6c757d"},
            barmode="group"
        )
        fig.update_layout(xaxis_title="Bewertungskriterium", yaxis_title="Mittelwert-Differenz (Rohpunkte)", plot_bgcolor='rgba(240,240,240,0.5)', height=500)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Detaillierte Datentabelle")
    def highlight_status(val):
        val_str = str(val)
        if 'OK' in val_str or '✅' in val_str: return 'background-color: #e6f9ec; color: #006600'
        elif 'Beobachten' in val_str or '⚠️' in val_str: return 'background-color: #fff4cc; color: #996600'
        elif 'Kritisch' in val_str or '🚨' in val_str: return 'background-color: #ffcccc; color: #990000; font-weight: bold'
        return ''
        
    if not df_f.empty:
        try:
            styled_df = df_f.style.map(highlight_status, subset=['Status', 'Maßnahme'])
        except AttributeError:
            styled_df = df_f.style.applymap(highlight_status, subset=['Status', 'Maßnahme'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # --- NEU: LESEHILFE UND TOLERANZBEREICHE GEMÄSS FACHLITERATUR --- [1]
        st.info("""
        **💡 Lesehilfe & Toleranzbereiche:**
        
        **1. p-Wert (Signifikanz):**
        - **p > 0,05:** Die Mittelwertunterschiede sind statistisch nicht bedeutsam. Es liegt kein Nachweis für einen systematischen Strenge-/Milde-Effekt vor. Keine Maßnahmen erforderlich.
        - **p ≤ 0,05:** Es liegt eine systematische Verzerrung (Bias) vor. Ein Bewerter ist signifikant strenger oder milder als der andere.
        
        **2. Cohen's d (Effektstärke / Praktische Relevanz):**
        *Wenn ein signifikanter Unterschied vorliegt, bestimmt dieser Wert den Handlungsbedarf:*
        - **|d| < 0,2 (Toleranzbereich):** Kleiner, vernachlässigbarer Effekt. Der Unterschied ist evtl. messbar, aber praktisch kaum relevant für die Notengebung. Meist keine Maßnahmen erforderlich (Beobachten).
        - **0,2 ≤ |d| < 0,8 (Mittlerer Effekt):** Die Abweichung ist spürbar ("visible effect"). Ein Bewerter urteilt deutlich strenger/milder. Eine Kalibrierungssitzung zur Abstimmung der Kriterien ist zwingend erforderlich.
        - **|d| ≥ 0,8 (Großer Effekt):** Starke, praktisch hochrelevante Diskrepanz im Bewertungsmaßstab. Dringende Überarbeitung der Kriterienanwendung und verpflichtende Nachschulung nötig.
        """)

with tab3:
    st.subheader("Bericht (PDF-Export)")
    st.markdown("Laden Sie den gefilterten Bericht herunter, um die Analyse der Prüferübereinstimmung zu dokumentieren.")
    
    def generate_pdf(df_export, level_filter, year_filter):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = styles['Heading1']
        title_style.textColor = colors.HexColor("#1f497d")
        
        elements.append(Paragraph("Bericht: Analyse der Prüferübereinstimmung (t-Test)", title_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"<b>Filtereinstellungen:</b> Niveau = {level_filter} | Jahr = {year_filter}", styles['Normal']))
        elements.append(Paragraph(f"Anzahl überprüfter Bewertungskonstellationen: {len(df_export)}", styles['Normal']))
        elements.append(Paragraph(f"Kritische Abweichungen (Interventionsbedarf): {len(df_export[df_export['Status'] == '🚨 Kritisch'])}", styles['Normal']))
        elements.append(Spacer(1, 1*cm))
        
        if not df_export.empty:
            pdf_df = df_export.astype(str)
            data = list((pdf_df.columns.tolist(),)) + pdf_df.values.tolist()
            
            t = Table(data, repeatRows=1)
            t.setStyle(TableStyle((
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1f497d")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP')
            )))
            
            for i in range(1, len(data)):
                if i % 2 == 0: t.setStyle(TableStyle((('BACKGROUND', (0, i), (-1, i), colors.white),)))
            elements.append(t)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    if not df_f.empty:
        pdf_buffer = generate_pdf(df_f, sel_niv, sel_jahr)
        st.download_button(
            label="📥 Bericht als PDF herunterladen",
            data=pdf_buffer,
            file_name=f"Prueferuebereinstimmung_{sel_niv}_{sel_jahr}.pdf",
            mime="application/pdf",
            type="primary"
        )


