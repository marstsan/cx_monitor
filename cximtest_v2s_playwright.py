from playwright.sync_api import sync_playwright
from datetime import datetime
from lib.SendNotification import SendNotification
from lib.Logger import Logger
from lib.CXDB import CXDB
from lib.CXWC import CXWC
import yaml
from time import sleep
import threading


def im_test(playwright):
    result = 'PASSED'

    time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    har_filename1 = f'imtest_v2s_staff_{time_stamp}.zip'
    har_filename2 = f'imtest_v2s_visitor_{time_stamp}.zip'
    video1 = har_filename1.replace('.zip', '.webm')
    video2 = har_filename2.replace('.zip', '.webm')
    browser1 = CXDB(playwright, har_filename1, lgr)
    browser2 = CXWC(playwright, har_filename2, lgr)
    flag = [True]
    ping_thread = threading.Thread(target=browser1.ping_record, args=(cxdb_url[8:], flag))
    ping_thread.start()

    inquery_picked_up = 0
    try:
        # staff log in and navigate to workspace
        browser1.login_cxdb(cxdb_url, staff, password)
        sleep(3)
        browser1.check_announcement()
        # browser1.page.evaluate("window.sessionStorage.forceRegion='prod-hk-01';")
        # browser1.page.reload()
        browser1.goto_workspace(cxdb_url)

        # visitor launch CXWC and start a chat inquiry with staff
        browser2.open_widget(cxwc_url)
        # browser2.page.evaluate("window.sessionStorage.forceRegion='prod-hk-01';")
        # browser2.page.reload()
        browser2.direct_chat_to_staff(staff_name)

        # staff pick up the chat inquiry
        browser1.pick_up_chat_inquiry()
        inquery_picked_up = 1
        sleep(5)    # wait 5 seconds to prevent the system prompt lately.

        # visitor send message to staff and validation
        message = f'message sent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        browser2.send_message(message)
        browser2.verify_the_last_message(message)
        sleep(2)
        browser1.verify_the_last_msg(message, receiver=True)
        sleep(5)  # prevent the display order incorrect

        # visitor send image to staff and validation
        file_path = 'testdata/test.png'
        browser2.send_image(file_path)
        browser2.verify_the_last_image(file_path)
        sleep(2)
        browser1.verify_the_last_image(file_path, receiver=True)
        sleep(5)    # prevent the display order incorrect

        # visitor send file to staff and validation
        file_path = 'testdata/test.txt'
        browser2.send_file(file_path)
        browser2.verify_the_last_file(file_path)
        sleep(2)
        browser1.verify_the_last_file(file_path, receiver=True)
        sleep(5)    # prevent the display order incorrect

        # visitor send audio note and validation
        browser2.send_audio_note(5)
        browser2.verify_the_last_audio_note()
        sleep(2)
        browser1.verify_the_last_audio_note(receiver=True)

    except AssertionError:
        result = 'FAILED'
        lgr.error('assertion failed.')
        browser1.page.screenshot(path=f'screens/im_v2s_s_{time_stamp}.png')
        browser2.page.screenshot(path=f'screens/im_v2s_v_{time_stamp}.png')
        browser1.send_remote_log()
        # browser2.send_remote_log()    # no remote log in WC

    except Exception as e:
        result = 'FAILED'
        lgr.error(str(e))
        browser1.page.screenshot(path=f'screens/im_v2s_s_{time_stamp}.png')
        browser2.page.screenshot(path=f'screens/im_v2s_v_{time_stamp}.png')
        browser1.send_remote_log()
        # browser2.send_remote_log()    # no remote log in WC

    finally:
        if inquery_picked_up == 1:
            # staff close the inquiry
            try:
                browser1.staff_close_inquiry()
            except Exception as e:
                result = 'FAILED'
                lgr.error(str(e))
                browser1.send_remote_log()

        # stop ping
        flag[0] = False
        ping_thread.join()

        if result == 'FAILED':
            browser1.context.close()  # close context to save har
            browser2.context.close()  # close context to save har
            browser1.video_rename(video1)
            browser2.video_rename(video2)
        else:
            browser1.remove_ping_record()

        browser1.close()        # close browser
        browser2.close()        # close browser
        sleep(1)
        browser1.video_remove()  # remove video if result is not FAILED
        browser2.video_remove()  # remove video if result is not FAILED
        lgr.info(f'Result: {result}')
        response = None
        if result == 'FAILED':
            try:
                sn = SendNotification('send_notification_rick')
                notification = f'Monitor - IM test (visitor to staff) failed at {time_stamp.replace("_", " ")}'
                notification += f'\nhar:\n\t{har_filename1}\n\t{har_filename2}'
                notification += f'\nvideo:\n\t{video1}\n\t{video2}'
                response = sn.send_notification(notification)
            except Exception as e:
                lgr.error('Send notification failed.')
                lgr.error(response)


if __name__ == '__main__':
    # test environment info
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['im_v2s']
    log_name = config['log_name']
    cxdb_url = config['cxdb_url']
    cxwc_url = config['cxwc_url']
    staff = config['staff']
    staff_name = config['staff_name']
    password = config['password']

    lgr = Logger(log_name).logger
    lgr.info('-'*20 + 'Start running.' + '-'*20)

    with sync_playwright() as playwright:
        im_test(playwright)
