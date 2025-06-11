# Clark County APN Property Scraper

A high-performance web scraper for extracting property information from Clark County Nevada's assessor website. This tool achieves **0.5-1 second per APN** using optimized requests + BeautifulSoup instead of browser automation.

## 🚀 Features

- **High Performance**: Target 0.5-1 second per APN (vs 3-5 seconds with Selenium)
- **Session Pooling**: Reuses HTTP connections for maximum efficiency
- **Smart Form Handling**: Handles ASP.NET viewstate and form submissions
- **Robust Parsing**: Intelligent HTML parsing with multiple fallback patterns
- **Streaming Output**: Real-time results writing to CSV
- **Progress Tracking**: Detailed logging and progress reporting
- **Error Recovery**: Comprehensive error handling and retry logic

## 📦 Installation

1. Clone or download this project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🏃 Usage

### Basic Usage
```bash
python main.py data/input/sample_apns.csv
```

### Advanced Usage
```bash
python main.py input.csv -o output.csv --column APN --log-level DEBUG
```

### Command Line Options
- `input_file`: Path to CSV file containing APNs (required)
- `-o, --output`: Output CSV file path (default: data/output/scraped_properties.csv)
- `-c, --column`: Column name containing APNs (default: APN)
- `--batch-size`: Batch size for writing results (default: 50)
- `--no-stream`: Disable streaming output (write in batches)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

## 📊 Output Data

The scraper extracts the following fields:
- **APN**: Assessor Parcel Number
- **Address**: Primary property address
- **City**: Property city
- **State**: Property state (typically NV)
- **Zip_Code**: Property ZIP code
- **Owner1**: Primary owner name
- **Owner2**: Secondary owner (if exists)
- **Location_Address**: Physical location (if different from address)
- **Mailing_Address**: Complete mailing address
- **Status**: Success/Error indicator

## 📁 Project Structure

```
RE_Scraper_Light/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── data/
│   ├── input/             # Input CSV files
│   │   └── sample_apns.csv
│   └── output/            # Output CSV files
├── src/
│   ├── models/
│   │   └── property.py    # Property data model
│   ├── scraper/
│   │   ├── web_scraper.py # HTTP scraping logic
│   │   └── data_parser.py # HTML parsing logic
│   └── utils/
│       └── csv_handler.py # CSV I/O operations
└── tests/                 # Unit tests
```

## ⚡ Performance Optimizations

1. **Session Reuse**: Single HTTP session with connection pooling
2. **Fast Parser**: lxml parser for maximum HTML parsing speed
3. **Efficient Form Handling**: Smart ASP.NET viewstate management
4. **Minimal Overhead**: No browser automation overhead
5. **Streaming I/O**: Real-time output writing reduces memory usage

## 🛠 Development

### Running Tests
```bash
python -m pytest tests/
```

### Debug Mode
```bash
python main.py input.csv --log-level DEBUG
```

## 📝 Example Input CSV

```csv
APN
138-04-305-011
162-25-101-008
177-33-402-005
```

## 📈 Expected Performance

- **Target Speed**: 0.5-1 second per APN
- **Success Rate**: 95%+ for valid APNs
- **Memory Usage**: < 100MB for typical workloads
- **Scalability**: Handles thousands of APNs efficiently

## 🔧 Troubleshooting

### Common Issues

1. **Network Timeouts**: Increase timeout in `ClarkCountyScraper.__init__()`
2. **Parse Failures**: Enable DEBUG logging to inspect HTML structure
3. **Rate Limiting**: Add delays between requests if needed

### Logs Location
Log files are created in the project root with timestamp:
`scraper_YYYYMMDD_HHMMSS.log`

## 📄 License

This project is for educational and research purposes. Please respect Clark County's terms of service and implement appropriate rate limiting.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request