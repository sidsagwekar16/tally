import requests
import xml.etree.ElementTree as ET
import argparse
from datetime import datetime

# Tally server URL (adjust if your Tally server runs on a different port or host)
TALLY_URL = "http://localhost:9000"

# Function to send XML request to Tally and get response
def send_tally_request(xml_data):
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(TALLY_URL, data=xml_data, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Tally: {e}")
        return None

# 1. Fetch Journal Vouchers NOT WORKING NOT WORKING 
def fetch_journal_vouchers(from_date, to_date):
    fetch_xml = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Export</TALLYREQUEST>
  <TYPE>Collection</TYPE>
  <ID>JournalVouchers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVFROMDATE TYPE="Date">{from_date}</SVFROMDATE>
    <SVTODATE TYPE="Date">{to_date}</SVTODATE>
    <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLMESSAGE>
     <COLLECTION NAME="JournalVouchers" ISMODIFY="No">
      <TYPE>Voucher</TYPE>
      <FETCH>ALLLEDGERENTRIES.*</FETCH>
      <FILTERS>VoucherTypeFilter</FILTERS>
     </COLLECTION>
     <SYSTEM TYPE="Formulae" NAME="VoucherTypeFilter">$$IsJournal:$$VoucherType</SYSTEM>
    </TDLMESSAGE>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    response = send_tally_request(fetch_xml)
    if response:
        print("\n=== Fetch Journal Vouchers Response ===")
        print(response)
        
        # Parse the response to check if any Journal Vouchers exist
        root = ET.fromstring(response)
        collection = root.find(".//COLLECTION")
        if collection is None:
            print("No COLLECTION tag found in the response.")
            return response
        
        vouchers = collection.findall("VOUCHER")
        if vouchers:
            print(f"Found {len(vouchers)} Journal Voucher(s):")
            for voucher in vouchers:
                voucher_number = voucher.find("VOUCHERNUMBER")
                amount = voucher.find("AMOUNT")
                narration = voucher.find("NARRATION")
                
                voucher_number_text = voucher_number.text if voucher_number is not None else "Unknown"
                amount_text = amount.text if amount is not None else "0.00"
                narration_text = narration.text if narration is not None else "No narration"
                
                print(f"- Voucher Number: {voucher_number_text}, Amount: {amount_text}, Narration: {narration_text}")
        else:
            print("No Journal Vouchers found for the specified date range.")
    return response

# 2. Create a Journal Voucher
def create_journal_voucher(voucher_number, date):
    create_xml = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Import</TALLYREQUEST>
  <TYPE>Data</TYPE>
  <ID>Vouchers</ID>
 </HEADER>
 <BODY>
  <DESC>
  </DESC>
  <DATA>
   <TALLYMESSAGE>
    <VOUCHER VCHTYPE="Journal" ACTION="Create">
     <DATE>{date}</DATE>
     <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
     <PARTYLEDGERNAME>Cash</PARTYLEDGERNAME>
     <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
     <NARRATION>Payment to Aparna for April 2025</NARRATION>
     <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>Aparna</LEDGERNAME>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <AMOUNT>5000.00</AMOUNT>
     </ALLLEDGERENTRIES.LIST>
     <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>Cash</LEDGERNAME>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <AMOUNT>-5000.00</AMOUNT>
     </ALLLEDGERENTRIES.LIST>
    </VOUCHER>
   </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>"""
    
    response = send_tally_request(create_xml)
    if response:
        print("\n=== Create Journal Voucher Response ===")
        print(response)
        root = ET.fromstring(response)
        created = root.find(".//CREATED")
        if created is not None and created.text == "1":
            print("Journal Voucher created successfully.")
        else:
            print("Failed to create Journal Voucher.")
    return response

# Main function with CLI support
def main():
    parser = argparse.ArgumentParser(description="Tally ERP 9 Journal Voucher CLI Tool")
    parser.add_argument('--fetch', action='store_true', help="Fetch Journal Vouchers for a date range")
    parser.add_argument('--create', action='store_true', help="Create a new Journal Voucher")
    parser.add_argument('--alter', action='store_true', help="Alter an existing Journal Voucher")
    parser.add_argument('--delete', action='store_true', help="Delete a Journal Voucher")
    parser.add_argument('--from-date', type=str, default="20250401", help="From date (YYYYMMDD, default: 20250401)")
    parser.add_argument('--to-date', type=str, default="20250401", help="To date (YYYYMMDD, default: 20250401)")
    parser.add_argument('--voucher-number', type=str, default="JV-001", help="Voucher number (default: JV-001)")
    parser.add_argument('--date', type=str, default="20250401", help="Voucher date (YYYYMMDD, default: 20250401)")

    args = parser.parse_args()

    # Check if at least one action is specified
    if not (args.fetch or args.create or args.alter or args.delete):
        parser.error("At least one action (--fetch, --create, --alter, --delete) must be specified.")

    # Execute the requested actions
    if args.fetch:
        print("Fetching Journal Vouchers...")
        fetch_journal_vouchers(args.from_date, args.to_date)

    if args.create:
        print("\nCreating a new Journal Voucher...")
        create_journal_voucher(args.voucher_number, args.date)


if __name__ == "__main__":
    main()