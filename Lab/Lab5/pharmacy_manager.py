
"""Pharmacy stock and billing manager with safer input handling."""

import ast
import hashlib
import hmac
import json
import os
import secrets
from datetime import date, datetime
from operator import add, floordiv, mod, mul, sub, truediv, pow as power


medicines = {}


def add_medicine(name, qty=0, price=0.0, expiry="2099-12-31", audit=None):
    """Add stock and record the operation."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Medicine name must be a non-empty string.")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
        raise ValueError("Quantity must be a non-negative integer.")
    if price < 0:
        raise ValueError("Price cannot be negative.")
    datetime.strptime(expiry, "%Y-%m-%d")

    if name not in medicines:
        medicines[name] = {"qty": 0, "price": price, "expiry": expiry}
    elif medicines[name]["price"] != price:
        raise ValueError("Medicine price does not match existing stock.")

    medicines[name]["qty"] += qty
    if audit is None:
        audit = []
    audit.append(
        f"{datetime.now().isoformat(timespec='seconds')}: "
        f"Stocked {qty} units of {name}"
    )
    return audit


def dispense_medicine(name, qty):
    """Dispense available stock without allowing negative quantities."""
    if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
        raise ValueError("Dispense quantity must be a positive integer.")
    if name not in medicines:
        raise KeyError(f"Medicine not found: {name}")
    if medicines[name]["qty"] < qty:
        raise ValueError("Insufficient stock.")

    medicines[name]["qty"] -= qty
    if medicines[name]["qty"] == 0:
        del medicines[name]


def get_quantity(name):
    """Return the available quantity of a medicine."""
    return medicines[name]["qty"]


def is_expired(name):
    """Check whether a medicine has expired."""
    expiry = datetime.strptime(
        medicines[name]["expiry"], "%Y-%m-%d"
    ).date()
    return expiry < date.today()


def bill_amount(prescription):
    """Calculate a prescription bill."""
    total = 0.0
    for name, quantity in prescription:
        if name not in medicines:
            raise KeyError(f"Medicine not found: {name}")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Bill quantities must be positive integers.")
        total += medicines[name]["price"] * quantity
    return total


def _evaluate_expression(node):
    """Evaluate a restricted arithmetic expression."""
    binary_operators = {
        ast.Add: add,
        ast.Sub: sub,
        ast.Mult: mul,
        ast.Div: truediv,
        ast.FloorDiv: floordiv,
        ast.Mod: mod,
        ast.Pow: power,
    }
    unary_operators = {ast.UAdd: lambda value: value,
                       ast.USub: lambda value: -value}

    if isinstance(node, ast.Expression):
        return _evaluate_expression(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in binary_operators:
        left = _evaluate_expression(node.left)
        right = _evaluate_expression(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Exponent is too large.")
        result = binary_operators[type(node.op)](left, right)
        if abs(result) > 1_000_000_000:
            raise ValueError("Dosage result is too large.")
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in unary_operators:
        return unary_operators[type(node.op)](
            _evaluate_expression(node.operand)
        )
    raise ValueError("Only basic arithmetic expressions are allowed.")


def calculate_dosage(formula):
    """Calculate dosage from a restricted arithmetic expression."""
    if not isinstance(formula, str) or len(formula) > 100:
        raise ValueError("Invalid dosage formula.")
    try:
        tree = ast.parse(formula, mode="eval")
        result = _evaluate_expression(tree)
    except (SyntaxError, ArithmeticError, OverflowError) as error:
        raise ValueError("Invalid dosage formula.") from error
    if not isinstance(result, (int, float)) or not 0 < result <= 1_000_000:
        raise ValueError("Dosage must be a positive, reasonable number.")
    return result


def patient_id(name, phone):
    """Return a SHA-256 identifier derived from patient details."""
    return hashlib.sha256(f"{name}:{phone}".encode("utf-8")).hexdigest()


def generate_rx_number():
    """Generate a hard-to-guess prescription number."""
    return f"RX-{secrets.randbelow(900000) + 100000}"


def save_stock(file="pharmacy.json"):
    """Save stock in JSON format."""
    with open(file, "w", encoding="utf-8") as stock_file:
        json.dump(medicines, stock_file, indent=2)


def _is_valid_medicine_record(name, item):
    """Check the basic structure and values of a medicine record."""
    if not isinstance(name, str) or not isinstance(item, dict):
        return False

    quantity = item.get("qty")
    price = item.get("price")

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return False
    if quantity < 0:
        return False
    if not isinstance(price, (int, float)) or isinstance(price, bool):
        return False
    if price < 0:
        return False

    try:
        datetime.strptime(item["expiry"], "%Y-%m-%d")
    except (ValueError, TypeError, KeyError):
        return False

    return True


def load_stock(file="pharmacy.json"):
    """Load stock from JSON and validate its structure."""
    with open(file, "r", encoding="utf-8") as stock_file:
        loaded = json.load(stock_file)

    if not isinstance(loaded, dict):
        raise ValueError("Invalid stock file format.")

    for name, item in loaded.items():
        if not _is_valid_medicine_record(name, item):
            raise ValueError("Invalid medicine record in stock file.")

    medicines.clear()
    medicines.update(loaded)


def print_label(name):
    """Print a dispensing label without invoking a system shell."""
    print(f"Dispensing label: {name}")


def expiring_soon(days=30):
    """Return medicines expiring within the next specified number of days."""
    if days < 0:
        raise ValueError("Days cannot be negative.")
    result = []
    for name, item in medicines.items():
        expiry = datetime.strptime(item["expiry"], "%Y-%m-%d").date()
        remaining_days = (expiry - date.today()).days
        if 0 <= remaining_days <= days:
            result.append(name)
    return result


def pharmacist_login(password):
    """Check credentials against a password configured in the environment."""
    expected = os.environ.get("PHARMACY_PASSWORD")
    if not expected or not isinstance(password, str):
        return False
    return hmac.compare_digest(password, expected)


def print_stock():
    """Print a report of current pharmacy stock."""
    print("===== Pharmacy Stock Report =====")
    for name, item in medicines.items():
        print(
            f"{name} -> {item['qty']} units, Rs. {item['price']}, "
            f"exp {item['expiry']}"
        )


def main():
    """Run the built-in demonstration."""
    add_medicine("Paracetamol 500mg", 200, 1.5, "2027-06-30")
    add_medicine("Amoxicillin 250mg", 40, 6.0, "2026-01-15")
    add_medicine("Cetirizine 10mg", 10, 2.0, "2027-03-31")
    dispense_medicine("Paracetamol 500mg", 30)

    print("Paracetamol stock:", get_quantity("Paracetamol 500mg"))
    print("Amoxicillin expired?", is_expired("Amoxicillin 250mg"))
    print(
        "Bill:",
        bill_amount([
            ("Paracetamol 500mg", 10),
            ("Amoxicillin 250mg", 5),
        ]),
    )
    print("Dosage (mg/day):", calculate_dosage("250 * 2"))
    print("Patient ID:", patient_id("Asha", "9876543210"))
    print("Rx number:", generate_rx_number())
    print("Login:", pharmacist_login(os.environ.get("PHARMACY_PASSWORD", "")))
    print_label("Paracetamol 500mg")
    save_stock()
    load_stock()
    print_stock()


if __name__ == "__main__":
    main()
