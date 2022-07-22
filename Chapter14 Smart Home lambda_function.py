# Thanks to Jeff Nunn at Amazon

# -*- coding: utf-8 -*-
# The skill serves as an example on how to use the
# Alexa Smart Home Skill APIs

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import boto3
import json
import logging
import sys
import itertools

from alexa.skills.smarthome.alexa_response import AlexaResponse
from botocore.config import Config

config = Config(region_name = 'eu-west-1') # Replace with your region, if necessary

sqs_client = boto3.client('sqs', config=config)
sqs_queue_url = 'https://sqs.eu-west-1.amazonaws.com/559144307262/senseHatQueue' # Replace with the Amazon SQS Queue Url value generated by CloudFormation and found in your `setup.txt` file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(request, context): 
    logger.info('+++++ request')
    logger.info(request)
    
    if context is not None:
        logger.info('+++++ context')
        logger.info(context)

    # Validate we have an Alexa directive
    if 'directive' not in request:
        response = AlexaResponse({
            'name': 'ErrorResponse',
            'payload': {'type': 'INVALID_DIRECTIVE',
                        'message': 'Missing key: directive, Is the request a valid Alexa Directive?'}
        }).get()
        
        return send_response(response)

    # Check the payload version
    payload_version = request['directive']['header']['payloadVersion']
    if payload_version != '3':
        response = AlexaResponse({
            'name': 'ErrorResponse',
            'payload': {'type': 'INTERNAL_ERROR',
                        'message': 'This skill only supports Smart Home API version 3'}
        }).get()
        
        return send_response(response)

    # Handle the incoming request from Alexa based on the namespace
    name = request['directive']['header']['name']
    namespace = request['directive']['header']['namespace']

    if namespace == 'Alexa.Authorization':
        if name == 'AcceptGrant':
            # Note: This sample accepts any grant request
            # In your implementation you would use the code and token to get and store access tokens
            grant_code = request['directive']['payload']['grant']['code']
            grantee_token = request['directive']['payload']['grantee']['token']
            response = AlexaResponse({'namespace': 'Alexa.Authorization', 'name': 'AcceptGrant.Response'}).get()

            return send_response(response)
    
    if namespace == 'Alexa.Discovery':
        response = AlexaResponse({'namespace': 'Alexa.Discovery', 'name': 'Discover.Response'})

        # Load any capability definitions (e.g., PowerController, ModeController, ToggleController, etc)
        capabilities = []

        ## PowerController
        power_controller_capabilities = load_capability_definition("PowerController")
        capabilities.append(power_controller_capabilities)
        
        ## ColorController
        color_controller_capabilities = load_capability_definition("ColorController")
        capabilities.append(color_controller_capabilities)
        
        # Flatten capabilities into a single list
        capabilities = list(itertools.chain.from_iterable(capabilities))
        
        # Add the base Alexa interface
        base_interface = {
          "type": "AlexaInterface",
          "interface": "Alexa",
          "version": "3"
        }
        capabilities.append(base_interface)

        response.add_payload_endpoint({
            'endpointId': 'sense-hat-01', 
            'friendlyName': 'Sense Hat display', 
            'manufacturerName': 'Developer', 
            'description': 'A Raspberry Pi Sense hat Smart Home skills', 
            'capabilities': capabilities
        })
        
        response = response.get()
        return send_response(response)
        
    if namespace == 'Alexa.PowerController':
        endpoint_id = request['directive']['endpoint']['endpointId']
        power_state_value = 'OFF' if name == 'TurnOff' else 'ON'
        token = request['directive']['endpoint']['scope']['token']
        correlation_token = request['directive']['header']['correlationToken']

        message = {
            'endpointId':endpoint_id, 
            'namespace':'Alexa.PowerController', 
            'name':'powerState', 
            'value':power_state_value
        }
        
        if send_device_state_message(message):
            response = AlexaResponse({
                'correlationToken': correlation_token,
                'token': token,
                'endpointId': endpoint_id
            })
            
            response.add_context_property({
                'namespace':'Alexa.PowerController', 
                'name': 'powerState', 
                'value': power_state_value
            })
            response = response.get()
        else:        
            response = AlexaResponse({
                'name': 'ErrorResponse',
                'payload': {
                    'type': 'ENDPOINT_UNREACHABLE',
                    'message': 'Unable to set endpoint state.'
                }
            }).get()

        return send_response(response)

    if namespace == 'Alexa.RangeController':
        # Continue your learning!
        # You can implement Alexa.RangeController for your virtual fireplace via 
        #   https://github.com/alexa/skill-sample-smarthome-fireplace-python/tree/main/continued-learning/RangeController
        pass

    if namespace == 'Alexa.ColorController':

        endpoint_id = request['directive']['endpoint']['endpointId']
        token = request['directive']['endpoint']['scope']['token']
        correlation_token = request['directive']['header']['correlationToken']
        
        color_value = request['directive']['payload']['color']
        logger.info('+++++ color_value')
        logger.info(color_value)
        
        message = {
            'endpointId':endpoint_id, 
            'namespace':'Alexa.ColorController', 
            'name':'color', 
            'value':color_value
        }
        
        if send_device_state_message(message):
            response = AlexaResponse({
                'correlationToken': correlation_token,
                'token': token,
                'endpointId': endpoint_id
            })
            
            response.add_context_property({
                'namespace':'Alexa.ColorController', 
                'name': 'color', 
                'value': color_value
            })
            response = response.get()
        else:        
            response = AlexaResponse({
                'name': 'ErrorResponse',
                'payload': {
                    'type': 'ENDPOINT_UNREACHABLE',
                    'message': 'Unable to set endpoint state.'
                }
            }).get()

        return send_response(response)

    
    if namespace == 'Alexa.ModeController':
        # Continue your learning!
        # You can implement Alexa.ModeController for your virtual fireplace via 
        #   https://github.com/alexa/skill-sample-smarthome-fireplace-python/tree/main/continued-learning/ModeController
        pass

def send_device_state_message(opts={}):
    message_body = json.dumps(opts)

    try:
        return sqs_client.send_message(QueueUrl=sqs_queue_url, MessageBody=message_body)
    except:
        e = sys.exc_info()[0]
        logger.info('+++++ error sending message')
        logger.info(message_body)
        logger.error(e)
        return None

    logger.info('+++++ SQS Response')
    logger.info(sqs_response)

def send_response(response):
    # TODO Validate the response
    logger.info('+++++ lambda_handler response')
    logger.info(json.dumps(response))
    
    return response

def load_capability_definition(capability):
    with open(f'./capabilities/{capability}.json') as f:
        controller = json.load(f)

    capabilities = []

    if isinstance(controller, dict):
        capabilities.append(controller)
    elif isinstance(controller, list):
        for i in range(len(controller)):
            capabilities.append(controller[i])

    return capabilities
