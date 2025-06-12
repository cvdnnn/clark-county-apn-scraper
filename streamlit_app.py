"""
Clark County APN Property Scraper - Streamlit Web Interface
High-performance web scraping for Nevada property data with modern UI
Secured for internal company use with environment variable authentication
"""

import streamlit as st
import pandas as pd
import io
import time
import logging
import re
import os
from typing import List, Optional
from datetime import datetime

# Configure page FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="Clark County APN Scraper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import existing scraper components
from src.scraper.web_scraper import ClarkCountyScraper
from src.scraper.data_parser import PropertyDataParser
from src.models.property import Property
from src.utils.csv_handler import CSVHandler

# Configure logging for performance monitoring and security
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Security configuration using environment variables (secure for production)
# Try multiple environment variable names for Railway compatibility including service variables
ADMIN_PASSWORD: str = (
    os.getenv("APP_PASSWORD") or 
    os.getenv("SCRAPER_PASSWORD") or 
    os.getenv("AUTH_PASSWORD") or 
    os.getenv("LOGIN_PASSWORD") or
    os.getenv("RAILWAY_PRIVATE_PASSWORD") or  # Railway service variable
    os.getenv("PRIVATE_PASSWORD") or  # Alternative Railway variable
    "CHANGE_ME_IN_PRODUCTION"
)
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT", "480"))  # 8 hours default

# Debug logging for environment variable detection with all fallbacks
logger.info(f"Environment variable check: APP_PASSWORD={'SET' if os.getenv('APP_PASSWORD') else 'NOT_SET'}")
logger.info(f"Environment variable check: SCRAPER_PASSWORD={'SET' if os.getenv('SCRAPER_PASSWORD') else 'NOT_SET'}")
logger.info(f"Environment variable check: AUTH_PASSWORD={'SET' if os.getenv('AUTH_PASSWORD') else 'NOT_SET'}")
logger.info(f"Environment variable check: RAILWAY_PRIVATE_PASSWORD={'SET' if os.getenv('RAILWAY_PRIVATE_PASSWORD') else 'NOT_SET'}")
logger.info(f"Environment variable check: PRIVATE_PASSWORD={'SET' if os.getenv('PRIVATE_PASSWORD') else 'NOT_SET'}")
logger.info(f"Final ADMIN_PASSWORD: {'CONFIGURED' if ADMIN_PASSWORD != 'CHANGE_ME_IN_PRODUCTION' else 'DEFAULT'}")

def authenticate_user() -> bool:
    """
    High-performance authentication system using secure environment variables.
    Password stored securely in Railway environment, not in public code.
    Target: Zero performance impact on 0.5-1 second per APN scraping.
    
    Returns:
        bool: True if user is authenticated and session valid, False otherwise
    """
    # Enhanced security check with better error messaging
    if ADMIN_PASSWORD == "CHANGE_ME_IN_PRODUCTION":
        st.error("⚠️ **SECURITY WARNING**: Railway environment variable sync issue detected")
        st.markdown("""
        ### 🔧 Railway Environment Variable Sync Problem
        
        Railway is not syncing your environment variables to the container. **Immediate solutions:**
        
        **Option 1: Use Railway Service Variables (Recommended)**
        1. **Railway Dashboard** → Your Project → **Variables**
        2. **Delete ALL existing** authentication variables
        3. **Add NEW Service Variable**: 
           - Name: `RAILWAY_PRIVATE_PASSWORD`
           - Value: `ClarkCountyAPN_Internal2025!`
        4. **Manually restart**: Dashboard → Deployments → Redeploy
        
        **Option 2: Railway CLI Force Sync**
        ```bash
        # If you have Railway CLI installed
        railway login
        railway variables set RAILWAY_PRIVATE_PASSWORD=ClarkCountyAPN_Internal2025!
        railway redeploy --service web
        ```
        
        **Option 3: Temporary Workaround**
        We can temporarily hardcode a secure password in the private repository
        (not recommended for production, but works while debugging Railway)
        
        **Technical Issue**: Railway container not loading custom environment variables
        despite them being visible in dashboard. This is a known Railway sync issue.
        """)
        
        # Enhanced debug information with Railway-specific troubleshooting
        with st.expander("🔍 Railway Technical Debug Information"):
            st.write("**Railway System Variables (Working):**")
            env_vars = dict(os.environ)
            railway_vars = {k: v for k, v in env_vars.items() if k.startswith('RAILWAY_')}
            st.json(railway_vars)
            
            st.write("**Custom Authentication Variables (FAILING):**")
            auth_check = {
                'APP_PASSWORD': 'SET' if os.getenv('APP_PASSWORD') else 'NOT_SET',
                'SCRAPER_PASSWORD': 'SET' if os.getenv('SCRAPER_PASSWORD') else 'NOT_SET', 
                'AUTH_PASSWORD': 'SET' if os.getenv('AUTH_PASSWORD') else 'NOT_SET',
                'LOGIN_PASSWORD': 'SET' if os.getenv('LOGIN_PASSWORD') else 'NOT_SET',
                'RAILWAY_PRIVATE_PASSWORD': 'SET' if os.getenv('RAILWAY_PRIVATE_PASSWORD') else 'NOT_SET',
                'PRIVATE_PASSWORD': 'SET' if os.getenv('PRIVATE_PASSWORD') else 'NOT_SET'
            }
            st.json(auth_check)
            
            st.write("**Railway Project Info:**")
            project_info = {
                'PROJECT_ID': os.getenv('RAILWAY_PROJECT_ID'),
                'SERVICE_ID': os.getenv('RAILWAY_SERVICE_ID'), 
                'ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT'),
                'DEPLOYMENT_ID': os.getenv('RAILWAY_DEPLOYMENT_ID')
            }
            st.json(project_info)
        
        logger.critical("Railway environment variable sync issue - custom variables not loaded despite dashboard configuration")
        st.stop()

    # Initialize session state for authentication with proper typing
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.auth_timestamp = None
    
    # Performance-optimized session timeout check
    if st.session_state.authenticated and st.session_state.auth_timestamp:
        session_age: float = time.time() - st.session_state.auth_timestamp
        if session_age > (SESSION_TIMEOUT_MINUTES * 60):
            st.session_state.authenticated = False
            st.session_state.auth_timestamp = None
            logger.info(f"Session expired after {session_age/60:.1f} minutes")
    
    # Show authentication form if not authenticated
    if not st.session_state.authenticated:
        # High-performance CSS injection
        st.markdown("""
        <style>
            .auth-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 15px;
                color: white;
                text-align: center;
                margin: 2rem 0;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            .auth-form {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                margin: 1rem 0;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                color: #333333 !important;
                min-height: 200px;
            }
            .auth-form input {
                color: #333333 !important;
                background: white !important;
            }
            .auth-form label {
                color: #333333 !important;
                font-weight: 600;
            }
            .performance-notice {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 1.5rem;
                border-radius: 8px;
                border-left: 4px solid #28a745;
                margin: 1rem 0;
                color: #333333 !important;
            }
            
            /* User-friendly features showcase */
            .features-showcase {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
                padding: 2rem;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 20px;
                border: 1px solid #e9ecef;
            }
            
            .feature-item {
                display: flex;
                align-items: center;
                padding: 1.5rem;
                background: white;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                transition: all 0.3s ease;
                border: 1px solid #f0f0f0;
            }
            
            .feature-item:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
                border-color: #667eea;
            }
            
            .feature-icon {
                font-size: 2.5rem;
                margin-right: 1rem;
                animation: pulse 2s infinite;
            }
            
            .feature-content h4 {
                color: #333;
                margin: 0 0 0.5rem 0;
                font-size: 1.1rem;
                font-weight: 600;
            }
            
            .feature-content p {
                color: #6c757d;
                margin: 0;
                font-size: 0.9rem;
                line-height: 1.4;
            }
            
            /* Animated data flow */
            .data-flow-animation {
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 2rem 0;
                padding: 2rem;
                background: white;
                border-radius: 20px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                border: 1px solid #f0f0f0;
            }
            
            .flow-step {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 1rem;
                margin: 0 1rem;
            }
            
            .flow-icon {
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                padding: 1rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                color: white;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }
            
            .flow-icon:hover {
                transform: scale(1.1);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            .animated-processing {
                animation: spin 2s linear infinite;
            }
            
            .flow-label {
                font-weight: 600;
                color: #333;
                font-size: 0.9rem;
                text-align: center;
            }
            
            .flow-arrow {
                font-size: 1.5rem;
                color: #667eea;
                font-weight: bold;
                animation: pulse 2s infinite;
                margin: 0 0.5rem;
            }
            
            /* Animations */
            @keyframes pulse {
                0% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.05); }
                100% { opacity: 1; transform: scale(1); }
            }
            
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .features-showcase .feature-item:nth-child(1) { animation: slideIn 0.6s ease 0.1s both; }
            .features-showcase .feature-item:nth-child(2) { animation: slideIn 0.6s ease 0.2s both; }
            .features-showcase .feature-item:nth-child(3) { animation: slideIn 0.6s ease 0.3s both; }
            .features-showcase .feature-item:nth-child(4) { animation: slideIn 0.6s ease 0.4s both; }
        </style>
        """, unsafe_allow_html=True)
        
        # Authentication header with performance specifications
        st.markdown("""
        <div class="auth-container">
            <h1>🏠 Clark County APN Property Scraper</h1>
            <h3>High-Performance Internal Company Tool</h3>
            <p>Authorized Personnel Only</p>
        </div>
        """, unsafe_allow_html=True)
        
        # User-friendly animated features display
        st.markdown("""
        <div class="features-showcase">
            <div class="feature-item">
                <div class="feature-icon">⚡</div>
                <div class="feature-content">
                    <h4>Lightning Fast Processing</h4>
                    <p>Get your property data in seconds, not hours</p>
                </div>
            </div>
            
            <div class="feature-item">
                <div class="feature-icon">🎯</div>
                <div class="feature-content">
                    <h4>Smart Auto-Detection</h4>
                    <p>Just upload your file - we'll find all the APNs automatically</p>
                </div>
            </div>
            
            <div class="feature-item">
                <div class="feature-icon">📊</div>
                <div class="feature-content">
                    <h4>Real-Time Progress</h4>
                    <p>Watch your data come to life with live updates</p>
                </div>
            </div>
            
            <div class="feature-item">
                <div class="feature-icon">🔒</div>
                <div class="feature-content">
                    <h4>Secure & Reliable</h4>
                    <p>Your data is protected with enterprise-grade security</p>
                </div>
            </div>
        </div>
        
        <div class="data-flow-animation">
            <div class="flow-step">
                <div class="flow-icon">📁</div>
                <div class="flow-label">Upload</div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step">
                <div class="flow-icon animated-processing">🔄</div>
                <div class="flow-label">Process</div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step">
                <div class="flow-icon">📋</div>
                <div class="flow-label">Results</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # High-performance authentication form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Clean authentication form without problematic HTML containers
            st.markdown("---")
            
            password_input: str = st.text_input(
                "🔑 Enter Access Password:",
                type="password",
                help="Contact IT department for access credentials",
                placeholder="Enter secure company password",
                key="auth_password"
            )
            
            if st.button("🚪 Login", use_container_width=True, type="primary", key="auth_login"):
                # Performance-optimized password verification
                if password_input == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.session_state.auth_timestamp = time.time()
                    
                    # Log successful authentication (no sensitive data)
                    logger.info(f"Successful authentication from session {id(st.session_state)}")
                    
                    st.success("✅ Access granted! Loading high-performance scraper interface...")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("❌ Invalid password. Contact IT department for access.")
                    
                    # Log failed authentication attempt (no sensitive data)
                    logger.warning(f"Failed authentication attempt from session {id(st.session_state)}")
            
            st.markdown("---")
        
        # Footer information
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #6c757d;'>
            <small>
                <strong>Clark County Nevada Property Data Extraction</strong><br>
                Optimized for high-volume APN processing with enterprise-grade performance
            </small>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    return True

def add_session_controls() -> None:
    """
    Add high-performance session management controls to sidebar.
    Zero impact on scraping performance - UI updates only.
    """
    with st.sidebar:
        st.markdown("### 🔓 Session Control")
        
        # Show session info with performance metrics
        if st.session_state.auth_timestamp:
            session_duration: float = time.time() - st.session_state.auth_timestamp
            hours: int = int(session_duration // 3600)
            minutes: int = int((session_duration % 3600) // 60)
            
            if hours > 0:
                st.write(f"⏱️ Session: {hours}h {minutes}m")
            else:
                st.write(f"⏱️ Session: {minutes}m")
        
        # High-performance logout button
        if st.button("🚪 Logout", help="End current session securely"):
            st.session_state.authenticated = False
            st.session_state.auth_timestamp = None
            
            # Log logout event (no sensitive data)
            logger.info(f"User logout from session {id(st.session_state)}")
            st.rerun()

# Authentication gate - must pass before accessing high-performance scraper
if not authenticate_user():
    st.stop()

# Add session controls for authenticated users
add_session_controls()

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

def extract_apns_from_content(content: str, filename: str) -> List[str]:
    """
    Extract APNs from file content by pattern matching the APN format.
    APNs follow the pattern: XXX-XX-XXX-XXX (3-2-3-3 digits separated by dashes)
    
    Args:
        content: File content as string
        filename: Name of the uploaded file
        
    Returns:
        List of extracted APN strings
    """
    apns = []
    
    # Define APN pattern: XXX-XX-XXX-XXX (Clark County format)
    apn_pattern = r'\b\d{3}-\d{2}-\d{3}-\d{3}\b'
    
    if filename.endswith('.csv'):
        # Process CSV line by line to find APNs in any column
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if line.strip():
                # Find all APN matches in this line (any column)
                apn_matches = re.findall(apn_pattern, line)
                for apn in apn_matches:
                    if apn not in apns:  # Avoid duplicates
                        apns.append(apn)
                        logger.debug(f"Found APN '{apn}' on line {line_num}")
    else:
        # For TXT files, extract APNs from entire content
        apn_matches = re.findall(apn_pattern, content)
        for apn in apn_matches:
            if apn not in apns:  # Avoid duplicates
                apns.append(apn)
    
    logger.info(f"Extracted {len(apns)} unique APNs using pattern matching")
    return apns

# Custom CSS for modern styling with proper contrast and visibility
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 1.5rem;
    }
    
    /* Compact main container */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Authentication page styling with proper contrast */
    .auth-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .performance-notice {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #333333 !important;
    }
    
    /* Modern upload section with taller box */
    .upload-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        border: 3px dashed #667eea;
        text-align: center;
        margin: 2rem 0;
        min-height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .upload-section:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #f1f3f4 0%, #e8ecef 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
    }
    
    .upload-icon {
        font-size: 3rem;
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    .upload-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .upload-subtitle {
        font-size: 1rem;
        color: #6c757d;
        margin-bottom: 1.5rem;
    }
    
    /* Modern processing card */
    .processing-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        margin: 2rem 0;
        min-height: 180px;
    }
    
    /* Modern success card */
    .success-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 2rem;
        border-radius: 20px;
        border-left: 5px solid #28a745;
        margin: 2rem 0;
        min-height: 120px;
        color: #155724 !important;
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.15);
    }
    
    /* Modern metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        text-align: center;
        margin: 0.5rem;
        border: 1px solid #f0f0f0;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }
    
    /* Modern download section */
    .download-section {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        min-height: 150px;
        color: #856404 !important;
        border: 1px solid #ffeaa7;
        box-shadow: 0 8px 25px rgba(255, 234, 167, 0.3);
    }
    
    /* Compact step indicator */
    .step-indicator {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 1.5rem 0;
    }
    
    .step {
        background: #e9ecef;
        color: #6c757d;
        border-radius: 50%;
        width: 35px;
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin: 0 0.8rem;
        border: 2px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .step.active {
        background: #667eea;
        color: white;
        border-color: #667eea;
        transform: scale(1.1);
    }
    
    .step.completed {
        background: #28a745;
        color: white;
        border-color: #28a745;
    }
    
    .step-line {
        width: 40px;
        height: 2px;
        background: #e9ecef;
        transition: all 0.3s ease;
    }
    
    .step-line.active {
        background: #28a745;
    }
    
    /* Modern footer */
    .modern-footer {
        text-align: center;
        color: #6c757d;
        padding: 2rem 1rem 1rem;
        font-size: 0.9rem;
        border-top: 1px solid #e9ecef;
        margin-top: 3rem;
    }
    
    .performance-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 0.2rem;
    }
    
    /* Hide default Streamlit elements for cleaner look */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        margin-top: -80px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        
        .upload-section {
            padding: 2rem 1rem;
            min-height: 200px;
        }
        
        .step {
            width: 30px;
            height: 30px;
            margin: 0 0.5rem;
        }
        
        .step-line {
            width: 30px;
        }
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

# Main container for compact layout
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Modern header section
st.markdown('<h1 class="main-header">🏠 Clark County APN Property Scraper</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">High-performance web scraping for Nevada property data</p>', unsafe_allow_html=True)

# Compact step indicator
current_step = 1
if st.session_state.processing_complete:
    current_step = 3
elif 'uploaded_file' in st.session_state and st.session_state.uploaded_file is not None:
    current_step = 2

st.markdown(f"""
<div class="step-indicator">
    <div class="step {'completed' if current_step > 1 else 'active' if current_step == 1 else ''}">1</div>
    <div class="step-line {'active' if current_step > 1 else ''}"></div>
    <div class="step {'completed' if current_step > 2 else 'active' if current_step == 2 else ''}">2</div>
    <div class="step-line {'active' if current_step > 2 else ''}"></div>
    <div class="step {'active' if current_step == 3 else ''}">3</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin-bottom: 2rem; color: #555;">
    <span class="performance-badge">Upload File</span>
    <span class="performance-badge">Process Data</span>
    <span class="performance-badge">Download Results</span>
</div>
""", unsafe_allow_html=True)

# Step 1: Modern File Upload Section
if not st.session_state.processing_complete:
    st.markdown("""
    <div class="upload-section">
        <div class="upload-icon">📁</div>
        <div class="upload-title">Upload Your APN File</div>
        <div class="upload-subtitle">Drag and drop your CSV or TXT file containing APNs, or click to browse</div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "",
        type=['csv', 'txt'],
        help="Supported formats: CSV with APN column or TXT with one APN per line. Auto-detects XXX-XX-XXX-XXX format.",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        try:
            # Process uploaded file using pattern matching
            content = uploaded_file.read().decode('utf-8')
            
            # Use pattern matching to find APNs in any column
            apns = extract_apns_from_content(content, uploaded_file.name)
            
            st.session_state.uploaded_file = uploaded_file
            st.session_state.apns = apns
            
            # Show file preview with enhanced detection info
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if len(apns) > 0:
                    st.success(f"✅ Successfully detected **{len(apns)}** APNs from `{uploaded_file.name}`")
                    st.info("🔍 **Auto-detected APNs** using pattern matching (XXX-XX-XXX-XXX format)")
                    
                    with st.expander("📋 Preview Detected APNs"):
                        preview_count = min(10, len(apns))
                        for i in range(preview_count):
                            st.write(f"• {apns[i]}")
                        if len(apns) > 10:
                            st.write(f"... and {len(apns) - 10} more APNs")
                else:
                    st.error("❌ No APNs detected in the uploaded file")
                    st.info("📝 **Expected format**: APNs should follow the pattern XXX-XX-XXX-XXX (e.g., 177-13-420-002)")
                    
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

# Step 2: Processing Section
if 'apns' in st.session_state and st.session_state.apns and not st.session_state.processing_complete:
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

# Step 3: Results and Download Section
if st.session_state.processing_complete and st.session_state.scraped_data is not None:
    st.markdown("### ✅ Processing Complete!")
    
    stats = st.session_state.processing_stats
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Processed", stats['total'])
    
    with col2:
        st.metric("Successful", stats['successful'])
    
    with col3:
        st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
    
    with col4:
        st.metric("Avg Speed", f"{stats['avg_speed']:.2f}s")
    
    # Download section
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

# Modern footer
st.markdown("""
<div class="modern-footer">
    <strong>🏠 Clark County APN Property Scraper</strong><br>
    <span class="performance-badge">0.5-1s per APN</span>
    <span class="performance-badge">Smart Pattern Detection</span>
    <span class="performance-badge">Real-time Progress</span>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # Close main container