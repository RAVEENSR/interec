
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


def get_activeness_ranked_list(data_frame):
    return True
