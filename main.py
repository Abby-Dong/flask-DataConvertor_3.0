from flask import Flask, request, render_template, send_file
import csv, os, re
from werkzeug.utils import secure_filename
from datetime import datetime
from searcher import fetch_product_details

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def format_price(raw_price):
    try:
        price_float = round(float(raw_price), 2)
        return "US$" + "{:,.2f}".format(price_float)
    except:
        return "US$TBD"

def strip_html(text):
    return re.sub('<[^<]+?>', '', text)

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    download_file = None

    if request.method == "POST":
        uploaded_file = request.files["csv_file"]
        if uploaded_file.filename.endswith(".csv"):
            filename = secure_filename(uploaded_file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(input_path)

            with open(input_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                products = list(reader)

            for row in products:
                name = row['Product Name']
                original_desc = row.get("Part NumberDesc", "").strip()
                original_price = row.get("Product Price", "").strip()
                original_link = row.get("Product Link", "").strip()

                data = fetch_product_details(name)
                if not data:
                    continue

                # 描述比對
                fetched_desc = data.get("product_description", "").strip()

                # 價格格式化與比對
                raw_price = data.get("product_price", "").strip()
                original_price_raw = data.get("product_price_orginal", "").strip()
                need_manual_check = (raw_price == original_price_raw)
                formatted_price = format_price(raw_price)
                if need_manual_check:
                    formatted_price += " (Manually Check)"

                # 連結比對
                fetched_link = f"https://www.iotmart.com/s/product/detail/{data.get('product_id')}?language=en_US" if data.get("product_id") else ""

                results.append({
                    "Product Name": name,
                    "Part NumberDesc": f'<span class="changed">{fetched_desc}</span>' if original_desc != fetched_desc else fetched_desc,
                    "Product Price": f'<span class="changed">{formatted_price}</span>' if original_price != formatted_price else formatted_price,
                    "Product Link": f'<span class="changed">{fetched_link}</span>' if original_link != fetched_link else f'<a href="{fetched_link}" target="_blank">{fetched_link}</a>'
                })

            # === 產出乾淨 CSV ===
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_filename = f"result_{timestamp}.csv"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
                fieldnames = ["Product Name", "Part NumberDesc", "Product Price", "Product Link"]
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()

                for r in results:
                    writer.writerow({key: strip_html(r[key]) for key in fieldnames})

            download_file = output_filename

    return render_template("index.html", results=results, download_file=download_file)

@app.route("/download/<filename>")
def download(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
