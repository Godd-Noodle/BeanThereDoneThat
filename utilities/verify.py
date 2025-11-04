from datetime import datetime,timedelta

from utilities.auth import generate_password_hash


#google package for checking phonenumbers
import phonenumbers





def check_password(password : str, current_user_password : str = None) -> list[str]:

    corrections = []

    if len(password) < 8:
        corrections.append("Password must be at least 8 characters long")
    if len(password) > 20:
        corrections.append("Password must be at most 20 characters long")
    if password == password.lower():
        corrections.append("Password must contain at least one uppercase letter")
    if password == password.upper():
        corrections.append("Password must contain at least one lowercase letter")

    hashed_password = generate_password_hash(current_user_password)

    if current_user_password and  hashed_password == current_user_password:
        corrections.append("Password and current user password are identical")

    return corrections

def check_location(lat : str, long : str):
    corrections = []
    if not lat or not long:
        corrections.append("Latitude and longitude must both be specified")

    try:
        lat = float(lat)

        if lat <= -90 or lat >= 90:
            corrections.append("Latitude is not between -90 and 90")

    except ValueError:
        corrections.append("Latitude is not valid")


    try:
        long = float(long)

        if long <= -180 or long >= 180:
            corrections.append("Longitude is not valid")

    except ValueError:
        corrections.append("Longitude is not between -180 and 180")



    return corrections


def check_name(names: [str]) -> list[str]:

    corrections = []

    small_names = [False for name in names if len(name) < 3]
    if False in small_names:
        corrections.append("Each name must be at least 3 characters long")

    long_names = [False for name in names if len(name) > 20]
    if False in long_names:
        corrections.append("Each name must be at most 20 characters long")

    is_all_upper = [False for name in names if not name.isupper()]
    if False in is_all_upper:
        corrections.append("Each name must contain at least one uppercase letter")

    if len(names) < 2:
        corrections.append("There must be at least 2 names")

    return corrections

def check_review(message: str) -> list[str]:

    corrections = []

    if not message:
        return ["message cannot be empty"]

    if len(message) < 3:
        corrections.append("Message must be at least 3 characters long")

    if len(message) > 50:
        corrections.append("Message must be at most 50 characters long")



    return corrections

def check_review_score(score: str) -> list[str]:

    corrections = []

    if not score:
        return ["Review score must not be empty"]

    if not score.isdigit():
        return ["Review score must be an integer"]

    if int(score) < 1:
        corrections.append("Review score must be at least 1")

    if int(score) > 5:
        corrections.append("Review score must be at most 5")

    return corrections



def check_date(year: int, month : int, day: int) -> bool:
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def check_dob(year: int | str, month : int | str, day: int | str) ->  str | list[str]:

    corrections = []

    if type(year) == str:
        try:
            year = int(year)

            if year in range(1900, datetime.today().year):
                corrections.append("Month must be an integer between 1-12")

        except ValueError:
            corrections.append("Year must be an integer")

    if type(month) == str:

        try:
            month = int(month)

            if month in range(1,12):
                corrections.append("Year must be an integer between 1900 and the current year")

        except ValueError:
            corrections.append("Year must be an integer")

    if type(day) == str:

        try:
            day = int(day)

            if day in range(1, 31):
                corrections.append("Day must be an integer between 1-31")

        except ValueError:
            corrections.append("Year must be an integer")

    if corrections:
        return corrections


    if not check_date(year, month, day):
        return "Not a valid date"

    if datetime(year, month, day) + timedelta(weeks=56*13) > datetime.now().date():
        return "User is too young to use this application"


def check_phone_number(phone : str) -> str | list[str]:
    if not phonenumbers.is_valid_number(phonenumbers.parse(phone)):
        return "Invalid phone number"