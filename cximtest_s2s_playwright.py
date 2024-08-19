from playwright.sync_api import sync_playwright
from datetime import datetime
from lib.SendNotification import SendNotification
from lib.Logger import Logger
from lib.CXDB import CXDB
import yaml
from time import sleep
import threading


def im_test(playwright):
    result = 'PASSED'

    time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    har_filename1 = f'imtest_s2s_staff1_{time_stamp}.zip'
    har_filename2 = f'imtest_s2s_staff2_{time_stamp}.zip'
    video1 = har_filename1.replace('.zip', '.webm')
    video2 = har_filename2.replace('.zip', '.webm')
    browser1 = CXDB(playwright, har_filename1, lgr)
    browser2 = CXDB(playwright, har_filename2, lgr)
    flag = [True]
    ping_thread = threading.Thread(target=browser1.ping_record, args=(cxdb_url[8:], flag))
    ping_thread.start()

    try:
        # log in and navigate to workspace
        browser1.login_cxdb(cxdb_url, staff1, password)
        browser2.login_cxdb(cxdb_url, staff2, password)
        sleep(3)
        browser1.check_announcement()
        browser2.check_announcement()
        # browser1.page.evaluate("window.sessionStorage.forceRegion='prod-hk-01';")
        # browser1.page.reload()
        # browser2.page.evaluate("window.sessionStorage.forceRegion='prod-hk-01';")
        # browser2.page.reload()
        browser1.goto_workspace(cxdb_url)
        browser2.goto_workspace(cxdb_url)

        # staff1 search the chatroom
        browser1.search_staff_chatroom(staff2_name)

        # staff1 send message and validation
        message = f'message sent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        browser1.send_msg_to_staff(staff2_name, message)
        browser2.page.click(f'text={staff1_name}')      # select staff1's chatroom
        sleep(2)
        browser1.verify_the_last_msg(message, receiver=False)
        browser2.verify_the_last_msg(message, receiver=True)
        sleep(5)  # prevent the display order incorrect

        # staff2 send PNG and validation
        file_path = f'testdata/test.png'
        browser2.send_image_to_staff(staff1_name, file_path)
        sleep(2)
        browser2.verify_the_last_image(file_path, receiver=False)
        browser1.verify_the_last_image(file_path, receiver=True)
        sleep(5)  # prevent the display order incorrect

        # staff1 send file and validation
        file_path = f'testdata/test.txt'
        browser1.send_file_to_staff(staff2_name, file_path)
        sleep(2)
        browser1.verify_the_last_file(file_path, receiver=False)
        browser2.verify_the_last_file(file_path, receiver=True)
        sleep(5)  # prevent the display order incorrect

        # staff2 send audio note and validation
        browser2.send_audio_note_to_staff(staff1_name, 5)
        sleep(2)
        browser2.verify_the_last_audio_note(receiver=False)
        browser1.verify_the_last_audio_note(receiver=True)

    except AssertionError:
        result = 'FAILED'
        lgr.error('assertion failed.')
        browser1.page.screenshot(path=f'screens/im_s2s_s1_{time_stamp}.png')
        browser2.page.screenshot(path=f'screens/im_s2s_s2_{time_stamp}.png')
        browser1.send_remote_log()
        browser2.send_remote_log()

    except Exception as e:
        result = 'FAILED'
        lgr.error(str(e))
        browser1.page.screenshot(path=f'screens/im_s2s_s1_{time_stamp}.png')
        browser2.page.screenshot(path=f'screens/im_s2s_s2_{time_stamp}.png')
        browser1.send_remote_log()
        browser2.send_remote_log()

    finally:
        # stop ping
        flag[0] = False
        ping_thread.join()

        if result == 'FAILED':
            browser1.context.close()    # close context to save har
            browser2.context.close()    # close context to save har
            sleep(1)
            browser1.video_rename(video1)
            browser2.video_rename(video2)
        else:
            browser1.remove_ping_record()

        browser1.close()        # close browser
        browser2.close()        # close browser
        sleep(1)
        browser1.video_remove()     # remove video if result is not FAILED
        browser2.video_remove()     # remove video if result is not FAILED
        lgr.info(f'Result: {result}')

        response = None
        if result == 'FAILED':
            try:
                sn = SendNotification('send_notification_rick')
                notification = f'Monitor - IM test (staff to staff) failed at {time_stamp.replace("_", " ")}'
                notification += f'\nhar:\n\t{har_filename1}\n\t{har_filename2}'
                notification += f'\nvideo:\n\t{video1}\n\t{video2}'
                response = sn.send_notification(notification)
            except Exception as e:
                lgr.error('Send notification failed.')
                lgr.error(response)

if __name__ == '__main__':
    # test environment info
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['im_s2s']
    log_name = config['log_name']
    cxdb_url = config['cxdb_url']
    staff1 = config['staff1']
    staff1_name = config['staff1_name']
    staff2 = config['staff2']
    staff2_name = config['staff2_name']
    password = config['password']

    lgr = Logger(log_name).logger
    lgr.info('-'*20 + 'Start running.' + '-'*20)

    with sync_playwright() as playwright:
        im_test(playwright)
