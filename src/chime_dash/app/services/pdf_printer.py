import json
import base64
import pickle
from time import sleep

from dash import Dash
from dash.testing.application_runners import ThreadedRunner
from dash.testing.composite import DashComposite
from dash_bootstrap_components.themes import BOOTSTRAP
import dash_bootstrap_components as dbc
from selenium import webdriver


def send_devtools(driver, cmd, params={}):
  resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
  url = driver.command_executor._url + resource
  body = json.dumps({'cmd': cmd, 'params': params})
  response = driver.command_executor._request('POST', url, body)
  if response['status']:
    raise Exception(response.get('value'))
  return response.get('value')


def save_as_pdf(driver, path, options={}):
  # https://timvdlippe.github.io/devtools-protocol/tot/Page#method-printToPDF
  result = send_devtools(driver, "Page.printToPDF", options)
  with open(path, 'wb') as file:
    file.write(base64.b64decode(result['data']))


def print_to_pdf(component, kwargs):
    app = Dash(
        __name__,
        external_stylesheets=[
        "https://www1.pennmedicine.org/styles/shared/penn-medicine-header.css",
        BOOTSTRAP,
    ]
    )

    layout = dbc.Container(
        children=component.html,
        fluid=True,
        className="mt-5",
    )

    app.layout = layout
    app.title = 'CHIME Printer'

    outputs = component.callback(**kwargs)

    @app.callback(component.callback_outputs, [])
    def callback(*args):  # pylint: disable=W0612
        return outputs

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')

    with ThreadedRunner() as starter:
        with DashComposite(starter, browser='Chrome', options=[chrome_options]) as dc:
            dc.start_server(app, port=8051)
            while 'Loading...' in dc.driver.page_source:
                sleep(1)
            save_as_pdf(dc.driver, r'page.pdf', {'landscape': False})
            dc.driver.quit()