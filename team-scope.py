import argparse
import os
import time
import requests
import csv
import click
from kubernetes import client, config


# from kubernetes.client import configuration


def sysdig_request(method, url, headers, params=None, _json=None) -> requests.Response:
    SLEEP_429_SECONDS = 30
    objRequestResult = requests.Response
    try:
        objRequestResult = requests.request(method=method, url=url, headers=headers, params=params, json=_json)
        objRequestResult.raise_for_status()
        while objRequestResult.status_code == 429:
            print(f"Got status 429, Sleeping for {SLEEP_429_SECONDS} seconds before trying again")
            time.sleep(SLEEP_429_SECONDS)
            objRequestResult = requests.request(method=method, url=url, headers=headers, params=params, json=_json)
    except requests.exceptions.HTTPError as e:
        print(" ERROR ".center(80, "-"))
        print(e)
        exit(1)
    except requests.exceptions.RequestException as e:
        print(e)
        exit(1)

    return objRequestResult


arrNSAnnotation = {}
arrNSLabels = {}


def get_namespace_annotations(annotation_key):
    # Retrieve all namespaces
    namespaces = v1.list_namespace().items

    for namespace in namespaces:
        annotations = namespace.metadata.annotations
        if annotations and annotation_key in annotations:
            arrNSAnnotation[namespace.metadata.name] = annotations[annotation_key]
    print(f" Retrieved annotations for namespaces")


def get_namespace_labels(label_key):
    # Retrieve all namespaces
    namespaces = v1.list_namespace().items

    for namespace in namespaces:
        labels = namespace.metadata.labels
        if labels and label_key in labels:
            arrNSLabels[namespace.metadata.name] = labels[label_key]
    print(f" Retrieved labels for namespaces")


def build_payload(arr_team, str_new_filter):
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
        "zoneIds": [],
        "allZones": arr_team['allZones']
    }
    return payload


def validate_choice(ctx, param, value):
    if value.lower() not in ['y', 'n']:
        raise click.BadParameter('Invalid choice. Please enter Y or N.')
    return value.lower()


if __name__ == "__main__":
    objParser = argparse.ArgumentParser(description='"label" and "annotation" are mutually exclusive.  I.E specify one or the other')
    group = objParser.add_mutually_exclusive_group(required=True)
    group.add_argument('--label', required=False,
                       type=str,
                       default=os.environ.get('LABEL', None),
                       help='Label to look for (Default: LABEL Environment Variable)')
    group.add_argument('--annotation', required=False,
                       type=str,
                       default=os.environ.get('ANNOTATION', None),
                       help='Annotation to look for (Default: ANNOTATION Environment Variable)')
    objParser.add_argument('--api_url',
                           required=False,
                           type=str,
                           default=os.environ.get('API_URL', None),
                           help='API URL I.E https://app.au1.sysdig.com (Default: API_URL Environment variable')
    objParser.add_argument('--team_config',
                           required=False,
                           type=str,
                           default=os.environ.get('TEAM_CONFIG', None),
                           help='Team config CSV (Default: TEAM_CONFIG Environment variable)')
    objParser.add_argument('--context_config',
                           required=False,
                           type=str,
                           default=os.environ.get('CONTEXT_CONFIG', None),
                           help='Context config file (Default: CONTEXT_CONFIG Environment variable)')
    objParser.add_argument('--silent',
                           action='store_true',
                           help='Run without user interaction (i.e do not prompt to proceed)')

    objArgs = objParser.parse_args()
    if objArgs.api_url is None or objArgs.team_config is None or objArgs.context_config is None:
        if objArgs.annotation and objArgs.label is None:
            objParser.parse_args(['--help'])
            exit(1)

    api_token = os.environ.get('SECURE_API_TOKEN')
    if api_token is not None:
        auth_header = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    else:
        print('Please set the SECURE_API_TOKEN environment variable to continue')
        exit(1)

    print(f"Processing Input File '{objArgs.team_config}'")
    with open(objArgs.team_config) as teamcsv:
        arrTeamConfig = list(csv.reader(teamcsv, delimiter=','))
        arrTeamConfig.pop(0)

    config.load_kube_config()
    with open(objArgs.context_config) as contextscsvfile:
        arrContextsConfig = list(csv.reader(contextscsvfile, delimiter=','))
        arrContextsConfig.pop(0)

    # Get Namespace Information
    for row in arrContextsConfig:
        if len(row) == 1:
            print(f"\nProcessing Context: '{row}'")
            v1 = client.CoreV1Api(api_client=config.new_client_from_config(context=row[0]))
            if objArgs.annotation is not None:
                get_namespace_annotations(objArgs.annotation)
            else:
                get_namespace_labels(objArgs.label)

    with open(file='todo.csv', mode='w', newline='') as todocsv:
        writer = csv.writer(todocsv, delimiter=',')
        writer.writerow(['Team Name', 'Team ID', 'Namespace'])
        for row in arrTeamConfig:
            if len(row) == 3:
                if objArgs.annotation is not None:
                    arrNamespaces = list({k: v for k, v in arrNSAnnotation.items() if v.startswith(row[2])}.keys())
                else:
                    arrNamespaces = list({k: v for k, v in arrNSLabels.items() if v.startswith(row[2])}.keys())
                for todo_row in arrNamespaces:
                    writer.writerow([row[0], row[1], todo_row])

    # Option to continue or not
    print(f"\n")
    if not objArgs.silent:
        print(f"'todo.csv' hss ben written to the current directory outlining the team -> namespace mapping.\nPlease review before proceeding")
        choice = click.prompt('\nWould you like to proceed with execution?: Y or N', default='N', type=click.STRING, prompt_suffix=' ')
        choice = validate_choice(None, None, choice)
        if choice == 'n':
            print(f"Action cancelled.  Exiting...")
            exit(1)
        confirm = click.confirm('Are you SURE you want to proceed?', default=False)
        if not confirm:
            print(f"Action cancelled.  Exiting...")
            exit(1)
    else:
        print(f"Running with --silent flag, continuing")

    print(f"\n")
    for row in arrTeamConfig:
        if len(row) == 3:
            if objArgs.annotation is not None:
                arrNamespaces = list({k: v for k, v in arrNSAnnotation.items() if v.startswith(row[2])}.keys())
                print(f"Processing Team: '{row[0]}, TeamID:'{row[1]}.  Looking for annotation: '{objArgs.annotation}={row[2]}', found in the following namespaces {arrNamespaces}")
            else:
                arrNamespaces = list({k: v for k, v in arrNSLabels.items() if v.startswith(row[2])}.keys())
                print(f"Processing Team: '{row[0]}, TeamID:'{row[1]}.  Looking for label: '{objArgs.label}={row[2]}', found in the following namespaces {arrNamespaces}")
            if len(arrNamespaces) !=0:
                team_url = f"{objArgs.api_url}/api/teams/{row[1]}"
                arrTeam = (sysdig_request(method='GET', url=team_url, headers=auth_header)).json()
                strFilter = ','.join(f'"{value}"' for value in arrNamespaces)
                arrPayload = build_payload(arr_team=arrTeam['team'], str_new_filter=strFilter)
                objResult = sysdig_request(method='PUT', url=team_url, headers=auth_header, _json=arrPayload)
                print(f"Update Result Code: {objResult.status_code}")
            else:
                print(f"No matching annotation/label. Skipping...")
