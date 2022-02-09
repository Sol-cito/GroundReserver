import requests, calendar, logging, time
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
        raise Exception
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
        Logger.info('Reservation Response Code : ' + str(res.status_code))
        if res.ok:
            Logger.info("Reservation Success : " + str(result_dictionary.get(availableField)))
        else:
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
        except Exception as e:
            Logger.info("Program End with Error")
        finally:
            print("--End--")
            Logger.info("Program End-------------")
            time.sleep(10)


if __name__ == '__main__':
    LOGIN_INFO = {
        "id": "dataenggu",
        "password": "Solda9010!"
    }

    target_date = set([
        '2022-03-26'
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
