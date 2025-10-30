from flask import Flask, jsonify, request
from sqlalchemy import text
import validators
from utils.utils import validate_schema, custom_base62_encode
from src.models import db, URLS, AccessLog
from src.schemas import URLSchema

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:password@fincome-db:5432/mydatabase"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

SHORT_URL_PREFIX = "http://short.est/"


@app.route("/encode", methods=["POST"])
@validate_schema(URLSchema())
def encode_url(url: str):
    existing_url = URLS.query.filter_by(original=url).first()
    if existing_url:
        return jsonify(short_url=f"{SHORT_URL_PREFIX}{existing_url.short}")

    new_url_shortened = URLS(original=url)
    db.session.add(new_url_shortened)
    db.session.commit()

    short_id = custom_base62_encode(new_url_shortened.id)
    new_url_shortened.short = short_id
    db.session.commit()

    return jsonify(short_url=f"{SHORT_URL_PREFIX}{short_id}")


@app.route("/decode", methods=["GET"])
def decode_url():
    short_url = request.args.get("short_url")
    if (
        not short_url
        or not validators.url(short_url)
        or not short_url.startswith(SHORT_URL_PREFIX)
    ):
        return jsonify(error="Bad Request", message="Invalid or missing short URL"), 400

    short_id = short_url.split("/")[-1]
    url_data = db.session.query(URLS).filter(URLS.short == short_id).first()

    if not url_data:
        return jsonify(error="Not Found", message="Short URL not found"), 404

    access_log = AccessLog(url_id=url_data.id)
    db.session.add(access_log)
    db.session.commit()

    return jsonify(original_url=url_data.original)


@app.route("/stats", methods=["GET"])
def stats_last_18_months():
    q = text("""
        SELECT
          to_char(date_trunc('month', a.created_at), 'YYYY-MM') AS month_key,
          COUNT(DISTINCT a.url_id) AS unique_urls
        FROM access_logs a
        WHERE a.created_at >= CURRENT_DATE - INTERVAL '18 months'
        GROUP BY 1
        ORDER BY 1 DESC
    """)
    rows = db.session.execute(q).mappings().all()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
