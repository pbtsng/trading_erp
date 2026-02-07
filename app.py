from flask import Flask,render_template,request,redirect,session,jsonify
import sqlite3
from werkzeug.security import generate_password_hash,check_password_hash

app = Flask(__name__)
app.secret_key="secret"
DB="database/trading.db"

def db():
    return sqlite3.connect(DB)

# ---------------- LOGIN ----------------

@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db()
        u=con.execute("SELECT * FROM users_mast WHERE username=?",
                      (request.form["username"],)).fetchone()
        if u and check_password_hash(u[2],request.form["password"]):
            session["user"]=u[0]
            session["role"]=u[3]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ---------------- ACCOUNT MASTER ----------------

@app.route("/accounts",methods=["GET","POST"])
def accounts():
    if session.get("role") not in ["admin","manager"]:
        return redirect("/dashboard")

    con=db()
    if request.method=="POST":
        con.execute(
            "INSERT INTO acc_mast(acc_name,acc_type) VALUES (?,?)",
            (request.form["name"],request.form["type"])
        )
        con.commit()

    rows=con.execute("SELECT * FROM acc_mast").fetchall()
    return render_template("accounts.html",rows=rows)

# ---------------- ITEM MASTER ----------------

@app.route("/items",methods=["GET","POST"])
def items():
    if session.get("role") not in ["admin","manager"]:
        return redirect("/dashboard")

    con=db()
    if request.method=="POST":
        con.execute(
            "INSERT INTO item_mast(item_name) VALUES (?)",
            (request.form["name"],)
        )
        con.commit()

    rows=con.execute("SELECT * FROM item_mast").fetchall()
    return render_template("items.html",rows=rows)

# ---------------- SALE ORDER ----------------

@app.route("/sale",methods=["GET","POST"])
def sale():
    con=db()

    if request.method=="POST":

        qty=float(request.form["qty"])
        rate=float(request.form["rate"])
        amt=qty*rate

        # ---------- CUSTOMER ----------
        if request.form["acc_id"]:
            acc_id = request.form["acc_id"]
        else:
            name = request.form["customer_name"].strip()

            row = con.execute(
                "SELECT acc_id FROM acc_mast WHERE acc_name=?",
                (name,)
            ).fetchone()

            if row:
                acc_id = row[0]
            else:
                cur = con.execute(
                    "INSERT INTO acc_mast(acc_name,acc_type) VALUES (?,?)",
                    (name,"Customer")
                )
                acc_id = cur.lastrowid

        # ---------- ITEM ----------
        if request.form["item_id"]:
            item_id = request.form["item_id"]
        else:
            iname = request.form["item_name"].strip()

            row = con.execute(
                "SELECT item_id FROM item_mast WHERE item_name=?",
                (iname,)
            ).fetchone()

            if row:
                item_id = row[0]
            else:
                cur = con.execute(
                    "INSERT INTO item_mast(item_name) VALUES (?)",
                    (iname,)
                )
                item_id = cur.lastrowid

        con.execute("""
        INSERT INTO sale_orders
        (so_date,acc_id,item_id,qty,rate,amount,user_code)
        VALUES (?,?,?,?,?,?,?)
        """,(request.form["date"],
             acc_id,
             item_id,
             qty,rate,amt,session["user"]))

        con.commit()

    customers=con.execute(
        "SELECT * FROM acc_mast WHERE acc_type='Customer'"
    ).fetchall()

    items=con.execute("SELECT * FROM item_mast").fetchall()

    rows=con.execute("""
    SELECT so_id,so_date,acc_name,item_name,qty,rate,amount
    FROM sale_orders
    JOIN acc_mast ON sale_orders.acc_id = acc_mast.acc_id
    JOIN item_mast ON sale_orders.item_id = item_mast.item_id
    """).fetchall()

    return render_template("sale_order.html",
                           customers=customers,
                           items=items,
                           rows=rows)


# ---------------- PURCHASE ORDER ----------------

@app.route("/purchase",methods=["GET","POST"])
def purchase():
    con=db()

    if request.method=="POST":

        qty=float(request.form["qty"])
        rate=float(request.form["rate"])
        amt=qty*rate

        # ---------- SUPPLIER ----------
        if request.form["acc_id"]:
            acc_id = request.form["acc_id"]
        else:
            name = request.form["supplier_name"].strip()

            row = con.execute(
                "SELECT acc_id FROM acc_mast WHERE acc_name=?",
                (name,)
            ).fetchone()

            if row:
                acc_id = row[0]
            else:
                cur = con.execute(
                    "INSERT INTO acc_mast(acc_name,acc_type) VALUES (?,?)",
                    (name,"Supplier")
                )
                acc_id = cur.lastrowid

        # ---------- ITEM ----------
        if request.form["item_id"]:
            item_id = request.form["item_id"]
        else:
            iname = request.form["item_name"].strip()

            row = con.execute(
                "SELECT item_id FROM item_mast WHERE item_name=?",
                (iname,)
            ).fetchone()

            if row:
                item_id = row[0]
            else:
                cur = con.execute(
                    "INSERT INTO item_mast(item_name) VALUES (?)",
                    (iname,)
                )
                item_id = cur.lastrowid

        con.execute("""
        INSERT INTO purchase_orders
        (po_date,acc_id,item_id,qty,rate,amount,user_code)
        VALUES (?,?,?,?,?,?,?)
        """,(request.form["date"],
             acc_id,
             item_id,
             qty,rate,amt,session["user"]))

        con.commit()

    suppliers=con.execute(
        "SELECT * FROM acc_mast WHERE acc_type='Supplier'"
    ).fetchall()

    items=con.execute("SELECT * FROM item_mast").fetchall()

    rows=con.execute("""
    SELECT po_id,po_date,acc_name,item_name,qty,rate,amount
    FROM purchase_orders
    JOIN acc_mast ON purchase_orders.acc_id = acc_mast.acc_id
    JOIN item_mast ON purchase_orders.item_id = item_mast.item_id
    """).fetchall()

    return render_template("purchase_order.html",
                           suppliers=suppliers,
                           items=items,
                           rows=rows)
# ---------------- add_account ----------------

@app.route("/add_account", methods=["POST"])
def add_account():
    name = request.form["name"]
    atype = request.form["type"]
    mobile = request.form.get("mobile")
    pan = request.form.get("pan")
    gstin = request.form.get("gstin")
    address = request.form.get("address")
    city = request.form.get("city")
    state = request.form.get("state")

    con = db()

    row = con.execute(
        "SELECT acc_id FROM acc_mast WHERE acc_name=?",
        (name,)
    ).fetchone()

    if not row:
        con.execute("""
        INSERT INTO acc_mast
        (acc_name,acc_type,mobile,pan,gstin,address,city,state)
        VALUES (?,?,?,?,?,?,?,?)
        """,(name,atype,mobile,pan,gstin,address,city,state))
        con.commit()

    return redirect(request.referrer)


# ---------------- PURCHASE ORDER ----------------

@app.route("/add_item", methods=["POST"])
def add_item():
    name = request.form["name"]

    con = db()

    row = con.execute(
        "SELECT item_id FROM item_mast WHERE item_name=?",
        (name,)
    ).fetchone()

    if not row:
        con.execute(
            "INSERT INTO item_mast(item_name) VALUES (?)",
            (name,)
        )
        con.commit()

    return redirect(request.referrer)

# ---------------- Loading Advice ----------------

@app.route("/loading_advice",methods=["GET","POST"])
def loading_advice():

    con=db()

    if request.method=="POST":

        cur = con.execute("""
        INSERT INTO loading_advice_head
        (la_date,vehicle_no,user_code)
        VALUES (?,?,?)
        """,(request.form["date"],
             request.form["vehicle"],
             session["user"]))

        la_id = cur.lastrowid

        so_ids   = request.form.getlist("so_id")
        po_ids   = request.form.getlist("po_id")
        items    = request.form.getlist("item")
        sections = request.form.getlist("section")
        batchs   = request.form.getlist("batch")
        qtys     = request.form.getlist("qty")

        for i in range(len(qtys)):

            if qtys[i]=="":
                continue

            qty=float(qtys[i])

            srate = con.execute(
                "SELECT rate FROM sale_orders WHERE so_id=?",
                (so_ids[i],)
            ).fetchone()[0]

            prate = con.execute(
                "SELECT rate FROM purchase_orders WHERE po_id=?",
                (po_ids[i],)
            ).fetchone()[0]

            amt = qty * srate
            diff = srate-prate

            con.execute("""
            INSERT INTO loading_advice_body
            (la_id,so_id,po_id,item_name,section,part,
             qty,purchase_rate,sale_rate,rate_diff,amount)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,(la_id,so_ids[i],po_ids[i],
                 items[i],sections[i],batchs[i],
                 qty,prate,srate,diff,amt))

            con.execute("""
            UPDATE sale_orders
            SET supplied_qty = supplied_qty + ?
            WHERE so_id=?
            """,(qty,so_ids[i]))

            con.execute("""
            UPDATE purchase_orders
            SET supplied_qty = supplied_qty + ?
            WHERE po_id=?
            """,(qty,po_ids[i]))

        con.commit()

    sales = con.execute("""
        SELECT so_id FROM sale_orders
        WHERE qty-supplied_qty>0
    """).fetchall()

    purchases = con.execute("""
        SELECT po_id FROM purchase_orders
        WHERE qty-supplied_qty>0
    """).fetchall()

    return render_template("loading_advice.html",
        sales=sales,
        purchases=purchases)

@app.route("/get_so/<int:so_id>")
def get_so(so_id):
    con = db()
    row = con.execute("""
        SELECT s.so_id,a.acc_name,s.qty,s.supplied_qty,s.rate
        FROM sale_orders s
        JOIN acc_mast a ON s.acc_id=a.acc_id
        WHERE s.so_id=?
    """,(so_id,)).fetchone()

    if row:
        return jsonify({
            "customer": row[1],
            "balance": row[2]-row[3],
            "rate": row[4]
        })
    return jsonify({})
@app.route("/get_po/<int:po_id>")
def get_po(po_id):
    con = db()
    row = con.execute("""
        SELECT p.po_id,a.acc_name,p.qty,p.supplied_qty,p.rate,i.item_name
        FROM purchase_orders p
        JOIN acc_mast a ON p.acc_id=a.acc_id
        JOIN item_mast i ON p.item_id=i.item_id
        WHERE p.po_id=?
    """,(po_id,)).fetchone()

    if row:
        return jsonify({
            "supplier": row[1],
            "balance": row[2]-row[3],
            "rate": row[4],
            "item": row[5]
        })
    return jsonify({})


if __name__=="__main__":
    app.run(host="192.168.1.20", port=5000)
