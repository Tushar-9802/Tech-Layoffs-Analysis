# 📊 Tech Layoff Analysis (2020–2025)

A comprehensive data exploration of **global tech layoffs** from the pandemic through the rise of AI — revealing patterns across companies, industries, and locations, with **advanced custom metrics** to uncover rarely seen insights.

---

## 🔍 Project Highlights

- 📈 **Temporal trends** of layoffs across funding stages, company sizes, and sectors  
- 🧠 **Advanced metrics introduced**:
  - **Layoff Efficiency Score (LES)**
  - **Layoff Instability Score (LIS)**
  - **Layoff Severity Index (LSI)**
  - **Location Fragility Index**
  - **Industry Survivability Score**
  - **Bounceback Potential Score**
- 🌎 **Geo-based fragility** insights and sector resilience mapping  
- 💡 **Contextual reasoning** tied to real-world events  
  *(COVID-19, funding slowdowns, AI boom, geopolitical shifts)*  

---

## 🖥️ Project Components

### 1. **Jupyter Notebook (`EDA.ipynb`)**
The notebook contains:
- **Static, text-based inferences** alongside charts
- **Step-by-step exploratory analysis**
- **Contextual insights** based on real-world events
- **Advanced calculated metrics** explained in detail

Run it locally to reproduce the **original exploratory workflow** and annotations.

---

### 2. **Streamlit Dashboard**
An **interactive** version of the analysis that lets you:
- Filter data by **year**, **country**, **industry**, and **company**
- View **dynamic, graph-based inferences** in real-time
- Access **three main pages**:
  1. **Trends** – High-level layoffs patterns over time  
  2. **Company** – Deep dive into specific companies and comparisons  
  3. **Custom Metrics** – Advanced calculated indicators like LES, LIS, and LSI  

🚀 **Live Deployment:**  
[**Tech Layoffs Analysis – Streamlit App**](https://tushar9802-tech-layoffs-analysis.streamlit.app/)


---

## 🚀 Getting Started

1. Clone the repo:
```
git clone https://github.com/Tushar-9802/Tech-Layoffs-Analysis.git
```


🧾 Section 5: Requirements  
---

## 🧪 Requirements

The following Python libraries are required:

-streamlit>=1.31
-pandas
-plotly
-numpy
-matplotlib
-seaborn
-xlsxwriter   # for XLSX downloads


- Install dependencies:


```
pip install -r requirements.txt
```

🧾 Section 6: Author
---

## 📬 Author

**Tushar Jaju**  

🔗 (https://www.linkedin.com/in/tushar-jaju-240b501a6/)  
🎯 Data analyst and Python enthusiast focused on insight-driven storytelling.


🧾 Section 7: Dataset Source

---

 **📦Section 7: Dataset Source**

This project uses data from the publicly available Kaggle dataset:

**Layoffs Dataset by Swapnil Tripathi** 

🔗 https://www.kaggle.com/datasets/swaptr/layoffs  
📰 Compiled from Bloomberg, SF Business Times, TechCrunch, NYT, and user-submitted sources.

🧹 Cleaning and transformation steps included:
- Normalized timestamps and funding fields  
- Estimated missing company sizes  
- Engineered quarterly and severity-based metrics
  
🧾 Section 8: License

---

## 📄 License

This project is open-source and intended for research, educational, and portfolio use only.  
Data is shared under the Open Database License (ODbL).
