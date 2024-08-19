from playwright.sync_api import sync_playwright
from lib.SendNotification import SendNotification
from time import sleep, time
import yaml
import pyperclip
from datetime import datetime
from lib.Logger import Logger
from lib.CXDB import CXDB
import threading
import sys


def callmonitoring(playwright):
    result = 'PASSED'
    db_duration_locator = 'css=[data-testid="call-timer"]'
    wc_duration_locator = 'css=[data-testid="call-profile-ci-call-status-content"]'
    call_end_button = 'css=[data-testid="call-end"]'

    time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    har_filename1 = f'calltest_s2s_staff1_{time_stamp}.zip'
    har_filename2 = f'calltest_s2s_staff2_{time_stamp}.zip'
    video1 = har_filename1.replace('.zip', '.webm')
    video2 = har_filename2.replace('.zip', '.webm')
    total_sleep_time = 0
    call_id = ''
    browser1 = CXDB(playwright, har_filename1, lgr)
    browser2 = CXDB(playwright, har_filename2, lgr)
    call_log_available = False
    # flag = [True]
    # ping_thread = threading.Thread(target=browser1.ping_record, args=(cxdb_url[8:], flag))
    # ping_thread.start()

    try:
        browser1.login_cxdb(cxdb_url, staff1, password)
        browser2.login_cxdb(cxdb_url, staff2, password)
        sleep(3.0)
        # For prod announcement
        browser1.check_announcement()
        browser2.check_announcement()
        # For prod announcement

        browser1.goto_workspace(cxdb_url)
        browser2.goto_workspace(cxdb_url)
        browser2.make_an_onnet_call_to_staff(staff_name1)
        call_log_available = browser1.staff_pick_up_call()  # call log is available in the chatroom once the call is picking up
        assert call_log_available
        # Fetch the current duration after picked up
        call_log_available = browser2.db_verify_whether_call_is_connected('Browser2')
        assert call_log_available
        total_sleep_time = int(browser2.page.text_content(db_duration_locator)[3:5])
        # Check if the call still alive before time up
        while True:
            if not browser1.page.is_visible(db_duration_locator) or not browser2.page.is_visible(db_duration_locator):
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

        lgr.info('Finish script running. Staff call Staff passed')

    except AssertionError:
        result = 'FAILED'
        browser1.page.screenshot(path=f'screens/{time_stamp}_calltest_s2s_staff1_failed.png')
        browser2.page.screenshot(path=f'screens/{time_stamp}_calltest_s2s_staff2_failed.png')
        if call_log_available == True:
            browser2.open_call_log(callee=False, get_call_id=True)
            call_id = pyperclip.paste()
            lgr.error(f'Assertion failed. Call ID: {call_id}')
        browser1.send_remote_log()
        browser2.send_remote_log()

    except Exception as e:
        result = 'FAILED'
        browser1.page.screenshot(path=f'screens/{time_stamp}_calltest_s2s_staff1_failed.png')
        browser2.page.screenshot(path=f'screens/{time_stamp}_calltest_s2s_staff2_failed.png')
        if call_log_available == True:
            browser2.open_call_log(callee=False, get_call_id=True)
            call_id = pyperclip.paste()
            lgr.error(f'Assertion failed. Call ID: {call_id}')
        lgr.error(str(e))
        browser1.send_remote_log()
        browser2.send_remote_log()

    finally:
        # stop ping
        # flag[0] = False
        # ping_thread.join()

        if result == "FAILED":
            browser1.context.close()  # close context to save har
            browser2.context.close()  # close context to save har
            sleep(1)
            browser1.video_rename(video1)
            browser2.video_rename(video2)
        else:
            browser1.remove_ping_record()

        browser1.close()  # close browser
        browser2.close()  # close browser
        sleep(1)
        browser1.video_remove()  # remove video if result is not FAILED
        browser2.video_remove()  # remove video if result is not FAILED
        response = None
        if result == 'FAILED':
            try:
                sn = SendNotification('send_notification_jesse')
                if call_log_available == True:
                    response = sn.send_notification(f'Monitor - Call test (staff to staff) failed at {total_sleep_time} second:\nCall ID: {call_id}\n{har_filename1}\n{har_filename2}')
                else:
                    response = sn.send_notification(f'Monitor - Call test (staff to staff) failed at {total_sleep_time} second: \n{har_filename1}\n{har_filename2}')
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
    hang_up_seconds = int(sys.argv[1])

    # test environment info
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['call_s2s']
    log_name = config['log_name']
    cxdb_url = config['cxdb_url']
    cxwc_url = config['cxwc_url']
    staff1 = config['staff1']
    staff_name1 = config['staff_name1']
    staff2 = config['staff2']
    staff_name2 = config['staff_name2']
    password = config['password']

    lgr = Logger(log_name).logger
    lgr.info('-'*20 + 'Start running.' + '-'*20)

    with sync_playwright() as playwright:
        callmonitoring(playwright)
