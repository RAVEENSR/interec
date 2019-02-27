
# time_decaying_parameter
const_lambda = -1


def calculate_integrator_activeness(new_pr, old_pr):
    # calculate activeness of the integrator
    activeness = new_pr.created_date - old_pr.merged_data
    if hasattr(activeness, 'days'):
        activeness = activeness.days
    else:
        activeness = 0
    if activeness > 0:
        activeness = activeness ** const_lambda

    return activeness


def add_activeness_ranking(data_frame):
    data_frame["activeness_rank"] = data_frame["activeness"].rank(method='min', ascending=False)
