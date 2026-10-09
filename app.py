from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from database.oracle_db import get_oracle_connection
from database.mongo_db import leave_requests, overtime_requests, performance_reviews
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "hrm_pro_secret_key"


# Tai khoan demo noi bo
# Luu y: Do day la he thong HRM noi bo, tai khoan duoc cap san boi quan tri/nhan su,
# khong mo dang ky tu do cho nguoi dung ben ngoai.
USERS = {
    "nv001": {
        "password": "123",
        "role": "employee",
        "ma_nv": "NV001",
        "display_name": "Nhan vien NV001"
    },
    "hr001": {
        "password": "123",
        "role": "hr",
        "ma_nv": None,
        "display_name": "Bo phan nhan su"
    },
    "ql001": {
        "password": "123",
        "role": "manager",
        "ma_nv": None,
        "display_name": "Quan ly truc tiep"
    }
}


@app.context_processor
def inject_user():
    return {
        "current_user": session.get("username"),
        "current_role": session.get("role"),
        "current_display_name": session.get("display_name"),
        "current_ma_nv": session.get("ma_nv")
    }


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("Vui long dang nhap de su dung he thong.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "username" not in session:
                flash("Vui long dang nhap de su dung he thong.", "warning")
                return redirect(url_for("login"))

            if session.get("role") not in roles:
                flash("Tai khoan hien tai khong co quyen thuc hien chuc nang nay.", "danger")
                return redirect(url_for("index"))

            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()

        user = USERS.get(username)

        if user and user["password"] == password:
            session["username"] = username
            session["role"] = user["role"]
            session["ma_nv"] = user["ma_nv"]
            session["display_name"] = user["display_name"]

            flash("Dang nhap thanh cong.", "success")
            return redirect(url_for("index"))

        flash("Sai tai khoan hoac mat khau.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Da dang xuat.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    employee_count = 0

    try:
        conn = get_oracle_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM NHANVIEN")
        employee_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    except Exception as e:
        employee_count = f"Loi Oracle: {e}"

    try:
        if session.get("role") == "employee":
            ma_nv = session.get("ma_nv")
            leave_filter = {"ma_nv": ma_nv}
        else:
            leave_filter = {}

        leave_count = leave_requests.count_documents(leave_filter)
        pending_count = leave_requests.count_documents({**leave_filter, "trang_thai": "CHO_DUYET"})
        approved_count = leave_requests.count_documents({**leave_filter, "trang_thai": "DA_DUYET"})
        rejected_count = leave_requests.count_documents({**leave_filter, "trang_thai": "TU_CHOI"})

        chart_data = [
            {"label": "CHO_DUYET", "value": pending_count},
            {"label": "DA_DUYET", "value": approved_count},
            {"label": "TU_CHOI", "value": rejected_count}
        ]

        max_count = max([item["value"] for item in chart_data] + [1])

    except Exception:
        leave_count = "Chua ket noi MongoDB"
        pending_count = 0
        approved_count = 0
        rejected_count = 0
        chart_data = []
        max_count = 1

    return render_template(
        "index.html",
        employee_count=employee_count,
        leave_count=leave_count,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        chart_data=chart_data,
        max_count=max_count
    )


@app.route("/employees")
@login_required
@role_required("hr", "manager")
def employees():
    conn = get_oracle_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            nv.MANV,
            nv.HOTEN,
            nv.EMAIL,
            pb.TENPB,
            nv.CHUCVU,
            nv.LUONG,
            nv.NGAYPHEP_CONLAI
        FROM NHANVIEN nv
        LEFT JOIN PHONGBAN pb ON nv.MAPB = pb.MAPB
        ORDER BY nv.MANV
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("employees.html", employees=data)


@app.route("/employees/add", methods=["GET", "POST"])
@login_required
@role_required("hr")
def add_employee():
    if request.method == "POST":
        manv = request.form["manv"].strip()
        hoten = request.form["hoten"].strip()
        email = request.form["email"].strip()
        mapb = request.form["mapb"].strip()
        chucvu = request.form["chucvu"].strip()
        luong = float(request.form["luong"])
        ngayphep = int(request.form["ngayphep"])
        manv_quanly = request.form.get("manv_quanly") or None

        conn = get_oracle_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO NHANVIEN (
                    MANV, HOTEN, EMAIL, MAPB, CHUCVU, LUONG, NGAYPHEP_CONLAI, MANV_QUANLY
                )
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
            """, [manv, hoten, email, mapb, chucvu, luong, ngayphep, manv_quanly])

            conn.commit()
            flash("Them nhan vien thanh cong.", "success")
            return redirect(url_for("employees"))
        except Exception as e:
            flash(f"Loi them nhan vien: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("add_employee.html")


@app.route("/departments")
@login_required
@role_required("hr", "manager")
def departments():
    conn = get_oracle_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH phongban_tree (mapb, tenpb, mapb_cha, cap) AS (
            SELECT mapb, tenpb, mapb_cha, 1
            FROM phongban
            WHERE mapb_cha IS NULL

            UNION ALL

            SELECT pb.mapb, pb.tenpb, pb.mapb_cha, pbt.cap + 1
            FROM phongban pb
            JOIN phongban_tree pbt ON pb.mapb_cha = pbt.mapb
        )
        SELECT 
            LPAD(' ', (cap - 1) * 4) || tenpb AS cay_phong_ban,
            mapb,
            mapb_cha,
            cap
        FROM phongban_tree
        ORDER BY cap, mapb
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("departments.html", departments=data)


@app.route("/leaves")
@login_required
def leaves():
    if session.get("role") == "employee":
        data = list(
            leave_requests.find({"ma_nv": session.get("ma_nv")}).sort("created_at", -1)
        )
    else:
        data = list(leave_requests.find().sort("created_at", -1))

    return render_template("leaves.html", leaves=data)


@app.route("/leaves/create", methods=["GET", "POST"])
@login_required
def create_leave():
    if request.method == "POST":
        ma_don = request.form["ma_don"].strip()

        # Neu la nhan vien thi chi duoc tao don cho chinh minh.
        # Neu la HR/quan ly thi co the nhap ma nhan vien bat ky de demo.
        if session.get("role") == "employee":
            ma_nv = session.get("ma_nv")
        else:
            ma_nv = request.form["ma_nv"].strip()

        # Kiem tra ma nhan vien co ton tai trong Oracle khong
        conn = get_oracle_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM NHANVIEN WHERE MANV = :1", [ma_nv])
        exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        if exists == 0:
            flash("Ma nhan vien khong ton tai trong Oracle. Vui long nhap dung ma nhan vien.", "danger")
            return redirect(url_for("create_leave"))

        tu_ngay = request.form["tu_ngay"]
        den_ngay = request.form["den_ngay"]
        so_ngay = int(request.form["so_ngay"])
        ly_do = request.form["ly_do"].strip()

        leave_requests.insert_one({
            "ma_don": ma_don,
            "ma_nv": ma_nv,
            "loai_don": "NGHI_PHEP",
            "tu_ngay": tu_ngay,
            "den_ngay": den_ngay,
            "so_ngay": so_ngay,
            "ly_do": ly_do,
            "trang_thai": "CHO_DUYET",
            "sync_status": "PENDING",
            "error_message": "",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "lich_su_duyet": [
                {
                    "hanh_dong": "TAO_DON",
                    "nguoi_thuc_hien": ma_nv,
                    "thoi_gian": datetime.now()
                }
            ]
        })

        flash("Tao don nghi phep thanh cong.", "success")
        return redirect(url_for("leaves"))

    return render_template("create_leave.html")


@app.route("/leaves/approve/<id>")
@login_required
@role_required("hr", "manager")
def approve_leave(id):
    leave = leave_requests.find_one({"_id": ObjectId(id)})

    if not leave:
        flash("Khong tim thay don nghi phep.", "danger")
        return redirect(url_for("leaves"))

    if leave["trang_thai"] != "CHO_DUYET":
        flash("Don nay da duoc xu ly.", "warning")
        return redirect(url_for("leaves"))

    # Danh dau dang xu ly dong bo truoc khi goi Oracle
    leave_requests.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "sync_status": "PROCESSING",
                "error_message": "",
                "updated_at": datetime.now()
            }
        }
    )

    conn = get_oracle_connection()
    cursor = conn.cursor()

    try:
        # Goi Stored Procedure Oracle de tru ngay phep
        cursor.callproc("SP_TRU_NGAY_PHEP", [
            leave["ma_nv"],
            leave["ma_don"],
            leave["so_ngay"]
        ])

        # Neu Oracle xu ly thanh cong thi cap nhat MongoDB
        leave_requests.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "trang_thai": "DA_DUYET",
                    "sync_status": "SUCCESS",
                    "error_message": "",
                    "updated_at": datetime.now()
                },
                "$push": {
                    "lich_su_duyet": {
                        "hanh_dong": "DA_DUYET",
                        "nguoi_duyet": session.get("username"),
                        "thoi_gian": datetime.now()
                    }
                }
            }
        )

        flash(
            "Duyet don thanh cong. Oracle da tru ngay phep, MongoDB da cap nhat trang thai.",
            "success"
        )

    except Exception as e:
        leave_requests.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "sync_status": "FAILED",
                    "error_message": str(e),
                    "updated_at": datetime.now()
                },
                "$push": {
                    "lich_su_duyet": {
                        "hanh_dong": "LOI_DONG_BO",
                        "nguoi_duyet": session.get("username"),
                        "thoi_gian": datetime.now(),
                        "loi": str(e)
                    }
                }
            }
        )

        flash(f"Loi khi duyet don: {e}", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("leaves"))


@app.route("/leaves/reject/<id>")
@login_required
@role_required("hr", "manager")
def reject_leave(id):
    leave_requests.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "trang_thai": "TU_CHOI",
                "sync_status": "SUCCESS",
                "error_message": "",
                "updated_at": datetime.now()
            },
            "$push": {
                "lich_su_duyet": {
                    "hanh_dong": "TU_CHOI",
                    "nguoi_duyet": session.get("username"),
                    "thoi_gian": datetime.now()
                }
            }
        }
    )

    flash("Tu choi don thanh cong. MongoDB da cap nhat trang thai.", "success")
    return redirect(url_for("leaves"))


@app.route("/reports/leave-status")
@login_required
@role_required("hr", "manager")
def leave_status_report():
    # 1. Thong ke so luong don theo trang thai
    status_pipeline = [
        {
            "$group": {
                "_id": "$trang_thai",
                "so_luong": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "so_luong": -1
            }
        }
    ]

    # 2. Thong ke so don va tong so ngay nghi theo nhan vien
    employee_pipeline = [
        {
            "$group": {
                "_id": "$ma_nv",
                "tong_so_don": {"$sum": 1},
                "tong_so_ngay_nghi": {"$sum": "$so_ngay"}
            }
        },
        {
            "$sort": {
                "tong_so_ngay_nghi": -1
            }
        }
    ]

    # 3. Thong ke tong so ngay nghi theo trang thai
    day_by_status_pipeline = [
        {
            "$group": {
                "_id": "$trang_thai",
                "tong_so_ngay": {"$sum": "$so_ngay"},
                "so_luong_don": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "tong_so_ngay": -1
            }
        }
    ]

    status_reports = list(leave_requests.aggregate(status_pipeline))
    employee_reports = list(leave_requests.aggregate(employee_pipeline))
    day_status_reports = list(leave_requests.aggregate(day_by_status_pipeline))

    return render_template(
        "report.html",
        status_reports=status_reports,
        employee_reports=employee_reports,
        day_status_reports=day_status_reports
    )


@app.route("/performance")
@login_required
@role_required("hr", "manager")
def performance():
    data = list(performance_reviews.find().sort("nam", -1))
    return render_template("performance.html", reviews=data)


if __name__ == "__main__":
    app.run(debug=True)
