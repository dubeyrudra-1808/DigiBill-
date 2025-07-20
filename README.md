# 🧾 Bill Processor Pro

**Bill Processor Pro** is an intelligent invoice extraction tool built with FastAPI, Tesseract OCR, and Google Gemini 1.5 Flash. It allows users to upload receipts or invoices in PDF or image formats, extracts key structured data such as items, tax, total, business details, and returns a clean JSON response.

---

## 🚀 Features

- ✅ Supports PDF, PNG, JPG, JPEG formats (max size: 10MB)
- 🔍 High-accuracy OCR with Tesseract
- 🤖 AI-based parsing with Gemini 1.5 Flash
- 📤 Drag-and-drop file upload interface
- 🧠 Structured output in JSON format
- 💡 Real-time validation and feedback
- 🛡️ Temporary file cleanup after processing
- 🧪 API health and Gemini test endpoints

---

## 📂 Project Structure

```
bill-processor-pro/
├── main.py               # FastAPI backend logic
├── index.html            # Frontend UI with TailwindCSS
├── requirements.txt      # Python dependencies
├── uploads/              # Temporary file storage
└── README.md             # Project documentation
```

---

## 🔧 Prerequisites

Make sure the following tools are installed:

### 🐍 Python
- Version: Python 3.8+

### 📦 System Dependencies

| Tool        | Description              | Installation Guide |
|-------------|--------------------------|---------------------|
| **Tesseract** | OCR engine                 | [Tesseract Install](https://github.com/tesseract-ocr/tesseract) |
| **Poppler**   | Convert PDF to image       | [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/) or `apt install poppler-utils` |

---

## ⚙️ Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/bill-processor-pro.git
cd bill-processor-pro
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Set your Gemini API key in the environment:

```bash
export GEMINI_API_KEY=your_gemini_api_key
```

Or create a `.env` file:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
```

---

## ▶️ Run the Application

Start the FastAPI server:

```bash
python main.py
```

Open the `index.html` file in your browser to access the frontend interface.

---

## 🌐 API Endpoints

| Method | Endpoint         | Description                        |
|--------|------------------|------------------------------------|
| POST   | `/upload`        | Upload file and get JSON response |
| GET    | `/health`        | API health check                  |
| GET    | `/test-gemini`   | Test Gemini API connection        |

---

## 🧾 Sample Output

```json
{
  "business_name": "ABC Mart",
  "business_address": "123 High Street, Delhi",
  "business_phone": "9999999999",
  "bill_number": "INV12345",
  "date": "2025-07-20",
  "time": "14:45",
  "items": [
    {
      "name": "Notebook",
      "quantity": 2,
      "unit_price": 50,
      "total_price": 100
    },
    {
      "name": "Pen",
      "quantity": 3,
      "unit_price": 10,
      "total_price": 30
    }
  ],
  "subtotal": 130,
  "tax_amount": 23.4,
  "tax_percentage": 18,
  "discount": 10,
  "total_amount": 143.4,
  "payment_method": "UPI",
  "customer_info": "John Doe"
}
```

---

## 🖥️ Frontend Features

- 🔄 Drag-and-drop & button file uploads
- 📄 Displays structured JSON results
- 📋 One-click copy to clipboard
- 🔄 Graceful fallback if Gemini API fails
- 🧼 Auto-cleans uploaded files

---

## 🚧 Future Enhancements

- [ ] Add database integration (MongoDB / PostgreSQL)
- [ ] Enable file download of extracted JSON/CSV
- [ ] Deploy on Render / Railway / Streamlit Cloud
- [ ] Add login and usage tracking
- [ ] Enhance mobile responsiveness

---

## 🙋 Author

**Devansh Pratap**  
🎓 B.Tech - Information Technology  
📧 devansh@example.com  
🔗 [LinkedIn](https://www.linkedin.com/in/your-profile)

---

## 📄 License

This project is intended for academic and personal use only. For commercial licensing, contact the author.

---
