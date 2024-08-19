from playwright.sync_api import sync_playwright
from datetime import datetime
from lib.SendNotification import SendNotification
from lib.Logger import Logger
from lib.CXDB import CXDB
from lib.CXWC import CXWC
from time import sleep
import yaml
import threading


def oneclickcall_test(playwright):
    result = 'PASSED'

    time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    har_filename1 = f'oneclickcall_staff_{time_stamp}.zip'
    har_filename2 = f'oneclickcall_visitor_{time_stamp}.zip'
    video1 = har_filename1.replace('.zip', '.webm')
    video2 = har_filename2.replace('.zip', '.webm')
    browser1 = CXDB(playwright, har_filename1, lgr)
    browser2 = CXWC(playwright, har_filename2, lgr)
    flag = [True]
    ping_thread = threading.Thread(target=browser1.ping_record, args=(cxdb_url[8:], flag))
    ping_thread.start()

    try:
        # Staff log in and navigate to workspace. Visitor opens CXWC widget, meanwhile will trigger one-click call
        browser1.login_cxdb(cxdb_url, staff1, password)
        sleep(3)
        browser1.check_announcement()
        browser1.goto_workspace(cxdb_url)

        browser2.open_widget(cxwc_url)

        # Staff picks up the call
        browser1.page.locator('[data-testid="call-answer"]').click()

        # Staff checks whether end call button is in call view, if False then throw exception
        sleep(5.0)
        if not (browser1.page.locator('[data-testid="call-end"]').is_visible()):
            raise Exception("Call was not successfully picked up by Staff.")

        # Wait for 10 seconds, and visitor side ends the call
        sleep(10.0)
        browser2.page.frame_locator(CXWC.WIDGET_IFRAME).locator('[data-testid="call-end"]').click()

        # Staff and visitor checks whether call view was dismissed after call-end, if False then throw exception
        sleep(5.0)
        if not browser2.page.frame_locator(CXWC.WIDGET_IFRAME).locator('[data-testid="agent-call"]').is_visible():
            raise Exception("Call was not successfully ended.")

        # Staff close the enquiry
        browser1.staff_close_inquiry()

    except Exception as e:
        result = 'FAILED'
        lgr.error(str(e))
        browser1.page.screenshot(path=f'screens/oneclickcall_s1_{time_stamp}.png')
        browser2.page.screenshot(path=f'screens/oneclickcall_s2_{time_stamp}.png')
        browser1.send_remote_log()
        # browser2.send_remote_log()

    finally:
        # stop ping
        flag[0] = False
        ping_thread.join()

        if result == 'FAILED':
            browser1.context.close()  # close context to save har
            browser2.context.close()  # close context to save har
            sleep(1)
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
                sn = SendNotification('send_notification_jack')
                notification = f'Monitor - One-click Call Test Failed'
                notification += f'\nHAR file:\n\t{har_filename1}\n\t{har_filename2}'
                notification += f'\nVideo file:\n\t{video1}\n\t{video2}'
                response = sn.send_notification(notification)
            except Exception as e:
                lgr.error('Send notification failed.')
                lgr.error(response.json())


if __name__ == '__main__':
    # test environment info
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['one_click_call']
    log_name = config['log_name']
    cxdb_url = config['cxdb_url']
    cxwc_url = config['cxwc_url']
    staff1 = config['staff1']
    password = config['password']

    lgr = Logger(log_name).logger
    lgr.info('-'*20 + 'Start running.' + '-'*20)

    with sync_playwright() as playwright:
        oneclickcall_test(playwright)
