__author__ = 'tinglev@kth.se'

import json
from os import device_encoding
import re
import os
import json
import shutil
import logging
import tempfile
import requests
from urllib.parse import urlparse
from azure.storage.blob import BlobServiceClient, BlobProperties, ContentSettings
from flask import Flask, jsonify, request
from flask_executor import Executor
import environment
import process

def process_callback(future):
    logger = logging.getLogger(__name__)
    result = future.result()
    if result[1]:
        logger.debug('Error when generating report: %s', result[1])
        return
    logger.debug('Generated report for %s', result[0])
    if 'callback' in result[0]:
        logger.debug('Calling %s with deployment data', result[0]['callback'])
        requests.post(result[0]['callback'], result[0])

app = Flask(__name__)
executor = Executor(app)
executor.add_default_done_callback(process_callback)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


@app.route('/api/lighthouse/_monitor', methods=['GET'])
def monitor():
    return 'APPLICATION_STATUS: OK'

@app.route('/api/lighthouse', methods=['POST'])
def create_report():
    logger = logging.getLogger(__name__)
    if not request.is_json:
        return jsonify({'error': 'post is not json (bad content-type?)'}), 400
    req_json = request.get_json()
    logger.debug('Got data: %s', json.dumps(req_json))
    executor.submit(process_deployment, req_json)
    return jsonify({'status': 'accepted'}), 202

def process_deployment(deployment):
    error = verify_deployment(deployment)
    if error:
        return deployment, error
    for u in deployment['urls']:
        process_url_to_scan(deployment, u)
    return deployment, None

def verify_deployment(deployment):
    if 'application' not in deployment:
        return '"application" missing from deployment json'
    if 'commit' not in deployment:
        return '"commit" missing from deployment json'
    if 'environment' not in deployment:
        return '"environment" missing from deployment json'
    if 'urls' not in deployment:
        return '"urls" missing from deployment json'
    if 'team' not in deployment:
        return '"team" missing from deployment json'
    if not isinstance(deployment['urls'], list):
        return '"urls" in deployment json is not an array'
    if len(deployment['urls']) < 1:
        return '"urls" must contain atleast one url to scan'
    return None

def process_url_to_scan(deployment, url_to_scan):
    logger = logging.getLogger(__name__)
    try:
        tmp_dir = tempfile.mkdtemp()
        logger.debug('Temp dir created, running headless-lighthouse')
        image = environment.get_lighthouse_image()
        output = process.run_with_output(f'docker run -e URL={url_to_scan} '
                                         f'-v {tmp_dir}:/report '
                                         f'{image}')
        logger.debug('Output from lighthouse was: "%s"', output)
        app_name = deployment['application']
        commit = deployment['commit']
        url_path = urlparse(url_to_scan).path.replace('/', '-')
        report_path = f'{tmp_dir}/{app_name}_{commit}_{url_path}'
        os.rename(f'{tmp_dir}/report.report.html', f'{report_path}.html')
        os.rename(f'{tmp_dir}/report.report.json', f'{report_path}.json')

        logger.debug(f'Report path is {report_path}.html')
        upload_to_storage(deployment, report_path, url_path)
    finally:
        if os.path.exists(tmp_dir) and os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)

def upload_to_storage(deployment, report_path, url_path):
    logger = logging.getLogger(__name__)
    logger.info('Lighthouse connections string found, uploading report')
    connect_str = environment.get_storage_conn_string()
    client = BlobServiceClient.from_connection_string(connect_str)
    container = 'no team'
    if 'team' in deployment:
        container = deployment['team']
    try:
        logger.debug(f'Using container "{container}"')
        client.create_container(container)
    except:
        logger.debug('Container already exists')
    clean_old_blobs(deployment, client, container, url_path)
    html_path = f'{report_path}.html'
    json_path = f'{report_path}.json'
    filename = os.path.basename(html_path)
    logger.debug('Generated filename "%s"', filename)
    blob_properties = get_blob_properties(filename)
    blob_client = client.get_blob_client(container=container, blob=blob_properties)
    with open(html_path, "rb") as data:
        try:
            blob_client.upload_blob(data)
            blob_client.set_http_headers(content_settings=blob_properties.content_settings)
        except Exception as ex:
            logger.debug('Couldnt upload file. Does it already exist? Ex: %s', ex)
    filename = os.path.basename(json_path)
    blob_properties = get_blob_properties(filename)
    blob_client = client.get_blob_client(container=container, blob=blob_properties)
    with open(json_path, "rb") as data:
        try:
            blob_client.upload_blob(data)
            blob_client.set_http_headers(content_settings=blob_properties.content_settings)
        except Exception as ex:
            logger.debug('Couldnt upload file. Does it already exist? Ex: %s', ex)
    logger.info('Report upload complete')

def get_blob_properties(filename):
    logger = logging.getLogger(__name__)
    props = BlobProperties()
    content = ContentSettings()
    logger.debug('Settings props for file %s', filename)
    props.name = filename
    if '.json' in filename:
        content.content_type = 'application/json'
    elif '.html' in filename:
        content.content_type = 'text/html'
    else:
        content.content_type = 'text/plain'
    logger.debug('Content-type set to %s', content.content_type)
    content.content_disposition = f'inline; filename={filename}'
    props.content_settings = content
    return props

def clean_old_blobs(deployment, service_client, container_name, url_path):
    logger = logging.getLogger(__name__)
    client = service_client.get_container_client(container_name)
    app_name = deployment['application']
    blobs = client.list_blobs(name_starts_with=app_name)
    as_list = [
        b for b 
        in blobs 
        if b.name.replace('.html', '').replace('.json', '').endswith(url_path)
    ]
    as_list.sort(key=lambda b:b.last_modified, reverse=True)
    max_files_per_path = 10
    if len(as_list) > max_files_per_path:
        logger.info(f'Cleaning {len(as_list) - max_files_per_path} old reports')
        for b in as_list[max_files_per_path:]:
            blob_client = service_client.get_blob_client(
                container=container_name,
                blob=b.name
            )
            blob_client.delete_blob()
