"""
scripmaster.py
Instrument master download and DB population
"""
import csv
from io import StringIO
from logger import get_logger
from auth import get_client
from database import db

logger = get_logger(__name__)

SEGMENTS = ['nse_cm', 'nse_fo', 'bse_cm', 'bse_fo', 'cde_fo']

def download_segment(segment_name: str) -> bool:
    """Download scrip master for a specific segment and save to database."""
    logger.info(f"Downloading scrip master for segment: {segment_name}")
    try:
        client = get_client()
        if not client:
            logger.error("Failed to get authenticated client.")
            return False

        response = client.scrip_master(exchange_segment=segment_name)
        if not response:
            logger.error(f"Empty response for segment {segment_name}")
            return False

        items_to_insert = []
        data = []
        
        # Handle both list of dicts and CSV text/URL formats
        if isinstance(response, str):
            if response.startswith("http://") or response.startswith("https://"):
                import requests
                logger.info(f"Downloading CSV from URL: {response}")
                csv_resp = requests.get(response, timeout=30)
                if csv_resp.status_code == 200:
                    reader = csv.DictReader(StringIO(csv_resp.text))
                    data = list(reader)
                else:
                    logger.error(f"Failed to fetch CSV from URL: {csv_resp.status_code}")
                    return False
            else:
                reader = csv.DictReader(StringIO(response))
                data = list(reader)
        elif isinstance(response, list):
            data = response
        else:
            logger.error(f"Unexpected response format for {segment_name}")
            return False

        # Map fields to database schema
        for row in data:
            def get_val(keys):
                for k in keys:
                    if k in row: return row[k]
                return ""
            
            token = get_val(['pSymbol', 'instrument_token', 'token', 'pTrdSymbol'])
            if not token:
                continue

            strike = get_val(['pStrikePrice', 'strike', 'strike_price'])
            strike = float(strike) if strike and strike.replace('.', '', 1).isdigit() else 0.0

            lot_size = get_val(['pLotSize', 'lot_size', 'board_lot_quantity'])
            lot_size = int(float(lot_size)) if lot_size and str(lot_size).replace('.', '', 1).isdigit() else 1
            
            tick_size = get_val(['pTickSize', 'tick_size'])
            tick_size = float(tick_size) if tick_size and str(tick_size).replace('.', '', 1).isdigit() else 0.05

            items_to_insert.append({
                "token": str(token),
                "symbol": str(get_val(['pSymbolName', 'symbol', 'name'])),
                "trading_symbol": str(get_val(['pTrdSymbol', 'trading_symbol', 'trd_symbol'])),
                "exchange": segment_name.split('_')[0].upper() if '_' in segment_name else "NSE",
                "segment": segment_name,
                "instrument_type": str(get_val(['pInstrumentType', 'instrument_type'])),
                "expiry": str(get_val(['pExpiryDate', 'expiry_date', 'expiry'])),
                "strike": strike,
                "option_type": str(get_val(['pOptionType', 'option_type'])),
                "lot_size": lot_size,
                "tick_size": tick_size,
                "isin": str(get_val(['pISIN', 'isin']))
            })

        if items_to_insert:
            db.bulk_insert(items_to_insert)
            logger.info(f"Inserted {len(items_to_insert)} records for {segment_name}")
            return True
        else:
            logger.warning(f"No valid records parsed for {segment_name}")
            return False

    except Exception as e:
        logger.error(f"Error downloading segment {segment_name}: {e}")
        return False

def download_all():
    """Download scrip master for all configured segments."""
    logger.info("Starting scrip master download for all segments")
    db.clear_all()
    success_count = 0
    
    for segment in SEGMENTS:
        if download_segment(segment):
            success_count += 1
            
    logger.info(f"Completed scrip master download. Success: {success_count}/{len(SEGMENTS)}")
    
if __name__ == '__main__':
    download_all()
