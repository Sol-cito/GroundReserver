import requests, calendar, logging, time, json, os
from datetime import datetime

PROJECT_NAME = "Ground Reserver"
Logger = logging.getLogger(PROJECT_NAME)


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
    if not res.ok:
        Logger.error("Login fail")
        raise Exception('[Error] 로그인에 실패하였습니다. ID/Password를 다시 확인하세요.')
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


def searchAllAvailableFields(session, target_date, target_time):
    Logger.info("Execute searchAllAvailableFields()")
    date_list = getWeekendDateList() if not target_date else list(target_date)
    field_list = ['A', 'B', 'C', 'D', 'E', 'H', 'I']

    result_dictionary = {}

    for field in field_list:
        for date in date_list:
            URL = "http://www.futsalbase.com/api/reservation/allList/?stadium=" + field + "&date=" + date
            res = session.get(URL)
            if not res.ok: continue
            for element in res.json().get('data'):
                if 'szDInfo' not in element.keys():  # if not reserved
                    if target_date and str(element.get('ssdate')) not in target_date: continue
                    if target_time and not isTargetTimeIncluded(element.get('strtime'), target_time): continue
                    result_dictionary[field] = element
    Logger.info("AllAvailableFields Result : " + str(result_dictionary))
    Logger.info("End searchAllAvailableFields()")
    return result_dictionary


def isTargetTimeIncluded(available_time, target_time):
    return str(available_time).strip() in target_time


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


def executeReserver(LOGIN_INFO, target_date, target_time):
    setLogger()
    Logger.info("Program Start-------------")
    Logger.info(target_date)
    Logger.info(target_time)

    while 1:
        try:
            print("Start-------------")
            with requests.session() as session:
                szId = login(LOGIN_INFO, session)

                result_dictionary = searchAllAvailableFields(session, target_date, target_time)

                if result_dictionary:
                    reserveGround(result_dictionary, szId, session)
        except Exception:
            Logger.info("Program End with Error")
            raise Exception('[Error] 구장 예약에 실패하였습니다. 개발자에게 문의하세요.')
        finally:
            print("--End--")
            Logger.info("Program End-------------")
            time.sleep(10)


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


def openLoginFile(LOGIN_INFO):
    f = None
    try:
        f = open('login.txt')
        lineCnt = 0
        for line in f:
            if lineCnt == 0:
                LOGIN_INFO["id"] = line.strip()
            elif lineCnt == 1:
                LOGIN_INFO["password"] = line.strip()
            lineCnt += 1
        if lineCnt < 1:
            raise Exception('[Error] login.txt 파일을 다시 확인해주세요.')
    except Exception as e:
        raise Exception('[Error] login.txt 파일을 다시 확인해주세요.')
    finally:
        if f:
            f.close()


if __name__ == '__main__':
    LOGIN_INFO = {
    }

    try:
        openLoginFile(LOGIN_INFO)

        target_date = set([
            '2022-05-14'
        ])

        target_time = set([
            # '04:00 ~ 06:00',  # for test
            '09:00 ~ 11:00',
            '10:00 ~ 12:00',
            '11:00 ~ 13:00',
            '12:00 ~ 14:00',
            '13:00 ~ 15:00',
            '14:00 ~ 16:00',
            '15:00 ~ 17:00',
            '16:00 ~ 18:00',
            '17:00 ~ 19:00',
            '18:00 ~ 20:00',
        ])

        executeReserver(LOGIN_INFO, target_date, target_time)
    except Exception as E:
        print(E)
