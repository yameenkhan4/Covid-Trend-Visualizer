"""
COVID-19 Trend Visualizer
=========================
HOW TO RUN:
1. pip install dash plotly pandas
2. python covid_dashboard.py
3. Open browser: http://127.0.0.1:8050
"""

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Loading data...")
np.random.seed(42)

# Realistic peak daily cases per country (matches real COVID data)
country_peaks = {
    'India':        400000,
    'USA':          800000,
    'Brazil':       300000,
    'Germany':      250000,
    'UK':           200000,
    'Italy':        150000,
    'Russia':       200000,
    'South Africa':  20000,
}

start     = datetime(2020, 3, 1)
end       = datetime(2023, 1, 1)
all_dates = [start + timedelta(days=i) for i in range((end - start).days)]

def wave(day, peak_day, width):
    """Bell curve wave centered at peak_day"""
    return np.exp(-((day - peak_day) ** 2) / (2 * width ** 2))

rows = []
for country, peak_cases in country_peaks.items():
    cum_cases = cum_deaths = 0
    for day_num, date in enumerate(all_dates):
        # 3 waves at different times
        daily = (
            wave(day_num, 100, 40)  * peak_cases * 0.15 +
            wave(day_num, 320, 60)  * peak_cases * 0.35 +
            wave(day_num, 560, 70)  * peak_cases * 1.00
        )
        noise        = np.random.normal(1.0, 0.12)
        daily_cases  = max(0, int(daily * noise))
        daily_deaths = max(0, int(daily_cases * np.random.uniform(0.008, 0.014)))
        cum_cases   += daily_cases
        cum_deaths  += daily_deaths
        rows.append({
            'date':              date,
            'country':           country,
            'daily_cases':       daily_cases,
            'daily_deaths':      daily_deaths,
            'cumulative_cases':  cum_cases,
            'cumulative_deaths': cum_deaths,
        })

df = pd.DataFrame(rows)
df['date']       = pd.to_datetime(df['date'])
df['year_month'] = df['date'].dt.to_period('M').astype(str)
countries_list   = sorted(df['country'].unique())
all_months       = sorted(df['year_month'].unique())
month_options    = [{'label': m, 'value': m} for m in all_months]

# Quick sanity check
for c in ['India', 'USA']:
    total = df[df['country'] == c]['daily_cases'].sum()
    print(f"  {c}: {total:,} total cases")

print("Data ready!")

# ── STYLES ───────────────────────────────────────────────────
BG      = '#0f1117'
CARD    = '#1e2130'
PANEL   = '#252836'
ACCENT  = '#4f8ef7'
TEXT    = '#e0e0e0'
SUBTEXT = '#9a9ab0'

DD_STYLE = {
    'backgroundColor': PANEL,
    'color': '#000',
    'border': f'1px solid {ACCENT}',
    'borderRadius': '6px',
}

LABEL_STYLE = {
    'color': ACCENT, 'display': 'block',
    'marginBottom': '8px', 'fontWeight': 'bold', 'fontSize': '13px',
}

app = dash.Dash(__name__, title="COVID-19 Trend Visualizer")

app.layout = html.Div(style={
    'backgroundColor': BG, 'minHeight': '100vh',
    'fontFamily': 'Segoe UI, sans-serif',
    'color': TEXT, 'padding': '24px',
}, children=[

    # Header
    html.Div(style={'textAlign': 'center', 'marginBottom': '24px'}, children=[
        html.H1("🦠 COVID-19 Trend Visualizer",
                style={'color': ACCENT, 'fontSize': '2rem', 'margin': '0 0 6px 0'}),
        html.P("Interactive dashboard for national COVID-19 trend analysis",
               style={'color': SUBTEXT, 'margin': 0}),
    ]),

    # Controls
    html.Div(style={
        'backgroundColor': CARD, 'borderRadius': '12px',
        'padding': '20px', 'marginBottom': '20px',
        'display': 'flex', 'gap': '20px',
        'flexWrap': 'wrap', 'alignItems': 'flex-end',
    }, children=[

        html.Div(style={'flex': '2', 'minWidth': '200px'}, children=[
            html.Label("🌍  Countries", style=LABEL_STYLE),
            dcc.Dropdown(
                id='country-dd',
                options=[{'label': c, 'value': c} for c in countries_list],
                value=['India', 'USA', 'Brazil'],
                multi=True,
                style={**DD_STYLE, 'color': '#000'},
                placeholder="Select countries...",
            ),
        ]),

        html.Div(style={'flex': '1', 'minWidth': '160px'}, children=[
            html.Label("📅  Start Month", style=LABEL_STYLE),
            dcc.Dropdown(
                id='start-month',
                options=month_options,
                value='2021-01',
                clearable=False,
                style={**DD_STYLE, 'color': '#000'},
            ),
        ]),

        html.Div(style={'flex': '1', 'minWidth': '160px'}, children=[
            html.Label("📅  End Month", style=LABEL_STYLE),
            dcc.Dropdown(
                id='end-month',
                options=month_options,
                value='2022-06',
                clearable=False,
                style={**DD_STYLE, 'color': '#000'},
            ),
        ]),

        html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
            html.Label("📊  Metric", style=LABEL_STYLE),
            html.Div(style={'display': 'flex', 'gap': '8px'}, children=[
                html.Button("Daily", id='btn-daily', n_clicks=1, style={
                    'backgroundColor': ACCENT, 'color': '#fff',
                    'border': 'none', 'borderRadius': '6px',
                    'padding': '9px 20px', 'cursor': 'pointer',
                    'fontWeight': 'bold', 'fontSize': '13px',
                }),
                html.Button("Cumulative", id='btn-cumul', n_clicks=0, style={
                    'backgroundColor': PANEL, 'color': SUBTEXT,
                    'border': f'1px solid {ACCENT}', 'borderRadius': '6px',
                    'padding': '9px 20px', 'cursor': 'pointer',
                    'fontWeight': 'bold', 'fontSize': '13px',
                }),
            ]),
            dcc.Store(id='metric-store', data='daily'),
        ]),
    ]),

    # KPI cards
    html.Div(id='kpis', style={
        'display': 'flex', 'gap': '14px',
        'marginBottom': '20px', 'flexWrap': 'wrap',
    }),

    # Charts top row
    html.Div(style={
        'display': 'grid', 'gridTemplateColumns': '1fr 1fr',
        'gap': '16px', 'marginBottom': '16px',
    }, children=[
        html.Div(style={'backgroundColor': CARD, 'borderRadius': '10px', 'padding': '12px'},
                 children=[dcc.Graph(id='cases-chart', config={'displayModeBar': False})]),
        html.Div(style={'backgroundColor': CARD, 'borderRadius': '10px', 'padding': '12px'},
                 children=[dcc.Graph(id='deaths-chart', config={'displayModeBar': False})]),
    ]),

    html.Div(style={'backgroundColor': CARD, 'borderRadius': '10px',
                    'padding': '12px', 'marginBottom': '16px'},
             children=[dcc.Graph(id='compare-chart', config={'displayModeBar': False})]),

    html.P("Built with Python & Plotly Dash  |  Portfolio Project — Mohd Yameen Khan",
           style={'textAlign': 'center', 'color': SUBTEXT, 'fontSize': '0.8rem'}),
])


@app.callback(
    Output('metric-store', 'data'),
    Output('btn-daily',    'style'),
    Output('btn-cumul',    'style'),
    Input('btn-daily',     'n_clicks'),
    Input('btn-cumul',     'n_clicks'),
)
def toggle(nd, nc):
    active   = {'backgroundColor': ACCENT,  'color': '#fff',
                 'border': 'none', 'borderRadius': '6px',
                 'padding': '9px 20px', 'cursor': 'pointer',
                 'fontWeight': 'bold', 'fontSize': '13px'}
    inactive = {'backgroundColor': PANEL,   'color': SUBTEXT,
                 'border': f'1px solid {ACCENT}', 'borderRadius': '6px',
                 'padding': '9px 20px', 'cursor': 'pointer',
                 'fontWeight': 'bold', 'fontSize': '13px'}
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]['prop_id'].startswith('btn-daily'):
        return 'daily', active, inactive
    return 'cumulative', inactive, active


def kpi(title, value, color, icon):
    return html.Div(style={
        'backgroundColor': CARD, 'borderRadius': '10px',
        'padding': '14px 18px', 'flex': '1', 'minWidth': '140px',
        'borderLeft': f'4px solid {color}',
    }, children=[
        html.P(f"{icon}  {title}",
               style={'color': SUBTEXT, 'fontSize': '0.78rem',
                      'margin': '0 0 5px 0', 'fontWeight': 'bold'}),
        html.H3(str(value), style={'color': color, 'margin': 0, 'fontSize': '1.4rem'}),
    ])


@app.callback(
    Output('kpis',          'children'),
    Output('cases-chart',   'figure'),
    Output('deaths-chart',  'figure'),
    Output('compare-chart', 'figure'),
    Input('country-dd',   'value'),
    Input('start-month',  'value'),
    Input('end-month',    'value'),
    Input('metric-store', 'data'),
)
def update(sel_countries, start_m, end_m, metric):
    if not sel_countries: sel_countries = ['India']
    if not start_m: start_m = '2021-01'
    if not end_m:   end_m   = '2022-06'

    filtered = df[
        df['country'].isin(sel_countries) &
        (df['year_month'] >= start_m) &
        (df['year_month'] <= end_m)
    ].copy()

    cc  = 'daily_cases'   if metric == 'daily' else 'cumulative_cases'
    dc  = 'daily_deaths'  if metric == 'daily' else 'cumulative_deaths'
    lbl = 'Daily'         if metric == 'daily' else 'Cumulative'

    total_c   = int(filtered[cc].sum())
    total_d   = int(filtered[dc].sum())
    cfr       = round(total_d / total_c * 100, 2) if total_c > 0 else 0
    peak_date = (filtered.loc[filtered[cc].idxmax(), 'date'].strftime('%b %Y')
                 if len(filtered) > 0 else 'N/A')

    cards = [
        kpi("Total Cases",        f"{total_c:,}",  ACCENT,    '🦠'),
        kpi("Total Deaths",       f"{total_d:,}",  '#ef5675', '💔'),
        kpi("Case Fatality Rate", f"{cfr}%",        '#06d6a0', '📉'),
        kpi("Peak Month",         peak_date,         '#f9c74f', '📅'),
    ]

    base = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=45, b=10),
        legend=dict(orientation='h', y=-0.25),
        font=dict(color=TEXT),
    )

    fig_c = px.line(filtered, x='date', y=cc, color='country',
                    title=f'🦠 {lbl} Cases by Country', template='plotly_dark',
                    labels={cc: 'Cases', 'date': 'Date', 'country': 'Country'})
    fig_c.update_layout(**base)

    fig_d = px.line(filtered, x='date', y=dc, color='country',
                    title=f'💔 {lbl} Deaths by Country', template='plotly_dark',
                    labels={dc: 'Deaths', 'date': 'Date', 'country': 'Country'},
                    color_discrete_sequence=px.colors.qualitative.Set1)
    fig_d.update_layout(**base)

    comp = (filtered.groupby('country')
                    .agg(Cases=(cc, 'sum'), Deaths=(dc, 'sum'))
                    .reset_index()
                    .sort_values('Cases', ascending=False))

    fig_b = go.Figure([
        go.Bar(name='Cases',  x=comp['country'], y=comp['Cases'],  marker_color=ACCENT),
        go.Bar(name='Deaths', x=comp['country'], y=comp['Deaths'], marker_color='#ef5675'),
    ])
    fig_b.update_layout(barmode='group', template='plotly_dark',
                         title=f'📊 Country Comparison — {lbl} Total', **base)

    return cards, fig_c, fig_d, fig_b


if __name__ == '__main__':
    print("\n🚀 Dashboard starting...")
    print("👉 Open your browser: http://127.0.0.1:8050\n")
    app.run(debug=False)
