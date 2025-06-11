"""Main application for Clark County APN property scraper."""

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List

from src.models.property import Property
from src.scraper.web_scraper import ClarkCountyScraper
from src.scraper.data_parser import PropertyDataParser
from src.utils.csv_handler import CSVHandler


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )


def scrape_properties(
    input_file: str,
    output_file: str,
    apn_column: str = "APN",
    batch_size: int = 50,
    stream_output: bool = True
) -> None:
    """
    Main scraping function.
    
    Args:
        input_file: Path to input CSV file with APNs
        output_file: Path to output CSV file for results
        apn_column: Name of column containing APNs
        batch_size: Number of properties to process before writing batch
        stream_output: Whether to stream results to file as they're processed
    """
    logger = logging.getLogger(__name__)
    
    # Initialize components
    csv_handler = CSVHandler()
    scraper = ClarkCountyScraper()
    parser = PropertyDataParser()
    
    try:
        # Read APNs from input file
        apns = csv_handler.read_apns_from_csv(input_file, apn_column)
        if not apns:
            logger.error("No APNs found in input file")
            return
        
        logger.info(f"Starting to scrape {len(apns)} properties")
        
        # Track progress and results
        start_time = time.time()
        processed_properties: List[Property] = []
        successful_count = 0
        failed_count = 0
        
        for i, apn in enumerate(apns, 1):
            logger.info(f"Processing {i}/{len(apns)}: {apn}")
            
            # Format APN
            formatted_apn = csv_handler.format_apn(apn)
            
            # Scrape property data
            soup, detail_url = scraper.scrape_property(formatted_apn)
            
            if soup:
                # Parse property data
                property_data = parser.parse_property_data(soup, formatted_apn)
                
                if property_data.status.startswith("Success"):
                    successful_count += 1
                    logger.info(f"Successfully scraped {formatted_apn}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to extract data for {formatted_apn}: {property_data.status}")
            else:
                # Create property with error status
                property_data = Property(apn=formatted_apn)
                property_data.mark_error("Failed to fetch page")
                failed_count += 1
                logger.error(f"Failed to scrape {formatted_apn}")
            
            processed_properties.append(property_data)
            
            # Stream output if enabled
            if stream_output:
                csv_handler.append_property_to_csv(property_data, output_file)
            
            # Write batch if not streaming
            elif len(processed_properties) >= batch_size:
                csv_handler.write_properties_to_csv(processed_properties, output_file)
                processed_properties.clear()
            
            # Progress update
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                estimated_total = avg_time * len(apns)
                remaining = estimated_total - elapsed
                
                logger.info(f"Progress: {i}/{len(apns)} ({i/len(apns)*100:.1f}%) - "
                           f"Avg: {avg_time:.2f}s/APN - "
                           f"Est. remaining: {remaining/60:.1f} min")
        
        # Write final batch if not streaming
        if not stream_output and processed_properties:
            csv_handler.write_properties_to_csv(processed_properties, output_file)
        
        # Final statistics
        total_time = time.time() - start_time
        avg_time = total_time / len(apns)
        
        logger.info(f"Scraping completed!")
        logger.info(f"Total time: {total_time/60:.2f} minutes")
        logger.info(f"Average time per APN: {avg_time:.2f} seconds")
        logger.info(f"Successful: {successful_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Success rate: {successful_count/len(apns)*100:.1f}%")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {e}")
    finally:
        scraper.close()


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="High-Performance Clark County APN Property Scraper"
    )
    
    parser.add_argument(
        "input_file",
        help="Path to input CSV file containing APNs"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="data/output/scraped_properties.csv",
        help="Path to output CSV file (default: data/output/scraped_properties.csv)"
    )
    
    parser.add_argument(
        "-c", "--column",
        default="APN",
        help="Name of column containing APNs (default: APN)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for writing results (default: 50)"
    )
    
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output (write in batches instead)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    # Run scraper
    scrape_properties(
        input_file=args.input_file,
        output_file=args.output,
        apn_column=args.column,
        batch_size=args.batch_size,
        stream_output=not args.no_stream
    )
    
    return 0


if __name__ == "__main__":
    exit(main())