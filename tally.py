from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Body
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import pandas as pd
from typing import List, Dict, Any
import os
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv
load_dotenv()
import uuid
from datetime import datetime
import json
import html

from typing import List

import io
import logging

from sqlalchemy import text
import xlrd
import math
import re


from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not found! Is your .env loaded?")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TALLY_URL = "http://localhost:9000"
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




class PushToTallyRequest(BaseModel):
    statement_id: str           # Unique key to fetch transactions from your DB
    selected_company: str = "Test"   # Optionally allow frontend to select Tally company

class CompanyCreate(BaseModel):
    tenant_id: str
    name: str
    description: str = None  # Optional


def clean_xml(xml: str) -> str:
    # Remove numeric character refs for control characters (decimal 0–31 except TAB/CR/LF)
    # e.g. &#4;, &#0;, etc
    xml = re.sub(r'&#([0-8]|1[0-9]|2[0-9]|3[01]);', '', xml)
    # Remove invalid literal unicode chars as before
    xml = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\uFFFE\uFFFF]', '', xml)
    return xml



GET_COMPANY_XML = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>List of Companies</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="List of Companies" ISINITIALIZE="Yes">
            <TYPE>Company</TYPE>
            <NATIVEMETHOD>NAME</NATIVEMETHOD>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""


@app.post("/companies")
def create_company(
    tenant_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    company_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO companies (id, tenant_id, name, description, created_at, updated_at)
            VALUES (:id, :tenant_id, :name, :description, :created_at, :updated_at)
        """),
        {
            "id": company_id,
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )
    db.commit()
    return {"company_id": company_id}

@app.post("/tenants")
def create_tenant(name: str, db: Session = Depends(get_db)):
    # You can auto-generate a UUID for tenant_id
    tenant_id = str(uuid.uuid4())
    db.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, :name)"),
        {"id": tenant_id, "name": name}
    )
    db.commit()
    return {"tenant_id": tenant_id}


@app.get("/companies")
def get_companies():
    headers = {"Content-Type": "application/xml"}
    try:
        resp = requests.post(TALLY_URL, data=GET_COMPANY_XML, headers=headers, timeout=10)
        resp.raise_for_status()
        company_names = []
        tree = ET.fromstring(resp.text)
        for comp in tree.findall(".//COMPANY"):
            name = comp.find("NAME")
            if name is not None:
                company_names.append(name.text)
        return {"companies": company_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.patch("/transactions/bulk")
def bulk_update_transactions(
    updates: List[dict] = Body(...), 
    db: Session = Depends(get_db)
):
    updated = 0
    for upd in updates:
        txn_id = upd.pop("id", None)
        if not txn_id:
            continue  # Or: raise HTTPException(400, "Missing id in one update")
        allowed_fields = [  "from_ledger", "to_ledger", "voucher", "status", "narration", "remark",  "withdrawal_amount", "deposit_amount"]
        fields = {k: v for k, v in upd.items() if k in allowed_fields}
        if not fields:
            continue
        set_clause = ", ".join([f"{k} = :{k}" for k in fields])
        fields["id"] = txn_id
        db.execute(
            text(f"UPDATE transactions SET {set_clause} WHERE id = :id"),
            fields
        )
        updated += 1
    db.commit()
    return {"success": True, "updated": updated}
    

# -- UTILS --
def safe_str(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return ""
    return str(val).strip()

def safe_float(val):
    try:
        f = float(str(val).replace(",", ""))
        if math.isnan(f):
            return 0.0
        return f
    except Exception:
        return 0.0

# ---------- 3. Modular Excel Upload & Parse to JSON ----------
def parse_hdfc_statement(contents: bytes, filename: str) -> dict:
    import io
    import pandas as pd
    import math

    def safe_str(val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return ""
        return str(val).strip()

    def safe_float(val):
        try:
            f = float(str(val).replace(",", ""))
            if math.isnan(f):
                return 0.0
            return f
        except Exception:
            return 0.0

    # Always use engine="xlrd" for .xls and openpyxl for .xlsx
    if filename.endswith(".xls"):
        engine = "xlrd"
    else:
        engine = "openpyxl"

    # Step 1: Load with NO HEADER, find the real header row
    df = pd.read_excel(io.BytesIO(contents), sheet_name=0, engine=engine, header=None)
    header_row = None
    for idx, row in df.iterrows():
        vals = [safe_str(v) for v in row.values]
        if "Date" in vals and "Narration" in vals:
            header_row = idx
            break
    if header_row is None:
        raise Exception("Could not find transaction header in Excel file.")

    # Step 2: Reload using the actual header row
    df_transactions = pd.read_excel(
        io.BytesIO(contents),
        sheet_name=0,
        skiprows=header_row,
        header=0,
        engine=engine
    )

    # Step 3: Parse transactions as before
    transactions = []
    for _, row in df_transactions.iterrows():
        if pd.isna(row.get('Date')) or "STATEMENT SUMMARY" in str(row.get('Date', '')):
            break
        try:
            date_str = safe_str(row['Date'])
            if not date_str or date_str.lower() == "nan":
                continue
            date = pd.to_datetime(date_str, format="%d/%m/%y").strftime("%Y-%m-%d")
            narration = safe_str(row['Narration'])
            ref_no = safe_str(row['Chq./Ref.No.'])
            value_date = pd.to_datetime(safe_str(row['Value Dt']), format="%d/%m/%y").strftime("%Y-%m-%d")
            withdrawal_amt = safe_float(row['Withdrawal Amt.'])
            deposit_amt = safe_float(row['Deposit Amt.'])
            closing_balance = safe_float(row['Closing Balance'])
            transaction_type = "debit" if withdrawal_amt > 0 else "credit"
            category = "UPI Payment" if "UPI" in narration else "Other"
            transactions.append({
                "date": date,
                "narration": narration,
                "ref_no": ref_no,
                "value_date": value_date,
                "withdrawal_amount": withdrawal_amt,
                "deposit_amount": deposit_amt,
                "closing_balance": closing_balance,
                "transaction_type": transaction_type,
                "category": category,
                "from_ledger" : None,
                 "to_ledger" : None,
                   "voucher" : None,
                    "status" : None,
            })
        except Exception:
            continue
    return {"transactions": transactions}



@app.post("/statements/upload")
async def upload_bank_statement(
    company_id: str = Form(...),
    company_name: str = Form(...),
    bank: str = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files allowed")
    contents = await file.read()
    try:
        parsed_json = parse_hdfc_statement(contents, file.filename)
    except Exception as e:
        print(f"❌ Failed to parse statement: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    transactions = parsed_json.get("transactions", [])
    if not transactions:
        print("⚠️ No transactions found in the uploaded file.")
        raise HTTPException(status_code=400, detail="No transactions found in statement.")

    statement_id = str(uuid.uuid4())
    print(f"ℹ️ Inserting bank statement: {statement_id}, company: {company_name}, bank: {bank}")

    # Insert statement metadata
    db.execute(
        text("""
        INSERT INTO bank_statements (id, company_id, company_name, bank_name, created_at)
        VALUES (:id, :company_id, :company_name, :bank_name, :created_at)
        """),
        {
            "id": statement_id,
            "company_id": company_id,
            "company_name": company_name,
            "bank_name": bank,
            "created_at": datetime.utcnow(),
        }
    )
    print("✅ Inserted bank_statement metadata.")

    # Insert each transaction as a row in transactions table
    insert_count = 0
    for txn in transactions:
        txn_id = str(uuid.uuid4())
        print(f"  ➜ Inserting txn {txn_id} | date={txn.get('date')}, narration={txn.get('narration')}, amount={txn.get('withdrawal_amount', 0) or txn.get('deposit_amount', 0)}")
        db.execute(
            text("""
            INSERT INTO transactions (
                id, statement_id, company_id, date, narration, ref_no, value_date, withdrawal_amount, deposit_amount,
                closing_balance, transaction_type, category, from_ledger, to_ledger, voucher, status, created_at
            ) VALUES (
                :id, :statement_id, :company_id, :date, :narration, :ref_no, :value_date, :withdrawal_amount, :deposit_amount,
                :closing_balance, :transaction_type, :category, :from_ledger, :to_ledger, :voucher, :status, :created_at
            )
            """),
            {
                "id": txn_id,
                "statement_id": statement_id,
                 "company_id": company_id,
                "date": txn["date"],
                "narration": txn["narration"],
                "ref_no": txn["ref_no"],
                "value_date": txn["value_date"],
                "withdrawal_amount": txn["withdrawal_amount"],
                "deposit_amount": txn["deposit_amount"],
                "closing_balance": txn["closing_balance"],
                "transaction_type": txn["transaction_type"],
                "category": txn["category"],
                "from_ledger": txn.get("from_ledger"),
                "to_ledger": txn.get("to_ledger"),
                "voucher": txn.get("voucher"),
                "status": txn.get("status"),
                "created_at": datetime.utcnow(),
            }
        )
        insert_count += 1

    db.commit()
    print(f"✅ {insert_count} transactions inserted for statement {statement_id}.")

    return {
        "statement_id": statement_id,
        "inserted_transactions": insert_count,
        "message": "Statement uploaded and transactions stored"
    }




@app.post("/statements/{statement_id}/push-to-tally")
def push_statement_to_tally(statement_id: str, db: Session = Depends(get_db)):
    # 1. Fetch transactions for the given statement_id
    rows = db.execute(
        text("SELECT * FROM transactions WHERE statement_id = :sid"),
        {"sid": statement_id}
    ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No transactions found for this statement.")

    # 2. Generate XML
    envelope = ET.Element("ENVELOPE")
    body = ET.SubElement(envelope, "BODY")
    importdata = ET.SubElement(body, "IMPORTDATA")
    requestdesc = ET.SubElement(importdata, "REQUESTDESC")
    ET.SubElement(requestdesc, "REPORTNAME").text = "Vouchers"
    requestdata = ET.SubElement(importdata, "REQUESTDATA")
    for row in rows:
        tallymsg = ET.SubElement(requestdata, "TALLYMESSAGE")
        voucher = ET.SubElement(tallymsg, "VOUCHER")
        # Use column names; adjust these as per your schema
        for col, val in row._mapping.items():
            if col not in ("id", "statement_id"):  # skip technical cols
                ET.SubElement(voucher, col.upper()).text = str(val) if val is not None else ""

    xml_str = ET.tostring(envelope, encoding="utf-8").decode()

    # 3. Push to Tally
    resp = requests.post("http://localhost:9000", data=xml_str, headers={"Content-Type": "application/xml"})
    return {"status": resp.status_code, "tally_response": resp.text}

@app.get("/statements/{statement_id}")
def get_statement(statement_id: str, db: Session = Depends(get_db)):
    stmt = "SELECT parsed_json FROM bank_statements WHERE id=:id"
    result = db.execute(stmt, {"id": statement_id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result[0]


@app.get("/transactions")
def get_transactions(statement_id: str, db: Session = Depends(get_db)):
    # This returns an iterable of dictionaries
    result = db.execute(
        text("SELECT * FROM transactions WHERE statement_id=:sid"),
        {"sid": statement_id}
    )
    rows = result.mappings().all()
    return rows


@app.patch("/transactions/{txn_id}")
def update_transaction(txn_id: str, data: dict = Body(...), db: Session = Depends(get_db)):
    allowed_fields = ["from_ledger", "to_ledger", "voucher_type", "status", "narration", "remark", "amount"]
    fields = {k: v for k, v in data.items() if k in allowed_fields}
    set_clause = ", ".join([f"{k} = :{k}" for k in fields])
    if not fields:
        raise HTTPException(400, "No valid fields to update.")
    fields["id"] = txn_id
    db.execute(
        text(f"UPDATE transactions SET {set_clause} WHERE id = :id"),
        fields
    )
    db.commit()
    return {"success": True}

@app.get("/ledgers")
def get_ledgers(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT name FROM ledgers")).fetchall()
    return [r[0] for r in result]

def print_xml_debug(xml_str, err=None):
    # Always write the raw XML to a file for inspection
    with open("debug_tally_ledgers.xml", "w", encoding="utf-8", errors="replace") as f:
        f.write(xml_str)
    print("✅ [DEBUG] Wrote Tally XML response to debug_tally_ledgers.xml")
    if err and hasattr(err, 'position'):
        line, col = err.position
        lines = xml_str.splitlines()
        context = ""
        if 0 < line <= len(lines):
            context = lines[line - 1]
            print(f"⚠️ Problem line {line}:\n{context}")
            if 0 < col <= len(context):
                print(f"⚠️ Character at column {col}: {repr(context[col-1])}")
            else:
                print("⚠️ Column out of range.")
        else:
            print("⚠️ Line out of range.")

def parse_ledgers(xml_response: str):
    ledgers = []
    try:
        xml_response = clean_xml(xml_response)
        # Debug: log what we're parsing
        print_xml_debug(xml_response)
        root = ET.fromstring(xml_response)
        for ledger in root.findall('.//LEDGER'):
            name = ledger.findtext('.//NAME')
            parent = ledger.findtext('.//PARENT')
            if name:
                ledgers.append({"name": name, "parent": parent})
    except ET.ParseError as e:
        print_xml_debug(xml_response, e)
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")
    except Exception as e:
        print_xml_debug(xml_response)
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")
    return ledgers

def send_to_tally(xml: str) -> str:
    headers = {"Content-Type": "application/xml"}
    try:
        response = requests.post(TALLY_URL, data=xml.encode("utf-8"), headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Tally connection failed: {str(e)}")
    
@app.post("/sync-ledgers/{tenant_id}/{company_id}/{company_name}")
def sync_ledgers(
    tenant_id: str,
    company_id: str,
    company_name: str,
    db: Session = Depends(get_db),
):
    # 1. Fetch ledgers from Tally for the given company_name
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
            <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="All Ledgers" ISINITIALIZE="Yes">
                <TYPE>Ledger</TYPE>
                <NATIVEMETHOD>NAME</NATIVEMETHOD>
                <NATIVEMETHOD>PARENT</NATIVEMETHOD>
              </COLLECTION>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """

    # 2. Call Tally and parse ledgers
    tally_response = send_to_tally(xml)
    ledgers = parse_ledgers(tally_response)

    # 3. Upsert (insert or update) groups (ledger_groups)
    group_name_to_id = {}
    for ledger in ledgers:
        parent = ledger.get("parent", "").strip() if ledger.get("parent") else None
        if parent and parent not in group_name_to_id:
            result = db.execute(
                text("""
                    INSERT INTO ledger_groups (tenant_id, name)
                    VALUES (:tenant_id, :name)
                    ON CONFLICT (tenant_id, name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """),
                {"tenant_id": tenant_id, "name": parent}
            )
            group_id = result.fetchone()[0]
            group_name_to_id[parent] = group_id

    db.commit()

    # 4. Upsert ledgers, linking to both company and group
    for ledger in ledgers:
        name = ledger["name"].strip()
        parent = ledger.get("parent", "").strip() if ledger.get("parent") else None
        group_id = group_name_to_id.get(parent)
        db.execute(
            text("""
                INSERT INTO ledgers (tenant_id, company_id, name, group_id)
                VALUES (:tenant_id, :company_id, :name, :group_id)
                ON CONFLICT (tenant_id, company_id, name) DO UPDATE
                SET group_id = EXCLUDED.group_id
            """),
            {"tenant_id": tenant_id, "company_id": company_id, "name": name, "group_id": group_id}
        )

    db.commit()
    return {"ok": True, "ledgers_synced": len(ledgers)}






@app.post("/convert-json-to-tallyxml")
def convert_json_to_tallyxml(payload: dict):
    envelope = ET.Element("ENVELOPE")
    body = ET.SubElement(envelope, "BODY")
    importdata = ET.SubElement(body, "IMPORTDATA")
    requestdesc = ET.SubElement(importdata, "REQUESTDESC")
    ET.SubElement(requestdesc, "REPORTNAME").text = "Vouchers"
    requestdata = ET.SubElement(importdata, "REQUESTDATA")
    for txn in payload["transactions"]:
        tallymsg = ET.SubElement(requestdata, "TALLYMESSAGE")
        voucher = ET.SubElement(tallymsg, "VOUCHER")
        for k, v in txn.items():
            ET.SubElement(voucher, k.upper()).text = str(v)
    xml_str = ET.tostring(envelope, encoding="utf-8").decode()
    return {"tally_xml": xml_str}

@app.post("/push-to-tally")
def push_to_tally(payload: dict):
    tally_url = "http://localhost:9000"  # Replace with your Tally server endpoint
    xml_data = payload.get("tally_xml")
    if not xml_data:
        raise HTTPException(status_code=400, detail="Missing Tally XML")
    resp = requests.post(tally_url, data=xml_data, headers={"Content-Type": "application/xml"})
    return {"status": resp.status_code, "response": resp.text}





#frontend apis 
def get_date_xml(val):
    """
    Accepts string (YYYY-MM-DD), datetime.date, or datetime.datetime.
    Returns date in Tally format (YYYYMMDD). Falls back to today.
    """
    from datetime import datetime, date
    if val is None:
        return datetime.now().strftime("%Y%m%d")
    # If already date object
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y%m%d")
    # If string
    try:
        return datetime.strptime(str(val), "%Y-%m-%d").strftime("%Y%m%d")
    except Exception:
        # Try parsing other string formats if needed
        try:
            return pd.to_datetime(str(val)).strftime("%Y%m%d")
        except Exception:
            return datetime.now().strftime("%Y%m%d")


def escape_xml(text: str) -> str:
    if text is None:
        return ""
    return html.escape(str(text), quote=False)


def generate_tally_xml_from_db_transactions(
    transactions: list,
    selected_company: str = "Test"
) -> str:
    """
    - transactions: List of dicts, each a transaction row (from your database)
    - selected_company: Name of the active company in Tally
    Returns: XML string ready for Tally import
    """
    import xml.etree.ElementTree as ET
    from datetime import datetime

    root = ET.Element("ENVELOPE")
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
    body = ET.SubElement(root, "BODY")
    importdata = ET.SubElement(body, "IMPORTDATA")
    requestdesc = ET.SubElement(importdata, "REQUESTDESC")
    ET.SubElement(requestdesc, "REPORTNAME").text = "Vouchers"
    static_vars = ET.SubElement(requestdesc, "STATICVARIABLES")
    ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = selected_company
    requestdata = ET.SubElement(importdata, "REQUESTDATA")

    for tx in transactions:
        # Safety: handle missing/None values
        voucher_type = tx.get("voucher", "Payment")
    
        date_xml = get_date_xml(tx.get("date") or tx.get("value_date"))

        narration = escape_xml(tx.get("narration", ""))
        from_ledger = tx.get("from_ledger", "")
        to_ledger = tx.get("to_ledger", "")
        # Determine amount and Dr/Cr based on transaction_type or amounts
        if tx.get("withdrawal_amount", 0) > 0:
            amount = tx["withdrawal_amount"]
            is_deemed_positive1 = "Yes"
            is_deemed_positive2 = "No"
            amount1 = -amount
            amount2 = amount
        else:
            amount = tx.get("deposit_amount", 0)
            is_deemed_positive1 = "No"
            is_deemed_positive2 = "Yes"
            amount1 = amount
            amount2 = -amount

        # XML structure per transaction
        tally_msg = ET.SubElement(requestdata, "TALLYMESSAGE")
        voucher = ET.SubElement(
            tally_msg, "VOUCHER",
            VCHTYPE=voucher_type,
            ACTION="Create",
            OBJVIEW="Accounting Voucher View"
        )
        # Minimal required fields
        ET.SubElement(voucher, "DATE").text = date_xml
        ET.SubElement(voucher, "NARRATION").text = narration
        ET.SubElement(voucher, "VOUCHERTYPENAME").text = voucher_type
        ET.SubElement(voucher, "VOUCHERNUMBER").text = tx.get("ref_no", "")
        # From Ledger
        ledger_entry1 = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(ledger_entry1, "LEDGERNAME").text = from_ledger
        ET.SubElement(ledger_entry1, "ISDEEMEDPOSITIVE").text = is_deemed_positive1
        ET.SubElement(ledger_entry1, "AMOUNT").text = str(amount1)
        # To Ledger
        ledger_entry2 = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(ledger_entry2, "LEDGERNAME").text = to_ledger
        ET.SubElement(ledger_entry2, "ISDEEMEDPOSITIVE").text = is_deemed_positive2
        ET.SubElement(ledger_entry2, "AMOUNT").text = str(amount2)

    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str




def generate_voucher_xml_from_tx(tx: dict, selected_company: str) -> str:
    # Parse date (ensure fallback if None)
    date_xml = get_date_xml(tx.get("date") or tx.get("value_date"))


    voucher_type = (tx.get("voucher") or "Payment").capitalize()
    narration = tx.get("narration", "")
    from_ledger = tx.get("from_ledger", "")
    to_ledger = tx.get("to_ledger", "")
    ref_no = tx.get("ref_no", "")
    
    # Amount logic
    if tx.get("withdrawal_amount", 0) > 0:
        amount = float(tx["withdrawal_amount"])
        is_deemed_positive1 = "Yes"
        is_deemed_positive2 = "No"
        amount1 = -amount
        amount2 = amount
    else:
        amount = float(tx.get("deposit_amount", 0))
        is_deemed_positive1 = "No"
        is_deemed_positive2 = "Yes"
        amount1 = amount
        amount2 = -amount

    voucher_number = ref_no or f"VCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    guid = str(uuid.uuid4())

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
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
          <VOUCHER VCHTYPE="{voucher_type}" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>{guid}</GUID>
            <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
            <DATE>{date_xml}</DATE>
            <NARRATION>{narration}</NARRATION>
            <VOUCHERTYPENAME>{voucher_type}</VOUCHERTYPENAME>
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>{from_ledger}</LEDGERNAME>
              <ISDEEMEDPOSITIVE>{is_deemed_positive1}</ISDEEMEDPOSITIVE>
              <AMOUNT>{amount1}</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>{to_ledger}</LEDGERNAME>
              <ISDEEMEDPOSITIVE>{is_deemed_positive2}</ISDEEMEDPOSITIVE>
              <AMOUNT>{amount2}</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
"""
    return xml


@app.post("/api/push-db-transactions-to-tally")
async def push_db_transactions_to_tally(
    body: PushToTallyRequest = Body(...),
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("SELECT * FROM transactions WHERE statement_id = :sid"),
        {"sid": body.statement_id}
    )
    transactions = result.mappings().all()
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this statement_id.")

    responses = []
    batch_size = 1
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        tx = batch[0]
        try:
            xml_str = generate_voucher_xml_from_tx(tx, body.selected_company)
            # Debug: Save XML and transaction details to a file for inspection
            with open(f"tally_debug_batch_{i//batch_size+1}.xml", "w", encoding="utf-8") as f:
                f.write(xml_str)
            print(f"\n=== [DEBUG] Batch {i//batch_size+1} XML ===\n{xml_str}\n")
            print(f"--- [DEBUG] Transaction Data: ---\n{json.dumps(tx, indent=2, default=str)}\n")
        except Exception as e:
            responses.append({
                "batch": i // batch_size + 1,
                "status": "Failed",
                "error": f"XML generation error: {str(e)}",
                "transaction": tx
            })
            continue

        try:
            tally_response = send_to_tally(xml_str)
            try:
                root = ET.fromstring(tally_response)
                if "<LINEERROR>" in tally_response:
                    error = root.find(".//LINEERROR")
                    error_detail = error.text if error is not None else "Unknown error"
                    responses.append({
                        "batch": i // batch_size + 1,
                        "status": "Failed",
                        "error": error_detail,
                        "tally_response": tally_response,
                        "transaction": tx
                    })
                else:
                    created = root.find(".//CREATED")
                    if created is not None and int(created.text) > 0:
                        responses.append({
                            "batch": i // batch_size + 1,
                            "status": "Success",
                            "tally_response": tally_response,
                            "transaction": tx
                        })
                    else:
                        responses.append({
                            "batch": i // batch_size + 1,
                            "status": "Failed",
                            "error": "Voucher not created",
                            "tally_response": tally_response,
                            "transaction": tx
                        })
            except ET.ParseError:
                responses.append({
                    "batch": i // batch_size + 1,
                    "status": "Failed",
                    "error": "Invalid response from Tally",
                    "tally_response": tally_response,
                    "transaction": tx
                })
        except HTTPException as e:
            responses.append({
                "batch": i // batch_size + 1,
                "status": "Failed",
                "error": str(e.detail),
                "transaction": tx
            })

    return {
        "message": f"Pushed {sum(1 for r in responses if r['status'] == 'Success')} of {len(responses)} transactions.",
        "results": responses
    }


@app.get("/ledgers/by-company/{company_id}")
def get_ledgers_by_company(company_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT id, name, group_id FROM ledgers WHERE company_id=:cid"),
        {"cid": company_id}
    )
    ledgers = [{"id": row[0], "name": row[1], "group_id": row[2]} for row in result]
    return ledgers

@app.get("/")
def health_check():
    return {"status": "Tally SaaS API is running"}
