#!/usr/bin/env python3

import aws_cdk as cdk

from combination_rds.combination_rds_stack import CombinationRdsStack


app = cdk.App()
CombinationRdsStack(app, "CombinationRdsStack")

app.synth()
