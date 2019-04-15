import logging

from flask import Flask, redirect, url_for
from flask import render_template
from flask import request
from flask.json import jsonify
from gevent.pywsgi import WSGIServer

from interec.interec_processor import InterecProcessor

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')
interec = InterecProcessor('akka')
interec.set_weight_combination_for_factors(alpha=0.1, beta=0.2, gamma=0.7, date_window=0)
navbar_info = {'repository': interec.database,
               'pr_count': interec.pr_count,
               'integrator_count': interec.integrator_count}


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', navbar_info=navbar_info)


@app.route('/load_set_weights')
def load_set_weights():
    return render_template('load_set_weights.html', navbar_info=navbar_info)


@app.route('/set_weights', methods=['POST'])
def set_weights():
    alpha = request.form['alpha']
    beta = request.form['beta']
    gamma = request.form['gamma']
    interec.set_weight_combination_for_factors(alpha=float(alpha), beta=float(beta), gamma=float(gamma), date_window=0)
    return render_template('index.html', navbar_info=navbar_info)


@app.route('/load_get_weight_accuracy')
def load_get_weight_accuracy():
    return render_template('load_get_weight_accuracy.html', navbar_info=navbar_info)


@app.route('/get_weight_accuracy', methods=['POST'])
def get_weight_accuracy():
    offset = request.form['offset1']
    limit = request.form['limit1']
    result_object = interec.calculate_scores_and_get_weight_combinations_for_factors(offset=int(offset),
                                                                                     limit=int(limit))
    return render_template('get_weight_accuracy.html', navbar_info=navbar_info, results=result_object)


@app.route('/get_weight_accuracy_by_file', methods=['POST'])
def get_weight_accuracy_by_file():
    offset = request.form['offset2']
    limit = request.form['limit2']
    file_name = request.form['file_name']
    result_object = interec.get_weight_combinations_for_factors(offset=int(offset), limit=int(limit),
                                                                main_data_csv_file_name=file_name, use_csv_file=True)
    return render_template('get_weight_accuracy.html', navbar_info=navbar_info, results=result_object)


@app.route('/load_integrators')
def load_integrators():
    integrator_list = []
    for row in interec.all_integrators:
        integrator_list.append({'id': row['integrator_id'], 'name': row['integrator_login']})
    return render_template('load_integrators.html', navbar_info=navbar_info, integrator_list=integrator_list)


@app.route('/load_new_pr')
def load_new_pr():
    integrator_list = []
    for row in interec.all_integrators:
        integrator_list.append({'name': row['integrator_login']})
    return render_template('load_new_pr.html', navbar_info=navbar_info, integrator_list=integrator_list)


@app.route('/new_pr', methods=['POST'])
def new_pr():
    global navbar_info

    pr_id = request.form['id']
    requester_login = request.form['requester_login']
    title = request.form['title']
    description = request.form['description']
    created_date = request.form['created_date']
    merged_date = request.form['merged_date']
    files = request.form['files']
    integrator_login = request.form['integrator_login']
    interec.add_pr_to_db(pr_number=pr_id, requester_login=requester_login, title=title, description=description,
                         created_date=created_date, merged_date=merged_date, integrator_login=integrator_login,
                         files=files)
    # update the nav bar info
    navbar_info = {'repository': interec.database,
                   'pr_count': interec.pr_count,
                   'integrator_count': interec.integrator_count}
    return redirect(url_for('index'))


@app.route('/load_find_integrators')
def load_find_integrators():
    return render_template('load_find_integrators.html', navbar_info=navbar_info)


@app.route('/find_integrators', methods=['POST', 'GET'])
def find_integrators():
    if request.method == 'POST':
        pr_id = request.form['id']
        requester_login = request.form['requester_login']
        title = request.form['title']
        description = request.form['description']
        created_date = request.form['created_date']
        files = request.form['files']

        ranked_five_df = interec.get_related_integrators_for_pr(pr_id, requester_login, title, description, created_date,
                                                                files)
    else:
        pr_id = request.args['prId']
        logging.info(pr_id)
        ranked_five_df = interec.get_related_integrators_for_pr_by_pr_number(pr_id)
        logging.info(ranked_five_df)
        pr_data = interec.get_pr_details(pr_id)
        requester_login = pr_data[2]
        title = pr_data[3]
        description = pr_data[4]
        created_date = pr_data[5]
        files = pr_data[8]

    rec_integrators = []
    for index, row in ranked_five_df.iterrows():
        integrator_object = {'rank': int(row['final_rank']),
                             'username': row['integrator'],
                             'f_score': "{0:.2f}".format(row['combined_score']),
                             'fp_score': "{0:.2f}".format(row['std_file_similarity']),
                             't_score': "{0:.2f}".format(row['std_text_similarity']),
                             'a_score': "{0:.2f}".format(row['std_activeness'])}
        rec_integrators.append(integrator_object)

    pr = {'title': title,
          'description': description,
          'pr_id': pr_id,
          'created_date': created_date,
          'files': files,
          'requester_login': requester_login}

    weights = {'alpha': interec.alpha,
               'beta': interec.beta,
               'gamma': interec.gamma}

    return render_template('find_integrators.html', pr=pr, weights=weights, integrators=rec_integrators,
                           navbar_info=navbar_info)


@app.route('/new')
def api_add_new_pr():
    pr_id = request.form['id']
    requester_login = request.form['requester_login']
    title = request.form['title']
    description = request.form['description']
    created_date = request.form['created_date']
    merged_date = request.form['merged_date']
    files = request.form['files']
    integrator_login = request.form['integrator_login']
    flag = interec.add_pr_to_db(pr_number=pr_id, requester_login=requester_login, title=title, description=description,
                                created_date=created_date, merged_date=merged_date, integrator_login=integrator_login,
                                files=files)
    return jsonify(result=flag)


@app.route('/integrators')
def api_get_integrators():
    integrator_list = []
    for row in interec.all_integrators:
        integrator_list.append({'id': row['integrator_id'], 'name': row['integrator_login']})
    return jsonify(integrators=integrator_list)


@app.route('/set_weights', methods=['POST'])
def api_set_weights():
    alpha = request.form['alpha']
    beta = request.form['beta']
    gamma = request.form['gamma']
    flag = interec.set_weight_combination_for_factors(alpha=float(alpha), beta=float(beta), gamma=float(gamma))
    return jsonify(result=flag)


@app.route('/get_weight_combination_accuracy', methods=['POST'])
def api_get_weight_accuracy():
    offset = request.form['offset1']
    limit = request.form['limit1']
    result_object = interec.calculate_scores_and_get_weight_combinations_for_factors(offset=int(offset),
                                                                                     limit=int(limit))
    return jsonify(result=result_object)


@app.route('/find_pr_integrators', methods=['POST'])
def api_find_pr_integrators():
    pr_id = request.form['id']
    requester_login = request.form['requester_login']
    title = request.form['title']
    description = request.form['description']
    created_date = request.form['created_date']
    files = request.form['files']

    ranked_five_df = interec.get_related_integrators_for_pr(pr_id, requester_login, title, description, created_date,
                                                                files)

    rec_integrators = []
    for index, row in ranked_five_df.iterrows():
        integrator_object = {'rank': int(row['final_rank']),
                             'username': row['integrator'],
                             'f_score': "{0:.2f}".format(row['combined_score']),
                             'fp_score': "{0:.2f}".format(row['std_file_similarity']),
                             't_score': "{0:.2f}".format(row['std_text_similarity']),
                             'a_score': "{0:.2f}".format(row['std_activeness'])}
        rec_integrators.append(integrator_object)

    return jsonify(integrators=rec_integrators)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()


# TODO: Add logs
