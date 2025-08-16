# CrowdSense - Organized Project Structure

## 📁 **Clean, Organized Architecture**

The CrowdSense project is now properly organized with clear separation between production code, simulation code, utilities, and web components.

```
CrowdSense/
├── 📂 core/                        # 🎯 MAIN APPLICATION LOGIC
│   ├── crowdsense_enhanced.py      # Enhanced disaster detection system
│   ├── anomaly_detection.py        # Smart anomaly detection (Z-score/EWMA)
│   ├── location_extraction.py      # NER and geocoding for locations
│   ├── database.py                 # SQLite database operations
│   └── scheduler.py                # Background task scheduling
│
├── 📂 simulation/                  # 🧪 SIMULATION & TESTING
│   ├── simulation.py               # Disaster simulation engine
│   ├── crowdsense_simulation.py    # Simulation-enabled system
│   └── trigger_disaster.py         # Manual disaster triggers
│
├── 📂 utils/                       # 🔧 UTILITY FUNCTIONS
│   ├── config.py                   # Configuration and environment
│   ├── alert.py                    # SMS alert functionality
│   ├── logging_config.py           # Structured logging and metrics
│   └── check_sms_status.py         # SMS troubleshooting tools
│
├── 📂 web/                         # 🌐 WEB INTERFACE
│   └── hackathon_app/              # Flask web dashboard
│       ├── app.py                  # Production web app
│       ├── app_simulation.py       # Simulation web app
│       └── templates/              # HTML templates
│           ├── index.html          # Production dashboard
│           └── index_simulation.html # Simulation dashboard
│
├── 📄 main.py                      # 🚀 Main application entry point
├── 📄 crowdsense.py                # 🌐 Production disaster detection
├── 📄 simulate.py                  # 🧪 Easy simulation interface
├── 📄 run.py                       # ⚡ Quick start script
├── 📄 README.md                    # 📖 Comprehensive documentation
└── 📄 requirements.txt             # 📦 Python dependencies
```

## 🎯 **Usage Examples**

### **Production Mode** (Real APIs)
```bash
# Single analysis with real Twitter/News APIs
python crowdsense.py

# Full web dashboard with real data
python main.py web
```

### **Simulation Mode** (Testing)
```bash
# Quick disaster simulation
python simulate.py earthquake
python simulate.py flood --severity severe

# Interactive simulation mode
python simulate.py -i

# Web dashboard with simulation controls
python main.py simulation
```

### **Component Testing**
```bash
# Test all components
python main.py test

# Test background monitoring
python main.py background

# Quick start (defaults to web mode)
python run.py
```

## 🧩 **Module Responsibilities**

### **Core Modules** (`core/`)
- **`crowdsense_enhanced.py`**: Main disaster detection logic with real APIs
- **`anomaly_detection.py`**: Statistical anomaly detection algorithms
- **`location_extraction.py`**: NER-based location extraction and geocoding
- **`database.py`**: SQLite database operations and data management
- **`scheduler.py`**: Background task scheduling and management

### **Simulation Modules** (`simulation/`)
- **`simulation.py`**: Disaster scenario engine and Twitter API simulation
- **`crowdsense_simulation.py`**: Enhanced system with simulation support
- **`trigger_disaster.py`**: Command-line disaster scenario triggers

### **Utility Modules** (`utils/`)
- **`config.py`**: Environment variables and configuration management
- **`alert.py`**: SMS alert functionality with carrier filtering fixes
- **`logging_config.py`**: Structured logging and metrics collection
- **`check_sms_status.py`**: SMS troubleshooting and testing tools

### **Web Modules** (`web/`)
- **`app.py`**: Flask web application for production use
- **`app_simulation.py`**: Flask web application with simulation controls
- **Templates**: HTML templates for dashboard interfaces

## ✅ **Benefits of New Structure**

1. **🎯 Clear Separation**: Production vs. simulation code clearly separated
2. **📦 Modular Design**: Each component has a specific responsibility
3. **🔄 Easy Maintenance**: Changes to one module don't affect others
4. **🧪 Better Testing**: Simulation code isolated for testing purposes
5. **📚 Improved Documentation**: Each directory has a clear purpose
6. **🚀 Easy Deployment**: Production code (`core/`) can be deployed separately

## 🎛️ **Import Structure**

All modules properly import from their organized locations:
- Core modules import from `core.*`
- Simulation modules import from `simulation.*`
- Utilities import from `utils.*`
- Web modules import from `web.*`

## 🔧 **Development Workflow**

1. **Production Development**: Work in `core/` directory
2. **Simulation Development**: Work in `simulation/` directory
3. **Web Development**: Work in `web/` directory
4. **Configuration Changes**: Update `utils/config.py`
5. **Testing**: Use `simulate.py` or `main.py test`

The project is now enterprise-ready with proper structure and separation of concerns! 🎉
