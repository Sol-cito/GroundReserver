import requests, calendar, json
from datetime import datetime


def login(loginInfo, session):
    URL = "http://www.futsalbase.com/api/login"
    params = {
        "id": loginInfo.get("id"),
        "password": loginInfo.get("password")
    }
    # activate session
    res = session.post(URL, params)
    print("[Login Response Code] : ", res.status_code)


def getDateList():
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
    return date_list


def searchAllAvailableFields(session):
    date_list = getDateList()
    field_list = ['A', 'B', 'C', 'D', 'E', 'H', 'I']

    for field in field_list:
        print(field)
        for date in date_list:
            URL = "http://www.futsalbase.com/api/reservation/allList/?stadium=" + field + "&date=" + date
            res = session.get(URL)
            if res.ok:
                for element in res.json().get('data'):
                    if 'szDInfo' not in element.keys():
                        print(element)
    print("----end")


if __name__ == '__main__':

    # TO-DO
    # 1. logger
    # 2. Kakao Notification
    # 3. actually making reservation

    LOGIN_INFO = {
        "id": "dataenggu",
        "password": "Solda9010!"
    }
    with requests.session() as session:
        login(LOGIN_INFO, session)
        searchAllAvailableFields(session)
