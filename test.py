from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import io
from datetime import datetime
import xml.etree.ElementTree as ET
import logging
import requests
import html

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Tally URL for HTTP POST requests
TALLY_URL = "http://localhost:9000"

# In-memory storage for the JSON data (simulating a backend)
stored_data: Dict[str, Any] = {}

# Pydantic model for transaction updates (for frontend modifications)
class TransactionUpdate(BaseModel):
    index: int
    narration: Optional[str] = None
    amount: Optional[float] = None

# Function to escape special characters in XML
def escape_xml(text: str) -> str:
    if not text:
        return ""
    return html.escape(str(text), quote=False)

# Function to extract counterparty name from narration (for UPI transactions)
def extract_counterparty_name(narration: str) -> str:
    if "UPI" in narration:
        parts = narration.split("-")
        if len(parts) > 1:
            return parts[1].strip().capitalize()
    return "Unknown Counterparty"

# Function to fetch all ledgers from Tally
def fetch_all_ledgers(selected_company: str) -> List[str]:
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
    logger.info(f"Fetch ledgers response:\n{result}")
    ledgers = []
    try:
        root = ET.fromstring(result)
        for ledger in root.findall(".//LEDGER"):
            name = ledger.find(".//LANGUAGENAME.LIST/NAME.LIST/NAME")
            if name is not None and name.text:
                ledgers.append(name.text)
    except Exception as e:
        logger.error(f"Could not parse ledgers: {str(e)}")
    return ledgers

# Function to check if a ledger exists
def check_ledger_exists(ledger_name: str, selected_company: str) -> bool:
    ledgers = fetch_all_ledgers(selected_company)
    return ledger_name in ledgers

# Function to fetch available voucher types from Tally
def fetch_voucher_types(selected_company: str) -> List[str]:
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
    logger.info(f"Fetch voucher types response:\n{result}")
    voucher_types = []
    try:
        root = ET.fromstring(result)
        for vtype in root.findall(".//VOUCHERTYPE"):
            name = vtype.find(".//NAME")
            if name is not None and name.text:
                voucher_types.append(name.text)
    except Exception as e:
        logger.error(f"Could not parse voucher types: {str(e)}")
    return voucher_types

# Function to generate Tally XML for ledger creation
def generate_ledger_xml(ledger_name: str, parent_group: str) -> str:
    root = ET.Element("ENVELOPE")
    
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
    
    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "All Masters"
    
    request_data = ET.SubElement(import_data, "REQUESTDATA")
    
    tally_message = ET.SubElement(request_data, "TALLYMESSAGE")
    ledger = ET.SubElement(tally_message, "LEDGER", NAME=ledger_name, RESERVEDNAME="")
    ET.SubElement(ledger, "NAME").text = ledger_name
    ET.SubElement(ledger, "PARENT").text = parent_group
    ET.SubElement(ledger, "ISDEEMEDPOSITIVE").text = "No"
    ET.SubElement(ledger, "OPENINGBALANCE").text = "0"
    
    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

# Function to generate Tally XML for a batch of transactions
def generate_tally_xml(json_data: Dict[str, Any], selected_company: str = "Test", batch_transactions: List[Dict] = None) -> str:
    root = ET.Element("ENVELOPE")
    
    # Only include ledger creation for counterparties if this is the first batch
    if batch_transactions is None or batch_transactions == json_data["transactions"][:len(batch_transactions)]:
        header_ledger = ET.SubElement(root, "HEADER")
        ET.SubElement(header_ledger, "TALLYREQUEST").text = "Import Data"
        
        body_ledger = ET.SubElement(root, "BODY")
        import_data_ledger = ET.SubElement(body_ledger, "IMPORTDATA")
        
        request_desc_ledger = ET.SubElement(import_data_ledger, "REQUESTDESC")
        ET.SubElement(request_desc_ledger, "REPORTNAME").text = "All Masters"
        
        request_data_ledger = ET.SubElement(import_data_ledger, "REQUESTDATA")
        
        counterparties = set()
        for transaction in json_data["transactions"]:
            if transaction["transaction_type"] == "debit":
                counterparty = extract_counterparty_name(transaction["narration"])
                counterparties.add(counterparty)
        
        for counterparty in counterparties:
            if counterparty == "Unknown Counterparty":
                continue
            tally_message = ET.SubElement(request_data_ledger, "TALLYMESSAGE")
            ledger = ET.SubElement(tally_message, "LEDGER", NAME=counterparty, RESERVEDNAME="")
            ET.SubElement(ledger, "NAME").text = counterparty
            ET.SubElement(ledger, "PARENT").text = "Sundry Creditors"
            ET.SubElement(ledger, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(ledger, "OPENINGBALANCE").text = "0"
    
    # Voucher Creation Section
    header_voucher = ET.SubElement(root, "HEADER")
    ET.SubElement(header_voucher, "TALLYREQUEST").text = "Import Data"
    
    body_voucher = ET.SubElement(root, "BODY")
    import_data_voucher = ET.SubElement(body_voucher, "IMPORTDATA")
    
    request_desc_voucher = ET.SubElement(import_data_voucher, "REQUESTDESC")
    ET.SubElement(request_desc_voucher, "REPORTNAME").text = "Vouchers"
    static_vars = ET.SubElement(request_desc_voucher, "STATICVARIABLES")
    ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = selected_company
    
    request_data_voucher = ET.SubElement(import_data_voucher, "REQUESTDATA")
    
    bank_ledger = "ICICI Bank"
    cash_ledger = "Cash"
    fallback_ledger = "Miscellaneous Expenses"
    
    logger.info(f"Using ledgers: Bank={bank_ledger}, Cash={cash_ledger}, Fallback={fallback_ledger}")
    
    transactions_to_process = batch_transactions if batch_transactions is not None else json_data["transactions"]
    
    for transaction in transactions_to_process:
        tally_message = ET.SubElement(request_data_voucher, "TALLYMESSAGE")
        
        voucher_type = "Payment" if transaction["transaction_type"] == "debit" else "Receipt"
        amount = transaction["withdrawal_amount"] if transaction["transaction_type"] == "debit" else transaction["deposit_amount"]
        
        if transaction["transaction_type"] == "debit":
            from_ledger = bank_ledger
            to_ledger = extract_counterparty_name(transaction["narration"])
            if to_ledger == "Unknown Counterparty":
                to_ledger = fallback_ledger
        else:
            from_ledger = cash_ledger
            to_ledger = bank_ledger
        
        logger.info(f"Transaction ref_no={transaction['ref_no']}: from_ledger={from_ledger}, to_ledger={to_ledger}")
        
        guid = f"VCH-{transaction['ref_no']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        voucher_number = f"VCH-{transaction['ref_no']}"
        
        voucher = ET.SubElement(tally_message, "VOUCHER", VCHTYPE=voucher_type, ACTION="Create", OBJVIEW="Accounting Voucher View")
        ET.SubElement(voucher, "GUID").text = guid
        ET.SubElement(voucher, "VOUCHERNUMBER").text = voucher_number
        ET.SubElement(voucher, "DATE").text = datetime.strptime(transaction["date"], "%Y-%m-%d").strftime("%Y%m%d")
        ET.SubElement(voucher, "NARRATION").text = escape_xml(transaction["narration"])
        ET.SubElement(voucher, "VOUCHERTYPENAME").text = voucher_type
        
        ledger_entry1 = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(ledger_entry1, "LEDGERNAME").text = from_ledger
        ET.SubElement(ledger_entry1, "ISDEEMEDPOSITIVE").text = "Yes" if transaction["transaction_type"] == "debit" else "No"
        amount1 = -amount if transaction["transaction_type"] == "debit" else amount
        ET.SubElement(ledger_entry1, "AMOUNT").text = str(amount1)
        
        ledger_entry2 = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(ledger_entry2, "LEDGERNAME").text = to_ledger
        ET.SubElement(ledger_entry2, "ISDEEMEDPOSITIVE").text = "No" if transaction["transaction_type"] == "debit" else "Yes"
        amount2 = amount if transaction["transaction_type"] == "debit" else -amount
        ET.SubElement(ledger_entry2, "AMOUNT").text = str(amount2)
    
    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

# Function to send XML to Tally via HTTP POST
def send_to_tally(xml_data: str) -> str:
    # Log the XML to a file for debugging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"tally_xml_{timestamp}.xml", "w", encoding="utf-8") as f:
        f.write(xml_data)
    
    logger.info("Sending XML data to Tally")
    logger.debug(f"XML content:\n{xml_data}")
    
    try:
        response = requests.post(TALLY_URL, data=xml_data.encode("utf-8"))
        response.raise_for_status()
        logger.info(f"Tally response: {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending data to Tally: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending data to Tally: {str(e)}")

# Endpoint to upload and parse the Excel file
@app.post("/upload-statement/")
async def upload_statement(file: UploadFile):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")

    # Read the Excel file
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Sheet 1", engine="xlrd", header=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing Excel file: {str(e)}")

    # Debug: Log the entire DataFrame to inspect its structure
    logger.info("DataFrame shape: %s", df.shape)
    logger.info("DataFrame:\n%s", df.to_string())

    # Parse the Excel data into JSON
    try:
        account_info = {}
        transaction_start_row = None
        for idx, row in df.iterrows():
            row_values = str(row.values)
            if "Date" in row_values and "Narration" in row_values:
                transaction_start_row = idx
                break

        if transaction_start_row is None:
            logger.warning("Could not find transaction header row in Excel file")
            transactions = []
        else:
            df_transactions = pd.read_excel(
                io.BytesIO(contents),
                sheet_name="Sheet 1",
                skiprows=transaction_start_row,
                header=0,
                engine="xlrd"
            )

            logger.info("Transaction DataFrame head:\n%s", df_transactions.head().to_string())
            logger.info("Transaction DataFrame columns: %s", df_transactions.columns.tolist())

            transactions = []
            for idx, row in df_transactions.iterrows():
                if pd.isna(row.get('Date')) or "STATEMENT SUMMARY" in str(row.get('Date', '')):
                    break

                try:
                    date_str = str(row['Date']).strip()
                    if not date_str or date_str.lower() == "nan":
                        continue

                    date = pd.to_datetime(date_str, format="%d/%m/%y").strftime("%Y-%m-%d")
                    narration = str(row['Narration']).strip()
                    ref_no = str(row['Chq./Ref.No.']).strip()
                    value_date = pd.to_datetime(str(row['Value Dt']).strip(), format="%d/%m/%y").strftime("%Y-%m-%d")

                    withdrawal_amt = 0.0
                    deposit_amt = 0.0
                    closing_balance = 0.0

                    withdrawal_str = str(row['Withdrawal Amt.']).strip()
                    if withdrawal_str and withdrawal_str.lower() != "nan":
                        try:
                            withdrawal_amt = float(withdrawal_str.replace(',', ''))
                        except ValueError:
                            logger.warning(f"Invalid Withdrawal Amt. in row {idx}: {withdrawal_str}")

                    deposit_str = str(row['Deposit Amt.']).strip()
                    if deposit_str and deposit_str.lower() != "nan":
                        try:
                            deposit_amt = float(deposit_str.replace(',', ''))
                        except ValueError:
                            logger.warning(f"Invalid Deposit Amt. in row {idx}: {deposit_str}")

                    closing_balance_str = str(row['Closing Balance']).strip()
                    if closing_balance_str and closing_balance_str.lower() != "nan":
                        try:
                            closing_balance = float(closing_balance_str.replace(',', ''))
                        except ValueError:
                            logger.warning(f"Invalid Closing Balance in row {idx}: {closing_balance_str}")

                    transaction_type = "debit" if withdrawal_amt > 0 else "credit"
                    category = "UPI Payment" if "UPI" in narration else "Other"

                    transaction = {
                        "date": date,
                        "narration": narration,
                        "ref_no": ref_no,
                        "value_date": value_date,
                        "withdrawal_amount": withdrawal_amt,
                        "deposit_amount": deposit_amt,
                        "closing_balance": closing_balance,
                        "transaction_type": transaction_type,
                        "category": category
                    }
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Error parsing transaction row {idx}: {row.to_dict()}, Error: {str(e)}")
                    continue

        json_data = {"account_info": account_info, "transactions": transactions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Excel data: {str(e)}")

    statement_id = "statement_1"
    stored_data[statement_id] = json_data

    return {"statement_id": statement_id, "data": json_data}

# Endpoint to retrieve the stored JSON (for frontend display)
@app.get("/statement/{statement_id}")
async def get_statement(statement_id: str):
    if statement_id not in stored_data:
        raise HTTPException(status_code=404, detail="Statement not found")
    return stored_data[statement_id]

# Endpoint to modify a transaction (simulating frontend updates)
@app.put("/statement/{statement_id}/transaction")
async def update_transaction(statement_id: str, update: TransactionUpdate):
    if statement_id not in stored_data:
        raise HTTPException(status_code=404, detail="Statement not found")

    transactions = stored_data[statement_id]["transactions"]
    if update.index < 0 or update.index >= len(transactions):
        raise HTTPException(status_code=400, detail="Invalid transaction index")

    if update.narration is not None:
        transactions[update.index]["narration"] = update.narration
    if update.amount is not None:
        if transactions[update.index]["transaction_type"] == "debit":
            transactions[update.index]["withdrawal_amount"] = update.amount
            transactions[update.index]["deposit_amount"] = 0.0
        else:
            transactions[update.index]["deposit_amount"] = update.amount
            transactions[update.index]["withdrawal_amount"] = 0.0

    if transactions:
        current_balance = transactions[0]["closing_balance"] - (transactions[0]["deposit_amount"] - transactions[0]["withdrawal_amount"])
    else:
        current_balance = 0.0

    for i, tx in enumerate(transactions):
        if tx["transaction_type"] == "debit":
            current_balance -= tx["withdrawal_amount"]
        else:
            current_balance += tx["deposit_amount"]
        tx["closing_balance"] = current_balance

    return {"message": "Transaction updated", "data": stored_data[statement_id]}

# Endpoint to send data to Tally via HTTP POST in batches
@app.get("/statement/{statement_id}/tally-sync")
async def send_to_tally_endpoint(statement_id: str, selected_company: str = "Test"):
    if statement_id not in stored_data:
        raise HTTPException(status_code=404, detail="Statement not found")

    json_data = stored_data[statement_id]
    transactions = json_data["transactions"]
    
    if not transactions:
        return {"message": "No transactions to sync with Tally"}

    # Step 1: Validate financial year
    financial_year_start = datetime.strptime("2025-04-01", "%Y-%m-%d")
    financial_year_end = datetime.strptime("2026-03-31", "%Y-%m-%d")
    for tx in transactions:
        tx_date = datetime.strptime(tx["date"], "%Y-%m-%d")
        if tx_date < financial_year_start or tx_date > financial_year_end:
            logger.warning(f"Transaction date {tx['date']} (ref_no={tx['ref_no']}) is outside the financial year 2025-2026")

    # Step 2: Validate ledgers
    required_ledgers = [
        ("ICICI Bank", "Bank Accounts"),
        ("Cash", "Cash-in-hand"),
        ("Miscellaneous Expenses", "Indirect Expenses")
    ]
    
    for ledger_name, parent_group in required_ledgers:
        if not check_ledger_exists(ledger_name, selected_company):
            logger.info(f"Creating ledger: {ledger_name} under {parent_group}")
            xml_str = generate_ledger_xml(ledger_name, parent_group)
            try:
                response = send_to_tally(xml_str)
                try:
                    root = ET.fromstring(response)
                    if "<LINEERROR>" in response:
                        error = root.find(".//LINEERROR")
                        error_detail = error.text if error is not None else "Unknown error"
                        raise HTTPException(status_code=400, detail=f"Ledger {ledger_name} creation failed: {error_detail}")
                    else:
                        logger.info(f"Ledger {ledger_name} created or already exists")
                except ET.ParseError:
                    logger.warning(f"Invalid response from Tally for ledger {ledger_name}: {response}")
                    raise HTTPException(status_code=500, detail=f"Invalid response from Tally for ledger {ledger_name}")
            except HTTPException as e:
                logger.warning(f"Failed to create ledger {ledger_name}: {e.detail}")
                raise

    # Validate counterparty ledgers
    counterparties = set()
    for transaction in transactions:
        if transaction["transaction_type"] == "debit":
            counterparty = extract_counterparty_name(transaction["narration"])
            if counterparty != "Unknown Counterparty":
                counterparties.add(counterparty)

    for counterparty in counterparties:
        if not check_ledger_exists(counterparty, selected_company):
            logger.info(f"Creating counterparty ledger: {counterparty} under Sundry Creditors")
            xml_str = generate_ledger_xml(counterparty, "Sundry Creditors")
            try:
                response = send_to_tally(xml_str)
                try:
                    root = ET.fromstring(response)
                    if "<LINEERROR>" in response:
                        error = root.find(".//LINEERROR")
                        error_detail = error.text if error is not None else "Unknown error"
                        raise HTTPException(status_code=400, detail=f"Ledger {counterparty} creation failed: {error_detail}")
                    else:
                        logger.info(f"Ledger {counterparty} created or already exists")
                except ET.ParseError:
                    logger.warning(f"Invalid response from Tally for ledger {counterparty}: {response}")
                    raise HTTPException(status_code=500, detail=f"Invalid response from Tally for ledger {counterparty}")
            except HTTPException as e:
                logger.warning(f"Failed to create ledger {counterparty}: {e.detail}")
                raise

    # Step 3: Validate voucher types
    required_voucher_types = ["Payment", "Receipt"]
    available_voucher_types = fetch_voucher_types(selected_company)
    for vtype in required_voucher_types:
        if vtype not in available_voucher_types:
            raise HTTPException(status_code=400, detail=f"Voucher type '{vtype}' does not exist in Tally")

    # Step 4: Process transactions in batches of 1 (for debugging)
    batch_size = 1
    responses = []
    
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} transactions")
        
        # Generate XML for the batch
        xml_str = generate_tally_xml(json_data, selected_company, batch_transactions=batch)
        
        # Send the XML to Tally
        try:
            response = send_to_tally(xml_str)
            
            # Parse Tally's response
            try:
                root = ET.fromstring(response)
                if "<LINEERROR>" in response:
                    error = root.find(".//LINEERROR")
                    error_detail = error.text if error is not None else "Unknown error"
                    responses.append({"batch": i//batch_size + 1, "status": "Failed", "error": error_detail, "tally_response": response})
                else:
                    created = root.find(".//CREATED")
                    if created is not None and int(created.text) > 0:  # Updated logic to accept CREATED > 0
                        responses.append({"batch": i//batch_size + 1, "status": "Success", "tally_response": response})
                    else:
                        responses.append({"batch": i//batch_size + 1, "status": "Failed", "error": "Voucher not created", "tally_response": response})
            except ET.ParseError:
                responses.append({"batch": i//batch_size + 1, "status": "Failed", "error": "Invalid response from Tally", "tally_response": response})
        except HTTPException as e:
            responses.append({"batch": i//batch_size + 1, "status": "Failed", "error": e.detail})
    
    # Summarize the results
    success_count = sum(1 for r in responses if r["status"] == "Success")
    failure_count = len(responses) - success_count
    
    if failure_count == 0:
        return {"message": f"Successfully synced {len(transactions)} transactions to Tally", "batches": responses}
    else:
        return {"message": f"Synced {success_count} batches successfully, {failure_count} failed", "batches": responses}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)