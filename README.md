## Aegis Utils
This repo is used to keep utilities used in Aegis project

### Initialization
To install all dependant packages, please execute below command:
```console
# pip install -r requirements.txt
```

### Utility get_account_status.py
This utility is used to query Account Status API in batch. To check the usage of this utility:
```console
# ./get_account_status.py -h
usage:
        $ python {} -i <input_file_path> -o <output_file_path>

        The `input_file_path` point to a file which contains easy_id per line
        The `output_file_path` point to a file to hold the query result

Toolkit to query aegis account status API in batch
...
``` 
