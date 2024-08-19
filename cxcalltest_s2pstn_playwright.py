from playwright.sync_api import sync_playwright
from lib.SendNotification import SendNotification
from time import sleep, time
import yaml
import pyperclip
import random
from datetime import datetime
from lib.Logger import Logger
from lib.CXDB import CXDB
import threading
import sys

def select_pstn_number(hang_up_seconds):
    ## Randomly select a pstn number
    number_list_greater_than_100 = ['223831000', '266166000', '24122222',
                                    '225523111', '44499888', '280731166']
    # *223214311-中華郵政, *24128077-安泰銀行, *221821313-玉山銀行, 223831000-國泰世華
    # 266166000-滙豐銀行, 226553355-台新銀行, *221811111-第一銀行
    # *280239088-渣打銀行, *221711055-新光銀行, 24122222-彰化銀行, *225168518-台灣樂天
    # *227775488-華泰銀行, *280239088-凱基銀行, 225523111-上海銀行, 223577171-臺灣企銀
    # 44499888-台中商銀, 280731166-遠東銀行, 266129889-星展銀行, 24128077-安泰銀行, 223577171-臺灣企銀,
    # * 30未能接通頻率較高，先移除
    number_list_less_than_60 = ['223831000', '266166000', '24122222', '225523111',
                                '44499888', '280731166', '227458080', '221821988',
                                '221810103', '223146633', '228220122', '266129889']
    # 227458080-中國信託, 221821988-元大銀行, 221810103-華南銀行, 223146633-土地銀行, 228220122-陽信銀行
    # 266129889-星展銀行
    if hang_up_seconds >= 60:
        return random.choice(number_list_greater_than_100)
    else:
        return random.choice(number_list_less_than_60)

def callmonitoring(playwright):
    result = 'PASSED'
    db_duration_locator = 'css=[data-testid="call-timer"]'
    wc_duration_locator = 'css=[data-testid="call-profile-ci-call-status-content"]'
    call_end_button = 'css=[data-testid="call-end"]'

    time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    har_filename1 = f'calltest_s2pstn_staff_{time_stamp}.zip'
    video1 = har_filename1.replace('.zip', '.webm')
    call_log_available = False
    total_sleep_time = 0
    pstn_number = ''
    call_id = ''

    browser1 = CXDB(playwright, har_filename1, lgr)
    # flag = [True]
    # ping_thread = threading.Thread(target=browser1.ping_record, args=(cxdb_url[8:], flag))
    # ping_thread.start()

    try:
        browser1.login_cxdb(cxdb_url, staff1, password)
        # For prod announcement
        browser1.check_announcement()
        # For prod announcement
        browser1.goto_workspace(cxdb_url)
        sleep(3.0)
        pstn_number = select_pstn_number(hang_up_seconds)

        browser1.make_offnet_call_via_dialpad(country_code='886', phone_number = pstn_number)
        sleep(3.0)
        call_log_available = browser1.db_verify_whether_offnet_is_connected("Browser1")   # check duration
        assert call_log_available
        # Fetch the current duration after picked up
        total_sleep_time = int(browser1.page.text_content(db_duration_locator)[3:5])
        # Check if the call still alive before time up
        while True:
            if not browser1.page.is_visible(db_duration_locator):
                lgr.info(f'Call ended before 100 seconds timeout at {total_sleep_time} second')
                assert False
            else:
                sleep(1.0)
                if browser1.page.is_visible(db_duration_locator):
                    time_str = browser1.page.text_content(db_duration_locator)
                    try:
                        time_obj = datetime.strptime(time_str, '%M:%S')
                        total_sleep_time = time_obj.minute * 60 + time_obj.second
                    except:
                        lgr.info(f"Unable to parse the last time string: {time_str}")
                else:
                    lgr.info(f"db_duration_locator couldn't be found")
                    assert False
                # total_sleep_time += 1
                lgr.info(f'The call is last {total_sleep_time} seconds.')

            if total_sleep_time >= hang_up_seconds:
                browser1.db_action_in_audio_callview('EndCall')
                lgr.info(f'Call duration exceeds {hang_up_seconds} seconds, hang up call.')
                break

        lgr.info(f'Finish script running. Staff call PSTN:{pstn_number} passed')

    except AssertionError:
        result = 'FAILED'
        browser1.page.screenshot(path=f'screens/{time_stamp}_calltest_s2pstn_staff_failed.png')
        if call_log_available == True:
            browser1.open_call_log(callee=False, get_call_id=True)
            call_id = pyperclip.paste()
            lgr.error(f'Assertion failed. Call ID: {call_id}')
        browser1.send_remote_log()

    except Exception as e:
        result = 'FAILED'
        browser1.page.screenshot(path=f'screens/{time_stamp}_calltest_s2pstn_staff_failed.png')
        if call_log_available == True:
            browser1.open_call_log(callee=False, get_call_id=True)
            call_id = pyperclip.paste()
            lgr.error(f'Assertion failed. Call ID: {call_id}')
        lgr.error(str(e))
        browser1.send_remote_log()

    finally:
        # stop ping
        # flag[0] = False
        # ping_thread.join()

        if result == "FAILED":
            browser1.context.close()  # close context to save har
            sleep(1)
            browser1.video_rename(video1)
        else:
            browser1.remove_ping_record()

        browser1.close()  # close browser
        sleep(1)
        browser1.video_remove()  # remove video if result is not FAILED
        response = None
        if result == 'FAILED':
            try:
                sn = SendNotification('send_notification_jesse')
                if call_log_available == True:
                    response = sn.send_notification(f'Monitor - Call test (staff to PSTN:{pstn_number}) failed at {total_sleep_time} second:\ncall id: {call_id}\n{har_filename1}')
                else:
                    response = sn.send_notification(f'Monitor - Call test (staff to PSTN:{pstn_number}) failed at {total_sleep_time} second:\n{har_filename1}')
                lgr.info(f'Result: {result}')
            except Exception as e:
                lgr.error('Send notification failed.')
                lgr.error(response)
        else:
            lgr.info(f'Result: {result}')


if __name__ == '__main__':
    # get argv
    if len(sys.argv) < 2:
        print('please give argument for calling time in seconds.')
        sys.exit()
    if sys.argv[1] == 'random':
        hang_up_seconds = random.choice([30, 60, 90])
    else:
        hang_up_seconds = int(sys.argv[1])

    # test environment info
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['call_s2pstn']
    log_name = config['log_name']
    cxdb_url = config['cxdb_url']
    cxwc_url = config['cxwc_url']
    staff1 = config['staff1']
    staff_name1 = config['staff_name1']
    password = config['password']

    lgr = Logger(log_name).logger
    lgr.info('-'*20 + 'Start running.' + '-'*20)

    with sync_playwright() as playwright:
        callmonitoring(playwright)
