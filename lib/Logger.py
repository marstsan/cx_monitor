import logging, pathlib, yaml
from datetime import datetime


class Logger:
    def __init__(self, file_name, level=logging.INFO):
        config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['logger']
        log_folder = config['log_folder']
        har_folder = config['har_folder']
        # create required folders
        self.create_folder(log_folder)
        self.create_folder(har_folder)
        self.create_folder('screens')
        self.create_folder('ping_record')

        # config logger
        file_path = f'{log_folder}/{file_name}_{datetime.today().strftime("%Y-%m-%d")}.txt'
        logging.basicConfig(filename=file_path, encoding='utf-8', format='[%(asctime)s] [%(levelname)5s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        self.logger = logging.getLogger()
        self.logger.setLevel(level)

    @staticmethod
    def create_folder(folder_name):
        pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True)

