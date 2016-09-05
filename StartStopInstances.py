# Name          : StopInstances
# Author        : Bijohn Vincent
# Functionality : This script will start and stop AWS instances either by invoking lambda function from any server or based on tag values
# (1) If the function is invoked with a payload, this function will check what is the action to be performed. Sample payload:
#   {
#       "action": "<stop|start>",
#       "instances": "<NameTag1>[, <NameTag2>, <NameTag3>, ...]>"
#   }
#
#       Based on the action (Not case sensitive), function will start or stop the instances specified in the payload.
#       Start or stop function is restricted to instances having a Tag 'Start-StopHourUTC' for more control and 
#           unintentional stop or start of instances.
#
# (2) If there is no payload, it will check value of tag 'Start-StopHourUTC' and will start or stop instances based on the time specified.
#       This option is schedule based. Time will be read in UTC.
#       Expected tag value is : start:HH-stop:HH or start:HH or stop:HH or None
#       Both start and stop fields are not mandatory. You can use any one of the action as shown above.
#       If the servers are started or stopped on invocation only, just add 'none' as value. (False, 0, None, No & N will also work)
#


# Import modules
import boto3
import datetime


# Create Connection that can be used in all functions
ec2 =  boto3.client('ec2')

# Initialize global variables
now = datetime.datetime.now()
currentHour = now.hour


#
# This function starts the instances  passed as parameter
# Python list with instance names is the expected value
#
def StartInstances(instanceNames):

    # Get details of the instances that has name as in input parameter
    Reservations = ec2.describe_instances(Filters=[{'Name':'tag:Name', 'Values':instanceNames}])
    
    for Instances in Reservations['Reservations']:
        for Instance in Instances['Instances']:
            skipStart=True
            #print Instance['InstanceId'], Instance['State']['Name']
            
            # Start the instance only if it is in stopped state
            if Instance['State']['Name'] == 'stopped':
                
                # Ensures only instances with tag 'Start-StopHourUTC' can be started
                if 'Start-StopHourUTC' in str(Instance['Tags']):
                    skipStart=False
                    
                # starts the instance
                if not skipStart:
                    print "Starting %s with ip %s" %(Instance['InstanceId'], Instance['PrivateIpAddress'])
                    response = ec2.start_instances(
                        InstanceIds=[Instance['InstanceId']],
                        DryRun=False
                        )
                    #print response
                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        print 'API call status: Success'
                    else:
                        print 'API call status: Fail'
                
                else:
                    print "Not permitted to start servers without 'Start-StopHourUTC' tag"
            else:
                print Instance['PrivateIpAddress'] + " is not in stopped state" 
    return



#
# This function will stop the instances passed as parameter
# Python list with instance names is the expected value
#
def StopInstances(instanceNames):

    # Get details of the instances that has name as in input parameter
    Reservations = ec2.describe_instances(Filters=[{'Name':'tag:Name', 'Values':instanceNames}])
    
    for Instances in Reservations['Reservations']:
        for Instance in Instances['Instances']:
            skipStop=True
            #print Instance['InstanceId'], Instance['State']['Name']
            
            # Stop the instance only if it is in running state
            if Instance['State']['Name'] == 'running':
                
                # Ensures only instances with tag 'Start-StopHourUTC' can be stopped
                if 'Start-StopHourUTC' in str(Instance['Tags']):
                    skipStop=False
                
                # stops the instance
                if not skipStop:
                    print "Stopping %s with ip %s" %(Instance['InstanceId'], Instance['PrivateIpAddress'])
                    response = ec2.stop_instances(
                        InstanceIds=[Instance['InstanceId']],
                        DryRun=False
                        )
                    #print response
                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        print 'API call status: Success'
                    else:
                        print 'API call status: Fail'
                
                else:
                    print "Not permitted to stop servers without 'Start-StopHourUTC' tag."
            else:
                print Instance['PrivateIpAddress'] + " is not in running state" 
    return




#
# This function will read the tag Start-StopHourUTC and will take necessary action 
# by calling StartInstances() or StopInstances()
#
def CheckTagsAndTakeAction():

    # Filter instances that has specific Tag-key
    Reservations = ec2.describe_instances(Filters=[{'Name':'tag-key','Values':['Start-StopHourUTC']}])
    
    # Initialize name of instances to be started or stopped.
    instanceToStart = ""
    instanceToStop = ""
    
    for Instances in Reservations['Reservations']:
        for Instance in Instances['Instances']:
            print Instance['PrivateIpAddress'] + ":"
            skipAction=False   # Initilize skipAction for each instances
            
            # Process the Tags
            for tag in Instance['Tags']:
                
                # Find name of the instance so that it can be passed to the next function
                if tag['Key'] == 'Name':
                    instanceName = tag['Value']
                
                
                # Check if the tag is value is a negation. 
                # If yes, skip start or stop action.
                # Else split tag value with '-' as delimiter
                if tag['Key'] == 'Start-StopHourUTC':
                    StartStopHourList = []
                    StartStopHour = tag['Value'].replace(' ', '').lower()
                    print StartStopHour
                    if StartStopHour in ['n', 'no', 'false', 'none', '0']:
                        print Instance['PrivateIpAddress'] + " will be started or stopped only with manual invocation" 
                        skipAction=True
                        break
                    else:
                        if ':' in StartStopHour:
                            StartStopHourList = StartStopHour.split("-")
                            #print StartStopHourList
                        else:
                            print "Wrong format. Expected format start:HH-stop:HH or start:HH or stop:HH"
                            skipAction=True
            
            
            # skipAction is not set, by above loop, process the start and stop hours
            # and if start/stop hour is current UTC hour, append the instance name to
            # 'instanceToStart' or 'instanceToStop' based on action.
            if not skipAction:
                for action_time in StartStopHourList:
                    if 'start' in action_time.lower():
                        if int(action_time.split(':')[1]) == currentHour:
                            instanceToStart = instanceToStart + ","+ instanceName
                    elif 'stop' in action_time.lower():
                        if int(action_time.split(':')[1]) == currentHour:
                            instanceToStop = instanceToStop + ","+ instanceName
                    else:
                        print "Wrong action. Should be either 'start' or 'stop'."
    
    # Convert the comma separated instance names to a pythin list
    instanceToStart = instanceToStart.lstrip(',').split(',')
    instanceToStop = instanceToStop.lstrip(',').split(',')

    # If length of 'instanceToStart' or 'instanceToStop' variabble is greater
    # than 0, call curresponding function to start or stop the instances.
    if not instanceToStart == ['']:
        print "Statring : " + str(instanceToStart)
        StartInstances(instanceToStart)
    if not instanceToStop == ['']:
        print "Stopping : " + str(instanceToStop)
        StopInstances(instanceToStop)
    return    
    

#
# This is the main function 
#
def start_stop(json_val, context):
    #print json_val
    print "current hour(UTC) : " + str(currentHour)
    
    # If not invoked by CloudWatch event, process the json input and take necessary action
    if not 'Scheduled Event' in str(json_val):
        print "Manual invocation"
        
        # Validate the input json file print expected format if the json is in wrong format.
        if not 'action' in json_val or not 'instances' in json_val:
            print ''' Wrong input. Expected format:
                   {
                       "action": "<stop|start>",
                       "instances": "<NameTag1>[, <NameTag2>, <NameTag3>, ...]>"
                   }'''
            return None
        
        # Convert 'instances' in json to python 'list'. Remove unwanted spaces in the list.
        instances=map(str.strip,str(json_val['instances']).split(","))
        
        # Call correct function based on action 'start' or 'stop'
        if json_val['action'].lower() == 'start':
            StartInstances(instances)
        elif json_val['action'].lower() == 'stop':
            StopInstances(instances)
        else:
            print json_val['action'] + " is not a valid action. Action can be either 'start' or 'stop'"
    
    
    # If invoked by CloudWatch Scheduled Event, call function for checking tag and take action according to tag
    else:
        print "CloudWatch Scheduled event"
        CheckTagsAndTakeAction()
    return