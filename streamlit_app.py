"""
Clark County APN Property Scraper - Streamlit Web Interface
High-performance web scraping for Nevada property data with modern UI
"""

import streamlit as st
import pandas as pd
import io
import time
import logging
from typing import List
from datetime import datetime

# Import existing scraper components
from src.scraper.web_scraper import ClarkCountyScraper
from src.scraper.data_parser import PropertyDataParser
from src.models.property import Property
from src.utils.csv_handler import CSVHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Processing function - defined early so it can be called later
def process_apns(apns: List[str], delay: float):
    """Process APNs with real-time progress updates."""
    
    # Progress containers
    progress_container = st.container()
    status_container = st.empty()
    
    with progress_container:
        st.markdown("### 🔄 Processing in Progress...")
        progress_bar = st.progress(0)
        progress_text = st.empty()
    
    # Real-time metrics
    metrics_container = st.container()
    
    # Initialize scraper components
    csv_handler = CSVHandler()
    scraper = ClarkCountyScraper()
    parser = PropertyDataParser()
    
    properties: List[Property] = []
    start_time = time.time()
    successful_count = 0
    failed_count = 0
    
    try:
        for i, apn in enumerate(apns):
            current_time = time.time()
            elapsed_time = current_time - start_time
            avg_time_per_apn = elapsed_time / (i + 1) if i > 0 else 0
            eta_seconds = avg_time_per_apn * (len(apns) - i - 1) if i > 0 else 0
            
            # Update status
            status_container.markdown(f"""
            **Currently Processing:** `{apn}` ({i+1}/{len(apns)})  
            **Average Speed:** {avg_time_per_apn:.2f}s per APN  
            **ETA:** {eta_seconds/60:.1f} minutes remaining
            """)
            
            # Update real-time metrics
            with metrics_container:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Progress", f"{i}/{len(apns)}")
                with col2:
                    st.metric("Successful", successful_count)
                with col3:
                    st.metric("Failed", failed_count)
                with col4:
                    success_rate = (successful_count / i * 100) if i > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Format APN and scrape
            formatted_apn = csv_handler.format_apn(apn)
            
            try:
                soup, detail_url = scraper.scrape_property(formatted_apn)
                
                if soup:
                    property_data = parser.parse_property_data(soup, formatted_apn)
                    if property_data.status.startswith("Success"):
                        successful_count += 1
                    else:
                        failed_count += 1
                else:
                    property_data = Property(apn=formatted_apn)
                    property_data.mark_error("Failed to fetch page")
                    failed_count += 1
                
                properties.append(property_data)
                
            except Exception as e:
                error_property = Property(apn=formatted_apn)
                error_property.mark_error(str(e))
                properties.append(error_property)
                failed_count += 1
            
            # Update progress
            progress_bar.progress((i + 1) / len(apns))
            progress_text.text(f"Progress: {i+1}/{len(apns)} ({(i+1)/len(apns)*100:.1f}%)")
            
            # Apply delay
            if i < len(apns) - 1:
                time.sleep(delay)
        
        # Store results in session state
        total_time = time.time() - start_time
        avg_speed = total_time / len(apns)
        success_rate = (successful_count / len(apns)) * 100
        
        st.session_state.scraped_data = properties
        st.session_state.processing_stats = {
            'total': len(apns),
            'successful': successful_count,
            'failed': failed_count,
            'success_rate': success_rate,
            'total_time': total_time,
            'avg_speed': avg_speed
        }
        st.session_state.processing_complete = True
        
        # Clear progress display
        progress_container.empty()
        status_container.empty()
        metrics_container.empty()
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
    finally:
        scraper.close()

# Page configuration
st.set_page_config(
    page_title="Clark County APN Scraper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    
    .upload-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 2px dashed #6c757d;
        text-align: center;
        margin: 2rem 0;
    }
    
    .processing-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 0.5rem;
    }
    
    .download-section {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
    }
    
    .step-indicator {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
    }
    
    .step {
        background: #e9ecef;
        color: #6c757d;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin: 0 1rem;
    }
    
    .step.active {
        background: #667eea;
        color: white;
    }
    
    .step.completed {
        background: #28a745;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'processing_stats' not in st.session_state:
    st.session_state.processing_stats = None

# Header section
st.markdown('<h1 class="main-header">🏠 Clark County APN Property Scraper</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">High-performance web scraping for Nevada property data</p>', unsafe_allow_html=True)

# Step indicator
current_step = 1
if st.session_state.processing_complete:
    current_step = 3
elif 'uploaded_file' in st.session_state and st.session_state.uploaded_file is not None:
    current_step = 2

st.markdown(f"""
<div class="step-indicator">
    <div class="step {'completed' if current_step > 1 else 'active' if current_step == 1 else ''}">1</div>
    <div style="width: 50px; height: 2px; background: {'#28a745' if current_step > 1 else '#e9ecef'};"></div>
    <div class="step {'completed' if current_step > 2 else 'active' if current_step == 2 else ''}">2</div>
    <div style="width: 50px; height: 2px; background: {'#28a745' if current_step > 2 else '#e9ecef'};"></div>
    <div class="step {'active' if current_step == 3 else ''}">3</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <strong>Step 1:</strong> Upload File &nbsp;&nbsp;&nbsp;
    <strong>Step 2:</strong> Process Data &nbsp;&nbsp;&nbsp;
    <strong>Step 3:</strong> Download Results
</div>
""", unsafe_allow_html=True)

# Step 1: File Upload Section
if not st.session_state.processing_complete:
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📁 Upload Your APN File")
    st.markdown("Drag and drop your CSV or TXT file containing APNs, or click to browse")
    
    uploaded_file = st.file_uploader(
        "",
        type=['csv', 'txt'],
        help="Supported formats: CSV with APN column or TXT with one APN per line",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        try:
            # Process uploaded file
            content = uploaded_file.read().decode('utf-8')
            apns = []
            
            if uploaded_file.name.endswith('.csv'):
                # Handle CSV files
                lines = content.split('\n')
                # Try to find APN column or use first column
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        apn = line.split(',')[0].strip().strip('"')
                        if apn and apn.upper() != 'APN':
                            apns.append(apn)
            else:
                # Handle TXT files
                apns = [line.strip() for line in content.split('\n') if line.strip()]
            
            st.session_state.uploaded_file = uploaded_file
            st.session_state.apns = apns
            
            # Show file preview
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.success(f"✅ Successfully loaded **{len(apns)}** APNs from `{uploaded_file.name}`")
                
                if len(apns) > 0:
                    with st.expander("📋 Preview APNs"):
                        preview_count = min(10, len(apns))
                        for i in range(preview_count):
                            st.write(f"• {apns[i]}")
                        if len(apns) > 10:
                            st.write(f"... and {len(apns) - 10} more APNs")
            
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            
    st.markdown('</div>', unsafe_allow_html=True)

# Step 2: Processing Section
if 'apns' in st.session_state and st.session_state.apns and not st.session_state.processing_complete:
    st.markdown('<div class="processing-card">', unsafe_allow_html=True)
    st.markdown("### ⚡ Processing Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Ready to process {len(st.session_state.apns)} APNs**")
        st.markdown("• Target speed: 0.5-1 second per APN")
        st.markdown("• High-performance requests.Session + lxml parsing")
        st.markdown("• Real-time progress tracking")
    
    with col2:
        delay_setting = st.selectbox(
            "Request delay:",
            options=[0.2, 0.3, 0.5, 1.0],
            index=1,
            format_func=lambda x: f"{x}s"
        )
    
    # Start processing button
    if st.button("🚀 Start Processing", type="primary", use_container_width=True):
        process_apns(st.session_state.apns, delay_setting)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Step 3: Results and Download Section
if st.session_state.processing_complete and st.session_state.scraped_data is not None:
    st.markdown('<div class="success-card">', unsafe_allow_html=True)
    st.markdown("### ✅ Processing Complete!")
    
    stats = st.session_state.processing_stats
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Processed", stats['total'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Successful", stats['successful'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg Speed", f"{stats['avg_speed']:.2f}s")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download section
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    st.markdown("### 📥 Download Your Results")
    
    # Prepare CSV data
    df = pd.DataFrame([prop.to_dict() for prop in st.session_state.scraped_data])
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"clark_county_properties_{timestamp}.csv"
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label=f"📥 Download CSV ({len(df)} properties)",
            data=csv_buffer.getvalue(),
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        
        st.markdown(f"**File:** `{filename}`")
        st.markdown(f"**Size:** {len(csv_buffer.getvalue())} characters")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Data preview
    with st.expander("📊 Preview Results"):
        st.dataframe(df, use_container_width=True, height=400)
    
    # Reset button
    if st.button("🔄 Process New File", use_container_width=True):
        # Reset session state
        for key in ['processing_complete', 'scraped_data', 'processing_stats', 'uploaded_file', 'apns']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d; padding: 1rem;'>
    <small>
        🏠 <strong>Clark County APN Property Scraper</strong> • 
        High-performance Nevada property data extraction • 
        Built with Streamlit & Python
    </small>
</div>
""", unsafe_allow_html=True)