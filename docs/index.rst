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
   :statuscode 400: Bad request
   :status 500: An error occurred when getting integrators


.. http:post:: /new

   Add a reviewed and merged PR to the system.

   **Example request**:

   .. sourcecode:: http

      POST /new HTTP/1.1
      Host: http://localhost:5000/
      Content-Type: application/json

      {
            "id": 6453,
            "requester_login": "sime",
            "title": "Separate core memory usage computation in core_memusage.h",
            "description": "Remove support for computing recursive memory usage from memusage.h",
            "created_date_time": "2015-07-17 17:48:52",
            "merged_date_time": "2015-08-08 17:47:52",
            "files": "src/Makefile.a|src/txmempool.cpp",
            "integrator_login" "sam"
      }

   :reqheader Content-Type: application/json
   :<json int id: Id of the PR
   :<json string requester_login: Contributor username
   :<json string title: Title of the PR
   :<json string description: Description of the PR
   :<json string created_date_time: PR created date and time
   :<json string merged_date_time: PR merged date and time
   :<json string files: File paths of the PR
   :<json string integrator_login: PR integrator username
   :resheader Content-Type: text/html
   :status 200: PR successfully added to the system
   :statuscode 400: Bad request
   :status 500: An error occurred when adding the PR


.. http:post:: /set_weight_factors

   Sets the weights for each factor(file path similarity, text similarity, activeness) of the system.

   **Example request**:

   .. sourcecode:: http

      POST /set_weight_factors HTTP/1.1
      Host: http://localhost:5000/
      Content-Type: application/json

      {
            "alpha": 0.1,
            "gamma": 0.1,
            "beta": 0.8
      }

   :reqheader Content-Type: application/json
   :<json int alpha: Weight for file path similarity score
   :<json int beta: Weight for text similarity score
   :<json int gamma: Weight for activeness score
   :resheader Content-Type: text/html
   :status 200: Successfully weights are set.
   :statuscode 400: Bad request
   :status 500: An error occurred when setting the weights.


.. http:post:: /get_weight_combination_accuracy

   Calculates scores for every PR and provides accuracy for each factor weight combination.
   **Example request**:

   .. sourcecode:: http

      POST /get_weight_combination_accuracy HTTP/1.1
      Host: http://localhost:5000/
      Content-Type: application/json

      {
            "offset": 600,
            "limit": 200
      }

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
            "top5": 1,
            "mrr":0.79
        },
        {
            "alpha": 0.1,
            "beta": 0.2,
            "gamma": 0.7,
            "top1": 0,
            "top3": 1,
            "top5": 1,
            "mrr":0.65
        },
        {
            "alpha": 0.1,
            "beta": 0.3,
            "gamma": 0.6,
            "top1": 0,
            "top3": 1,
            "top5": 1,
            "mrr":0.78
        },
      ...
        ]
      }

   :reqheader Content-Type: application/json
   :<json int offset: One less than starting PR number which scores are needed to be calculated
   :<json int limit: Limit of the PRs needed to be considered when calculating scores from the start PR number
   :resheader Content-Type: application/json
   :status 200: Successfully returns accuracy for each factor weight combination.
   :statuscode 400: Bad request
   :status 500: An error occurred when calculating accuracy for each factor weight combination.


.. http:post:: /find_pr_integrators

   Calculates scores for each factor for each integrator and provides a ranked data frame which includes top five
   integrators.

   **Example request**:

   .. sourcecode:: http

      POST /find_pr_integrators HTTP/1.1
      Host: http://localhost:5000/
      Content-Type: application/json

      {
            "id": 6453,
            "requester_login": "sime",
            "title": "Separate core memory usage computation in core_memusage.h",
            "description": "Remove support for computing recursive memory usage from memusage.h",
            "created_date_time": "2015-07-17 17:48:52",
            "files": "src/Makefile.a|src/txmempool.cpp"
      }

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

   :reqheader Content-Type: application/json
   :<json string id: Id of the PR
   :<json string requester_login: Contributor username
   :<json string title: Title of the PR
   :<json string description: Description of the PR
   :<json string created_date_time: PR created date and time
   :<json string files: File paths of the PR
   :resheader Content-Type: application/json
   :status 200: Successfully returns five recommended integrators to review the pr.
   :statuscode 400: Bad request
   :status 500: An error occurred when finding suitable integrators.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
