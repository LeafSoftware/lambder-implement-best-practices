import boto3
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)

def ec2_regions():
  ec2 = boto3.client('ec2')
  resp = ec2.describe_regions()
  names = []
  for region in resp['Regions']:
    names.append(region['RegionName'])
  return names


# This is the method that will be registered
# with Lambda and run on a schedule
def handler(event={}, context={}):
  for region in ec2_regions():
    ec2 = boto3.resource('ec2', region_name=region)
    logger.info('Checking {} for default SGs'.format(region))
    for sg in ec2.security_groups.filter(Filters=[{"Name":"group-name","Values": ["default"]}]).all():
      for ingress in sg.ip_permissions:
        logger.info('Revoking ingress rule {} from {}'.format(json.dumps(ingress), sg.group_id))
        sg.revoke_ingress(GroupId=sg.group_id,IpPermissions=[ingress])
      for egress in sg.ip_permissions_egress:
        logger.info('Revoking egress rule {} from {}'.format(json.dumps(egress), sg.group_id))
        sg.revoke_egress(GroupId=sg.group_id,IpPermissions=[egress])

# If being called locally, just call handler
if __name__ == '__main__':
  import os
  import json
  import sys

  logging.basicConfig()
  event = {}

  # TODO if argv[1], read contents, parse into json
  if len(sys.argv) > 1:
    input_file = sys.argv[1]
    with open(input_file, 'r') as f:
      data = f.read()
    event = json.loads(data)

  result = handler(event)
  output = json.dumps(
    result,
    sort_keys=True,
    indent=4,
    separators=(',', ':')
  )
  logger.info(output)
