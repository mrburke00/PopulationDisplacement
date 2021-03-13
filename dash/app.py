import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from apps import index
from apps import local_dash


app = dash.Dash()
app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])



# Index Page callback
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-1':
        return local_dash.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)
