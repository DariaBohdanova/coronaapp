from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json
import locale
from datetime import datetime


locale.setlocale(locale.LC_ALL, 'de')

def parse_post_data(body):
    params = {}

    # action1=123&action2=443&action3=887
    # ['action1=123', 'action2=443', 'action3=887']
    # [action1, 123] [action2, 443] [action3, 887]
    # {action1: 123, action2: 443, action3: 887}

    for value in body.decode('utf-8').split('&'):
        value = value.split('=')
        if len(value) == 2:
            params[value[0]] = value[1]

    return params


def get_content(data):
    file = open('template.html', 'r')
    content = file.read()

    content = content.replace('{labels}', data['labels'])
    content = content.replace('{datasets}', data['datasets'])

    content = content.replace('{cases_all}', '{0:n}'.format(data['cases_all']))
    content = content.replace('{death_all}', '{0:n}'.format(data['death_all']))

    content = content.replace('{cases_new}', '{0:n}'.format(data['cases_new']))
    content = content.replace('{death_new}', '{0:n}'.format(data['death_new']))

    content = content.replace('{actions1_checked}', data['actions']['actions1'])
    content = content.replace('{actions2_checked}', data['actions']['actions2'])
    content = content.replace('{actions3_checked}', data['actions']['actions3'])
    content = content.replace('{actions4_checked}', data['actions']['actions4'])
    content = content.replace('{actions5_checked}', data['actions']['actions5'])

    content = content.replace('{date_from}', data['date']['from'])
    content = content.replace('{date_to}', data['date']['to'])

    return content.encode('utf-8')

def calculate_data(params={}):
    print(params)
    labels = []
    datasets = []
    data = {'s': [], 'i': [], 'r': [], 'd': []}

    actions1_checked = ''
    actions2_checked = ''
    actions3_checked = ''
    actions4_checked = ''
    actions5_checked = ''
    date_from = ''
    date_to = ''

    N = 83200000  # population
    B = 2.2  # the rate of infection
    G = 0.978  # the rate of recovery
    E = 0.0022  # the rate of mortality

    if 'actions1' in params:
        B = B * float(params['actions1'])
        actions1_checked = 'checked'

    if 'actions2' in params:
        B = B * float(params['actions2'])
        actions2_checked = 'checked'

    if 'actions3' in params:
        B = B * float(params['actions3'])
        actions3_checked = 'checked'

    if 'actions4' in params:
        B = B * float(params['actions4'])
        actions4_checked = 'checked'

    if 'actions5' in params:
        B = B * float(params['actions5'])
        actions5_checked = 'checked'

    if 'date_from' in params:
        date_from = params['date_from']

    if 'date_to' in params:
        date_to = params['date_to']

    # calculate days
    days = 30
    if len(date_from) > 0 and len(date_to) > 0:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        days = (date_to_obj - date_from_obj).days
        if days < 0:
            days = 0

    I0 = 1929410
    R0 = 749219
    D0 = 40936
    S0 = N - I0 - R0 - D0

    # set 0 day
    labels.append(0)
    data['s'].append(round(S0))
    data['i'].append(round(I0))
    data['r'].append(round(R0))
    data['d'].append(round(D0))

    S = S0
    I = I0
    R = R0
    D = D0

    for day in range(1, days + 1):
        labels.append(day)

        # deltas
        dS = -(B * I * S) / N
        dI = ((B * I * S) / N) - (G * I) - (E * I)
        dR = G * I
        dD = E * I

        S += dS
        I += dI
        R += dR
        D += dD

        data['s'].append(round(S))
        data['i'].append(round(I))
        data['r'].append(round(R))
        data['d'].append(round(D))

    cases_all = round(I + D + R)
    death_all = round(D)
    cases_new = round(cases_all - I0)
    death_new = round(death_all - D0)

    # datasets
    # Susceptible
    datasets.append({'label': 'Infizierbar', 'backgroundColor': 'blue', 'borderColor': 'blue', 'fill': False, 'data': data['s']})
    # Infectious
    datasets.append({'label': 'Infiziert', 'backgroundColor': 'orange', 'borderColor': 'orange', 'fill': False, 'data': data['i']})
    # Recovered
    datasets.append({'label': 'Genesen', 'backgroundColor': 'green', 'borderColor': 'green', 'fill': False, 'data': data['r']})
    # Deceased
    datasets.append({'label': 'Verstorben', 'backgroundColor': 'red', 'borderColor': 'red', 'fill': False, 'data': data['d']})

    return {
        'labels': json.dumps(labels),
        'datasets': json.dumps(datasets),
        'cases_all': cases_all,
        'death_all': death_all,
        'cases_new': cases_new,
        'death_new': death_new,
        'actions': {
            'actions1': actions1_checked,
            'actions2': actions2_checked,
            'actions3': actions3_checked,
            'actions4': actions4_checked,
            'actions5': actions5_checked
        },
        'date': {
            'from': date_from,
            'to': date_to
        }
    }


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(get_content(calculate_data()))
        self.wfile.write(response.getvalue())

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        params = parse_post_data(body)
        print(params)
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(get_content(calculate_data(params)))
        self.wfile.write(response.getvalue())


httpd = HTTPServer(('127.0.0.1', 8000), SimpleHTTPRequestHandler)
print('Serving HTTP on 127.0.0.1 port 8000 (http://127.0.0.1:8000/) ...')
httpd.serve_forever()
