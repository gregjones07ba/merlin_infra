#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.merlin_stack import MerlinStack


app = cdk.App()
MerlinStack(app, "Merlin",
    env=cdk.Environment(account='580938938844', region='us-east-1'),
)

app.synth()
