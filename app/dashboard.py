import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(
    page_title="Riksdagen Dashboard",
    page_icon="🏛️",
    layout="wide"
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/riksdagen")


@st.cache_resource
def get_connection():
    return psycopg2.connect(DATABASE_URL)


@st.cache_data(ttl=300)
def query(sql):
    conn = get_connection()
    return pd.read_sql(sql, conn)


st.title("🏛️ Riksdagen Live Dashboard")

col_header, col_btn = st.columns([4, 1])
with col_header:
    st.caption("Data hämtas automatiskt var 30:e minut från Riksdagens öppna API")
    st.info(f" Dashboard senast laddad: **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")
with col_btn:
    st.write("")
    st.write("")
    if st.button("Uppdatera nu", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

senaste_votering = query("SELECT MAX(datum) as max FROM voteringar").iloc[0]["max"]
st.success(f" Senaste votering i databasen: **{senaste_votering}** — live från Riksdagens API")

st.divider()


col1, col2, col3, col4, col5 = st.columns(5)
ledamoter_count  = query("SELECT COUNT(*) as n FROM ledamoter").iloc[0]["n"]
voteringar_count = query("SELECT COUNT(*) as n FROM voteringar").iloc[0]["n"]
dokument_count   = query("SELECT COUNT(*) as n FROM dokument").iloc[0]["n"]
kalender_count   = query("SELECT COUNT(*) as n FROM kalender").iloc[0]["n"]
anforanden_count = query("SELECT COUNT(*) as n FROM anforanden").iloc[0]["n"]

col1.metric(" Ledamöter",  ledamoter_count)
col2.metric(" Voteringar", voteringar_count)
col3.metric(" Dokument",   dokument_count)
col4.metric(" Kalender",   kalender_count)
col5.metric(" Anföranden", anforanden_count)

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    st.subheader(" Ledamöter per parti")
    df_parti = query("""
        SELECT parti, COUNT(*) as antal
        FROM ledamoter
        WHERE parti IS NOT NULL AND parti != ''
        GROUP BY parti ORDER BY antal DESC
    """)
    fig = px.bar(df_parti, x="parti", y="antal", color="antal",
                 color_continuous_scale="Blues",
                 labels={"parti": "Parti", "antal": "Antal ledamöter"})
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader(" Partifördelning")
    fig2 = px.pie(df_parti, values="antal", names="parti", hole=0.4,
                  color_discrete_sequence=px.colors.qualitative.Set3)
    fig2.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader(" Röstfördelning per parti (Ja / Nej / Frånvarande)")
df_rost = query("""
    SELECT parti,
           SUM(CASE WHEN rost = 'Ja' THEN 1 ELSE 0 END) as ja,
           SUM(CASE WHEN rost = 'Nej' THEN 1 ELSE 0 END) as nej,
           SUM(CASE WHEN rost = 'Frånvarande' THEN 1 ELSE 0 END) as franvarande
    FROM voteringar
    WHERE parti IS NOT NULL AND parti != ''
    GROUP BY parti ORDER BY ja DESC
""")
fig_rost = px.bar(
    df_rost, x="parti", y=["ja", "nej", "franvarande"],
    barmode="group",
    labels={"value": "Antal röster", "variable": "Röst", "parti": "Parti"},
    color_discrete_map={"ja": "#2ecc71", "nej": "#e74c3c", "franvarande": "#95a5a6"}
)
fig_rost.update_layout(legend_title_text="Röst")
st.plotly_chart(fig_rost, use_container_width=True)

st.divider()

st.subheader(" Jämför hur partier röstade på samma motion ")

df_motioner = query("""
    SELECT DISTINCT titel, punkt, riksmote
    FROM voteringar
    WHERE titel IS NOT NULL
    ORDER BY riksmote DESC, titel
    LIMIT 100
""")

motioner = df_motioner.apply(
    lambda r: f"{r['riksmote']} | {r['titel']} punkt {r['punkt']}", axis=1
).tolist()

vald_motion = st.selectbox("Välj motion:", motioner)

if vald_motion:
    delar = vald_motion.split(" | ")
    riksmote = delar[0]
    titel_punkt = delar[1]
    titel = titel_punkt.split(" punkt ")[0]
    punkt = titel_punkt.split(" punkt ")[1]

    df_motion_roster = query(f"""
        SELECT parti,
               SUM(CASE WHEN rost = 'Ja' THEN 1 ELSE 0 END) as ja,
               SUM(CASE WHEN rost = 'Nej' THEN 1 ELSE 0 END) as nej,
               SUM(CASE WHEN rost = 'Frånvarande' THEN 1 ELSE 0 END) as franvarande,
               COUNT(*) as totalt
        FROM voteringar
        WHERE titel = '{titel}' AND punkt = '{punkt}' AND riksmote = '{riksmote}'
        GROUP BY parti ORDER BY ja DESC
    """)

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        fig_m = px.bar(
            df_motion_roster, x="parti", y=["ja", "nej", "franvarande"],
            barmode="stack",
            labels={"value": "Antal", "variable": "Röst", "parti": "Parti"},
            color_discrete_map={"ja": "#2ecc71", "nej": "#e74c3c", "franvarande": "#95a5a6"}
        )
        st.plotly_chart(fig_m, use_container_width=True)
    with col_m2:
        st.dataframe(df_motion_roster, use_container_width=True, hide_index=True,
                     column_config={"parti": "Parti", "ja": "Ja", "nej": "Nej",
                                    "franvarande": "Frånvarande", "totalt": "Totalt"})

st.divider()

st.subheader(" Sök politiker — rösthistorik & anföranden ")

df_ledamoter = query("""
    SELECT id, namn, parti, valkrets FROM ledamoter
    WHERE namn IS NOT NULL ORDER BY namn
""")

namn_lista = df_ledamoter["namn"].tolist()
vald_namn = st.selectbox("Välj politiker:", ["-- Välj --"] + namn_lista)

if vald_namn and vald_namn != "-- Välj --":
    vald_rad = df_ledamoter[df_ledamoter["namn"] == vald_namn].iloc[0]
    intressent_id = vald_rad["id"]
    parti = vald_rad["parti"]
    valkrets = vald_rad["valkrets"]

    st.markdown(f"**{vald_namn}** — {parti} | {valkrets}")

    pk1, pk2, pk3 = st.columns(3)

    antal_roster = query(f"""
        SELECT COUNT(*) as n FROM voteringar
        WHERE intressent_id = '{intressent_id}'
    """).iloc[0]["n"]

    antal_tal = query(f"""
        SELECT COUNT(*) as n FROM anforanden
        WHERE intressent_id = '{intressent_id}'
    """).iloc[0]["n"]

    ja_pct = query(f"""
        SELECT ROUND(100.0 * SUM(CASE WHEN rost='Ja' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) as pct
        FROM voteringar WHERE intressent_id = '{intressent_id}'
    """).iloc[0]["pct"]

    pk1.metric(" Antal röster", antal_roster)
    pk2.metric(" Antal anföranden", antal_tal)
    pk3.metric(" Röstat Ja", f"{ja_pct}%")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown("**Rösthistorik**")
        df_politiker_rost = query(f"""
            SELECT rost, COUNT(*) as antal
            FROM voteringar
            WHERE intressent_id = '{intressent_id}'
            GROUP BY rost
        """)
        if not df_politiker_rost.empty:
            fig_pr = px.pie(df_politiker_rost, values="antal", names="rost",
                            hole=0.4,
                            color_discrete_map={"Ja": "#2ecc71", "Nej": "#e74c3c",
                                                "Frånvarande": "#95a5a6"})
            st.plotly_chart(fig_pr, use_container_width=True)
        else:
            st.info("Inga röster hittade")

    with col_p2:
        st.markdown("**Senaste anföranden**")
        df_politiker_tal = query(f"""
            SELECT talare, parti, LEFT(text, 200) as text
            FROM anforanden
            WHERE intressent_id = '{intressent_id}'
            LIMIT 5
        """)
        if not df_politiker_tal.empty:
            st.dataframe(df_politiker_tal, use_container_width=True, hide_index=True,
                         column_config={"talare": "Talare", "parti": "Parti", "text": "Text"})
        else:
            st.info("Inga anföranden hittade")

st.divider()

col_c, col_d = st.columns(2)
with col_c:
    st.subheader(" Mest aktiva talare")
    df_talare = query("""
        SELECT talare, parti, COUNT(*) as antal_tal
        FROM anforanden WHERE talare IS NOT NULL
        GROUP BY talare, parti
        ORDER BY antal_tal DESC LIMIT 15
    """)
    fig3 = px.bar(df_talare, x="antal_tal", y="talare", orientation="h",
                  color="parti",
                  labels={"antal_tal": "Antal anföranden", "talare": ""},
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig3.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.subheader(" Voteringar per parti")
    df_voteringar = query("""
        SELECT parti, COUNT(*) as antal
        FROM voteringar WHERE parti IS NOT NULL AND parti != ''
        GROUP BY parti ORDER BY antal DESC
    """)
    fig4 = px.bar(df_voteringar, x="parti", y="antal", color="antal",
                  color_continuous_scale="Reds",
                  labels={"parti": "Parti", "antal": "Antal röster"})
    fig4.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

col_e, col_f = st.columns(2)
with col_e:
    st.subheader(" Anföranden per parti")
    df_anf_parti = query("""
        SELECT parti, COUNT(*) as antal
        FROM anforanden WHERE parti IS NOT NULL AND parti != ''
        GROUP BY parti ORDER BY antal DESC
    """)
    fig5 = px.bar(df_anf_parti, x="parti", y="antal", color="antal",
                  color_continuous_scale="Greens",
                  labels={"parti": "Parti", "antal": "Antal anföranden"})
    fig5.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

with col_f:
    st.subheader("Senaste kalenderhändelser")
    df_kalender = query("""
    SELECT titel, start, plats, kategori
    FROM kalender 
    WHERE start IS NOT NULL
    ORDER BY ABS(EXTRACT(EPOCH FROM (start::timestamp - NOW())))
    LIMIT 10
""")
    st.dataframe(df_kalender, use_container_width=True, hide_index=True,
                 column_config={"titel": "Titel", "start": "Datum",
                                "plats": "Plats", "kategori": "Kategori"})

st.divider()

st.subheader(" Voteringar över tid")
df_time = query("""
    SELECT DATE(datum) as dag,
           SUM(CASE WHEN rost = 'Ja' THEN 1 ELSE 0 END) as ja,
           SUM(CASE WHEN rost = 'Nej' THEN 1 ELSE 0 END) as nej,
           SUM(CASE WHEN rost = 'Frånvarande' THEN 1 ELSE 0 END) as franvarande
    FROM voteringar WHERE datum IS NOT NULL
    GROUP BY dag ORDER BY dag
""")
fig_time = px.line(df_time, x="dag", y=["ja", "nej", "franvarande"],
                   labels={"value": "Antal röster", "variable": "Röst", "dag": "Datum"},
                   markers=True,
                   color_discrete_map={"ja": "#2ecc71", "nej": "#e74c3c", "franvarande": "#95a5a6"})
st.plotly_chart(fig_time, use_container_width=True)

st.divider()

st.subheader(" Senaste dokument")
df_dok = query("""
    SELECT titel, typ, datum, organ, dok_url
    FROM dokument WHERE datum IS NOT NULL
    ORDER BY datum DESC LIMIT 10
""")
st.dataframe(df_dok, use_container_width=True, hide_index=True,
             column_config={"titel": "Titel", "typ": "Typ", "datum": "Datum",
                            "organ": "Organ",
                            "dok_url": st.column_config.LinkColumn("Länk")})

st.divider()

st.subheader(" Pipeline Status")
s1, s2, s3 = st.columns(3)
s1.success("Kafka producers: ")
s2.success("Consumer → PostgreSQL: ")
s3.success("Dashboard: ")

db_size = query("SELECT pg_size_pretty(pg_database_size('riksdagen')) as size").iloc[0]["size"]
st.info(f" Databasstorlek: **{db_size}**")

st.caption(" Producers hämtar ny data var 30:e minut | Pipeline: Kafka → PostgreSQL → Dashboard")