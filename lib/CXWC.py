import logging

from playwright.sync_api import sync_playwright, Page
from time import sleep, time
import yaml
import shutil
from pathlib import Path
import os

class CXWC:
    WIDGET_IFRAME = '[data-testid="wc-iframe"]'
    WIDGET_ICON = '[data-testid="mcwc-widget"]'
    SEARCH_FIELD = '[data-testid="tag-search"]'
    DIRECTORY_TAG = '[data-testid="directory-type-tag"]'
    AGENT_CHAT = '[data-testid="agent-chat"]'
    AGENT_CALL = '[data-testid="agent-call"]'
    DIRECTORY_STAFF = '[data-testid="directory-type-staff"]'
    VISITOR_FORM_SUBMIT_BTN = '[data-testid="visitor-form-submit"]'
    CHATROOM_INPUT_FIELD = '[data-testid="chat-message"]'
    CHATROOM_SEND_MSG_BTN = '[data-testid="send-im"]'
    CHATROOM_UPLOAD_FILE = '[data-testid="file-upload"]'
    CHATROOM_AUDIO_NOTE = '[data-testid="send-audio"]'
    CHATROOM_AUDIO_NOTE_DONE = '[data-testid="record-done"]'
    CHATROOM_CLOSE = '[data-testid="close-room"]'
    CHATROOM_CLOSE_CONFIRM = '[data-testid="close-inquiry-confirm"]'

    def __init__(self, playwright: sync_playwright, har_filename, logger):
        config_log = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)['logger']
        har_folder = config_log['har_folder']
        self.lgr = logger
        self.videos_path = 'videos'
        size1 = {'width': 1920, 'height': 900}      # window size for testing
        size2 = {'width': 1536, 'height': 720}      # window size for video recording, file size reduce 1/2
        browser_args = ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream','--no-sandbox', '--disable-gpu', '--disable-extensions']
        self.browser = playwright.chromium.launch(headless=False, args=browser_args, channel='chrome')
        self.context = self.browser.new_context(record_video_dir=self.videos_path, viewport=size1, record_har_path=f'{har_folder}/{har_filename}', record_har_content='embed', record_video_size=size2)
        self.page = self.context.new_page()
        self.page.on('console', self.on_console)
        self.video_name = self.page.video.path()    # get video filename generated by playwright

    def on_console(self, console_message):
        if console_message.type == 'error':
            self.lgr.error(f"console {console_message.type}: {console_message.text}")
        elif console_message.type == 'warning':
            self.lgr.warning(f"console {console_message.type}: {console_message.text}")
        else:
            self.lgr.info(f"console {console_message.type}: {console_message.text}")

    def video_rename(self, new_name):
        shutil.move(self.video_name, Path(self.videos_path).joinpath(new_name))     # file rename

    def video_remove(self):
        if os.path.exists(self.video_name):     # check file exists
            os.remove(self.video_name)

    def open_widget(self, cxwc_url):
        self.page.goto(cxwc_url)
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.WIDGET_ICON).click()
        sleep(5)
        try_times = 0
        try_max_times = 3
        while try_times < try_max_times:
            if self.page.frame_locator(self.WIDGET_IFRAME).locator(self.VISITOR_FORM_SUBMIT_BTN).is_visible(timeout=5):
                self.page.frame_locator(self.WIDGET_IFRAME).locator(self.VISITOR_FORM_SUBMIT_BTN).click()     # close pre-chat form if visible
                break
            elif try_times != try_max_times-1:
                logging.info(f'retry to find pre-chat form submit button {try_times+1} times')
                try_times += 1
                sleep(5)
            else:
                logging.error(f'pre-chat form loading over {try_max_times*5} seconds')
                # assert False
                break
        self.lgr.info('<visitor> open the CXWC widget')

    def direct_chat_to_staff(self, staff_name):
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.DIRECTORY_STAFF).click()    # click directory icon
        sleep(2)
        if self.page.frame_locator(self.WIDGET_IFRAME).locator(self.SEARCH_FIELD).is_visible(timeout=5):
            self.page.frame_locator(self.WIDGET_IFRAME).locator(self.SEARCH_FIELD).fill(staff_name)     # input staff name in search field if visible
        self.page.frame_locator(self.WIDGET_IFRAME).locator(f'text={staff_name}').click()       # click on staff name
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.AGENT_CHAT).click()      # click chat icon
        self.lgr.info(f'<visitor> start a direct chat to <{staff_name}>')
        sleep(3)

    def direct_call_to_staff(self, staff_name):
        self.page.frame_locator(self.WIDGET_IFRAME).locator('[data-testid="directory-type-staff"]').click()    # click directory icon
        sleep(2)
        if self.page.frame_locator(self.WIDGET_IFRAME).locator(self.SEARCH_FIELD).is_visible(timeout=5):
            self.page.frame_locator(self.WIDGET_IFRAME).locator(self.SEARCH_FIELD).fill(staff_name)     # input staff name in search field if visible
        self.page.frame_locator(self.WIDGET_IFRAME).locator(f'text={staff_name}').click()       # click on staff name
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.AGENT_CALL).click()      # click chat icon
        self.lgr.info(f'visitor start a direct call to {staff_name}')
        sleep(3)

    def send_message(self, message):
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_INPUT_FIELD).fill(message)      # input message
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_SEND_MSG_BTN).click()     # click send button
        self.lgr.info('<visitor> send message to staff.')
        sleep(5)

    def verify_the_last_message(self, message):
        locator = 'div.scroll-content > div > div > :last-child [data-testid="message-sender-text-content"]'
        if message == self.page.frame_locator(self.WIDGET_IFRAME).locator(locator).text_content():
            self.lgr.info('message validation passed.')
        else:
            self.lgr.info('message validation failed.')
            assert False

    def send_image(self, file_path):
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_UPLOAD_FILE).set_input_files(file_path)
        self.lgr.info('<visitor> send image to staff.')
        sleep(5)

    def verify_the_last_image(self, file_path):
        locator = 'div.scroll-content > div > div > :last-child img'
        if file_path.split('/')[-1] == self.page.frame_locator(self.WIDGET_IFRAME).locator(locator).get_attribute('alt'):
            self.lgr.info('image validation passed.')
        else:
            self.lgr.info('image validation failed.')
            assert False

    def send_file(self, file_path):
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_UPLOAD_FILE).set_input_files(file_path)
        self.lgr.info('<visitor> send file to staff.')
        sleep(5)

    def verify_the_last_file(self, file_path):
        # locator = 'div.scroll-content > div > div > :last-child [data-testid="im-file-download-icon-btn"] > :last-child > :first-child'
        locator = '//*[@data-testid="im-file-download-icon-btn"]/../../div/p[1]'
        if file_path.split('/')[-1] == self.page.frame_locator(self.WIDGET_IFRAME).locator(locator).text_content():
            self.lgr.info('file validation passed.')
        else:
            self.lgr.info('file validation failed.')
            assert False

    def send_audio_note(self, seconds):
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_AUDIO_NOTE).click()
        sleep(seconds)
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_AUDIO_NOTE_DONE).click()
        self.lgr.info('<visitor> send audio note')
        sleep(5)

    def verify_the_last_audio_note(self):
        locator = 'div.scroll-content > div > div > :last-child [data-testid="message-sender-audio-content"]'
        if self.page.frame_locator(self.WIDGET_IFRAME).locator(locator).is_visible():
            self.lgr.info('audio note validation passed.')
        else:
            self.lgr.info('audio note validation failed.')
            assert False

    # def verify_whether_call_is_alive(self, timeout=10):
    #     call_is_alive = False
    #     duration_locator = 'css=[icon="callOutgoing"] > span'
    #     duration_min = self.page.frame_locator(self.WIDGET_IFRAME).locator(duration_locator).text_content()[0:2]
    #     duration_sec = self.page.frame_locator(self.WIDGET_IFRAME).locator(duration_locator).text_content()[3:5]
    #     while (not duration_min.isdigit()):
    #         timeout -= 1
    #         sleep(1.0)
    #         duration_min = self.page.frame_locator(self.WIDGET_IFRAME).locator(duration_locator).text_content()[0:2]
    #         duration_sec = self.page.frame_locator(self.WIDGET_IFRAME).locator(duration_locator).text_content()[3:5]
    #         if timeout == 0:
    #             if self.page.frame_locator(self.WIDGET_IFRAME).locator('css=[data-testid="call-end"]').is_visiable():
    #                 self.page.frame_locator(self.WIDGET_IFRAME).locator('css=[data-testid="call-end"]').click()
    #             self.lgr.info('The call is not connected')
    #             assert False
    #         call_is_alive = True
    #         if int(duration_min) == 0:
    #             self.lgr.info(f'Verified the call is connected')
    #         else:
    #             self.lgr.info(f'The call is last for {duration_min}:{duration_sec}')
    #
    #     return call_is_alive

    def wc_verify_whether_call_is_connected(self, browserName, timeout=30):
        call_log_available = False
        wc_duration_locator = 'css=[data-testid="call-profile-ci-call-status-content"]'
        for _ in range(timeout):
            duration_min = self.page.frame_locator(self.WIDGET_IFRAME).locator(wc_duration_locator).text_content()[0:2]
            duration_sec = self.page.frame_locator(self.WIDGET_IFRAME).locator(wc_duration_locator).text_content()[3:5]
            if duration_min.isdigit() and duration_sec.isdigit():
                self.lgr.info(f'{browserName}: Call duration >>> {duration_min}:{duration_sec}')
                call_log_available = True
                break

            if not call_log_available:
                self.lgr.info(f'{browserName}: Waiting for pickup...')
            sleep(1.0)

        if not call_log_available:
            self.lgr.info(f'{browserName}: Call is not connected.')

        return call_log_available

    def visitor_close_inquiry(self):
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_CLOSE).click()      # close X icon
        self.page.frame_locator(self.WIDGET_IFRAME).locator(self.CHATROOM_CLOSE_CONFIRM).click()   # click Close button
        self.lgr.info('<visitor> close the inquiry')

    def close(self):
        self.browser.close()
