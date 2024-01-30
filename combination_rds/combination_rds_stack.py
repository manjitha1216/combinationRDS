from constructs import Construct
from aws_cdk import CfnOutput
from aws_cdk import RemovalPolicy

from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    #aws_s3 as s3,
    #aws_lambda as lambda_,
    #aws_lambda_event_sources as lambda_event_sources,
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy

)

from constructs import Construct

from aws_cdk.aws_sns import (
    Topic  
)

from aws_cdk.aws_sqs import (
    Queue   
)

from aws_cdk.aws_sns_subscriptions import (
    SqsSubscription,
    EmailSubscription
)
from aws_cdk.aws_cloudwatch import (
    Alarm,
    Metric
)

from aws_cdk.aws_cloudwatch_actions import (
    AutoScalingAction,
    SnsAction
)


from aws_cdk import CfnOutput

from aws_cdk.aws_sns import (
    Topic  
)

from aws_cdk.aws_sqs import (
    Queue   
)

from aws_cdk.aws_sns_subscriptions import (
    SqsSubscription,
    EmailSubscription
)

from aws_cdk.aws_logs import (
    LogGroup,
    LogStream

)

class CombinationRdsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Prod_configs = self.node.try_get_context("envs")["Prod"]
        email_address = "nataliya.maroz@accenture.com"     
        
        eks_sns_topic = Topic(self, 'EKS SNS topic',display_name='EKS topic')
        rds_sns_topic = Topic(self, 'RDS SNS topic',display_name='RDS topic')

        eks_sqs_queue = Queue(self, 'EKSSQSQueue')
        rds_sqs_queue = Queue(self, 'RDSSQSQueue')
        
        eks_sns_topic.add_subscription(SqsSubscription(eks_sqs_queue))
        eks_sns_topic.add_subscription(SqsSubscription(rds_sqs_queue))
        
        eks_sns_topic.add_subscription(EmailSubscription(email_address))
        rds_sns_topic.add_subscription(EmailSubscription(email_address))

        #bucket = s3.Bucket(self, "mybucket")
        
        '''#crate queue
        queue = sqs.Queue(
            self, "SQSLambdaQueue",
            visibility_timeout=Duration.seconds(300),
        )'''

        '''#create our lambda function
        sqs_lambda = lambda_.Function(self, "SQSLambda",
                                      handler='lambda_handler.handler',
                                      runtime=lambda_.Runtime.PYTHON_3_10,
                                      code=lambda_.Code.from_asset('lambda'))
        # Create our event source
        sqs_event_source = lambda_event_sources.SqsEventSource(queue)

        #Add SQS event source to Lambda
        sqs_lambda.add_event_source(sqs_event_source)
'''

        #  Create a custome VPC
        custom_vpc = ec2.Vpc(
            self, "customvpc",
            ip_addresses= ec2.IpAddresses.cidr(Prod_configs['vpc_config']['vpc_cidr']),
            max_azs= 2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet", cidr_mask=Prod_configs["vpc_config"]["cidr_mask"], subnet_type=ec2.SubnetType.PUBLIC
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet", cidr_mask=Prod_configs["vpc_config"]["cidr_mask"], subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
                ),
            ])
        
        #Create an RDS Database
        myDB = rds.DatabaseInstance(self, 
                                    "MyDatabase",
                                    engine= rds.DatabaseInstanceEngine.MYSQL,
                                    vpc= custom_vpc,
                                    vpc_subnets= ec2.SubnetSelection(
                                        subnet_type= ec2.SubnetType.PUBLIC,
                                    ),
                                    credentials= rds.Credentials.from_generated_secret("Admin"),
                                    instance_type= ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3,
                                                                       ec2.InstanceSize.MICRO),
                                    port= 3306,
                                    allocated_storage= 20,
                                    multi_az= False,
                                    removal_policy= RemovalPolicy.DESTROY,
                                    cloudwatch_logs_exports=['error', 'general', 'slowquery', 'audit'], #comment if db is not deployed
                                    deletion_protection= False,
                                    publicly_accessible= True
                                    )
        
        myDB.connections.allow_from_any_ipv4(
            ec2.Port.tcp(3306),
            description= "Open port for connection"
        )

        
        CfnOutput(self, "RDSInstanceArn", value=myDB.instance_arn)

        rds_cpu_alarm = Alarm(
            self, 'RDSCPUAlarm',
            metric=myDB.metric_cpu_utilization(),
            threshold=40,                   #triggered if the CPU utilization exceeds 90%.
            evaluation_periods=1,           #how many times the line will be crossed until alarm rings
            alarm_name='RDSCPUHighAlarm',
            actions_enabled=True
        )
        
        rds_db_connection_alarm = Alarm(
            self, 'RDSConnectionsEvent',
            metric=myDB.metric_database_connections(),
            threshold=50,                   #triggered if the CPU utilization exceeds 90%.
            evaluation_periods=1,           #how many times the line will be crossed until alarm rings
            alarm_name='RDSConnectionsEvent',
            actions_enabled=True
        )
        
      
        rds_cpu_alarm.add_alarm_action(SnsAction(rds_sns_topic)) #subscribe sns topic to cloudwatch alarm
        rds_db_connection_alarm.add_alarm_action(SnsAction(rds_sns_topic)) #subscribe sns topic to cloudwatch alarm
        
        
        rds_log_group = LogGroup(self, "RDSLogGroup",
                                  log_group_name="/rds/log/group",
                                  removal_policy=RemovalPolicy.DESTROY)

        rds_log_stream = LogStream(self, "RDSLogStream",
                                    log_group=rds_log_group,
                                    log_stream_name="rds_log_stream")
        
        # Step 4: Configure RDS to Use Log Streams (check AWS RDS documentation)

        # Output the CloudWatch Logs Log Group and Log Stream ARNs
        CfnOutput(self, "LogGroupArn", value=rds_log_group.log_group_name)
        CfnOutput(self, "LogStreamName", value=rds_log_stream.log_stream_name)
     
                 
        # eks_cpu_alarm = Alarm(
        #     self, 'EKSCPUAlarm',
        #     metric=,
        #     threshold=90,
        #     evaluation_periods=3,
        #     alarm_name='EKSCPUHighAlarm',
        #     actions_enabled=True
        # )
