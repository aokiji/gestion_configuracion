import urllib.request
import boto3

HOSTED_ZONE_ID='Z2IDVHHSTJAHUS'

client = boto3.client('route53')

ip_str = urllib.request.urlopen("http://ipinfo.io/ip").read()
current_ip = ip_str.rstrip().decode()

changes = {
        'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'nico.multiservicioselmorche.es',
                    'Type': 'A',
                    'TTL': 300,
                    'ResourceRecords': [{ 'Value': current_ip }]
                    }
                }
            ]
        }
client.change_resource_record_sets(
        HostedZoneId=HOSTED_ZONE_ID,
        ChangeBatch=changes
        )
