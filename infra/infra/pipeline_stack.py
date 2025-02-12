from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_codebuild as codebuild,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_iam as iam,
    SecretValue,
    Duration,
)
from constructs import Construct

class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ECR Repository
        repository = ecr.Repository(
            self, "TodoAppRepository",
            repository_name="todo-app",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_images=True
        )

        # CodeBuild Project for Docker Build
        build_project = codebuild.PipelineProject(
            self, "DockerBuild",
            environment=codebuild.BuildEnvironment(
                privileged=True,
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            ),
            environment_variables={
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                    value=repository.repository_uri
                ),
                "CONTAINER_NAME": codebuild.BuildEnvironmentVariable(
                    value="todo-app"
                )
            },
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "pre_build": {
                        "commands": [
                            "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $REPOSITORY_URI",
                            "COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)",
                            "IMAGE_TAG=${COMMIT_HASH:=latest}"
                        ]
                    },
                    "build": {
                        "commands": [
                            "docker build -t $REPOSITORY_URI:$IMAGE_TAG .",
                            "docker tag $REPOSITORY_URI:$IMAGE_TAG $REPOSITORY_URI:latest"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "docker push $REPOSITORY_URI:$IMAGE_TAG",
                            "docker push $REPOSITORY_URI:latest",
                            "printf '[{\"name\":\"%s\",\"imageUri\":\"%s\"}]' $CONTAINER_NAME $REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json"
                        ]
                    }
                },
                "artifacts": {
                    "files": ["imagedefinitions.json"]
                }
            })
        )

        # Grant ECR permissions to CodeBuild
        repository.grant_pull_push(build_project)

        # Pipeline
        pipeline = codepipeline.Pipeline(
            self, "TodoAppPipeline",
            pipeline_name="todo-app-pipeline"
        )

        # Source Stage
        source_output = codepipeline.Artifact()
        source_action = pipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="your-github-username",
            repo="your-repo-name",
            branch="main",
            oauth_token=SecretValue.secrets_manager("github-token"),
            output=source_output
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # Build Stage
        build_project = codebuild.PipelineProject(
            self, "TodoAppBuild",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.12"
                        },
                        "commands": [
                            "pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": [
                            "pytest",
                            "cdk synth"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "cdk.out/**/*"
                    ]
                }
            }),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            )
        )

        build_output = codepipeline.Artifact()
        build_action = pipeline_actions.CodeBuildAction(
            action_name="Build",
            project=build_project,
            input=source_output,
            outputs=[build_output]
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]
        )

        # Deploy Stage
        deploy_action = pipeline_actions.CloudFormationCreateUpdateStackAction(
            action_name="Deploy",
            stack_name="TodoAppStack",
            template_path=build_output.at_path("TodoAppStack.template.json"),
            admin_permissions=True
        )

        pipeline.add_stage(
            stage_name="Deploy",
            actions=[deploy_action]
        )