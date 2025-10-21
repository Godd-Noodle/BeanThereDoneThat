from datetime import datetime,timedelta

from utilities.auth import generate_password_hash





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
