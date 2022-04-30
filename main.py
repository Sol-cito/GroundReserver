import requests, calendar, logging, time, json, re
from datetime import datetime

PROJECT_NAME = "Ground Reserver"
Logger = logging.getLogger(PROJECT_NAME)
LOGIN_FILE = 'login.txt'
TARGET_DATE_FILE = 'targetDate.txt'
TARGET_TIME_FILE = 'targetTime.txt'
LOGIN_ERROR_MESSAGE_NO_USER = '등록되지 않은 사용자입니다.'
LOGIN_ERROR_MESSAGE_INVALID_PASSWORD = '비밀번호가 일치하지 않습니다.'


def setLogger():
    Logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s] %(levelname)s / %(message)s"
    )

    file_handler = logging.FileHandler(filename="info.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    Logger.addHandler(file_handler)


def login(loginInfo, session):
    Logger.info("Execute login()")
    URL = "http://www.futsalbase.com/api/login"
    params = {
        "id": loginInfo.get("id"),
        "password": loginInfo.get("password")
    }
    # activate session
    res = session.post(URL, params)
    Logger.info('Login Response Code : ' + str(res.status_code))
    if res.json().get('message') == LOGIN_ERROR_MESSAGE_NO_USER:
        Logger.error("Login fail")
        raise ValueError('[Error] 등록되지 않은 사용자입니다. ID를 다시 확인하세요.')
    elif res.json().get('message') == LOGIN_ERROR_MESSAGE_INVALID_PASSWORD:
        Logger.error("Login fail")
        raise ValueError('[Error] 비밀번호가 일치하지 않습니다. Password를 다시 확인하세요.')
    elif not res.ok:
        Logger.error("Login fail")
        raise ValueError('[Error] 로그인에 실패하였습니다. ID/Password를 다시 확인하세요.')
    Logger.info("End login()")
    return res.json().get("user").get("szId")


def getWeekendDateList():
    Logger.info("Execute getDateList()")
    targetYear = datetime.today().year
    targetMonth = datetime.today().month + 1
    if targetMonth == 1: targetYear += 1

    targetMonthInfo = calendar.monthrange(targetYear, targetMonth)

    # 5 and 6 are sat, sun respectively
    date_firstSaturday = abs(5 - targetMonthInfo[0]) if targetMonthInfo[0] < 6 else 6
    date_firstSunday = abs(6 - targetMonthInfo[0])
    days = targetMonthInfo[1]

    date_list = []
    for i in range(date_firstSaturday, days, 7):
        date_list.append(
            str(datetime.strptime(str(targetYear) + "-" + str(targetMonth) + "-" + str(i + 1), "%Y-%m-%d").date()))
    for i in range(date_firstSunday, days, 7):
        date_list.append(
            str(datetime.strptime(str(targetYear) + "-" + str(targetMonth) + "-" + str(i + 1), "%Y-%m-%d").date()))
    Logger.info("Result : " + str(date_list))
    Logger.info("End getDateList()")
    return date_list


def searchAllAvailableFields(session, TARGET_DATE, TARGET_TIME):
    Logger.info("Execute searchAllAvailableFields()")
    date_list = getWeekendDateList() if not TARGET_DATE else list(TARGET_DATE)
    field_list = ['A', 'B', 'C', 'D', 'E', 'H', 'I']

    result_dictionary = {}

    for field in field_list:
        for date in date_list:
            URL = "http://www.futsalbase.com/api/reservation/allList/?stadium=" + field + "&date=" + date
            res = session.get(URL)
            if not res.ok: continue
            for element in res.json().get('data'):
                if 'szDInfo' not in element.keys():  # if not reserved
                    if TARGET_DATE and str(element.get('ssdate')) not in TARGET_DATE: continue
                    if TARGET_TIME and not isTargetTimeIncluded(element.get('strtime'), TARGET_TIME): continue
                    result_dictionary[field] = element
    Logger.info("AllAvailableFields Result : " + str(result_dictionary))
    Logger.info("End searchAllAvailableFields()")
    return result_dictionary


def isTargetTimeIncluded(available_time, TARGET_TIME):
    return str(available_time).strip() in TARGET_TIME


def reserveGround(result_dictionary, szId, session):
    Logger.info("Start reserveGround()")

    URL = "http://www.futsalbase.com/api/reservation/addList"

    for availableField in result_dictionary.keys():
        params = {
            "szId": szId,
            "szStadium": availableField,
            "szDDate": result_dictionary.get(availableField).get('ssdate'),
            "seletedList": [result_dictionary.get(availableField)]
        }
        res = session.post(URL, json=params)

        sendKakaoMessageToMe(
            '풋살장 빈 시간대 (' + str(result_dictionary.get(availableField).get('ssdate')) + ' ' +
            str(result_dictionary.get(availableField).get('strtime')) + ') 발견하여 예약 Post 요청 보냄')

        Logger.info('Reservation Response Code : ' + str(res.status_code))
        if res.ok:
            sendKakaoMessageToMe('풋살장 예약 성공!!!!!!!!!!!!')
            Logger.info("Reservation Success : " + str(result_dictionary.get(availableField)))
            print('풋살장 예약 성공!!!!!!!!!!!!')
            print('예약 시간 : ', str(result_dictionary.get(availableField)))
        else:
            sendKakaoMessageToMe('풋살장 예약 실패--------')
            Logger.error("Reservation Fail ")
            Logger.error("Fail Code : " + str(res.status_code))
        break
    Logger.info("End reserveGround()")


def executeReserver(LOGIN_INFO, TARGET_DATE, TARGET_TIME):
    setLogger()
    Logger.info("Program Start-------------")
    print("Crawling start.....")
    Logger.info(TARGET_DATE)
    Logger.info(TARGET_TIME)

    while 1:
        try:
            with requests.session() as session:
                szId = login(LOGIN_INFO, session)

                result_dictionary = searchAllAvailableFields(session, TARGET_DATE, TARGET_TIME)

                if result_dictionary:
                    reserveGround(result_dictionary, szId, session)
            time.sleep(10)
        except ValueError as e:
            Logger.info("Program End with Error")
            raise Exception(e)
        except Exception as e:
            Logger.info("Program End with Error")
            raise Exception('[Error] 구장 예약에 실패하였습니다. 개발자에게 문의하세요.')
        finally:
            Logger.info("Crawling End-------------")


def sendKakaoMessageToMe(inputText):
    with open("kakaoKeyInfo.json", "r") as file:
        kakaoKeyJsonData = json.load(file)

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    headers = {
        "Authorization": "Bearer " + kakaoKeyJsonData.get('access_token')
    }

    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": inputText,
            "link": {
                "web_url": "http://www.futsalbase.com/home",
                "mobile_web_url": "http://www.futsalbase.com/home",
            }
        })
    }

    response = requests.post(url, headers=headers, data=data)
    if response.json().get('result_code') == 0:
        Logger.info('Successfully sent kakao message')
    else:
        Logger.error('Kakao message fail ' + str(response.json()))


def readLoginFile(LOGIN_INFO):
    f = None
    try:
        f = open(LOGIN_FILE)
        lineCnt = 0
        for line in f:
            if lineCnt == 0:
                LOGIN_INFO["id"] = line.strip()
            elif lineCnt == 1:
                LOGIN_INFO["password"] = line.strip()
            lineCnt += 1
        if lineCnt < 1:
            raise ValueError()
    except ValueError:
        raise Exception('[Error] ID or PASSWORD가 누락되었습니다.', LOGIN_FILE, '파일을 다시 확인해주세요.')
    except Exception:
        raise Exception('[Error] ', LOGIN_FILE, '파일을 다시 확인해주세요.')
    finally:
        if f:
            f.close()


def readTargetDateFile(TARGET_DATE):
    f = None
    try:
        f = open(TARGET_DATE_FILE)
        regax = r'\d{4}-\d{2}-\d{2}$'
        for line in f:
            if not bool(re.match(regax, line.strip())):
                raise ValueError()
            TARGET_DATE.add(line.strip())
    except ValueError:
        raise Exception("[Error] 날짜 형식이 'xxxx-xx-xx'가 아닙니다.", TARGET_DATE_FILE, " 파일을 다시 확인해주세요.")
    except Exception as e:
        raise Exception('[Error] ', TARGET_DATE_FILE, ' 파일을 다시 확인해주세요.')
    finally:
        if f:
            f.close()


def readTargetTimeFile(TARGET_TIME):
    f = None
    try:
        f = open(TARGET_TIME_FILE)
        regax = r'\d{2}:\d{2} ~ \d{2}:\d{2}$'
        for line in f:
            if not bool(re.match(regax, line.strip())):
                raise ValueError()
            TARGET_TIME.add(line.strip())
    except ValueError:
        raise Exception("[Error] 시간 형식이 'xx:xx ~ xx:xx'가 아닙니다.", TARGET_TIME_FILE, " 파일을 다시 확인해주세요.")
    except Exception as e:
        print(e)
        raise Exception('[Error] ', TARGET_TIME_FILE, ' 파일을 다시 확인해주세요.')
    finally:
        if f:
            f.close()


if __name__ == '__main__':
    LOGIN_INFO = {}
    TARGET_DATE = set([])
    TARGET_TIME = set([])

    try:
        readLoginFile(LOGIN_INFO)
        readTargetDateFile(TARGET_DATE)
        readTargetTimeFile(TARGET_TIME)

        executeReserver(LOGIN_INFO, TARGET_DATE, TARGET_TIME)
    except Exception as E:
        print(E)
