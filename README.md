# Disclaimer

Notwithstanding anything that may be contained to the contrary in your agreement(s) with Sysdig, Sysdig provides no support, no updates, and no warranty or guarantee of any kind with respect to these script(s), including as to their functionality or their ability to work in your environment(s).  Sysdig disclaims all liability and responsibility with respect to any use of these scripts.  

# Sysdig Team-Scope
Example python code that allows you to set an annotation or label on a namespace and then assign those namespaces to a team via a CSV file by scanning kubeconfig contexts specified in a configuration file

_NOTE: This script uses unsupported, undocumented API's that may change at any point._


## teams.csv File format
Create a CSV file in with the following columns/rows
| Field | Mandatory? | Note |
|---|---|---|
| Sysdig Team Name | Y | Team name in the platform.  Used for informational purposes only.  Not referred to in code |
| Sysdig Team ID | Y | Team ID to modify.  Easily obtained from the UI via Settings -> Teams |
| Annotation / Label | Y | The actual annotation you are looking for  |

### Example CSV enteries
```
Sysdig Team Name,Sysdig Team ID,Annotation/Label value to find
Team1,40004969,a1
Team2,40004970,a2
Team3,40004971,a3
Team4,40004972,a4
Team5,40004973,a5
Label Team,40004990,labeltest
```


## Command Help
```
usage: team-scope.py [-h] (--label LABEL | --annotation ANNOTATION) [--api_url API_URL] [--team_config TEAM_CONFIG] [--context_config CONTEXT_CONFIG]

"label" and "annotation" are mutually exclusive. I.E specify one or the other

options:
  -h, --help            show this help message and exit
  --label LABEL         Label to look for (Default: LABEL Environment Variable)
  --annotation ANNOTATION
                        Annotation to look for (Default: ANNOTATION Environment Variable)
  --api_url API_URL     API URL I.E https://app.au1.sysdig.com (Default: API_URL Environment variable
  --team_config TEAM_CONFIG
                        Team config CSV (Default: TEAM_CONFIG Environment variable)
  --context_config CONTEXT_CONFIG
                        Context config file (Default: CONTEXT_CONFIG Environment variable)
```


## Environment Variables
If you dont want to set command line parameters, set the below environment variables instead

```
# Your Sysdig Secure API Token
export SECURE_API_TOKEN=1c708a83-e413-4c45-87fc-9df23a65142 

# Max # of Days from today that the expiration in the CSV is allowed to be in the future
export ANNOTATION=an_annotation
or
export LABEL=a_label

# Your Sysdig Secure region URL
export API_URL=https://app.au1.sysdig.com 

# Path to your defined csv file
export TEAM_CONFIG=./teams.csv

# Your context file
export CONTEXT_CONFIG=./contexts.csv
```

## Requirements
requirements.txt is provided for pip3 dependency installation.
Dependencies are 
1) argparse
2) requests
3) kubernetes
4) click
```
pip3 install -r requirements.txt
```


## Usage (assuming using anotation command line parameter).
*nb: SECURE_API_TOKEN needs to be an environment variable*
```
team-scope.py --annotation <annotation to find> --team_config <CSV file> --api_url <API_URL> --context_config
```

## Usage (assuming using label command line parameter).
*nb: SECURE_API_TOKEN needs to be an environment variable*
```
team-scope.py --label <label to find> --team_config <CSV file> --api_url <API_URL> --context_config context.txt
```

## Example output

```
Processing Input File 'teams.csv'

Processing Context: '['aaron@kubernetes']'
 Retrieved annotations for namespaces

Processing Context: '['kubernetes-admin@kubernetes']'
 Retrieved annotations for namespaces

'todo.csv' hss ben written to the current directory outlining the team -> namespace mapping.
Please review before proceeding

Would you like to proceed with execution?: Y or N [N]
Are you SURE you want to proceed? [y/N]:
```

_enter Y or N to either execute or cancel_

```

Processing Team: 'Team1, TeamID:'40003969.  Looking for annotation: 'my-annotation=a1', found in the following namespaces ['n1', 'n1-1']
Update Result Code: 200
Processing Team: 'Team2, TeamID:'40003970.  Looking for annotation: 'my-annotation=a2', found in the following namespaces ['n2', 'n2-1']
Update Result Code: 200
Processing Team: 'Team3, TeamID:'40003971.  Looking for annotation: 'my-annotation=a3', found in the following namespaces ['n3', 'n3-1']
Update Result Code: 200
Processing Team: 'Team4, TeamID:'40003972.  Looking for annotation: 'my-annotation=a4', found in the following namespaces ['n4', 'n4-1']
Update Result Code: 200
Processing Team: 'Team5, TeamID:'40003973.  Looking for annotation: 'my-annotation=a5', found in the following namespaces ['n5', 'n5-1', 'n5-2', 'n5-3']
Update Result Code: 200
Processing Team: 'Label Team, TeamID:'40003990.  Looking for annotation: 'my-annotation=labeltest', found in the following namespaces []
No matching annotation/label. Skipping...

Process finished with exit code 0
```
