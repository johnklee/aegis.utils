#!/usr/bin/env python
'''
This utility is used to query account status API in batch
'''
import json
import sys
import os
import requests
import logging
import coloredlogs
import argparse
import multiprocessing
import threading
import time
import queue
from tqdm import tqdm
from datetime import datetime


################################
# Constants
################################
MODU_PATH = os.path.dirname(__file__) if os.path.dirname(__file__) else './'
''' Path of current module '''

LOGGER_FORMAT = "%(threadName)s/%(levelname)s: <%(pathname)s#%(lineno)s> %(message)s"
''' Format of Logger '''

LOGGER_LEVEL = 10  # CRITICAL=50; ERROR=40; WARNING=30; INFO=20; DEBUG=10
''' Message level of Logger '''

API_HOST = 'http://localhost'
''' API host '''

API_PORT = 8080
''' API host port '''

API_STATUS_PATH = 'status'
''' API Status Path '''


################################
# Class
################################
class MyThreadGroup:
    '''
    Thread Group use to manage created threads

    Attributes
    ----------
    logger: logging.Logger
        Logger used to show message in console
    api_url: str
        API URL to query
    target: function
        Target function to be executed in thread
    input_datas: queue.Queue
        queue to retrieve input data
    output_datas: list
        used to hold process result
    err_datas: list
        used to hold error result

    '''
    def __init__(self, logger, api_url, target, input_datas, output_datas, err_datas):
        self.threads = []
        self.api_url = api_url
        self.logger = logger
        self.target = target
        self.input_datas = input_datas
        self.output_datas = output_datas
        self.err_datas = err_datas
        self.num_input_data = input_datas.qsize()

    @property
    def num_thread(self):
        '''
        Number of created thread
        '''
        return len(self.threads)

    def new_thread(self, num_thread):
        r'''
        Create given number of thread

        Parameters
        ----------
        num_thread: int
            The number of thread to create
        '''
        for _ in range(num_thread):
            thd = threading.Thread(
                target=self.target,
                name='worker_{}'.format(self.num_thread+1),
                args=(self.api_url, self.input_datas, self.output_datas, self.err_datas, self.logger)
            )
            self.threads.append(thd)

        self.logger.debug("{:,d} worker being created...".format(num_thread))

    def start(self):
        '''
        Start the created thread(s)
        '''
        for thd in self.threads:
            thd.start()

    def is_alive(self):
        '''
        Check if the created thread(s) are still alive or not

        Returns
        -------
        True if there is at least one thread is still alive; False otherwise.
        '''
        return False if len(self.threads) == 0 else any([thd.is_alive() for thd in self.threads])

    def join(self):
        '''
        Join all created threads and will only return when all created thread(s) are done.
        '''
        while self.is_alive():
            time.sleep(1)

    def tqdm(self):
        ''' Launch progress bar to show work status'''
        if self.is_alive() and self.num_input_data > 0:
            pbar = tqdm(total=self.num_input_data)
            rest_data_num = self.num_input_data
            while self.is_alive():
                time.sleep(0.1)
                new_rest_data_num = self.input_datas.qsize()
                consumed_num, rest_data_num = rest_data_num - new_rest_data_num, new_rest_data_num
                pbar.update(consumed_num)

            pbar.update(rest_data_num)
            pbar.close()

        print("")


################################
# Global Variables
################################
logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(LOGGER_LEVEL)
logger.propagate = False
coloredlogs.install(
    level=LOGGER_LEVEL,
    logger=logger,
    fmt=LOGGER_FORMAT)


def parse_args():
    ''' Parsing command line argument(s) '''
    parser = argparse.ArgumentParser(
        usage='''
        $ python {} -i <input_file_path> -o <output_file_path>

        The `input_file_path` point to a file which contains easy_id per line
        The `output_file_path` point to a file to hold the query result''',
        description='Toolkit to query aegis account status API in batch'
    )

    parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file to load in easy id. (default:%(default)s)')
    parser.add_argument('-o', '--output', type=str, default=None, help='Path of output file to store querying result. If not given, the result will be printed out to standard output')
    parser.add_argument('-e', '--error', type=str, default=None, help='Path of output file to store error message. If not given, the result will be printed out to standard output')
    parser.add_argument('--api_host', default=API_HOST, help='API Host to send request to. (default:%(default)s)')
    parser.add_argument('--api_port', type=int, default=API_PORT, help='API port. (default:%(default)s)')
    parser.add_argument('--api_status_path', type=str, default=API_STATUS_PATH, help='API path to query. (default:%(default)s)')
    parser.add_argument('--num_thread', type=int, default=multiprocessing.cpu_count(), help='Number of thread for parallelism. (default:%(default)s)')
    parser.add_argument('-s', '--show_status', action='store_true', default=False, help='Show progress bar')
    return parser.parse_args()


def query_account_status(api_url, input_datas, output_datas, err_datas, logger):
    '''
    Target function to query Account Status API

    Parameters
    ----------
    api_url: str
        API URL
    input_datas: queue.Queue
        queue to retrieve easy id
    output_datas: list
        place to store processing result
    err_datas: list
        place to store error message
    logger: logging.Logger
        Logger used to show message in console
    '''
    while not input_datas.empty():
        try:
            eid = input_datas.get()
            data = {"easy_id": int(eid)}
            # logger.debug("Process easy id={}...".format(eid))
            resp = requests.post(api_url, json=data)
            if resp.status_code == 200:
                data.update(resp.json())
                output_datas.append(data)
            else:
                data["error"] = "status code={}".format(resp.status_code)
                err_datas.append(data)
        except requests.exceptions.ConnectionError as e: # pylint: disable=invalid-name
            err_datas.append({"easy_id": eid, "error": str(e)})
        except Exception as e: # pylint: disable=invalid-name
            logger.exception("Something wrong: {}".format(e))
            if eid:
                err_datas.append({"easy_id": eid, "error": str(e)})


if __name__ == '__main__':
    st = datetime.now()
    args = parse_args()

    # 0) Evaluation input argument
    if not os.path.isfile(args.input):
        logger.error('Input file=%s does not exist!\n', args.input)
        sys.exit(1)

    # 1) Compose query URL
    request_url = "{}:{}/{}".format(args.api_host, args.api_port, args.api_status_path) # pylint: disable=invalid-name
    logger.info("Request URL=%s", request_url)

    # 2) Loading easy id list
    input_data_queue = queue.Queue()
    with open(args.input, 'r') as fh:
        _ = [input_data_queue.put(v) for v in filter(lambda e: not e.startswith("#"), map(lambda e: e.strip(), fh.readlines()))]

    logger.info("Total {:,d} easy id being loaded...".format(input_data_queue.qsize()))

    # 3) Start working
    output_datas = []
    err_datas = []
    tg = MyThreadGroup(logger, request_url, query_account_status, input_data_queue, output_datas, err_datas)
    tg.new_thread(args.num_thread)
    tg.start()
    if args.show_status:
        tg.tqdm()
    else:
        tg.join()

    # 4) Output
    if not args.output:
        logger.info("Collection of output datas ({:,d}):\n{}\n\n".format(len(output_datas), json.dumps(output_datas, indent=4)))
    else:
        with open(args.output, 'w') as fw:
            fw.write(json.dumps(output_datas, indent=4))

    if err_datas:
        if not args.error:
            logger.info("Collection of err datas ({:,d}):\n{}\n\n".format(len(err_datas), json.dumps(err_datas, indent=4)))
        else:
            with open(args.error, 'w') as fw:
                fw.write(json.dumps(err_datas, indent=4))

    logger.info("Exit with execution time=%s!\n", str(datetime.now() - st))
