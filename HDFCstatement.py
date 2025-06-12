from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import io
from datetime import datetime
import xml.etree.ElementTree as ET
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory storage for the JSON data (simulating a backend)
stored_data: Dict[str, Any] = {}

# Pydantic model for transaction updates (for frontend modifications)
class TransactionUpdate(BaseModel):
    index: int
    narration: Optional[str] = None
    amount: Optional[float] = None

# Function to generate Tally XML for bulk voucher creation
def generate_tally_xml(json_data: Dict[str, Any], selected_company: str = "Test") -> str:
    root = ET.Element("ENVELOPE")
    
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
    static_vars = ET.SubElement(request_desc, "STATICVARIABLES")
    ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = selected_company

    request_data = ET.SubElement(import_data, "REQUESTDATA")
    
    # Bank ledger (assumed to exist in Tally)
    bank_ledger = "HDFC Bank"

    for transaction in json_data["transactions"]:
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE")
        voucher = ET.SubElement(tally_message, "VOUCHER", VCHTYPE="Payment" if transaction["transaction_type"] == "debit" else "Receipt", ACTION="Create", OBJVIEW="Accounting Voucher View")
        
        ET.SubElement(voucher, "GUID").text = f"VCH-{transaction['ref_no']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        ET.SubElement(voucher, "VOUCHERNUMBER").text = f"VCH-{transaction['ref_no']}"
        ET.SubElement(voucher, "DATE").text = datetime.strptime(transaction["date"], "%Y-%m-%d").strftime("%Y%m%d")
        ET.SubElement(voucher, "NARRATION").text = transaction["narration"]
        ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Payment" if transaction["transaction_type"] == "debit" else "Receipt"

        # From ledger entry (Bank)
        ledger_entry1 = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(ledger_entry1, "LEDGERNAME").text = bank_ledger
        ET.SubElement(ledger_entry1, "ISDEEMEDPOSITIVE").text = "Yes" if transaction["transaction_type"] == "debit" else "No"
        amount1 = -transaction["withdrawal_amount"] if transaction["transaction_type"] == "debit" else transaction["deposit_amount"]
        ET.SubElement(ledger_entry1, "AMOUNT").text = str(amount1)

        # To ledger entry (assumed "Aparna" for debit, "Cash" for credit)
        ledger_entry2 = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        to_ledger = "Aparna" if transaction["transaction_type"] == "debit" else "Cash"
        ET.SubElement(ledger_entry2, "LEDGERNAME").text = to_ledger
        ET.SubElement(ledger_entry2, "ISDEEMEDPOSITIVE").text = "No" if transaction["transaction_type"] == "debit" else "Yes"
        amount2 = transaction["withdrawal_amount"] if transaction["transaction_type"] == "debit" else -transaction["deposit_amount"]
        ET.SubElement(ledger_entry2, "AMOUNT").text = str(amount2)

    # Convert the XML tree to a string
    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

# Endpoint to upload and parse the Excel file
@app.post("/upload-statement/")
async def upload_statement(file: UploadFile):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")

    # Read the Excel file
    try:
        contents = await file.read()
        # Use xlrd engine for .xls files
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Sheet 1", engine="xlrd", header=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing Excel file: {str(e)}")

    # Debug: Log the entire DataFrame to inspect its structure
    logger.info("DataFrame shape: %s", df.shape)
    logger.info("DataFrame:\n%s", df.to_string())

    # Parse the Excel data into JSON
    try:
        # Skip account_info parsing
        account_info = {}

        # Find the transaction header row dynamically
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
            # Read the DataFrame again, starting from the transaction header row
            # Set the header row explicitly to ensure correct column names
            df_transactions = pd.read_excel(
                io.BytesIO(contents),
                sheet_name="Sheet 1",
                skiprows=transaction_start_row,
                header=0,  # Use the first row after skiprows as the header
                engine="xlrd"
            )

            # Debug: Log the transaction DataFrame
            logger.info("Transaction DataFrame head:\n%s", df_transactions.head().to_string())
            logger.info("Transaction DataFrame columns: %s", df_transactions.columns.tolist())

            # Parse transactions from the DataFrame
            transactions = []
            for idx, row in df_transactions.iterrows():
                # Stop parsing at "STATEMENT SUMMARY"
                if pd.isna(row.get('Date')) or "STATEMENT SUMMARY" in str(row.get('Date', '')):
                    break

                # Parse each transaction row
                try:
                    # Clean and parse the data
                    date_str = str(row['Date']).strip()
                    if not date_str or date_str.lower() == "nan":
                        continue  # Skip rows with empty or invalid dates

                    date = pd.to_datetime(date_str, format="%d/%m/%y").strftime("%Y-%m-%d")
                    narration = str(row['Narration']).strip()
                    ref_no = str(row['Chq./Ref.No.']).strip()
                    value_date = pd.to_datetime(str(row['Value Dt']).strip(), format="%d/%m/%y").strftime("%Y-%m-%d")

                    # Clean numeric fields
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

    # Store the JSON in memory (simulating backend storage)
    statement_id = "statement_1"  # In a real app, this would be a unique ID
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

    # Update the transaction
    if update.narration is not None:
        transactions[update.index]["narration"] = update.narration
    if update.amount is not None:
        if transactions[update.index]["transaction_type"] == "debit":
            transactions[update.index]["withdrawal_amount"] = update.amount
            transactions[update.index]["deposit_amount"] = 0.0
        else:
            transactions[update.index]["deposit_amount"] = update.amount
            transactions[update.index]["withdrawal_amount"] = 0.0

    # Update closing balances (recompute based on the modified transactions)
    # Since we don't have opening_balance, assume the first transaction's closing_balance
    # is the starting point, or start from 0 if no transactions exist
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

    # Since account_info is empty, we can't update closing_balance here
    return {"message": "Transaction updated", "data": stored_data[statement_id]}

# Endpoint to generate Tally XML from the JSON
@app.get("/statement/{statement_id}/tally-xml")
async def generate_tally_xml_endpoint(statement_id: str, selected_company: str = "Test"):
    if statement_id not in stored_data:
        raise HTTPException(status_code=404, detail="Statement not found")

    json_data = stored_data[statement_id]
    xml_str = generate_tally_xml(json_data, selected_company)

    return {"tally_xml": xml_str}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)