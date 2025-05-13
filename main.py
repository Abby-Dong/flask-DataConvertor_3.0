from flask import Flask, request, render_template, send_file
import os, csv
from werkzeug.utils import secure_filename
from searcher import fetch_product_details  # ← 請確保你有這個模組

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        uploaded_file = request.files["csv_file"]
        if uploaded_file and uploaded_file.filename.endswith(".csv"):
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(filepath)

            with open(filepath, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product_name = row["Product Name"]
                    original_desc = row.get("Part NumberDesc", "").strip()
                    original_price = row.get("Product Price", "").strip()
                    original_link = row.get("Product Link", "").strip()

                    data = fetch_product_details(product_name)
                    if not data:
                        continue

                    fetched_desc = data.get("product_description", "").strip()
                    fetched_price = data.get("product_price", "").strip()
                    if fetched_price == data.get("product_price_orginal", ""):
                        fetched_price += "(Manually Check)"
                    fetched_price = "US$" + fetched_price
                    fetched_link = f"https://www.iotmart.com/s/product/detail/{data.get('product_id')}?language=en_US" if data.get("product_id") else ""

                    results.append({
                        "Product Name": product_name,
                        "Part NumberDesc": f'<span class="changed">{fetched_desc}</span>' if original_desc != fetched_desc else fetched_desc,
                        "Product Price": f'<span class="changed">{fetched_price}</span>' if original_price != fetched_price else fetched_price,
                        "Product Link": f'<span class="changed">{fetched_link}</span>' if original_link != fetched_link else f'<a href="{fetched_link}" target="_blank">{fetched_link}</a>'
                    })

    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)