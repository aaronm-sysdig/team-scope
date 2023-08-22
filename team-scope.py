import argparse
import os
import time
import requests
import csv
import logging
from kubernetes import client, config
from collections import defaultdict
__version__ = "1.1.0"

class MaxRetriesExceededError(Exception):
    """Custom exception for when max retries are hit."""
    pass


def sysdig_request(method, url, headers, params=None, _json=None, max_retries=5, base_delay=5,
                   max_delay=60, timeout=10) -> requests.Response:
    """
    This module provides functionality to fetch data from the Sysdig API, and returns the results.
    It will also handle 429 Too Many Requests and other transient errors by retrying the request.

    Version 1.2
    """
    retries = 0
    e = None
    while retries <= max_retries:
        try:
            response = requests.request(method=method, url=url, headers=headers, params=params, json=_json,
                                        timeout=timeout)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            # Handle specific HTTP errors like 429 (Too Many Requests)
            if response.status_code == 429:
                delay = min(base_delay * (2 ** retries), max_delay)
                logging.warning(f"Got status 429, retrying in {delay} seconds...")
            else:
                logging.error(f"HTTP Error for {url}: {e}")
                raise  # Reraise the exception

        except (requests.exceptions.Timeout, requests.exceptions.TooManyRedirects) as e:
            # Handle timeouts and redirects which can be transient
            delay = min(base_delay * (2 ** retries), max_delay)
            logging.warning(f"Error {e}. Retrying in {delay} seconds...")

        except requests.exceptions.RequestException as e:
            # For other types of exceptions, you might want to break out of the loop and not retry
            logging.error(f"Error making request to {url}: {e}")
            raise
        time.sleep(delay)
        retries += 1

    logging.error(f"Failed to fetch data from {url} after {max_retries} retries.")
    raise MaxRetriesExceededError(f"Max retries exceeded for {url}")


def get_namespace_annotations(namespaces, annotation_key):
    get_namespace_annotations_arr_annotations = {}
    for namespace in namespaces:
        annotations = namespace.metadata.annotations
        if annotations and annotation_key in annotations:
            get_namespace_annotations_arr_annotations[namespace.metadata.name] = annotations[annotation_key]
    logging.info(f" Retrieved annotations '{annotation_key}' for namespaces")
    return get_namespace_annotations_arr_annotations


def get_namespace_labels(namespaces, label_key):
    get_namespace_labels_arr_labels = {}
    for namespace in namespaces:
        labels = namespace.metadata.labels
        if labels and label_key in labels:
            get_namespace_labels_arr_labels[namespace.metadata.name] = labels[label_key]
    logging.info(f" Retrieved labels '{label_key}' for namespaces")
    return get_namespace_labels_arr_labels


def build_payload(arr_team, str_new_filter, str_zone_filter):
    payload = {
        "userRoles": arr_team['userRoles'],
        "id": arr_team['id'],
        "version": arr_team['version'],
        "name": arr_team['name'],
        "theme": arr_team['theme'],
        "defaultTeamRole": arr_team['defaultTeamRole'],
        "description": arr_team['description'],
        "show": "host",
        "searchFilter": None,
        "default": arr_team['default'],
        "immutable": arr_team['immutable'],
        "filter": f"kubernetes.namespace.name in ({str_new_filter})",
        "namespaceFilters": {
            "prometheusRemoteWrite": None
        },
        "canUseRapidResponse": arr_team['canUseRapidResponse'],
        "canUseSysdigCapture": arr_team['canUseSysdigCapture'],
        "canUseAgentCli": arr_team['canUseAgentCli'],
        "canUseCustomEvents": arr_team['canUseCustomEvents'],
        "canUseAwsMetrics": arr_team['canUseAwsMetrics'],
        "canUseBeaconMetrics": arr_team['canUseBeaconMetrics'],
        "products": [
            "SDS"
        ],
        "origin": "SYSDIG",
        "entryPoint": {
            "module": arr_team['entryPoint']['module']
        },
        "zoneIds": str_zone_filter,
        "allZones": not bool(str_zone_filter)
    }
    return payload


def validate_choice(value):
    if value not in ['y', 'n']:
        logging.info('Invalid choice. Please enter Y or N.')
        return False
    else:
        return True


def parse_command_line_arguments():
    objParser = argparse.ArgumentParser(
        description=f"team-scope.py {__version__} '--label' and '--annotation' are mutually exclusive.  I.E specify one or the other")
    group = objParser.add_mutually_exclusive_group(required=True)

    objParser.add_argument('--version', '-v',
                       action='version',
                       version='%(prog)s ' + __version__)
    group.add_argument('--label', '-l',
                       required=False,
                       action='store_true',
                       default=False,
                       help='Flag to denote looking for labels')
    group.add_argument('--annotation', '-a',
                       required=False,
                       action='store_true',
                       default=False,
                       help='Flag to denote looking for annotations')
    objParser.add_argument('--api-url',
                           required=True,
                           action='store',
                           type=str,
                           default=os.environ.get('API_URL', None),
                           help='API URL I.E https://app.au1.sysdig.com (Default: API_URL Environment variable')
    objParser.add_argument('--team-config', '-t',
                           required=True,
                           type=str,
                           default=os.environ.get('TEAM_CONFIG', None),
                           help='Team config CSV (Default: TEAM_CONFIG Environment variable)')
    objParser.add_argument('--context-config', '-c',
                           required=True,
                           type=str,
                           default=os.environ.get('CONTEXT_CONFIG', None),
                           help='Context config file (Default: CONTEXT_CONFIG Environment variable)')
    objParser.add_argument('--zone-config', '-z',
                           required=False,
                           type=str,
                           default=os.environ.get('ZONE_CONFIG', None),
                           help='Context config file (Default: CONTEXT_CONFIG Environment variable)')
    objParser.add_argument('--silent', '-s',
                           action='store_true',
                           help='Run without user interaction (i.e do not prompt to proceed)')
    objParser.add_argument('--debug', '-d',
                           action='store_true',
                           required=False,
                           default=False,
                           help='Log Debug')

    _obj_args = objParser.parse_args()
    if _obj_args.api_url is None or _obj_args.team_config is None or _obj_args.context_config is None:
        if _obj_args.annotation is False and _obj_args.label is False:
            objParser.parse_args(['--help'])
            exit(1)
    return _obj_args


def configure_logging():
    if obj_args.debug:
        logging_level = 'DEBUG'
    else:
        logging_level = 'INFO'
    logging.basicConfig(level=getattr(logging, logging_level),
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


def create_auth_header():
    api_token = os.environ.get('SECURE_API_TOKEN')
    if api_token is not None:
        _auth_header = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    else:
        logging.info('Please set the SECURE_API_TOKEN environment variable to continue')
        exit(1)
    return _auth_header


def process_context_and_cluster_input_files():
    logging.info(f"Processing Input File '{obj_args.team_config}'")
    with open(file=obj_args.team_config,
              mode='r') as teamcsv:
        _arr_team_config = list(csv.reader(teamcsv, delimiter=','))
        _arr_team_config.pop(0)
    _arr_annotation_label = list(set(sublist[2] for sublist in _arr_team_config))

    if obj_args.zone_config:
        logging.info(f"Processing zone Input File '{obj_args.zone_config}'")
        with open(file=obj_args.zone_config,
                  mode='r') as zonecsv:
            _arr_zone_config = list(csv.reader(zonecsv, delimiter=','))
            _arr_zone_config.pop(0)
    else:
        _arr_zone_config = None

    config.load_kube_config()
    with open(file=obj_args.context_config,
              mode='r') as context_file:
        _arr_contexts_config = [line.strip() for line in context_file]
        _arr_contexts_config.pop(0)

    return _arr_team_config, _arr_contexts_config, _arr_annotation_label, _arr_zone_config


def confirm_to_proceed():
    # Option to continue or not
    if not obj_args.silent:
        logging.info(f"'todo.csv' hss ben written to the current directory outlining the team -> namespace mapping."
                     f"\nPlease review before proceeding")
        while True:
            choice = input("\nWould you like to proceed with execution?: Y or N [N]: ").strip().lower() or 'n'
            if validate_choice(choice):
                break
        if choice == 'n':
            logging.info(f"Action cancelled.  Exiting...")
            exit(1)
        while True:
            choice = input("Are you SURE you want to proceed? [y/N] [N]: ").strip().lower() or 'n'
            if validate_choice(choice):
                break
        if choice != 'y':
            logging.info(f"Action cancelled.  Exiting...")
            exit(1)
    else:
        logging.info(f"Running with --silent flag, continuing")
    logging.info('Would you like to proceed with execution?: Y or N [N] = Y')
    logging.info('Are you SURE you want to proceed? [y/N] [N]: = Y')


def get_team_name(team_id, teams_list):
    for team in teams_list:
        if team[1] == team_id:
            return team[0]
    return None  # Return None if the team ID wasn't found


def write_todo_csv():
    with open(file='todo.csv', mode='w', newline='') as todocsv:
        writer = csv.writer(todocsv, delimiter=',')
        writer.writerow(['Team Name', 'Team ID', 'Namespace'])
        for key, value in arr_namespaces.items():
            str_team_name = get_team_name(key, arr_team_config)
            for sub_key in value.keys():
                writer.writerow([str(str_team_name), str(key), str(sub_key)])


if __name__ == "__main__":
    arr_ns_annotations = {}
    arr_ns_labels = {}

    obj_args = parse_command_line_arguments()
    configure_logging()
    auth_header = create_auth_header()
    arr_team_config, arr_contexts_config, arr_annotation_label, arr_zone_config = process_context_and_cluster_input_files()

    # Get Namespace Information
    for row in arr_contexts_config:
        if len(row) != 0:
            logging.info(f"Processing Context: '{row}'")
            v1 = client.CoreV1Api(api_client=config.new_client_from_config(context=row))
            arr_namespaces = v1.list_namespace().items  # Get namespaces
            # Process Annotations
            if obj_args.annotation:
                for annotation in arr_annotation_label:
                    arr_ns_annotations[annotation] = get_namespace_annotations(namespaces=arr_namespaces,
                                                                               annotation_key=annotation)
            else:
                # Process Labels
                for label in arr_annotation_label:
                    arr_ns_labels[label] = get_namespace_labels(namespaces=arr_namespaces,
                                                                label_key=label)
        else:
            logging.error('We could not find a valid Kubernetes context.  Exiting... (sorry)')
            exit(1)

    arr_zones = {}
    arr_namespaces = defaultdict(dict)

    for row in arr_team_config:
        arr_zones[row[1]] = {}

        if arr_zone_config is not None:  # I.e we have zones to configure
            arr_found = list({int(sublist[2]) for sublist in arr_zone_config if sublist[1] == row[1]})

            arr_zones[row[1]] = arr_found

        if obj_args.annotation:
            arr_found = dict({k: v for k, v in arr_ns_annotations[row[2]].items() if v.startswith(row[3])})
            arr_namespaces[row[1]].update(arr_found)
            logging.info(f"Processing Team: '{row[0]}, TeamID:'{row[1]}.  "
                         f"Looking for annotation: '{row[2]}={row[3]}', "
                         f"found in the following namespaces '{', '.join(arr_found) if len(arr_found) > 0 else 'None Found'}'")

        else:
            arr_found = dict({k: v for k, v in arr_ns_labels[row[2]].items() if v.startswith(row[3])})
            arr_namespaces[row[1]].update(arr_found)
            logging.info(f"Processing Team: '{row[0]}, "
                         f"TeamID:'{row[1]}.  Looking for label: '{row[2]}={row[3]}', "
                         f"found in the following namespaces '{', '.join(arr_found) if len(arr_found) > 0 else 'None Found'}'")

    write_todo_csv()
    confirm_to_proceed()

    # Send API Requests
    for row_teamid in arr_namespaces:
        if len(arr_namespaces[row_teamid]) != 0:
            team_url = f"{obj_args.api_url}/api/teams/{row_teamid}"
            arr_team = (sysdig_request(method='GET', url=team_url, headers=auth_header)).json()
            str_filter = ','.join(f'"{value}"' for value in arr_namespaces[row_teamid])
            arr_zone_filter = list(arr_zones[row_teamid])
            arr_payload = build_payload(arr_team=arr_team['team'], 
                                        str_new_filter=str_filter,
                                        str_zone_filter=arr_zone_filter)
            obj_result = sysdig_request(method='PUT', url=team_url, headers=auth_header, _json=arr_payload)
            logging.info(f"Updating Team: '{get_team_name(row_teamid,arr_team_config)}, "
                         f"TeamID:'{row_teamid}.")
            logging.debug(f" Payload {arr_payload}")
            logging.info(f"Update Result Code: {obj_result.status_code}")
        else:
            logging.info(f"No matching annotation/label. Skipping...")
