import subprocess
import os
import json
import requests

def create_xlsx_to_csv(file_to_copy):
    '''
    :param 1: source = should be filename with the path.
    '''
    # take the backup of 'file_to_copy' using "bkp_" as a prefix.
    source = file_to_copy
    head_tail = os.path.split(source)
    dest_path = head_tail[0]
    dest_filename = head_tail[1]
    dest = dest_path + '/' + 'bkp_' + dest_filename
    # print(dest)
    cmd = 'cp "%s" "%s"' % (source, dest)
    print(cmd)
    copyfile = subprocess.call(cmd, shell=True)

def read_file(file):
    file_to_read = file
    print(file_to_read)

def send_tele_json(json_file):
    """
    function will be called by the parent function to send json file data to telegram.
    :param json_file: json file name that needs to be parsed and sent to the telegram user.
    :return: telegram notification to the user.
    """
    file_to_read = json_file
    print(file_to_read)
    with open(file_to_read, 'r') as f:
        data = json.load(f)
        print(data)
        for item in data:
            stock = item['symbol']
            Previous_Close = item['previousClose']
            Today_Open = item['iep']
            Difference_of = item['change']
            if Today_Open > Previous_Close:
                gap = "GapUp"
                print(gap)
            else:
                gap = "GapDown"
                print(gap)
            message = f"Gap: {gap}\nStock: {stock}\n Close: {Previous_Close}, Open: {Today_Open}\n Difference: {Difference_of} Points\n\t"
            print(message)
            url = 'https://api.telegram.org/bot149641496:AAH-W_uuVD5ANZ4ugU-eIotwOlPAkB7hU/sendMessage?chat_id=<CHAT_ID>&text="{}"'.format(message)
            requests.get(url)

def send_tele_msg(msg):
    """
    function will be called by the parent function to send "messages/notification" to telegram.
    :param msg: the message to notify the user.
    :return: telegram message.
    """
    msg = msg
    # print(message)
    url = 'https://api.telegram.org/bot11641496:AAH-W_uuVD5AthNugU-eIotwOlPAkB7hU/sendMessage?chat_id=<CHAT_ID>&text={}'.format(msg)
    # url = 'https://api.telegram.org/bot1491641496:AAH-W_uuVD5AthNZ4ugU-eIotwOlPAkB7hU/sendMessage?chat_id=-610218234&text=test123'
    return requests.get(url)

