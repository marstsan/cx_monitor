from playwright.sync_api import sync_playwright
from datetime import datetime
from lib.SendNotification import SendNotification
from lib.Logger import Logger
from lib.CXDB import CXDB
from lib.CXWC import CXWC
from time import sleep
import yaml


def weblinkchat_test(playwright):
    result = 'PASSED'

    time_stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    har_filename1 = f'weblinkchat_staff_{time_stamp}.zip'
    har_filename2 = f'weblinkchat_visitor_{time_stamp}.zip'
    video1 = har_filename1.replace('.zip', '.webm')
    video2 = har_filename2.replace('.zip', '.webm')
    browser1 = CXDB(playwright, har_filename1, lgr)
    browser2 = CXWC(playwright, har_filename2, lgr)

    try:
        # Staff log in and navigate to workspace. Visitor opens CXWC widget, meanwhile will trigger one-click call
        browser1.login_cxdb(cxdb_url, staff1, password)
        sleep(3)
        browser1.check_announcement()
        browser1.goto_workspace(cxdb_url)

        browser2.page.goto(weblink_url)
        #browser2.page.locator('[data-testid="engage-button"]').click()
        browser2.page.locator('[data-testid="engage-chat-button"]').click()

        # Staff picks up the enquiry
        browser1.pick_up_chat_inquiry()

        # Staff checks whether end call button is in call view, if False then throw exception
        sleep(5.0)
        if not (browser1.page.locator('[data-testid="chatroom-editor"]').is_visible()) and not (browser2.page.frame_locator(CXWC.WIDGET_IFRAME).locator('[data-testid="chat-message"]').is_visible()):
            raise Exception("Chat enquiry was not successfully picked up by Staff.")

        # Staff closes the enquiry
        browser1.staff_close_inquiry()

    except Exception as e:
        result = 'FAILED'
        lgr.error(str(e))
        browser1.page.screenshot(path=f'screens/webclickchat_s1_{time_stamp}.png')
        browser2.page.screenshot(path=f'screens/webclickchat_s2_{time_stamp}.png')
        browser1.send_remote_log()
        # browser2.send_remote_log()

    finally:
        if result == 'FAILED':
            browser1.context.close()  # close context to save har
            browser2.context.close()  # close context to save har
            sleep(1)
            browser1.video_rename(video1)
            browser2.video_rename(video2)

        browser1.close()  # close browser
        browser2.close()  # close browser
        sleep(1)
        browser1.video_remove()  # remove video if result is not FAILED
        browser2.video_remove()  # remove video if result is not FAILED
        lgr.info(f'Result: {result}')
        response = None
        if result == 'FAILED':
            try:
                sn = SendNotification('send_notification_jack')
                notification = f'Monitor - Weblink Chat Test Failed'
                notification += f'HAR file:\n\t{har_filename1}\n\t{har_filename2}'
                notification += f'\nVideo file:\n\t{video1}\n\t{video2}'
                response = sn.send_notification(notification)
            except Exception as e:
                lgr.error('Send notification failed.')
                lgr.error(response.json())


if __name__ == '__main__':
    # test environment info
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['weblink_chat']
    log_name = config['log_name']
    cxdb_url = config['cxdb_url']
    weblink_url = config['weblink_url']
    staff1 = config['staff1']
    password = config['password']

    lgr = Logger(log_name).logger
    lgr.info('-'*20 + 'Start running.' + '-'*20)

    with sync_playwright() as playwright:
        weblinkchat_test(playwright)
