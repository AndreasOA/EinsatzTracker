import json
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from urllib.parse import unquote
from datetime import datetime
from time import sleep


def _notifyUser(url, msg):
        requests.get(url+msg).json()


def createDbElement(token: str, databaseId: str, enum: str, dueDate: str, fe_type: str, info: str, address: str, url: str) -> str:
    updateData = {
        "parent": {
            "database_id": databaseId
        },
        "properties": {
            "Enum": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": enum
                        }
                    }
                ]
            },
            "Date": {    
                "date": {
                "start": dueDate
                }
            },
            "Type": {
                "select": {
                    "name": fe_type
                }
            },
            "Info": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": info
                        }
                    }
                ]
            },
            "Addresse": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": address
                        }
                    }
                ]
            },
            "Maps": {
                "type": "url",
                "url": url
            }
        }
    }
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": "Bearer " + token,
        "accept": "application/json",
        "Notion-Version": "2022-06-28",
        "content-type": "application/json"
    }

    response = requests.post(url, json=updateData, headers=headers)

    return json.loads(response.text)


def readNotionDb(token, databaseId) -> dict:
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
    res = requests.post(readUrl, headers=headers)
    data = res.json()

    return data

def run(driver, data, url):
    try:
        driver.get('http://ooe.martinhochreiter.at/#current')
        driver.find_elements(By.CSS_SELECTOR, "[href='#current']")[-1].click()
        current = driver.find_element(By.ID, 'current')
        content = current.find_element(By.CLASS_NAME, 'content')
        open_tasks = content.find_elements(By.CLASS_NAME,'arrow')

        notionData = readNotionDb(data['notion']['token'], data['notion']['database_id'])
        notionData = notionData['results']

        for task in open_tasks:
            try:
                task_info = task.find_element(By.TAG_NAME, 'a').get_attribute("data-json")
            except:
                pass
            # Decode the URL
            decoded_str = unquote(task_info)
            # Parse the JSON
            task_data = json.loads(decoded_str)
            # Pretty-print the JSON
            task_id = task_data['num1']
            foundMatchingEvent = False

            for event in notionData:
                try:
                    task_id_notion = event['properties']['Enum']['title'][0]['text']['content']
                except TypeError:
                    task_id_notion= ''
                        
                if task_id_notion == task_id:
                    foundMatchingEvent = True
                    break
                        
            if not foundMatchingEvent:
                if task_data['einsatzart'] == 'BRAND':
                    msg_art = '🔥'
                elif task_data['einsatzart'] == 'PERSON':
                    msg_art = '👷'
                elif task_data['einsatzart'] == 'UNWETTER':
                    msg_art = '☁'
                    
                else:
                    msg_art = '❗'

                bezirk, ort = task_data['einsatzort'].split(' - ')
                if 'TECHNISCH' in task_data['einsatztyp']['text']:
                    msg_typ = 'Tech '
                elif 'BRAND' in task_data['einsatztyp']['text']:
                    msg_typ = 'Brand '
                else:
                    msg_typ = task_data['einsatztyp']['text'].capitalize()
                try:
                    typ_size = task_data['einsatztyp']['text'].split('"')[1].split('"')[0]
                    msg_typ += ' ' + typ_size.capitalize()
                except (ValueError, IndexError):
                    pass
                try:
                    msg_typ += ' | ' + task_data['einsatzsubtyp']['text'].capitalize()
                except (KeyError, AttributeError):
                    pass
                try:
                    address = task_data['adresse']['default'].capitalize()
                    address_notion = address + ', ' + ort.capitalize()
                except AttributeError:
                    address = 'N/A'
                try:
                    maps_tag = f'https://maps.google.com/?q={task_data["wgs84"]["lat"]},{task_data["wgs84"]["lng"]}'
                except:
                    maps_tag = ''

                # Parse input date string into datetime object
                dt = datetime.strptime(task_data['startzeit'], '%a, %d %b %Y %H:%M:%S %z')
                ret = createDbElement(data['notion']['token'], data['notion']['database_id'], task_id, str(dt), msg_art, msg_typ, address_notion, maps_tag)
                msg = f"{msg_art} {bezirk.upper()} ({ort.capitalize()}) \n Einsatz: {msg_typ} \n Adresse: {address} \n Maps: {maps_tag}"
                _notifyUser(url, msg)
    except:
        print("Overall Func Error")
        pass


f = open("credentials_fe.json")
data = json.load(f)
f.close()
t_api = data['telegram']['api_token']
t_id = data['telegram']['chat_id']
URL = f"https://api.telegram.org/bot{t_api}/sendMessage?chat_id={t_id}&text="

options = uc.ChromeOptions()
#options.add_argument("--headless=new")
options.add_argument("--disable-popup-blocking")
options.add_argument('--disable-notifications')
prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
options.add_experimental_option("prefs", prefs)
driver = uc.Chrome(options=options)

i = 0
while True:
    run(driver, data, URL)
    i += 1
    print(f"run {i}")
    sleep(300)











