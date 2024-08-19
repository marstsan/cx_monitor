import logging

from playwright.sync_api import sync_playwright
from datetime import datetime
from lib.SendNotification import SendNotification
from lib.Logger import Logger
from lib.CXDB import CXDB
import yaml
from time import sleep


def clean_imtest_files(playwright):
    lgr = Logger('clean_imtest_files').logger
    time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    har_filename = f'clean_{time_stamp}.zip'
    browser1 = CXDB(playwright, har_filename, lgr)

    try:
        # staff log in and navigate to workspace
        browser1.login_cxdb(cxdb_url, staff, password)
        browser1.goto_workspace(cxdb_url)

        # navigate to storage page
        browser1.page.goto(f'{cxdb_url}/#/setting/storage/')
        browser1.page.click('div.MuiTabs-flexContainer > button:nth-child(2)')      # select chat file tab
        sleep(2)
        browser1.page.click('thead.MuiTableHead-root > tr > th:nth-child(1) > span')    # check the checkbox for all row
        sleep(2)
        browser1.page.click('thead.MuiTableHead-root > tr > div button')        # click Delete
        browser1.page.click('[data-testid="confirm-button"]')      # click OK
        sleep(2)

    except Exception as e:
        logging.error(e)

    finally:
        browser1.close()
        sleep(1)
        browser1.video_remove()


if __name__ == '__main__':
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['im_v2s']
    log_name = config['log_name']
    cxdb_url = config['cxdb_url']
    staff = config['staff']
    staff_name = config['staff_name']
    password = config['password']

    with sync_playwright() as playwright:
        clean_imtest_files(playwright)