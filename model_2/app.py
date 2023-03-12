from datetime import datetime
from logging.config import dictConfig
import os

# import azure.functions as func
from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS
import pandas as pd
from werkzeug.exceptions import HTTPException

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.FileHandler',
            'filename': os.path.join('/var', 'logs', 'model_2.log'),
            'formatter': 'default',
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi'],
    }
})
app = Flask(__name__)
FRONTEND_HOST = os.environ.get("FRONTEND_HOST", "https://emcodist.com")
HEADERS = {"Content-Type": "application/json"}
CORS(app, origins=FRONTEND_HOST)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    message = f"{e.code}: {e.name} - {e.description}"
    return jsonify(error=message), e.code

@app.route('/v1/advanced_search')
def advanced_search():

    from EMCODIST_M2 import RELEVANT_TOPICS, search

    search_term = request.args.get('search_term', None)
    # NB: The search_term is required
    if not search_term:
        abort(400, description="A search_term parameter is required.")

    topics = request.args.getlist('topics[]')
    date_from = request.args.get('date_from', "")
    date_to = request.args.get('date_to', "")

    # checking topics
    if len(topics) == 0:
        topics = ['all', ]
    else:
        # Refuse requests to search non relevant topics
        for topic in topics:
            if topic not in RELEVANT_TOPICS:
                app.logger.warn(f"Topic {topic} not relevant for searching.")
                abort(400, description=f"Topic {topic} not relevant for searching.")

    #checking the from date
    if date_from:
        date_from = pd.to_datetime(date_from, infer_datetime_format=True).date()
    else:
        min_date = 'Fri, 1 Dec 2000 00:00:00 -0800' # default date
        date_from = pd.to_datetime(min_date, infer_datetime_format=True).date()

    #checking the to_date
    if date_to:
        date_to = pd.to_datetime(date_to, infer_datetime_format=True).date()
    else:
        max_date = 'Sat, 9 Oct 2004 14:20:21 -0700' # default date
        date_to = pd.to_datetime(max_date, infer_datetime_format=True).date()

    if date_from > date_to:
        abort(400, description="Problem with date range.  Start occurs after the end.")

    app.logger.info(f"START Model 2 search: {datetime.now()} search_term: {search_term}, topics: {topics}, date_from: {date_from}, date_to: {date_to}")
    response = make_response(search(search_term, topics, date_from, date_to), HEADERS)
    app.logger.info(f"END Model 2 search: {datetime.now()} search_term: {search_term}, topics: {topics}, date_from: {date_from}, date_to: {date_to}")
    return response


if __name__ == '__main__':
    app.run(host="0.0.0.0")

'''
#To run set these variables on windows
$ export FLASK_APP=app.py # your python file name
$ set FLASK_APP = app.py
$ export FLASK_ENV=development
$ set FLASK_DEBUG = True
$ flask run
'''
