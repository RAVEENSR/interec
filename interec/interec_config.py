#!/usr/bin/env python

mysql = {'host': 'localhost:3306',
         'user': 'root',
         'password': '',
         'db': 'akka',
         'pr_table': 'pull_request',
         'integrator_table': 'integrator',
         }

system_defaults = {'alpha': 0.1,
                   'beta': 0.2,
                   'gamma': 0.7,
                   }

system_constants = {'date_window': 120,
                    'const_lambda': -1
                    }
