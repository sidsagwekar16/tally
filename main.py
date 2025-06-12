from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import date
import uuid
import requests
import xml.etree.ElementTree as ET
from datetime import datetime  # Add this import

app = FastAPI()

TALLY_URL = "http://localhost:9000"  # Update if different


# ---------- MODELS ----------
class LedgerCreate(BaseModel):
    name: str
    group: str = "Bank Accounts"
    opening_balance: Optional[float] = 0.0
    is_debit: bool = True


class VoucherCreate(BaseModel):
    date: date
    voucher_type: Literal["payment", "receipt", "contra"]
    from_ledger: str
    to_ledger: str
    amount: float
    narration: Optional[str]


# ---------- XML HELPERS ----------
def generate_ledger_xml(ledger: LedgerCreate) -> str:
    return f"""
    <ENVELOPE>
      <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
      </HEADER>
      <BODY>
        <IMPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>All Masters</REPORTNAME>
          </REQUESTDESC>
          <REQUESTDATA>
            <TALLYMESSAGE>
              <LEDGER NAME="{ledger.name}" RESERVEDNAME="">
                <NAME>{ledger.name}</NAME>
                <PARENT>{ledger.group}</PARENT>
                <ISDEEMEDPOSITIVE>{"Yes" if ledger.is_debit else "No"}</ISDEEMEDPOSITIVE>
                <OPENINGBALANCE>{ledger.opening_balance}</OPENINGBALANCE>
              </LEDGER>
            </TALLYMESSAGE>
          </REQUESTDATA>
        </IMPORTDATA>
      </BODY>
    </ENVELOPE>
    """


def generate_voucher_xml(voucher: VoucherCreate, selected_company: str) -> str:
    """Generate XML for voucher creation with company context and unique identifiers."""
    voucher_number = f"VCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"  # Unique voucher number
    guid = str(uuid.uuid4())  # Unique GUID for the voucher
    return f"""
    <ENVELOPE>
      <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
      </HEADER>
      <BODY>
        <IMPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>Vouchers</REPORTNAME>
            <STATICVARIABLES>
              <SVCURRENTCOMPANY>{selected_company}</SVCURRENTCOMPANY>
            </STATICVARIABLES>
          </REQUESTDESC>
          <REQUESTDATA>
            <TALLYMESSAGE>
              <VOUCHER VCHTYPE="{voucher.voucher_type.capitalize()}" ACTION="Create" OBJVIEW="Accounting Voucher View">
                <GUID>{guid}</GUID>
                <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
                <DATE>{voucher.date.strftime('%Y%m%d')}</DATE>
                <NARRATION>{voucher.narration or ""}</NARRATION>
                <VOUCHERTYPENAME>{voucher.voucher_type.capitalize()}</VOUCHERTYPENAME>
                <ALLLEDGERENTRIES.LIST>
                  <LEDGERNAME>{voucher.from_ledger}</LEDGERNAME>
                  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                  <AMOUNT>-{voucher.amount}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
                <ALLLEDGERENTRIES.LIST>
                  <LEDGERNAME>{voucher.to_ledger}</LEDGERNAME>
                  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                  <AMOUNT>{voucher.amount}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
              </VOUCHER>
            </TALLYMESSAGE>
          </REQUESTDATA>
        </IMPORTDATA>
      </BODY>
    </ENVELOPE>
    """

def fetch_voucher_types(selected_company: str) -> list:
    """Fetch available voucher types from Tally."""
    xml = f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Voucher Types</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <SVCURRENTCOMPANY>{selected_company}</SVCURRENTCOMPANY>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Voucher Types" ISINITIALIZE="Yes">
                <TYPE>Voucher Type</TYPE>
                <NATIVEMETHOD>NAME</NATIVEMETHOD>
              </COLLECTION>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
    result = send_to_tally(xml)
    print("\n[DEBUG] Voucher Types Response:\n", result)
    voucher_types = []
    try:
        root = ET.fromstring(result)
        for vtype in root.findall(".//VOUCHERTYPE"):
            name = vtype.find(".//NAME")
            if name is not None and name.text:
                voucher_types.append(name.text)
    except Exception as e:
        print("❌ Could not parse voucher types:", str(e))
    return voucher_types

def generate_fetch_ledger_xml(name: str) -> str:
    return f"""
    <ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVCURRENTCOMPANY>Your Loaded Company</SVCURRENTCOMPANY>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Ledgers" ISINITIALIZE="Yes">
            <TYPE>Ledger</TYPE>
            <NATIVEMETHOD>*</NATIVEMETHOD>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
    """

def get_all_ledgers(selected_company: str):
    xml = f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>All Ledgers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <SVCURRENTCOMPANY>{selected_company}</SVCURRENTCOMPANY>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="All Ledgers" ISINITIALIZE="Yes">
                <TYPE>Ledger</TYPE>
                <NATIVEMETHOD>NAME</NATIVEMETHOD>
              </COLLECTION>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
    result = send_to_tally(xml)
    print("\n[DEBUG] Tally Response:\n", result)
    ledgers = []
    try:
        root = ET.fromstring(result)
        # Find all LEDGER elements and extract NAME from LANGUAGENAME.LIST/NAME.LIST
        for ledger in root.findall(".//LEDGER"):
            name = ledger.find(".//LANGUAGENAME.LIST/NAME.LIST/NAME")
            if name is not None and name.text:
                ledgers.append(name.text)
    except Exception as e:
        print("❌ Could not parse ledgers:", str(e))
    return ledgers

def generate_fetch_vouchers_xml(voucher_type: str, from_date: str, to_date: str) -> str:
    return f"""
    <ENVELOPE>
      <HEADER>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Voucher Collection</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
            <VOUCHERTYPENAME>{voucher_type.capitalize()}</VOUCHERTYPENAME>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Voucher Collection" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
              </COLLECTION>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """

def send_to_tally(xml: str) -> str:
    print("\n[DEBUG] XML Sent to Tally:\n", xml)  # Log XML sent
    try:
        response = requests.post(TALLY_URL, data=xml.encode("utf-8"))
        response.raise_for_status()
        print("\n[DEBUG] Tally Raw Response:\n", response.text)  # Log raw response
        return response.text
    except Exception as e:
        print("\n[DEBUG] Tally Request Failed:", str(e))  # Log error
        raise HTTPException(status_code=500, detail=f"Tally Error: {str(e)}")


# ---------- ROUTES ----------

@app.post("/bank/ledger")
def create_ledger(ledger: LedgerCreate):
    xml = generate_ledger_xml(ledger)
    result = send_to_tally(xml)
    if "<LINEERROR>" in result:
        raise HTTPException(status_code=400, detail="Tally Error while creating ledger")
    return {"message": "Ledger created successfully"}


@app.get("/bank/ledger/{name}")
def get_ledger(name: str):
    xml = generate_fetch_ledger_xml(name)
    result = send_to_tally(xml)
    return {"raw_response": result}

def check_ledger_exists(ledger_name: str, selected_company: str) -> bool:
    """Check if a ledger exists in Tally for the given company."""
    ledgers = get_all_ledgers(selected_company)
    print(f"\n[DEBUG] Ledgers found for company '{selected_company}': {ledgers}")
    return ledger_name in ledgers

@app.post("/bank/voucher")
def create_voucher(voucher: VoucherCreate, selected_company: str = "Test"):
    """Create a voucher in Tally with enhanced validation."""
    # Validate voucher type
    voucher_types = fetch_voucher_types(selected_company)
    print(f"\n[DEBUG] Available Voucher Types: {voucher_types}")
    if voucher.voucher_type.capitalize() not in voucher_types:
        raise HTTPException(status_code=400, detail=f"Voucher type '{voucher.voucher_type}' does not exist in Tally")

    # Validate ledger existence
    if not check_ledger_exists(voucher.from_ledger, selected_company):
        raise HTTPException(status_code=400, detail=f"From ledger '{voucher.from_ledger}' does not exist")
    if not check_ledger_exists(voucher.to_ledger, selected_company):
        raise HTTPException(status_code=400, detail=f"To ledger '{voucher.to_ledger}' does not exist")

    xml = generate_voucher_xml(voucher, selected_company)
    result = send_to_tally(xml)
    
    # Preprocess the response to ensure XML declaration
    if not result.strip().startswith("<?xml"):
        result = '<?xml version="1.0" encoding="UTF-8"?>\n' + result

    # Parse response for detailed error
    try:
        root = ET.fromstring(result)
        # Check if the response has a RESPONSE root tag
        if root.tag == "RESPONSE":
            created = root.find(".//CREATED")
            line_error = root.find(".//LINEERROR")
            exceptions = root.find(".//EXCEPTIONS")
            
            if created is not None and created.text == "1":
                return {"message": "Voucher created successfully"}
            else:
                error_detail = line_error.text if line_error is not None and line_error.text else "Unknown error"
                if exceptions is not None and exceptions.text == "1":
                    error_detail += " (Exception occurred in Tally)"
                print("\n[DEBUG] Voucher Creation Failed, Response:", result)
                raise HTTPException(status_code=400, detail=f"Tally Error: {error_detail}")
        else:
            # Handle ENVELOPE structure if needed
            error = root.find(".//LINEERROR")
            if error is not None and error.text:
                print("\n[DEBUG] Tally Error Details:", error.text)
                raise HTTPException(status_code=400, detail=f"Tally Error: {error.text}")
            
            created = root.find(".//CREATED")
            if created is not None and created.text == "1":
                return {"message": "Voucher created successfully"}
            else:
                print("\n[DEBUG] Voucher Creation Failed, Response:", result)
                raise HTTPException(status_code=400, detail="Tally Error: Voucher not created")
    except ET.ParseError:
        print("\n[DEBUG] Invalid XML Response:", result)
        raise HTTPException(status_code=500, detail="Tally Error: Invalid response XML")

@app.get("/bank/vouchers")
def fetch_vouchers(
    voucher_type: str = Query(..., pattern="^(payment|receipt|contra)$"),
    from_date: date = Query(...),
    to_date: date = Query(...)
):
    xml = generate_fetch_vouchers_xml(voucher_type, from_date.strftime('%Y%m%d'), to_date.strftime('%Y%m%d'))
    result = send_to_tally(xml)
    return {"raw_response": result}

# ---------- INTERACTIVE CLI ----------

def fetch_companies():
    xml = """
    <ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>List of Companies</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVIsSimpleCompany>No</SVIsSimpleCompany>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="List of Companies" ISINITIALIZE="Yes">
            <TYPE>Company</TYPE>
            <NATIVEMETHOD>Name</NATIVEMETHOD>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
    """
    print("\n🔍 Connecting to Tally...")
    response = send_to_tally(xml)
    print("\n[DEBUG] Tally XML Response:\n", response)   # <--- ADD THIS LINE
    companies = []
    try:
        root = ET.fromstring(response)
        for company in root.findall(".//COMPANY"):
            for child in company:
                if child.tag == "NAME":
                    if child.text:
                        companies.append(child.text)
    except Exception as e:
        print("❌ Could not parse company list:", str(e))
    return companies




def cli_mode():
    companies = fetch_companies()
    if not companies:
        print("❌ No companies found in Tally.")
        return

    print("\n📦 Available Companies:")
    for idx, c in enumerate(companies, start=1):
        print(f"  {idx}. {c}")

    selected = input("\nSelect a company (enter number): ")
    try:
        selected_company = companies[int(selected) - 1]
    except:
        print("❌ Invalid selection.")
        return

    print(f"\n✅ Selected company: {selected_company}")

    while True:
        print("\n📋 Select an operation:")
        print("  1. Create Ledger")
        print("  2. Fetch Ledger")
        print("  3. Create Voucher")
        print("  4. Fetch Vouchers")
        print("  5. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            name = input("Ledger name: ")
            group = input("Group (default: Bank Accounts): ") or "Bank Accounts"
            opening = float(input("Opening balance (default 0): ") or 0)
            is_debit = input("Is Debit? (yes/no): ").strip().lower() == "yes"
            ledger = LedgerCreate(name=name, group=group, opening_balance=opening, is_debit=is_debit)
            print(create_ledger(ledger))

        elif choice == "2":
            name = input("Ledger name to fetch: ")
            print(get_ledger(name))

        elif choice == "3":
            vtype = input("Voucher type (payment/receipt/contra): ").lower()
            if vtype not in ["payment", "receipt", "contra"]:
                print("❌ Invalid voucher type.")
                continue

            date_str = input("Date (YYYY-MM-DD): ")
            try:
                date_val = date.fromisoformat(date_str)
            except ValueError:
                print("❌ Invalid date format.")
                continue

            ledgers = get_all_ledgers(selected_company)
            if not ledgers:
                print("❌ No ledgers found.")
                continue

            print("\n📂 Available Ledgers:")
            for i, l in enumerate(ledgers):
                print(f"  {i+1}. {l}")

            try:
                from_idx = int(input("Select 'from ledger' (number): ")) - 1
                to_idx = int(input("Select 'to ledger' (number): ")) - 1
                if from_idx < 0 or from_idx >= len(ledgers) or to_idx < 0 or to_idx >= len(ledgers):
                    print("❌ Invalid ledger selection.")
                    continue
            except ValueError:
                print("❌ Invalid input.")
                continue

            try:
                amount = float(input("Amount: "))
                if amount <= 0:
                    print("❌ Amount must be positive.")
                    continue
            except ValueError:
                print("❌ Invalid amount.")
                continue

            narration = input("Narration (optional): ")

            voucher = VoucherCreate(
                date=date_val,
                voucher_type=vtype,
                from_ledger=ledgers[from_idx],
                to_ledger=ledgers[to_idx],
                amount=amount,
                narration=narration
            )
            try:
                # Pass selected_company to create_voucher
                result = create_voucher(voucher, selected_company=selected_company)
                print(result)
            except HTTPException as e:
                print(f"❌ Voucher creation failed: {e.detail}")
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")

        # ... (other menu options unchanged)

     

      
        elif choice == "4":
            vtype = input("Voucher type (payment/receipt/contra): ").lower()
            from_date = date.fromisoformat(input("From date (YYYY-MM-DD): "))
            to_date = date.fromisoformat(input("To date (YYYY-MM-DD): "))
            print(fetch_vouchers(vtype, from_date, to_date))

        elif choice == "5":
            print("👋 Exiting CLI.")
            break

        else:
            print("❌ Invalid choice. Try again.")


# Run CLI when this script is directly executed
if __name__ == "__main__":
    cli_mode()
