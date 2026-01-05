# RFID Reader Application - Modern Python Edition

A professional RFID tag reader control application with Windows 11 Fluent Design interface, modernized from a legacy C# Windows Forms application.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### Core Functionality
- **Real-time Tag Inventory** - Multi-antenna RFID tag scanning with live updates
- **Direction Detection** - Dual-sensor system for IN/OUT direction determination
- **Confidence Analysis** - RSSI slope and variance-based tag detection
- **Data Export** - Export inventory data to Excel format

### Reader Control
- Power configuration (0-33 dBm)
- Frequency region selection (US, China, Vietnam, Manual)
- RF Link Profile configuration
- Beeper control
- GPIO pin management
- S11 (Return Loss) measurement

### Modern UI
- Windows 11 Fluent Design language
- Clean, uncluttered layout with ample whitespace
- Rounded corners and modern typography (Segoe UI)
- Soft color palette with accent colors
- Responsive and accessible interface

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- Windows 10/11 (recommended for best Fluent Design experience)

### Setup

1. **Clone or download the project**
```bash
cd E:\Files\Py\rfid_reader_app
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## 🎮 Usage

### Running the Application
```bash
python main.py
```

### Quick Start Guide

1. **Connect to Reader**
   - Go to the "Connection" page
   - Select the COM port and baud rate (default: 115200)
   - Click "Connect"

2. **Start Inventory**
   - Navigate to "Inventory" page
   - Select active antennas (ANT 1-4)
   - Choose session (S0-S3) and target (A/B)
   - Click "Start Inventory"

3. **Configure Reader**
   - Use "Reader Settings" page to adjust power, frequency, etc.
   - Use "GPIO Control" for pin management

4. **Export Data**
   - Click "Export Excel" to save inventory data

## 📁 Project Structure

```
rfid_reader_app/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── models/                # Business logic & data models
│   ├── __init__.py
│   ├── data_models.py     # Core data structures
│   └── reader_model.py    # Tag processing & analysis
│
├── views/                 # UI components (Fluent Design)
│   ├── __init__.py
│   ├── main_window.py     # Main application window
│   ├── connection_page.py # Serial connection management
│   ├── inventory_page.py  # Real-time tag inventory
│   ├── settings_page.py   # Reader configuration
│   └── gpio_page.py       # GPIO control interface
│
├── controllers/           # Application logic
│   ├── __init__.py
│   └── reader_controller.py # Main controller
│
└── utils/                 # Utilities
    ├── __init__.py
    ├── serial_utils.py    # Serial communication
    └── export_utils.py    # Excel export
```

## 🏗️ Architecture

The application follows the **MVC (Model-View-Controller)** pattern:

- **Model** (`models/`) - Business logic, data processing, tag analysis
- **View** (`views/`) - PyQt6 UI components with Fluent Design
- **Controller** (`controllers/`) - Coordinates models and views, handles events

### Key Components

| Component | Description |
|-----------|-------------|
| `ReaderModel` | Tag processing, RSSI analysis, sensor state management |
| `SerialManager` | Serial port communication, sensor signal handling |
| `MainWindow` | Fluent Design navigation window |
| `InventoryPage` | Real-time tag list and detection display |
| `ReaderController` | Event handling, command execution |

## 🔧 Configuration

### Antenna Configuration
- Support for 4 antennas (ANT 1-4)
- Individual enable/disable per antenna
- Session selection: S0, S1, S2, S3
- Target selection: A, B

### Frequency Regions
| Region | Frequency Range |
|--------|-----------------|
| US (FCC) | 902-928 MHz |
| China | 920-925 MHz |
| Vietnam | 918-923 MHz |
| Manual | Custom range |

### RF Link Profiles
| Profile | Description |
|---------|-------------|
| Profile 0 | Tari 25μs, FM0, LF=40KHz |
| Profile 1 | Tari 25μs, Miller 4, LF=250KHz |
| Profile 2 | Tari 25μs, Miller 4, LF=300KHz |
| Profile 3 | Tari 6.25μs, FM0, LF=400KHz |

## 📊 Tag Detection Algorithm

The application uses a confidence-based detection system:

1. **RSSI Slope Analysis** - Calculates linear regression slope of RSSI over time
2. **Variance Analysis** - Measures RSSI variance for signal stability
3. **Confidence Score** - Combines slope and variance with configurable thresholds
4. **Multi-antenna Correlation** - Cross-references data from multiple antennas

Tags are marked as "detected" when they pass the confidence threshold on at least 2 out of 3 metrics (ANT1, ANT2, Combined).

## 🎨 Design System

### Color Palette
- **Primary**: #0078D4 (Windows 11 Blue)
- **Success**: #4CAF50
- **Error**: #F44336
- **Background**: #F8F8F8, #FFFFFF
- **Text**: #333333, #666666

### Typography
- **Font Family**: Segoe UI (Windows), SF Pro (macOS fallback)
- **Headings**: 24px DemiBold
- **Body**: 14px Regular
- **Caption**: 12px Regular

## 🐛 Troubleshooting

### Common Issues

**COM Port not showing**
- Ensure the USB driver is installed
- Try unplugging and reconnecting the reader
- Click "Refresh Ports" button

**Connection fails**
- Verify the correct baud rate (usually 115200)
- Check if another application is using the port
- Try a different USB port

**No tags detected**
- Verify antennas are connected and enabled
- Check power settings (increase if needed)
- Ensure tags are within range

## 📄 License

MIT License - feel free to use and modify for your projects.

## 🙏 Acknowledgments

- Original C# Windows Forms application
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - Python Qt bindings
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - Fluent Design components
- Microsoft Fluent Design System

"# security_gate_python" 
