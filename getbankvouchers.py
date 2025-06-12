import requests

# Tally server details
TALLY_URL = "http://localhost:9000"

def send_to_tally(xml: str) -> str:
    """Send XML request to Tally and return the response."""
    headers = {"Content-Type": "application/xml"}
    try:
        response = requests.post(TALLY_URL, data=xml.encode('utf-8'), headers=headers)
        response.raise_for_status()
        print("\n[DEBUG] Raw Response Bytes:\n", response.content)
        print("\n[DEBUG] Raw Tally Response:\n", response.content.decode('utf-8', errors='replace'))
        return response.content.decode('utf-8', errors='replace')
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Tally: {str(e)}")
        return ""

def fetch_all_vouchers(company_name: str, start_date: str, end_date: str):
    """Fetch the raw Tally response for all vouchers within a date range."""
    xml = f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>All Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
            <SVFROMDATE>{start_date}</SVFROMDATE>
            <SVTODATE>{end_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="All Vouchers" ISINITIALIZE="Yes">
                <TYPE>Voucher</TYPE>
                <NATIVEMETHOD>DATE</NATIVEMETHOD>
                <NATIVEMETHOD>VOUCHERTYPENAME</NATIVEMETHOD>
                <NATIVEMETHOD>VOUCHERNUMBER</NATIVEMETHOD>
                <NATIVEMETHOD>PARTYLEDGERNAME</NATIVEMETHOD>
                <NATIVEMETHOD>AMOUNT</NATIVEMETHOD>
                <NATIVEMETHOD>MASTERID</NATIVEMETHOD>
                <NATIVEMETHOD>NARRATION</NATIVEMETHOD>
                <NATIVEMETHOD>ALLLEDGERENTRIES.LIST</NATIVEMETHOD>
              </COLLECTION>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
    print("\n[DEBUG] XML Sent to Tally:\n", xml)
    response = send_to_tally(xml)
    return response

def main():
    """Main function to fetch and display the raw Tally response for all vouchers."""
    company_name = "Test"  # Replace with your company name
    start_date = "20240401"  # April 1, 2024 (YYYYMMDD format)
    end_date = "20250630"    # June 30, 2025 (YYYYMMDD format)
    print(f"Fetching all vouchers for company '{company_name}' from {start_date} to {end_date} at {TALLY_URL}")
    fetch_all_vouchers(company_name, start_date, end_date)

if __name__ == "__main__":
    main()