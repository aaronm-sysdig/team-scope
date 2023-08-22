# Disclaimer

Notwithstanding anything that may be contained to the contrary in your agreement(s) with Sysdig, Sysdig provides no support, no updates, and no warranty or guarantee of any kind with respect to these script(s), including as to their functionality or their ability to work in your environment(s).  Sysdig disclaims all liability and responsibility with respect to any use of these scripts.  

# Sysdig Team-Scope
Example python code that allows you to set an annotation or label on a namespace and then assign those namespaces to a team via a CSV file by scanning kubeconfig contexts specified in a configuration file.  Configuration of zones is also possible also.

NOTE: This script uses unsupported, undocumented APIs that may change at any point._


## teams.csv File format
Create a CSV file in with the following columns/rows
| Field | Mandatory? | Note |
| --- | --- | --- |
| Sysdig Team Name | Y | Team name in the platform.  Used for informational purposes only.  Not referred to in code |
| Sysdig Team ID | Y | Team ID to modify.  Easily obtained from the UI via Settings -> Teams |
| Annotation / Lanel Name | Y | Name of the annotation / label | 
| Annotation / Label | Y | The actual annotation / label you are looking for  |

### Example CSV entries - teams-annotation.csv
```
Sysdig Team Name,Sysdig Team ID,Annotation value to find,Value to find
Team1,40003969,my-annotation,a1
Team2,40003970,my-annotation,a2
Team3,40003971,my-annotation,a3
Team4,40003972,my-annotation,a4
Team5,40003973,my-annotation,a5
Team1,40003969,my-annotation-2,annotation2
```

### Example CSV entries - teams-label.csv
```
Sysdig Team Name,Sysdig Team ID,Label value to find,Value to find
Label Team,40003990,my-label,labeltest
```

## teams-zone.csv File format
Create a CSV file in with the following columns/rows to configure zones for your teams (MUST match the team id in your team config!!)
| Field | Mandatory? | Note |
| --- | --- | --- |
| Sysdig Team Name | Y | Team name in the platform.  Used for informational purposes only.  Not referred to in code |
| Sysdig Team ID | Y | Team ID to modify.  Easily obtained from the UI via Settings -> Teams |
| Sysdig Zone ID | T | The zone ID to associate with the team.  One per line but you can specify multiple |

### Example teams-zone.csv
```
Sysdig Team Name,Sysdig Zone ID
Team1,40003969,237960
Team1,40003969,249762
Team2,40003970,146701
Team3,40003971,235575
Team4,40003972,233407
Team5,40003973,291049
Team1,40003969,290818
Label Team,40003990,290818
```
## Command Help
```
usage: team-scope.py [-h] [--version] (--label | --annotation) --api-url API_URL --team-config TEAM_CONFIG --context-config CONTEXT_CONFIG [--zone-config ZONE_CONFIG] [--silent] [--debug]

team-scope.py 1.1.0 '--label' and '--annotation' are mutually exclusive. I.E specify one or the other

optional arguments:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --label, -l           Flag to denote looking for labels
  --annotation, -a      Flag to denote looking for annotations
  --api-url API_URL     API URL I.E https://app.au1.sysdig.com (Default: API_URL Environment variable
  --team-config TEAM_CONFIG, -t TEAM_CONFIG
                        Team config CSV (Default: TEAM_CONFIG Environment variable)
  --context-config CONTEXT_CONFIG, -c CONTEXT_CONFIG
                        Context config file (Default: CONTEXT_CONFIG Environment variable)
  --zone-config ZONE_CONFIG, -z ZONE_CONFIG
                        Context config file (Default: CONTEXT_CONFIG Environment variable)
  --silent, -s          Run without user interaction (i.e do not prompt to proceed)
  --debug, -d           Log Debug
```


## Environment Variables
If you don't want to set command line parameters, set the below environment variables instead
```
# Your Sysdig Secure API Token
export SECURE_API_TOKEN=1c708a83-e413-4c45-87fc-9df23a65142 

# Your Sysdig Secure region URL
export API_URL=https://app.au1.sysdig.com 

# Path to your defined csv file
export TEAM_CONFIG=./teams.csv

# Path to your defined zone csv file
export ZONE_CONFIG=./teams-zone.csv

# Your context file
export CONTEXT_CONFIG=./contexts.csv
```

## Requirements
requirements.txt is provided for pip3 dependency installation.
Dependencies are 
1) argparse
2) requests
3) kubernetes
```
pip3 install -r requirements.txt
```

## Example output - Interactive

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

## Example output - Silent
```
Processing Input File 'teams.csv'

Processing Context: '['aaron@kubernetes']'
 Retrieved annotations for namespaces

Processing Context: '['kubernetes-admin@kubernetes']'
 Retrieved annotations for namespaces


Running with --silent flag, continuing


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
```
