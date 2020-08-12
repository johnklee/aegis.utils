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
You can store easy id in a file (each line as an easy id) `easy_id_list.txt` and use this utility to do batch query as below:
```console
// Check content of input file. The line with prefix '#' will be ignored during process
$ head -n 3 easy_id_list.txt
10002
# test
1000000000000000000000000000000000

// Save querying result to file output.json and error message to err.json
$ ./get_account_status.py -i easy_id_list.txt -o output.json -e err.json
MainThread/INFO: <./get_account_status.py#224> Request URL=http://localhost:8080/status
MainThread/INFO: <./get_account_status.py#231> Total 167 easy id being loaded...
MainThread/DEBUG: <./get_account_status.py#99> 4 worker being created...
MainThread/INFO: <./get_account_status.py#258> Exit with execution time=0:00:01.013373!

// Check content of output.json
$ head -n 4 output.json
[
    {
        "easy_id": 10002,
        "reset": "2018-01-01T03:00:00Z",

// Check content of err.json
$ head -n 4 err.json
[
    {
        "easy_id": 1000000000000000000000000000000000,
        "error": "status code=400"
```
