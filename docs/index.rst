Welcome to InteRec's documentation!
===================================

.. autoclass:: interec.interec_processor.InterecProcessor
   :members:

.. toctree::
   :maxdepth: 2
   :caption: Contents:


InteRec APIs
==================
.. http:get:: /integrators

   Get the list of integrators for the repository.

   **Example request**:

   .. sourcecode:: http

      GET /integrators HTTP/1.1
      Host: http://localhost:5000/
      Accept: text/javascript

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
         "integrators": [
            {
                "id": 1,
                 "name": "jboner"
            },
            {
               "id": 2,
               "name": "viktorklang"
            }
          ]
      }

   :resheader Content-Type: application/json
   :statuscode 200: Request successful
   :statuscode 404: No integrators found


.. http:post:: /new

   Add a reviewed and merged PR to the system.

   :form id: Id of the PR
   :form requester_login: Contributor username
   :form title: Title of the PR
   :form description: Description of the PR
   :form created_date_time: PR created date and time
   :form merged_date_time: PR merged date and time
   :form files: File paths of the PR
   :form integrator_login: PR integrator username
   :resheader Content-Type: text/html
   :status 200: PR successfully added to the system
   :status 500: An error occurred when adding the PR


.. http:post:: /set_weight_factors

   Sets the weights for each factor(file path similarity, text similarity, activeness) of the system.

   :form alpha: Weight for file path similarity score
   :form beta: Weight for text similarity score
   :form gamma: Weight for activeness score
   :resheader Content-Type: text/html
   :status 200: Successfully weights are set.
   :status 500: An error occurred when setting the weights.


.. http:post:: /get_weight_combination_accuracy

   Calculates scores for every PR and provides accuracy for each factor weight combination.

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "result": [
        {
            "alpha": 0.1,
            "beta": 0.1,
            "gamma": 0.8,
            "top1": 0.33,
            "top3": 1,
            "top5": 1
        },
        {
            "alpha": 0.1,
            "beta": 0.2,
            "gamma": 0.7,
            "top1": 0,
            "top3": 1,
            "top5": 1
        },
        {
            "alpha": 0.1,
            "beta": 0.3,
            "gamma": 0.6,
            "top1": 0,
            "top3": 1,
            "top5": 1
        },
      ...
        ]
      }

   :form offset: tarting PR number which scores are needed to be calculated
   :form limit: Limit of the PRs needed to be considered when calculating scores from the start PR number
   :resheader Content-Type: application/json
   :status 200: Successfully returns accuracy for each factor weight combination.
   :status 500: An error occurred when calculating accuracy for each factor weight combination.


.. http:post:: /find_pr_integrators

   Calculates scores for each factor for each integrator and provides a ranked data frame which includes top five
   integrators.

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "integrators": [
        {
            "a_score": "100.00",
            "f_score": "90.00",
            "fp_score": "0.00",
            "rank": 1,
            "t_score": "100.00",
            "username": "rkuhn"
        },
        {
            "a_score": "81.83",
            "f_score": "67.90",
            "fp_score": "0.00",
            "rank": 2,
            "t_score": "53.08",
            "username": "ktoso"
        },
        ...
        {
            "a_score": "41.09",
            "f_score": "34.39",
            "fp_score": "0.00",
            "rank": 5,
            "t_score": "28.13",
            "username": "drewhk"
        }
        ]
      }

   :form id: Id of the PR
   :form requester_login: Contributor username
   :form title: Title of the PR
   :form description: Description of the PR
   :form created_date_time: PR created date and time
   :form files: File paths of the PR
   :resheader Content-Type: application/json
   :status 200: Successfully returns five recommended integrators to review the pr.
   :status 500: An error occurred when finding suitable integrators.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
