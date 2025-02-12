#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.pipeline_stack import PipelineStack
from infra.todoapp_stack import TodoAppStack


app = cdk.App()
app_stack = TodoAppStack(app, "TodoAppStack",
    env=cdk.Environment(
        account=app.account,
        region=app.region
    )
)

# Create the pipeline stack
pipeline_stack = PipelineStack(app, "TodoAppPipelineStack",
    env=cdk.Environment(
        account=app.account,
        region=app.region
    )
)

app.synth()
