
from datetime import date


def format_visitor_name(name):
    """Formats a full name as 'Surname, Given names'."""
    if not isinstance(name, str):
        return ""

    parts = name.split()

    if not parts:
        return ""

    if len(parts) == 1:
        return parts[0].title()

    return parts[-1].title() + ", " + " ".join(parts[:-1]).title()


def parse_group_ages(text):
    """Parses space-separated non-negative ages into a list of integers."""
    if not isinstance(text, str):
        return []

    parts = text.split()

    if not parts:
        return []

    try:
        ages = [int(age) for age in parts]

        if any(age < 0 for age in ages):
            return []

        return ages

    except ValueError:
        return []


def parse_visit_date(text):
    """Parses a valid YYYY-MM-DD date into a tuple."""
    if not isinstance(text, str):
        return None

    try:
        if len(text) != 10:
            return None

        if text[4] != "-" or text[7] != "-":
            return None

        year, month, day = map(int, text.split("-"))

        valid_date = date(year, month, day)

        return valid_date.year, valid_date.month, valid_date.day

    except (ValueError, TypeError):
        return None


def main():
    print("==== Running format_visitor_name ====")
    value = input("Enter a visitor's full name (e.g. asha rao): ")
    print("Name on ticket:", format_visitor_name(value))

    print("\n==== Running parse_group_ages ====")
    value = input("Enter the ages in the group separated by spaces (e.g. 34 12 70): ")
    print("Group ages:", parse_group_ages(value))

    print("\n==== Running parse_visit_date ====")
    value = input("Enter the visit date as YYYY-MM-DD (e.g. 2026-11-16): ")
    print("Visit date (year, month, day):", parse_visit_date(value))


if __name__ == "__main__":
    main()
