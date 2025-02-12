from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr as ecr,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    CfnOutput,
)
from constructs import Construct

class TodoAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        self.vpc = ec2.Vpc(
            self, "TodoAppVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ]
        )

        # Database Security Group
        self.db_security_group = ec2.SecurityGroup(
            self, "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for RDS instance",
            allow_all_outbound=True
        )

        # Database Secrets
        self.database_secret = secretsmanager.Secret(
            self, "DatabaseSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "postgres"}',
                generate_string_key="password",
                exclude_characters='"@/\\'
            )
        )

        # RDS Instance
        self.database = rds.DatabaseInstance(
            self, "TodoAppDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[self.db_security_group],
            credentials=rds.Credentials.from_secret(self.database_secret),
            multi_az=False,
            allocated_storage=20,
            max_allocated_storage=100,
            backup_retention=Duration.days(7),
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY
        )

        # ECS Cluster
        self.cluster = ecs.Cluster(
            self, "TodoAppCluster",
            vpc=self.vpc,
            container_insights=True
        )

        # ECR Repository
        self.repository = ecr.Repository(
            self, "TodoAppRepo",
            repository_name="todo-app",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_images=True
        )

        # Task Definition
        self.task_definition = ecs.FargateTaskDefinition(
            self, "TodoAppTask",
            memory_limit_mib=512,
            cpu=256
        )

        # Container Definition
        container = self.task_definition.add_container(
            "TodoAppContainer",
            image=ecs.ContainerImage.from_ecr_repository(self.repository),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="todo-app"
            ),
            environment={
                "ENVIRONMENT": "production",
            },
            secrets={
                "DATABASE_URL": ecs.Secret.from_secrets_manager(
                    self.database_secret
                )
            }
        )

        container.add_port_mappings(
            ecs.PortMapping(
                container_port=8000,
                protocol=ecs.Protocol.TCP
            )
        )

        # Fargate Service
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "TodoAppService",
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=2,
            public_load_balancer=True,
            assign_public_ip=False
        )

        # Lambda Function
        self.lambda_function = lambda_.Function(
            self, "TodoAppFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.lambda.handler",
            code=lambda_.Code.from_asset(".", 
                bundling=lambda_.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "ENVIRONMENT": "production",
                "PYTHONPATH": "/var/task",
            },
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            allow_public_subnet=False,
        )

        # Grant Lambda access to database secret
        self.database_secret.grant_read(self.lambda_function)

        # API Gateway
        api = apigw.LambdaRestApi(
            self, "TodoAppApi",
            handler=self.lambda_function,
            proxy=True,
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=10,
                throttling_burst_limit=20,
            )
        )

        # Outputs
        CfnOutput(
            self, "LoadBalancerDNS",
            value=self.fargate_service.load_balancer.load_balancer_dns_name
        )

        CfnOutput(
            self, "ECRRepositoryURI",
            value=self.repository.repository_uri
        )