# ScheduleStartStopEc2Lambda
This AWS Lambda function will help you to start and stop EC2 instances at regular intervals. Also you can invoke this function manually with proper input to start or stop specific instances.


This script will start and stop AWS instances either by invoking lambda function from any server or based on tag added to instances.


**(1)** If the function is invoked manually with a payload, this function will check what is the action to be performed. Syntax of the  payload should be as below:
```
  {
      "action": "<stop|start>",
      "instances": "<NameTag1>[, <NameTag2>, <NameTag3>, ...]>"
  }
```
Refer [AWS CLI - invoking Lambda function]( http://docs.aws.amazon.com/lambda/latest/dg/with-userapp-walkthrough-custom-events-invoke.html) to know about manual invokation of this Lambda function. You can write wrapper scripts to call this lambda function. Example for a wrapper script can be viewed at : [Wrapper written in bash using AWS CLI](https://github.com/bijohnvincent/cmapi_clusterstartstop/blob/master/startstopec2instances.sh) 


- Based on the action (Not case sensitive), function will start or stop the instances specified in the payload.
- Start or stop function is restricted to instances having a Tag 'Start-StopHour' for more control and unintentional stop or start of instances.

**(2)** If this Lambda function is triggered by AWS sheduled event, it will check value of tag 'Start-StopHour' and will start or stop instances based on the time specified.
- This option is schedule based. Time will be read in UTC.
- Expected tag value is : start:HH-stop:HH or start:HH or stop:HH
- Both fields are not mandatory. You can use any one of the action too.
- If the servers are started or stopped on invocation only, just add 'none' as value. (False, 0, None, No & N will also work)

## IAM policies
Following policy should be attached to the server from which this lamda fuction is invoked. This one is available as AWS managed policy 'AWSLambdaRole'.
```
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "lambda:InvokeFunction"
        ],
        "Resource": ["*"]
    }]
}
```


Following policy should be applied to the newly created Lambda function.
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:StartInstances",
                "ec2:StopInstances"
            ],
            "Resource": [
                "*"
            ]
        }
  ]
}
```

