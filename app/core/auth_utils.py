from datetime import datetime, timezone
import requests
import hashlib
import hmac
import json
import os


def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = hmac.new(("AWS4" + key).encode('utf-8'), date_stamp.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region_name.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service_name.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, "aws4_request".encode('utf-8'), hashlib.sha256).digest()
    return k_signing

def get_header(payload:dict, endpoint:str)->dict:
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    method = 'POST'
    service = 'sagemaker'
    head = 'https://'
    host = 'runtime.sagemaker.ap-southeast-1.amazonaws.com'
    region = 'ap-southeast-1'
    content_type = 'application/json'
    canonical_uri = f'/endpoints/{endpoint}/invocations'

    amz_date = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    date_stamp = datetime.utcnow().strftime('%Y%m%d')

    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    canonical_headers = 'host:' + host + '\n' + 'x-amz-content-sha256:' + payload_hash + '\n' + 'x-amz-date:' + amz_date + '\n'
    signed_headers = 'host;x-amz-content-sha256;x-amz-date'

    canonical_request = method + '\n' + canonical_uri + '\n' + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    signing_key = get_signature_key(secret_key, date_stamp, region, service)

    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    headers = {
        'X-Amz-Content-Sha256': payload_hash,
        'X-Amz-Date': amz_date,
        'Authorization': authorization_header,
        'Content-Type': content_type
    }
    return headers    