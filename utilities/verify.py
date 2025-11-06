from datetime import datetime, timedelta
from utilities.auth import generate_password_hash
import phonenumbers


def check_password(password: str, current_user_password: str = None) -> list[str]:
    corrections = []

    if len(password) < 8:
        corrections.append("Password must be at least 8 characters long")
    if len(password) > 20:
        corrections.append("Password must be at most 20 characters long")
    if password == password.lower():
        corrections.append("Password must contain at least one uppercase letter")
    if password == password.upper():
        corrections.append("Password must contain at least one lowercase letter")

    if current_user_password:
        hashed_password = generate_password_hash(password)
        if hashed_password == current_user_password:
            corrections.append("New password cannot be the same as current password")

    return corrections


def check_location(lat: str, long: str) -> list[str]:
    corrections = []

    if not lat or not long:
        corrections.append("Latitude and longitude must both be specified")
        return corrections

    try:
        lat = float(lat)
        if lat <= -90 or lat >= 90:
            corrections.append("Latitude must be between -90 and 90")
    except ValueError:
        corrections.append("Latitude is not a valid number")

    try:
        long = float(long)
        if long <= -180 or long >= 180:
            corrections.append("Longitude must be between -180 and 180")
    except ValueError:
        corrections.append("Longitude is not a valid number")

    return corrections


def check_name(names: list[str]) -> list[str]:
    corrections = []

    if len(names) < 2:
        corrections.append("There must be at least 2 names")
        return corrections

    for name in names:
        if len(name) < 3:
            corrections.append("Each name must be at least 3 characters long")
            break

    for name in names:
        if len(name) > 20:
            corrections.append("Each name must be at most 20 characters long")
            break

    for name in names:
        if not any(c.isupper() for c in name):
            corrections.append("Each name must contain at least one uppercase letter")
            break

    return corrections


def check_review(message: str) -> list[str]:
    corrections = []

    if not message:
        return ["Message cannot be empty"]

    if len(message) < 3:
        corrections.append("Message must be at least 3 characters long")

    if len(message) > 500:  # Changed from 50 to 500 for more realistic reviews
        corrections.append("Message must be at most 500 characters long")

    return corrections


def check_review_score(score: str) -> list[str]:
    corrections = []

    if not score:
        return ["Review score must not be empty"]

    if not str(score).isdigit():
        return ["Review score must be an integer"]

    score_int = int(score)

    if score_int < 1:
        corrections.append("Review score must be at least 1")

    if score_int > 5:
        corrections.append("Review score must be at most 5")

    return corrections


def check_date(year: int, month: int, day: int) -> bool:
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def check_dob(year: int | str, month: int | str, day: int | str) -> list[str]:
    corrections = []

    # Convert and validate year
    if isinstance(year, str):
        try:
            year = int(year)
        except ValueError:
            corrections.append("Year must be an integer")
            return corrections

    if not (1900 <= year <= datetime.today().year):
        corrections.append("Year must be between 1900 and the current year")

    # Convert and validate month
    if isinstance(month, str):
        try:
            month = int(month)
        except ValueError:
            corrections.append("Month must be an integer")
            return corrections

    if not (1 <= month <= 12):
        corrections.append("Month must be between 1 and 12")

    # Convert and validate day
    if isinstance(day, str):
        try:
            day = int(day)
        except ValueError:
            corrections.append("Day must be an integer")
            return corrections

    if not (1 <= day <= 31):
        corrections.append("Day must be between 1 and 31")

    if corrections:
        return corrections

    # Check if valid date
    if not check_date(year, month, day):
        return ["Not a valid date"]

    # Check if user is at least 13 years old (56 weeks * 13 years)
    dob = datetime(year, month, day)
    age_threshold = datetime.now() - timedelta(weeks=52 * 13)

    if dob > age_threshold:
        return ["User must be at least 13 years old to use this application"]

    return []


def check_phone_number(phone: str) -> list[str]:
    try:
        parsed = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed):
            return ["Invalid phone number"]
    except phonenumbers.NumberParseException:
        return ["Invalid phone number format"]

    return []
