import re
import pandas as pd
import streamlit as st
import altair as alt


def clean_total_column(totals):
    """Remove commas from total values and convert them to floats."""
    cleaned_totals = []
    for total in totals:
        cleaned_total = float(total.replace(',', ''))
        cleaned_totals.append(cleaned_total)
    return cleaned_totals


def extract_total(item_desc_column, keyword):
    """Extract and sum the quantities of a specified keyword from the 'Items Description' column."""
    total = 0
    quantities = []
    pattern = re.compile(r'(\d+)x' + keyword)

    for item in item_desc_column:
        matches = pattern.findall(item)
        if matches:
            quantity = sum(int(match) for match in matches)
            total += quantity
            quantities.append(quantity)
        else:
            quantities.append(0)

    return total, quantities


# Streamlit app

st.set_page_config(layout="wide")

# Add the logo in the sidebar
st.markdown(
    '<a href="https://www.pontisella-stampa.ch"><img src="https://www.pontisella-stampa.ch/wp-content/uploads/2022/'
    '05/cropped-Pontisella_Logo_RGB_pos_1000px.png" alt="Pontisella Logo" style="width: 5%;"/></a>',
    unsafe_allow_html=True
)
st.header("Analyse der Übernachtungen (Kyte Export)")
st.info("Befolge die Anleitung in der Sidebar um Übernachtungsdaten aus Kyte auszuwerten.")

# Sidebar instructions
st.sidebar.header("Anleitung")
st.sidebar.subheader("Schritt 1: Datenexport aus Kyte")

st.sidebar.markdown("""
1. Öffne die Kyte App und navigiere zu 'Bestellungen' (Orders).
2. Klicke oben rechts auf das Symbol zum Exportieren von Berichten (Export Reports).
3. Wähle den gewünschten Zeitraum aus und exportiere den Bericht für 'Verkäufe' (Sales) als CSV-Datei.
4. Die exportierte CSV-Datei wird dir per E-Mail zugeschickt.
""")

st.sidebar.subheader("Schritt 2: Datenupload")
st.sidebar.markdown("""
Lade die zuvor exportierte CSV-Datei hoch, um die Übernachtungsdaten und die berechneten Kurtaxen zu analysieren. 
Stelle sicher, dass die Datei folgende Spalten enthält:

- **Date/Time**: Datum und Uhrzeit der Übernachtung
- **Total**: Gesamtbetrag der Übernachtung
- **Items Description**: Beschreibung der Positionen (einschließlich Kurtaxe und Übernachtungen).
""")

uploaded_file = st.sidebar.file_uploader("Lade Deine CSV-Datei hoch", type=["csv"])

if uploaded_file is not None:
    st.sidebar.success("Datei erfolgreich hochgeladen!")
    data = pd.read_csv(uploaded_file)

    st.sidebar.subheader("Schritt 3: Datenanalyse")
    st.sidebar.markdown("""
    Klicke auf den Button **Daten analysieren**, um die Berechnungen basierend auf den hochgeladenen Daten zu starten.
    """)

    if st.sidebar.button("Daten analysieren"):
        # Clean totals
        data["Totals Cleaned"] = clean_total_column(data["Total"])

        # Ensure the Date/Time column is in datetime format
        data['Date/Time'] = pd.to_datetime(data['Date/Time'], format='%m/%d/%Y %I:%M %p')

        # Constants
        KURTAXE_COST_PER_PERSON = 3.2

        # Extract date range
        start_date = data['Date/Time'].min().strftime('%d.%m.%Y')
        end_date = data['Date/Time'].max().strftime('%d.%m.%Y')

        # Calculate totals
        total_kurtaxe, kurtaxe_quantities = extract_total(data['Items Description'], 'Kurtaxe')
        total_uebernachtungen, uebernachtungen_quantities = extract_total(data['Items Description'], 'Übernachtung')

        # Extracting other categories similarly...
        room_types = ['Rosmarin', 'Lavendel', 'Salbei', 'Thymian', 'Dachzimmer', 'Steinsuite', 'Holzsuite']
        room_totals = {}

        for room in room_types:
            total, _ = extract_total(data['Items Description'], f'Übernachtung {room}')
            room_totals[room] = total

        total_uebernachtungen_gutschein, _ = extract_total(data['Items Description'], 'Gutschein')
        total_hundepauschale, _ = extract_total(data['Items Description'], 'Hundepauschale')

        # Calculate costs
        data['Kurtaxe Cost'] = [qty * KURTAXE_COST_PER_PERSON for qty in kurtaxe_quantities]
        data['Übernachtung Cost'] = data['Totals Cleaned'] - data['Kurtaxe Cost']

        # Total costs
        total_kurtaxe_cost = data['Kurtaxe Cost'].sum()
        total_uebernachtungen_cost = data['Übernachtung Cost'].sum()

        # Display metrics using tabs for organization
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Übersicht Kennzahlen", "Aufschlüsselung nach Zimmern",
                                                "Monatliche Übernachtungen", "Zusätzliche Leistungen", "Rohdaten"])

        with tab1:
            st.metric("Analysezeitraum", f"{start_date} - {end_date}")
            st.subheader("Übersicht")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Gesamtanzahl Übernachtungen", total_uebernachtungen)

            with col2:
                st.metric("Gesamtanzahl Gäste (Kurtaxe)", total_kurtaxe)

            with col1:
                st.metric("Gesamtkosten für Übernachtungen", f"{total_uebernachtungen_cost:.2f} CHF")
                st.metric("Gesamtkostenanteil Kurtaxe", f"{total_kurtaxe_cost:.2f} CHF")
            with col2:
                st.metric("Gesamtkosten für Übernachtungen und Kurtaxe",
                          f"{total_uebernachtungen_cost + total_kurtaxe_cost:.2f} CHF")

        with tab2:
            col3, col4 = st.columns(2)

            with col3:
                st.metric("Analysezeitraum", f"{start_date} - {end_date}")
            with col4:
                st.metric("Gesamtanzahl Übernachtungen", total_uebernachtungen)

            st.subheader("Aufschlüsselung nach Zimmern")

            # Create columns for room totals and visualization
            col1, col2 = st.columns(2)

            # Using col1 for metrics display
            with col1:
                for room, total in room_totals.items():
                    st.metric(label=f"Anzahl Übernachtungen {room}", value=total)

            # Using col2 for pie chart display
            with col2:
                # Create DataFrame for visualizations with only room totals
                visualization_data = pd.DataFrame({
                    'Zimmertyp': list(room_totals.keys()),
                    'Anzahl Übernachtungen': list(room_totals.values())
                })

                # Calculate the percentage for each room category
                visualization_data['Percentage'] = (visualization_data['Anzahl Übernachtungen'] / visualization_data[
                    'Anzahl Übernachtungen'].sum()) * 100

                # Interactive pie chart using Altair for room categories with percentage labels
                pie_chart = (
                    alt.Chart(visualization_data)
                    .mark_arc(innerRadius=50)
                    .encode(
                        theta=alt.Theta(field='Anzahl Übernachtungen', type='quantitative'),
                        color=alt.Color(field='Zimmertyp', type='nominal', legend=alt.Legend(title="Zimmer")),
                        tooltip=['Zimmertyp', 'Anzahl Übernachtungen', alt.Tooltip('Percentage:Q', format='.2f')]
                    )
                    .properties(title="Verteilung der Übernachtungen nach Zimmertyp")
                )

                # Add text labels with percentages and adjust placement
                text = pie_chart.mark_text(radiusOffset=10, size=40).encode(
                    text=alt.Text('Percentage:Q', format='.1f'),
                    color=alt.value('white')  # Set to black for contrast (or white if the slices are dark)
                )

                # Display the pie chart with text labels
                st.altair_chart(pie_chart + text, use_container_width=True)

        with tab3:
            # Visualization for Übernachtungen per month
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Analysezeitraum", f"{start_date} - {end_date}")
            with col2:
                st.metric("Gesamtanzahl Übernachtungen", total_uebernachtungen)

            st.subheader("Monatliche Übernachtungen")

            # Extract month and year
            data['Monat'] = data['Date/Time'].dt.to_period('M')  # Extract month and year
            monthly_data = data.groupby('Monat')['Items Description'].apply(
                lambda x: extract_total(x, 'Übernachtung')[0]).reset_index()
            monthly_data.columns = ['Monat', 'Anzahl Übernachtungen']

            # Convert the 'Monat' from period to string for better labeling in the bar chart
            monthly_data['Monat'] = monthly_data['Monat'].dt.strftime('%Y-%m')

            # Interactive bar chart using Streamlit
            st.bar_chart(monthly_data.set_index('Monat'))

        with tab4:
            # Additional information
            st.metric("Analysezeitraum", f"{start_date} - {end_date}")
            st.subheader("Zusätzliche Leistungen")

            st.metric("Anzahl verkaufter Gutscheine", f"{total_uebernachtungen_gutschein}")
            st.metric("Anzahl Hunde (Hundepauschale)", f"{total_hundepauschale}")
            st.write("----------------------------")

        with tab5:
            st.metric("Analysezeitraum", f"{start_date} - {end_date}")
            st.subheader("Rohdaten")
            st.dataframe(data)

else:
    st.sidebar.warning("Bitte lade eine CSV-Datei hoch.")

# Add a copyright footer at the bottom of the app
st.markdown("""
    <hr>
    <div style='text-align: center;'>
        <p> Web App Design & Konzeption: © DF 2024. Alle Rechte vorbehalten.</p>
    </div>
    """, unsafe_allow_html=True)
